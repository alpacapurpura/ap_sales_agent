"""CopilotOrchestrator — Manages conversation state and streams responses via SSE.

# [COPILOT-SSE-V2] -> docs/domains/copilot/sse-protocol.md
# [COPILOT-CITATION-BLOCK] -> docs/domains/copilot/message-blocks.md
# [COPILOT-SSE-V2-ONLY-F8] -> docs/domains/copilot/redesign-2026-04/phases/F8-routing-cost-optim.md

After F8 §5.4 the orchestrator emits **only** v2 block events
(block_start / block_delta / block_end / block_append +
message_start / message_end + tool_start / tool_result + status / done /
error). The legacy ``text_chunk`` event was removed once the FE migrated
in F8 §5.5.

After F8 §5.3 the deep-agent harness is the only graph the orchestrator
runs — the legacy ReAct ``copilot_graph`` and its
``COPILOT_DEEP_AGENT_V2`` flag have both been deleted.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import structlog
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from src.core.context import set_conversation_id
from src.core.database import redis_client
from src.core.enums import ModelRole
from src.modules.assets.application.asset_extraction_service import (
    AssetExtractionService,
)
from src.modules.assets.infrastructure.repositories.asset_repository import (
    AssetRepository,
)
from src.modules.copilot.api.dto import ClientContextDTO, SSEEvent
from src.modules.copilot.application.extraction.active_job_state import load_active_job
from src.modules.copilot.application.guided.state import load_guided_state
from src.modules.copilot.application.observability import trace_recorder
from src.modules.copilot.application.observability.node_trace import (
    emit_node_trace_event,
)
from src.modules.copilot.application.orchestrator.deep_agent import (
    build_deep_agent_graph,
)
from src.modules.copilot.application.orchestrator.output_sanitizer import (
    sanitize_assistant_text,
)
from src.modules.copilot.application.orchestrator.state import (
    create_initial_copilot_state,
)
from src.modules.copilot.application.orchestrator.usage_tracking import UsageAccumulator
from src.modules.copilot.application.router import (
    RoutingRequest,
    build_default_router,
)
from src.modules.copilot.application.tools.registry import get_tools_for_context
from src.modules.copilot.infrastructure.repositories.conversation_repository import (
    ConversationRepository,
)
from src.modules.copilot.infrastructure.repositories.routing_log_repository import (
    RoutingLogRepository,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.orm import Session

    from src.modules.copilot.application.router import ModelRouter
    from src.modules.copilot.infrastructure.models.conversation_model import (
        CopilotConversationModel,
    )

logger = structlog.get_logger()

# Redis key prefix for active conversation context (TTL 1h)
REDIS_CONV_PREFIX = "copilot:conv:"
REDIS_CONV_TTL = 3600

# [COPILOT-DOC-HINT-LAYER] → docs/domains/copilot/asset-lifecycle.md
#
# Small docs are inlined; large docs emit a hint and rely on the
# ``read_document`` tool. This avoids blowing context for adjuntos that
# the user attached "for reference" but doesn't actually need reasoned over.
INLINE_DOCUMENT_THRESHOLD = 1800


def _doc_hint(
    *,
    asset_id: UUID,
    filename: str,
    summary: str | None,
    total_chars: int,
) -> str:
    """Emit a compact hint so the LLM knows an asset exists without spending tokens on it."""
    summary_line = (summary or "Sin resumen disponible todavía.").strip()
    return (
        f"[Documento adjunto: {filename}]\n"
        f"asset_id: {asset_id}\n"
        f"resumen: {summary_line}\n"
        f"tamaño: {total_chars} caracteres\n"
        "Si necesitas su contenido, llama a la herramienta `read_document` "
        "con ese asset_id (opcionalmente con una query para buscar dentro).\n"
        "[/Documento adjunto]"
    )


def _doc_inline(*, filename: str, asset_id: UUID, text: str) -> str:
    """Verbatim inline for small docs — includes asset_id for re-reference."""
    return f"[Documento adjunto: {filename} (asset_id: {asset_id})]\n{text}\n[/Documento adjunto]"


def _render_document_block(
    block: dict,
    *,
    repo: AssetRepository,
    db: Session,
    tenant_id: UUID,
) -> str | None:
    """Return the context chunk for a ``document`` block.

    Small docs inlined verbatim; large docs hinted (summary + asset_id).
    Extraction is triggered on demand if the asset hasn't been processed
    yet — this makes the flow robust against uploads where the background
    extractor hasn't finished.
    """
    asset_id_raw = block.get("asset_id")
    filename = block.get("filename") or "documento"
    try:
        asset_uuid = UUID(str(asset_id_raw))
    except (ValueError, TypeError):
        logger.warning("copilot_chat_attachment_bad_asset_id", asset_id=asset_id_raw)
        return None

    asset = repo.get_by_id(asset_uuid, tenant_id=tenant_id)
    if not asset:
        logger.warning("copilot_chat_attachment_asset_missing", asset_id=str(asset_uuid))
        return None

    # Trigger extraction if pending — idempotent.
    if asset.extraction_status not in ("extracted", "skipped", "failed"):
        try:
            refreshed = AssetExtractionService(db).ensure_extracted(
                asset_uuid,
                tenant_id=tenant_id,
            )
            if refreshed is not None:
                asset = refreshed
        except Exception:
            logger.exception(
                "copilot_chat_attachment_extract_failed",
                asset_id=str(asset_uuid),
            )

    extracted = (asset.extracted_text or "").strip()
    total_chars = len(extracted)

    if extracted and total_chars <= INLINE_DOCUMENT_THRESHOLD:
        return _doc_inline(filename=filename, asset_id=asset.id, text=extracted)

    # No extracted text yet, or too large — emit a hint pointing at read_document.
    return _doc_hint(
        asset_id=asset.id,
        filename=filename,
        summary=asset.extracted_summary,
        total_chars=total_chars,
    )


def _render_attachment_context(
    blocks: list[dict] | None,
    *,
    tenant_id: UUID,
    db: Session,
) -> str:
    """Materialize user-supplied attachment blocks into plain text the LLM can reason over."""
    if not blocks:
        return ""

    repo = AssetRepository(db)

    sections: list[str] = []
    for block in blocks:
        btype = block.get("type")
        if btype == "document":
            rendered = _render_document_block(block, repo=repo, db=db, tenant_id=tenant_id)
            if rendered:
                sections.append(rendered)
        elif btype == "audio":
            transcript = str(block.get("transcript") or "").strip()
            sections.append(
                f"[Audio adjunto — transcripción]\n{transcript}\n[/Audio adjunto]"
                if transcript
                else "[Audio adjunto sin transcripción disponible.]"
            )
        elif btype == "image":
            alt = block.get("alt") or block.get("filename") or block.get("url") or "imagen"
            sections.append(f"[Imagen adjunta: {alt}]")
        elif btype == "video":
            ref = block.get("filename") or block.get("url") or "video"
            sections.append(f"[Video adjunto: {ref}]")

    return "\n\n".join(sections)


# ── Tool → Block adapters ──────────────────────────────────────────────────────
# Registration + handlers live in block_adapters.py (SSoT). Adding a new
# block-emitting tool does NOT require editing this file.

from src.modules.copilot.application.orchestrator.block_adapters import (
    tool_result_to_blocks as _tool_result_to_block,
)

_TYPE_TO_CARD_KIND: dict[str, str] = {
    "proposal": "proposal",
    "alternatives_card": "alternatives",
    "alternatives": "alternatives",
    "clarify": "clarify",
    "clarify_card": "clarify",
    "checkpoint": "checkpoint",
    "interview_complete": "interview_complete",
    "metric_summary": "metric_summary",
    "comparison": "comparison",
    "checklist": "checklist",
    "multi_option": "multi_option",
    "navigation": "navigation",
}
"""Map from UIAction.type → CardBlock.card_kind (CONTRACT-MULTIMODAL §6)."""


def _ui_action_to_card_block(action: dict) -> dict | None:
    """Wrap a UIAction dict as a CardBlock dict for SSE v2.

    Only wraps action types that map to known card_kind values.
    Unknown types → None (emit only legacy ui_action, no block).

    Payload shape is validated against
    ``copilot.domain.card_payloads.CARD_PAYLOAD_MODELS`` in warn-only mode:
    a mismatch logs a structured warning but the card is still emitted so
    the frontend can degrade gracefully instead of blanking on LLM drift.

    CONTRACT reference: CONTRACT-MULTIMODAL §6 (ui_action → CardBlock).
    """
    action_type = str(action.get("type", ""))
    card_kind = _TYPE_TO_CARD_KIND.get(action_type)
    if not card_kind:
        return None

    from src.modules.copilot.domain.card_payloads import validate_card_payload

    ok, err = validate_card_payload(card_kind, action)
    if not ok:
        logger.warning(
            "card_payload_schema_mismatch",
            card_kind=card_kind,
            action_type=action_type,
            error=err,
        )

    return {
        "id": str(uuid4()),
        "type": "card",
        "card_kind": card_kind,
        "payload": action,
        "status": "pending",
    }


def _write_todos_to_plan_card(tool_input: object) -> dict | None:
    """Synthesize a ``plan_card`` block from the deep-agent ``write_todos`` args.

    The deepagents ``write_todos`` tool stores ``state.todos`` and returns a
    ToolMessage with a stringified todo list — too lossy to round-trip.
    Instead we read the *input args* of the tool call (``{"todos": [...]}``),
    where each Todo carries ``{content, status, activeForm?}``.

    Returns ``None`` for malformed inputs so the caller falls back to the
    legacy ``tool_result`` path without breaking the stream.
    """
    if not isinstance(tool_input, dict):
        return None
    raw_todos = tool_input.get("todos")
    if not isinstance(raw_todos, list) or not raw_todos:
        return None
    normalized: list[dict] = []
    for item in raw_todos:
        if not isinstance(item, dict):
            continue
        content = str(item.get("content", "")).strip()
        if not content:
            continue
        status = str(item.get("status", "pending")).lower()
        if status not in {"pending", "in_progress", "completed"}:
            status = "pending"
        normalized.append(
            {
                "content": content,
                "status": status,
                "active_form": str(item.get("activeForm") or item.get("active_form") or "").strip(),
            },
        )
    if not normalized:
        return None
    return {
        "id": str(uuid4()),
        "type": "card",
        "card_kind": "plan_card",
        "payload": {"todos": normalized},
        "status": "pending",
    }


# LLM streaming timeout (seconds). If the LLM hangs, the SSE stream will
# emit an error event after this duration instead of blocking indefinitely.
# Configurable via env var COPILOT_STREAM_TIMEOUT_SECONDS.
COPILOT_STREAM_TIMEOUT_SECONDS: int = int(
    os.environ.get("COPILOT_STREAM_TIMEOUT_SECONDS", "60"),
)

_TRACE_PREVIEW_CHARS = 2_000


# [COPILOT-ROUTING-WIRE-F11] -> docs/domains/copilot/redesign-2026-04/learnings/F11-housekeeping.md
#
# Single ``ModelRouter`` shared across requests. ``build_default_router`` is
# pure construction (no I/O) but resolves NANO settings each call — keep one
# instance per process. The LLMClassifier inside is stateless + lazy on its
# LLM resolver, so concurrent requests are safe. List-as-cell avoids the
# `global` statement (PLW0603) — mutating a module-level container is fine.
_DEFAULT_ROUTER_CELL: list[ModelRouter] = []


def _get_default_router() -> ModelRouter:
    """Lazy module singleton. Avoids construction on import (test isolation)."""
    if not _DEFAULT_ROUTER_CELL:
        _DEFAULT_ROUTER_CELL.append(build_default_router())
    return _DEFAULT_ROUTER_CELL[0]


def _truncate_for_trace(value: object) -> object:
    """Shorten long strings + dicts for the trace ``data`` payload.

    Keeps observability writes bounded without losing the head of a payload,
    which is almost always enough for "why did this tool return X?" style
    debugging.
    """
    if isinstance(value, str):
        if len(value) > _TRACE_PREVIEW_CHARS:
            return value[:_TRACE_PREVIEW_CHARS] + " [truncated]"
        return value
    if isinstance(value, dict):
        try:
            serialised = json.dumps(value, default=str)
        except (TypeError, ValueError):
            return {"__repr__": repr(value)[:_TRACE_PREVIEW_CHARS]}
        if len(serialised) > _TRACE_PREVIEW_CHARS:
            return {
                "__truncated__": True,
                "preview": serialised[:_TRACE_PREVIEW_CHARS],
            }
        return value
    return value


def _sanitize_ai_messages(messages: list) -> list:
    """Strip JSON blocks from every AIMessage.content in the list.

    Invoked just before persistence so the chat history stays clean even
    when the LLM ignores the "no JSON in chat" prompt rule. Non-AIMessage
    entries pass through untouched.
    """
    cleaned: list = []
    for msg in messages:
        if isinstance(msg, AIMessage) and isinstance(msg.content, str) and msg.content:
            new_content = sanitize_assistant_text(msg.content)
            if new_content != msg.content:
                # Preserve tool_calls and any additional_kwargs; only rewrite content.
                cleaned.append(
                    AIMessage(
                        content=new_content,
                        additional_kwargs=msg.additional_kwargs,
                        response_metadata=msg.response_metadata,
                        tool_calls=getattr(msg, "tool_calls", []),
                        id=msg.id,
                    ),
                )
                continue
        cleaned.append(msg)
    return cleaned


def _build_turn_end_data(*, usage: UsageAccumulator, acc: _StreamAccumulator) -> dict:
    """Build the JSONB ``data`` payload for the ``turn_end`` trace event.

    Merges ``UsageAccumulator.as_log_dict()`` (model + prompt/completion/total
    tokens, cached_input_tokens, cache_hit_rate, cost_usd) with stream-shape
    fields the recorder needs (response length, message count, block count).

    Anchor: ``[COPILOT-CACHE-PREFIX-F8]``. Without these fields persisted on
    ``copilot_trace_event``, the F8 cache instrumentation never reaches the
    admin ``/copilot-routing`` dashboard or downstream cost reports.
    """
    return {
        **usage.as_log_dict(),
        "response_length": len(acc.full_response),
        "message_count": len(acc.messages),
        "block_count": len(acc.emitted_blocks),
    }


@dataclass
class _StreamAccumulator:
    """Mutable accumulator shared between stream_chat and _run_graph_stream."""

    full_response: str = ""
    messages: list = field(default_factory=list)
    last_tool_call_ids: dict[str, str] = field(default_factory=dict)
    emitted_blocks: list[dict] = field(default_factory=list)
    # v2 text block tracking
    text_block_id: str | None = None
    text_block_markdown: str = ""
    block_index: int = 0
    # Observability — populated by stream_chat, read by handlers for span
    # parenting. Kept here (not in CopilotState) so the trace span tree can
    # span the entire orchestrator call, including persistence.
    recorder: object | None = None


class CopilotOrchestrator:
    """Orchestrate the Copilot agent.

    Manage conversation state, persist history, and stream SSE events to the frontend.
    """

    def __init__(self, db: Session) -> None:
        """Initialize copilot orchestrator."""
        self.db = db
        self.conv_repo = ConversationRepository(db)

    def _build_client_context(self, context: ClientContextDTO | None) -> dict:
        """Build the graph-facing ``ClientContext`` dict from the incoming DTO.

        ``guided_mode`` is populated later, server-side, from
        ``copilot_conversations.procedure_state["guided"]`` — the frontend
        doesn't have to know whether guided mode is active for this
        conversation.
        """
        if not context:
            return {
                "current_route": None,
                "selected_fields": [],
                "form_data": {},
                "locale": "es",
            }
        return {
            "current_route": context.current_route,
            "selected_fields": [f.model_dump() if hasattr(f, "model_dump") else f for f in context.selected_fields],
            "form_data": context.form_data,
            "locale": context.locale,
        }

    def _read_procedure_state(
        self,
        conv_id: str | None,
        tenant_id: UUID | None,
    ) -> dict | None:
        """Single DB read of ``copilot_conversations.procedure_state`` JSONB.

        Tenant-scoped by rule ``tenant-isolation.md``: a missing ``tenant_id``
        or a conversation that belongs to another tenant returns ``None``.
        Callers parse the result with ``load_guided_state`` / ``load_active_job``
        to avoid hitting the connection pool twice per request.
        """
        if not conv_id or tenant_id is None:
            return None
        from sqlalchemy import text

        try:
            row = self.db.execute(
                text(
                    "SELECT procedure_state FROM copilot_conversations WHERE id = :id AND tenant_id = :tenant_id",
                ),
                {"id": conv_id, "tenant_id": str(tenant_id)},
            ).scalar()
        except Exception as exc:  # noqa: BLE001 — orchestrator resilience
            logger.warning(
                "procedure_state_read_failed",
                conv_id=conv_id,
                error=str(exc),
            )
            return None
        return row if isinstance(row, dict) else None

    def _prepare_conversation(
        self,
        *,
        user_id: UUID,
        tenant_id: UUID,
        message: str,
        conversation_id: str | None,
        context: ClientContextDTO | None,
        blocks: list[dict] | None = None,
    ) -> tuple[str, UUID, CopilotConversationModel, dict]:
        """Resolve/create conversation and build LangGraph state. Returns (conv_id, conv_uuid, existing_conv, state)."""
        conv_id = conversation_id or str(uuid.uuid4())
        conv_uuid = UUID(conv_id)

        existing_conv = self.conv_repo.get_by_id(conv_uuid, tenant_id, user_id)
        if not existing_conv:
            existing_conv = self.conv_repo.create(
                conversation_id=conv_uuid,
                tenant_id=tenant_id,
                user_id=user_id,
            )
            self.db.commit()

        client_ctx = self._build_client_context(context)

        # Hydrate guided + active-extraction state for this conversation with
        # a SINGLE DB read. Both flags live as sibling keys in the same JSONB
        # column (``procedure_state``) — one conversation can hold both
        # (guided paused while a URL scrape runs), only guided, only active
        # job, or neither (pure free-form chat). Two reads hit the connection
        # pool twice and doubled request latency for no reason.
        procedure_state = self._read_procedure_state(conv_id, tenant_id)
        guided = load_guided_state(procedure_state)
        active_job = load_active_job(procedure_state)
        client_ctx["guided_mode"] = guided is not None
        active_job_json = active_job.to_json() if active_job is not None else None
        client_ctx["active_extraction_job"] = active_job_json

        state = create_initial_copilot_state(
            user_id=user_id,
            tenant_id=tenant_id,
            conversation_id=conv_id,
            client_context=client_ctx,
        )
        state["guided_state"] = guided.to_json() if guided is not None else None
        state["active_extraction_job"] = active_job_json

        # Publish the conversation id so tools invoked by the LLM can persist
        # conversation-scoped state (e.g. guided progress) without receiving
        # it as an argument.
        set_conversation_id(conv_id)

        history_messages = self._load_history(conv_id, tenant_id, existing_conv)
        attachment_context = _render_attachment_context(blocks, tenant_id=tenant_id, db=self.db)
        user_content = message
        if attachment_context:
            user_content = f"{message.strip()}\n\n{attachment_context}" if message.strip() else attachment_context
        state["messages"] = [*history_messages, HumanMessage(content=user_content)]
        return conv_id, conv_uuid, existing_conv, state

    def _record_routing_decision(
        self,
        *,
        tenant_id: UUID,
        conversation_id: UUID,
        message_id: UUID,
        user_msg: str,
        state: dict,
        recorder: object | None,
        router: ModelRouter | None = None,
    ) -> None:
        """Persist a ``RoutingDecision`` for this turn (telemetry only).

        Wires F8 ``build_default_router`` into the runtime so
        ``copilot_routing_log`` populates and the admin Streamlit
        ``/copilot-routing`` shows real data. Failures here MUST NOT block
        the chat stream — log + skip + rollback so the conversation flow
        proceeds.

        ``router`` is injected for tests; production uses the module
        singleton via ``_get_default_router()``.
        """
        try:
            client_ctx = state.get("client_context", {}) or {}
            active_job = state.get("active_extraction_job")
            guided = bool(client_ctx.get("guided_mode"))
            procedure_active = guided or bool(active_job)
            mode = "procedure" if procedure_active else "chat"
            tools = get_tools_for_context(client_ctx)
            tools_count = len(tools)
            request = RoutingRequest(
                user_msg=user_msg,
                route=client_ctx.get("current_route"),
                mode=mode,
                available_tool_count=tools_count,
                procedure_active=procedure_active,
            )
            chosen_router = router if router is not None else _get_default_router()
            decision = chosen_router.select(request)
            confidence = float(decision.confidence) if decision.confidence is not None else None
            RoutingLogRepository(self.db).insert(
                tenant_id=tenant_id,
                conversation_id=conversation_id,
                message_id=message_id,
                tier_selected=decision.tier.value,
                classifier_used=decision.classifier_used.value,
                reason=decision.reason,
                confidence=confidence,
                user_msg_length=len(user_msg),
                tools_available=tools_count,
            )
            self.db.commit()
            if recorder is not None:
                recorder.record(
                    event_type="routing_decision",
                    name="model_router",
                    data={
                        "tier": decision.tier.value,
                        "classifier": decision.classifier_used.value,
                        "reason": decision.reason,
                        "confidence": confidence,
                        "available_tool_count": tools_count,
                        "procedure_active": procedure_active,
                    },
                )
        except Exception as exc:  # noqa: BLE001 — routing telemetry resilience
            import contextlib as _contextlib

            logger.warning(
                "routing_decision_failed",
                error=str(exc),
                error_type=type(exc).__name__,
            )
            with _contextlib.suppress(Exception):
                self.db.rollback()

    async def stream_chat(
        self,
        *,
        user_id: UUID,
        tenant_id: UUID,
        message: str,
        conversation_id: str | None = None,
        context: ClientContextDTO | None = None,
        blocks: list[dict] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Process a user message and yield SSE v2 events.

        Emits the canonical v2 stream
        (status / message_start / block_start / block_delta / block_end /
        block_append / tool_start / tool_result / ui_action / message_end /
        done / error). The legacy ``text_chunk`` channel was removed in
        F8 §5.4 once the FE migrated to the block_* render path.
        """
        conv_id, conv_uuid, existing_conv, state = self._prepare_conversation(
            user_id=user_id,
            tenant_id=tenant_id,
            message=message,
            conversation_id=conversation_id,
            context=context,
            blocks=blocks,
        )

        yield SSEEvent(event="status", data={"state": "thinking"}).to_sse()

        from src.core.config import settings as _settings

        usage = UsageAccumulator(model=_settings.get_model(ModelRole.AGENT))
        acc = _StreamAccumulator()

        # Open an observability turn envelope. Every LLM call / tool call /
        # card emission records against this recorder so one SQL query per
        # turn_id reconstructs the whole interaction timeline.
        recorder = trace_recorder.start(
            tenant_id=tenant_id,
            user_id=user_id,
            conversation_id=conv_uuid,
        )
        acc.recorder = recorder
        turn_start_ts = time.monotonic()
        recorder.record(
            event_type="turn_start",
            name="copilot_chat",
            data={
                "message_preview": message[:200],
                "current_route": state.get("client_context", {}).get("current_route"),
                "guided_mode": bool(state.get("client_context", {}).get("guided_mode")),
                "attachment_count": len(blocks or []),
            },
        )

        # F11.1: Pre-generate the assistant message id so the routing log row
        # references the same id as the message_start SSE event. Telemetry
        # only — failures must NOT block the stream.
        msg_id = str(uuid4())
        self._record_routing_decision(
            tenant_id=tenant_id,
            conversation_id=conv_uuid,
            message_id=UUID(msg_id),
            user_msg=message,
            state=state,
            recorder=recorder,
        )

        try:
            async for sse_str in self._run_graph_stream(
                state=state,
                usage=usage,
                acc=acc,
                msg_id=msg_id,
            ):
                yield sse_str
        except Exception as exc:
            recorder.record(
                event_type="error",
                name="stream_exception",
                status="error",
                data={
                    "error_type": type(exc).__name__,
                    "error_message": str(exc)[:500],
                },
            )
            raise

        usage.log(conversation_id=conv_id, tenant_id=str(tenant_id))

        # Sanitize AI messages before persistence: the sanitizer already ran
        # on acc.full_response when the last text block was finalized, but
        # _persist_messages serializes acc.messages (the raw LangGraph
        # pipeline state) — so any JSON blobs the LLM emitted survive unless
        # we strip them here too.
        acc.messages = _sanitize_ai_messages(acc.messages)

        self._persist_messages(
            conv_uuid,
            tenant_id,
            conv_id,
            message,
            acc.full_response,
            acc.messages,
            existing_conv,
            emitted_blocks=list(acc.emitted_blocks),
        )

        recorder.record(
            event_type="turn_end",
            name="copilot_chat",
            duration_ms=int((time.monotonic() - turn_start_ts) * 1000),
            data=_build_turn_end_data(usage=usage, acc=acc),
        )

        yield SSEEvent(event="status", data={"state": "done"}).to_sse()
        yield SSEEvent(event="done", data={"conversation_id": conv_id}).to_sse()

    async def _run_graph_stream(
        self,
        *,
        state: dict,
        usage: UsageAccumulator,
        acc: _StreamAccumulator,
        msg_id: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """Run the LangGraph stream and emit SSE events (v1 legacy + v2 blocks).

        Accumulates full_response, messages, and emitted_blocks into *acc*
        so that stream_chat can persist them after the generator exhausts.

        ``msg_id`` is the assistant message id — pre-generated by
        ``stream_chat`` so the routing log row (F11.1) and the
        ``message_start`` SSE event share the same uuid. Defaults to a fresh
        uuid for direct invocations / tests.
        """
        from src.shared.domain.datetime_utils import utc_now as _utc_now

        if msg_id is None:
            msg_id = str(uuid4())
        streaming_started_at = _utc_now()

        try:
            yield SSEEvent(event="status", data={"state": "streaming"}).to_sse()
            yield SSEEvent(
                event="message_start",
                data={
                    "message_id": msg_id,
                    "role": "assistant",
                    "created_at": streaming_started_at.isoformat(),
                },
            ).to_sse()

            async with asyncio.timeout(COPILOT_STREAM_TIMEOUT_SECONDS):
                graph = build_deep_agent_graph(state)
                async for event in graph.astream_events(state, version="v2"):
                    usage.update_from_event(event)
                    # F9 [COPILOT-NODE-TRACE-F9] — emit node_enter/node_exit for
                    # LangGraph transitions so admin trace reconstructs per-node timeline.
                    emit_node_trace_event(acc.recorder, event)

                    # on_tool_end: route to v2-aware handler that also emits block_append
                    if event.get("event") == "on_tool_end":
                        tool_sse = self._handle_tool_end_v2(
                            event,
                            acc.messages,
                            acc.last_tool_call_ids,
                            acc,
                            msg_id,
                        )
                        if tool_sse:
                            yield tool_sse
                        continue

                    sse, text_chunk = self._process_stream_event(
                        event,
                        acc.messages,
                        acc.last_tool_call_ids,
                    )
                    if text_chunk:
                        acc.full_response += text_chunk
                        async for block_sse in self._emit_text_chunk_v2(acc, msg_id, text_chunk):
                            yield block_sse
                    if sse:
                        yield sse

        except TimeoutError:
            logger.warning(
                "copilot_stream_timeout",
                timeout_seconds=COPILOT_STREAM_TIMEOUT_SECONDS,
                partial_response_length=len(acc.full_response),
            )
            yield SSEEvent(
                event="error",
                data={
                    "message": (
                        "La respuesta del asistente excedió el tiempo limite. "
                        "Tu mensaje parcial se ha conservado. Intenta de nuevo."
                    ),
                },
            ).to_sse()

        except Exception as e:
            logger.exception("copilot_stream_error", error=str(e))
            yield SSEEvent(
                event="error",
                data={"message": "Ocurrio un error procesando tu mensaje. Intenta de nuevo."},
            ).to_sse()
            acc.full_response = ""
            acc.messages = []
            return

        # Finalize v2 text block. The sanitizer is the last line of defense
        # against the LLM ignoring the "no JSON in chat" prompt rule — it
        # strips raw code-fenced payloads so the persisted message and the
        # FE's final render stay clean, even if streamed deltas briefly
        # flashed the JSON on the client.
        if acc.text_block_id is not None:
            sanitized_markdown = sanitize_assistant_text(acc.text_block_markdown)
            acc.text_block_markdown = sanitized_markdown
            acc.full_response = sanitized_markdown
            final_text_block: dict = {
                "id": acc.text_block_id,
                "type": "text",
                "markdown": sanitized_markdown,
            }
            yield SSEEvent(
                event="block_end",
                data={
                    "message_id": msg_id,
                    "block_id": acc.text_block_id,
                    "final": final_text_block,
                },
            ).to_sse()
            acc.emitted_blocks.append(final_text_block)

        tokens_used = getattr(usage, "total_tokens", None)
        yield SSEEvent(
            event="message_end",
            data={
                "message_id": msg_id,
                "status": "sent",
                "tokens_used": tokens_used,
                "blocks": acc.emitted_blocks,
            },
        ).to_sse()

    @staticmethod
    async def _emit_text_chunk_v2(
        acc: _StreamAccumulator,
        msg_id: str,
        text_chunk: str,
    ) -> AsyncGenerator[str, None]:
        """Emit block_start (first chunk) + block_delta for a text chunk (v2)."""
        if acc.text_block_id is None:
            acc.text_block_id = str(uuid4())
            acc.text_block_markdown = ""
            yield SSEEvent(
                event="block_start",
                data={
                    "message_id": msg_id,
                    "block_id": acc.text_block_id,
                    "type": "text",
                    "index": acc.block_index,
                    "partial": {
                        "id": acc.text_block_id,
                        "type": "text",
                        "markdown": "",
                    },
                },
            ).to_sse()

        acc.text_block_markdown += text_chunk
        yield SSEEvent(
            event="block_delta",
            data={
                "message_id": msg_id,
                "block_id": acc.text_block_id,
                "delta": {"markdown": text_chunk},
            },
        ).to_sse()

    def _process_stream_event(
        self,
        event: dict,
        accumulated_messages: list,
        last_tool_call_ids: dict[str, str],
    ) -> tuple[str | None, str | None]:
        """Process a single LangGraph stream event.

        Returns (sse_string | None, text_chunk | None).

        sse_string: zero or more SSE event strings concatenated. The caller
            yields this directly. For tool events it is
            tool_start/tool_result/ui_action. F8 §5.4 — the legacy
            ``text_chunk`` SSE was removed; the v2 ``block_delta`` family
            is now the only render path.

        text_chunk: raw text content when the LLM emitted a streaming token.
            The caller uses this to build the v2 ``block_delta`` events.
        """
        kind = event.get("event")

        if kind == "on_chat_model_stream":
            chunk = event.get("data", {}).get("chunk")
            if chunk and hasattr(chunk, "content") and chunk.content:
                # v2 block_delta is built by the caller from the returned
                # text chunk. No SSE frame is emitted at this stage — the
                # block lifecycle (block_start / block_delta / block_end)
                # is owned by ``_emit_text_chunk_v2`` and the finaliser.
                return None, chunk.content
            return None, None

        if kind == "on_chat_model_end":
            output = event.get("data", {}).get("output")
            if isinstance(output, AIMessage):
                accumulated_messages.append(output)
                if output.tool_calls:
                    for tc in output.tool_calls:
                        last_tool_call_ids[tc["name"]] = tc["id"]
            return None, None

        if kind == "on_tool_start":
            tool_name = event.get("name", "unknown")
            tool_input = event.get("data", {}).get("input", {})
            return (
                SSEEvent(
                    event="tool_start",
                    data={"tool": tool_name, "args": tool_input},
                ).to_sse(),
                None,
            )

        if kind == "on_tool_end":
            return self._handle_tool_end(
                event,
                accumulated_messages,
                last_tool_call_ids,
            ), None

        return None, None

    def _handle_tool_end(
        self,
        event: dict,
        accumulated_messages: list,
        last_tool_call_ids: dict[str, str],
    ) -> str:
        """Handle on_tool_end event: capture ToolMessage and emit SSE events."""
        tool_name = event.get("name", "unknown")
        tool_output = event.get("data", {}).get("output", "")

        if isinstance(tool_output, ToolMessage):
            accumulated_messages.append(tool_output)
        elif isinstance(tool_output, str):
            tool_call_id = last_tool_call_ids.pop(tool_name, "")
            accumulated_messages.append(
                ToolMessage(
                    content=tool_output,
                    name=tool_name,
                    tool_call_id=tool_call_id,
                ),
            )

        # Cap at 4 KB (matches trace recorder MAX_PAYLOAD_CHARS). Enough to
        # carry the full AsyncToolJob dispatch JSON — job_id, poll_endpoint,
        # module, scope, mode, target_label_es, etc. — which the frontend must
        # parse to register polling for extraction tools. The previous 500-char
        # cap truncated that payload and broke the chip/badge/summary pipeline.
        result_sse = SSEEvent(
            event="tool_result",
            data={"tool": tool_name, "result": str(tool_output)[:4000]},
        ).to_sse()

        # If tool result contains a ui_action, emit it
        parsed = tool_output if isinstance(tool_output, dict) else None
        if not parsed and isinstance(tool_output, str):
            try:
                parsed = json.loads(tool_output)
            except (json.JSONDecodeError, ValueError):
                parsed = None

        if isinstance(parsed, dict) and "ui_action" in parsed:
            result_sse += SSEEvent(event="ui_action", data=parsed["ui_action"]).to_sse()

        return result_sse

    @staticmethod
    def _maybe_emit_plan_card(
        tool_name: str,
        tool_input: object,
        msg_id: str,
        acc: _StreamAccumulator,
    ) -> str:
        """Synthesize + emit a ``plan_card`` block when ``write_todos`` ran.

        Deep-agent ``write_todos`` mutates state.todos but emits no
        ``ui_action`` payload, so the existing card pipeline never sees
        it. We tap the tool *args* (always populated for that call) to
        build a typed card block and reuse the existing ``block_append``
        + trace ``card_emitted`` plumbing.

        # [COPILOT-DEEP-AGENT-V2] -> docs/domains/copilot/redesign-2026-04/phases/F2-deep-agents-harness.md
        """
        if tool_name != "write_todos":
            return ""
        plan_card = _write_todos_to_plan_card(tool_input)
        if plan_card is None:
            return ""
        sse = SSEEvent(
            event="block_append",
            data={"message_id": msg_id, "block": plan_card},
        ).to_sse()
        acc.emitted_blocks.append(plan_card)
        if acc.recorder is not None:
            acc.recorder.record(
                event_type="card_emitted",
                name="plan_card",
                data={
                    "card_kind": "plan_card",
                    "source_tool": tool_name,
                    "todo_count": len(plan_card["payload"]["todos"]),
                },
            )
        return sse

    def _handle_tool_end_v2(
        self,
        event: dict,
        accumulated_messages: list,
        last_tool_call_ids: dict[str, str],
        acc: _StreamAccumulator,
        msg_id: str,
    ) -> str:
        """Handle on_tool_end: legacy events + v2 block_append events.

        Extends _handle_tool_end with SSE v2 block_append emission for tools
        that map to canonical MessageBlock types (CONTRACT-MULTIMODAL §6, §8, §10).

        # [COPILOT-SSE-V2] → docs/domains/copilot/sse-protocol.md
        # [COPILOT-CITATION-BLOCK] → docs/domains/copilot/message-blocks.md §citation
        # [COPILOT-OUTBOUND-ASSETS] → docs/domains/copilot/outbound-assets.md

        Two SSE channels per tool call:
        - ``tool_result`` + ``ui_action`` (delegated to ``_handle_tool_end``)
          — generic side-channel events the FE uses for plain-text tool
          status + lightweight UI affordances. Always emitted.
        - ``block_append`` — emits a typed v2 ``MessageBlock`` for tools
          that map to canonical block types (citations, documents, cards).
          Non-text blocks (image/audio/citation/card) are atomic — no
          streaming deltas. They use ``block_append`` (not
          block_start/end) because they appear as tool results, not as
          the primary streaming content. FE appends them to the message
          blocks list.
        """
        tool_name = event.get("name", "unknown")
        tool_output = event.get("data", {}).get("output", "")
        tool_input = event.get("data", {}).get("input", {})

        # Step 1 — emit tool_result + ui_action via the legacy-format handler.
        result_sse = self._handle_tool_end(event, accumulated_messages, last_tool_call_ids)

        # Step 2 — attempt v2 block_append for mapped tools
        blocks = _tool_result_to_block(tool_name, tool_output)
        if blocks is not None:
            for block in blocks:
                result_sse += SSEEvent(
                    event="block_append",
                    data={"message_id": msg_id, "block": block},
                ).to_sse()
                acc.emitted_blocks.append(block)

        # Step 3 — ui_action → CardBlock (v2 wrap, in addition to legacy ui_action)
        # Check if tool output has ui_action that wasn't already wrapped
        parsed_output: dict | None = None
        if isinstance(tool_output, dict):
            parsed_output = tool_output
        elif isinstance(tool_output, str):
            try:
                parsed_output = json.loads(tool_output)
            except (json.JSONDecodeError, ValueError):
                parsed_output = None

        if isinstance(parsed_output, dict) and "ui_action" in parsed_output:
            action = parsed_output["ui_action"]
            card_block = _ui_action_to_card_block(action)
            if card_block:
                result_sse += SSEEvent(
                    event="block_append",
                    data={"message_id": msg_id, "block": card_block},
                ).to_sse()
                acc.emitted_blocks.append(card_block)
                if acc.recorder is not None:
                    acc.recorder.record(
                        event_type="card_emitted",
                        name=card_block.get("card_kind") or "card",
                        data={
                            "card_kind": card_block.get("card_kind"),
                            "source_tool": tool_name,
                            "payload_keys": list(action.keys()) if isinstance(action, dict) else [],
                        },
                    )

        # Step 3.5 — F2 plan_card from deep-agent ``write_todos`` (helper).
        result_sse += self._maybe_emit_plan_card(tool_name, tool_input, msg_id, acc)

        # Step 4 — persist a tool_call trace row so debugging is SQL-queryable.
        if acc.recorder is not None:
            tool_status = "ok"
            if isinstance(parsed_output, dict) and parsed_output.get("status") == "error":
                tool_status = "error"
            output_preview = tool_output if isinstance(tool_output, str) else json.dumps(tool_output, default=str)
            acc.recorder.record(
                event_type="tool_call",
                name=tool_name,
                status=tool_status,
                data={
                    "args": _truncate_for_trace(tool_input),
                    "output_preview": _truncate_for_trace(output_preview),
                },
            )

        return result_sse

    def _persist_messages(
        self,
        conv_uuid: UUID,
        tenant_id: UUID,
        conv_id: str,
        message: str,
        full_response: str,
        accumulated_messages: list,
        existing_conv: CopilotConversationModel,
        *,
        emitted_blocks: list[dict] | None = None,
    ) -> None:
        """Persist conversation messages to DB and Redis cache.

        ``emitted_blocks`` carries the canonical MessageBlock dicts produced
        during streaming (text block finalization, card blocks, tool-result
        blocks). They are attached to the LAST assistant message so that a
        post-stream refetch of ``/copilot/conversations/{id}`` rebuilds the
        same visual state — previously cards evaporated after the React
        Query invalidation because the serializer only kept role+content.
        """
        if not full_response and not accumulated_messages:
            return

        new_messages = self._serialize_messages(
            [HumanMessage(content=message), *accumulated_messages],
        )
        # Fallback: if no accumulated messages, persist simple format
        if not accumulated_messages:
            from src.shared.domain.datetime_utils import utc_now as _utc_now

            now_iso = _utc_now().isoformat()
            new_messages = [
                {
                    "id": str(uuid.uuid4()),
                    "role": "user",
                    "content": message,
                    "status": "sent",
                    "created_at": now_iso,
                },
                {
                    "id": str(uuid.uuid4()),
                    "role": "assistant",
                    "content": full_response,
                    "status": "sent",
                    "created_at": now_iso,
                },
            ]

        if emitted_blocks:
            self._attach_blocks_to_last_assistant(new_messages, emitted_blocks)

        self.conv_repo.append_messages(conv_uuid, tenant_id, new_messages)

        # Auto-title on first message
        if not existing_conv.title and message:
            title = message[:80] + ("..." if len(message) > 80 else "")
            self.conv_repo.update_title(conv_uuid, tenant_id, title)

        self.db.commit()
        self._cache_history(conv_id, tenant_id, new_messages)

    def _load_history(self, conv_id: str, tenant_id: UUID, conv_model: CopilotConversationModel) -> list:
        """Load conversation history, preferring Redis cache."""
        # Try Redis first
        redis_key = f"{REDIS_CONV_PREFIX}{conv_id}"
        try:
            cached = redis_client.get(redis_key) if redis_client else None
            if cached:
                raw_messages = json.loads(cached)
                return self._deserialize_messages(raw_messages)
        except Exception as e:  # noqa: BLE001 — Redis cache resilience
            logger.debug("redis_history_miss", conv_id=conv_id, error=str(e))

        # Fallback to DB
        if conv_model and conv_model.messages:
            # Re-cache in Redis
            try:
                if redis_client:
                    redis_client.setex(
                        redis_key,
                        REDIS_CONV_TTL,
                        json.dumps(conv_model.messages, ensure_ascii=False),
                    )
            except Exception:  # noqa: BLE001 — orchestrator resilience
                pass
            return self._deserialize_messages(conv_model.messages)

        return []

    def _cache_history(self, conv_id: str, tenant_id: UUID, new_messages: list) -> None:
        """Append new messages to Redis cache."""
        redis_key = f"{REDIS_CONV_PREFIX}{conv_id}"
        try:
            if not redis_client:
                return
            cached = redis_client.get(redis_key)
            existing = json.loads(cached) if cached else []
            existing.extend(new_messages)
            redis_client.setex(
                redis_key,
                REDIS_CONV_TTL,
                json.dumps(existing, ensure_ascii=False),
            )
        except Exception as e:  # noqa: BLE001 — Redis cache resilience
            logger.debug("redis_cache_error", error=str(e))

    @staticmethod
    def _attach_blocks_to_last_assistant(
        serialized: list[dict],
        emitted_blocks: list[dict],
    ) -> None:
        """Attach ``emitted_blocks`` to the last assistant message in-place.

        The final AIMessage of a turn is what the UI renders as "the answer" —
        cards + citations + tool results are all associated with it.
        Intermediate AIMessages (inside a tool loop) keep their simple
        role+content shape so they remain compatible with v1 consumers.
        """
        for msg in reversed(serialized):
            if msg.get("role") == "assistant":
                msg["blocks"] = emitted_blocks
                return

    @staticmethod
    def _serialize_messages(messages: list) -> list[dict]:
        """Convert LangChain message objects to persistable dicts.

        Every persisted message carries ``id``, ``status`` and ``created_at`` so
        the frontend merge-by-id logic can deduplicate reliably. Without these
        fields, a mid-job conversation refetch (triggered when per-wave
        extraction pills land) re-renders the whole transcript and the user
        sees duplicates + missing "sent" indicators.

        Preserves ``tool_calls`` on AIMessages and ToolMessages for replay.
        """
        from src.shared.domain.datetime_utils import utc_now as _utc_now

        result = []
        for msg in messages:
            base: dict = {
                "id": str(uuid.uuid4()),
                "status": "sent",
                "created_at": _utc_now().isoformat(),
            }
            if isinstance(msg, HumanMessage):
                result.append({**base, "role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                d: dict = {**base, "role": "assistant", "content": msg.content}
                if msg.tool_calls:
                    d["tool_calls"] = [
                        {"id": tc["id"], "name": tc["name"], "args": tc["args"]} for tc in msg.tool_calls
                    ]
                result.append(d)
            elif isinstance(msg, ToolMessage):
                result.append(
                    {
                        **base,
                        "role": "tool",
                        "content": msg.content,
                        "tool_call_id": msg.tool_call_id,
                        "name": msg.name,
                    },
                )
        return result

    @staticmethod
    def _deserialize_messages(raw_messages: list) -> list:
        """Convert persisted dict messages to LangChain message objects.

        Backward compatible: messages without tool_calls or tool role
        are handled as before.
        """
        result = []
        for msg in raw_messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                result.append(HumanMessage(content=content))
            elif role == "assistant":
                if msg.get("tool_calls"):
                    result.append(
                        AIMessage(content=content, tool_calls=msg["tool_calls"]),
                    )
                else:
                    result.append(AIMessage(content=content))
            elif role == "tool":
                result.append(
                    ToolMessage(
                        content=content,
                        tool_call_id=msg.get("tool_call_id", ""),
                        name=msg.get("name", ""),
                    ),
                )
        return result
