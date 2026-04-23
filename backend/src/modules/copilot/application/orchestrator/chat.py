"""CopilotOrchestrator — Manages conversation state and streams responses via SSE."""

# [COPILOT-SSE-V2] -> docs/domains/copilot/sse-protocol.md
# [COPILOT-CITATION-BLOCK] -> docs/domains/copilot/message-blocks.md
#
# SSE v2 dual-emit strategy (CONTRACT-MULTIMODAL §6.3):
#   - COPILOT_EMIT_LEGACY_SSE=true (default): emit both legacy (text_chunk,
#     tool_result, ui_action) AND new v2 (block_start, block_delta, block_end,
#     message_start, message_end) events side by side.
#   - COPILOT_EMIT_LEGACY_SSE=false: emit ONLY v2 events. Set this once all
#     FE clients have been migrated to the v2 block renderer (Phase P7).
#
# Migration phases (see CONTRACT §13):
#   P4 (current): dual-emit active. Old FE ignores block_* events. New FE
#                 prefers block_* and ignores text_chunk.
#   P7 (future):  flip COPILOT_EMIT_LEGACY_SSE=false, remove text_chunk branch.

from __future__ import annotations

import asyncio
import json
import os
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
from src.modules.copilot.application.guided.persistence import read_state as read_guided_state
from src.modules.copilot.application.orchestrator.graph import copilot_graph
from src.modules.copilot.application.orchestrator.state import (
    create_initial_copilot_state,
)
from src.modules.copilot.application.orchestrator.usage_tracking import UsageAccumulator
from src.modules.copilot.infrastructure.repositories.conversation_repository import (
    ConversationRepository,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.orm import Session

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
# [COPILOT-CITATION-BLOCK] → docs/domains/copilot/message-blocks.md §citation
# [COPILOT-OUTBOUND-ASSETS] → docs/domains/copilot/outbound-assets.md


def _kb_to_citations(parsed: object) -> list[dict] | None:
    """Convert search_knowledge_base result to CitationBlock list."""
    if not isinstance(parsed, list):
        return None
    blocks: list[dict] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        blocks.append(
            {
                "id": str(uuid4()),
                "type": "citation",
                "source": str(item.get("source") or item.get("metadata", {}).get("title") or ""),
                "snippet": str(item.get("snippet") or item.get("content") or "")[:500],
                "score": item.get("score"),
                "url": item.get("url") or item.get("metadata", {}).get("url"),
            }
        )
    return blocks


def _asset_item_to_block(item: dict) -> dict | None:
    """Convert a single asset dict to a typed block dict. Returns None for unknown kinds."""
    kind = str(item.get("kind", "")).lower()
    asset_id = str(item.get("asset_id", ""))
    public_url = str(item.get("public_url", ""))
    mime = str(item.get("mime", "application/octet-stream"))
    filename = str(item.get("filename", ""))

    if kind == "image":
        return {
            "id": str(uuid4()),
            "type": "image",
            "asset_id": asset_id,
            "url": public_url,
            "mime": mime,
            "alt": item.get("description") or filename or None,
        }
    if kind == "audio":
        return {
            "id": str(uuid4()),
            "type": "audio",
            "asset_id": asset_id,
            "url": public_url,
            "mime": mime,
            "transcript": "",  # assets don't carry transcript; caller may enrich
        }
    if kind == "video":
        return {
            "id": str(uuid4()),
            "type": "video",
            "asset_id": asset_id,
            "url": public_url,
            "mime": mime,
        }
    if kind == "document":
        return {
            "id": str(uuid4()),
            "type": "document",
            "asset_id": asset_id,
            "url": public_url,
            "mime": mime,
            "filename": filename,
            "size_bytes": int(item.get("size_bytes", 0)),
        }
    # Unknown kind → skip
    return None


def _assets_to_media_blocks(parsed: object) -> list[dict] | None:
    """Convert search_assets / get_asset result to asset block list."""
    if isinstance(parsed, dict):
        if "error" in parsed:
            return None
        items = [parsed]
    elif isinstance(parsed, list):
        items = [i for i in parsed if isinstance(i, dict) and "error" not in i]
    else:
        return None

    result_blocks: list[dict] = []
    for item in items:
        block = _asset_item_to_block(item)
        if block is not None:
            result_blocks.append(block)
    return result_blocks


# Dispatch table: tool_name → handler(parsed) -> list[dict] | None
_TOOL_BLOCK_HANDLERS: dict[str, object] = {
    "search_knowledge_base": _kb_to_citations,
    "search_assets": _assets_to_media_blocks,
    "get_asset": _assets_to_media_blocks,
}


def _tool_result_to_block(tool_name: str, result: object) -> list[dict] | None:
    """Convert a tool result to a list of MessageBlock dicts for SSE v2 block_append.

    Returns None if the tool output is not mapped to a block type (caller emits
    only the legacy tool_result event in that case).
    Returns an empty list if the tool output is a valid empty collection.

    Mapped tools:
    - search_knowledge_base  → list[CitationBlock]
    - search_assets          → list[ImageBlock | AudioBlock | VideoBlock | DocumentBlock]
    - get_asset              → [ImageBlock | AudioBlock | VideoBlock | DocumentBlock]

    All other tools → None.

    CONTRACT reference: CONTRACT-MULTIMODAL §6, §8, §10.
    """
    handler = _TOOL_BLOCK_HANDLERS.get(tool_name)
    if handler is None:
        return None

    result_str: str = result if isinstance(result, str) else json.dumps(result)
    try:
        parsed = json.loads(result_str)
    except (json.JSONDecodeError, ValueError):
        logger.debug("tool_result_to_block_invalid_json", tool_name=tool_name)
        return None

    return handler(parsed)  # type: ignore[operator]


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


# LLM streaming timeout (seconds). If the LLM hangs, the SSE stream will
# emit an error event after this duration instead of blocking indefinitely.
# Configurable via env var COPILOT_STREAM_TIMEOUT_SECONDS.
COPILOT_STREAM_TIMEOUT_SECONDS: int = int(
    os.environ.get("COPILOT_STREAM_TIMEOUT_SECONDS", "60"),
)

# SSE v2 migration flag (CONTRACT-MULTIMODAL §6.3).
# true  -> dual-emit: legacy events + v2 block events (P4-P6).
# false -> v2 only (P7 onwards).
_EMIT_LEGACY_SSE: bool = os.environ.get("COPILOT_EMIT_LEGACY_SSE", "true").lower() not in {
    "false",
    "0",
    "no",
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

        # Hydrate the guided-setup state for this conversation (if any). The
        # tools and prompt layer both read from ``state["guided_state"]`` so
        # we only hit the DB once per turn.
        guided = read_guided_state(conv_id)
        client_ctx["guided_mode"] = guided is not None

        state = create_initial_copilot_state(
            user_id=user_id,
            tenant_id=tenant_id,
            conversation_id=conv_id,
            client_context=client_ctx,
        )
        state["guided_state"] = guided.to_json() if guided is not None else None

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
        """Process a user message and yield SSE events.

        Emits both legacy v1 events and v2 block events during the migration
        window (COPILOT_EMIT_LEGACY_SSE=true). See module-level comment for
        the dual-emit strategy.
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

        async for sse_str in self._run_graph_stream(state=state, usage=usage, acc=acc):
            yield sse_str

        usage.log(conversation_id=conv_id, tenant_id=str(tenant_id))

        self._persist_messages(
            conv_uuid,
            tenant_id,
            conv_id,
            message,
            acc.full_response,
            acc.messages,
            existing_conv,
        )

        yield SSEEvent(event="status", data={"state": "done"}).to_sse()
        yield SSEEvent(event="done", data={"conversation_id": conv_id}).to_sse()

    async def _run_graph_stream(
        self,
        *,
        state: dict,
        usage: UsageAccumulator,
        acc: _StreamAccumulator,
    ) -> AsyncGenerator[str, None]:
        """Run the LangGraph stream and emit SSE events (v1 legacy + v2 blocks).

        Accumulates full_response, messages, and emitted_blocks into *acc*
        so that stream_chat can persist them after the generator exhausts.
        """
        from src.shared.domain.datetime_utils import utc_now as _utc_now

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
                async for event in copilot_graph.astream_events(state, version="v2"):
                    usage.update_from_event(event)

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

                    legacy_sse, text_chunk = self._process_stream_event(
                        event,
                        acc.messages,
                        acc.last_tool_call_ids,
                    )
                    if text_chunk:
                        acc.full_response += text_chunk
                        async for block_sse in self._emit_text_chunk_v2(acc, msg_id, text_chunk):
                            yield block_sse
                    if legacy_sse:
                        yield legacy_sse

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

        # Finalize v2 text block
        if acc.text_block_id is not None:
            final_text_block: dict = {
                "id": acc.text_block_id,
                "type": "text",
                "markdown": acc.text_block_markdown,
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
            yields this directly. For text chunks this is the legacy
            ``text_chunk`` event (only emitted when _EMIT_LEGACY_SSE=True);
            for tool events it is tool_start/tool_result/ui_action.

        text_chunk: raw text content when the LLM emitted a streaming token.
            The caller uses this to build the v2 ``block_delta`` events
            independently of the legacy flag.
        """
        kind = event.get("event")

        if kind == "on_chat_model_stream":
            chunk = event.get("data", {}).get("chunk")
            if chunk and hasattr(chunk, "content") and chunk.content:
                # Legacy text_chunk event -- only emit when flag is on (P4-P6).
                # v2 block_delta is built by the caller from the returned text_chunk.
                legacy_sse = (
                    SSEEvent(
                        event="text_chunk",
                        data={"content": chunk.content},
                    ).to_sse()
                    if _EMIT_LEGACY_SSE
                    else None
                )
                return legacy_sse, chunk.content
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

        result_sse = SSEEvent(
            event="tool_result",
            data={"tool": tool_name, "result": str(tool_output)[:500]},
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

        Dual-emit strategy (same as text streaming):
        - Legacy: tool_result + ui_action events always emitted (when _EMIT_LEGACY_SSE).
        - v2: block_append event emitted for mapped tools, containing the typed block.

        Non-text blocks (image/audio/citation/card) are atomic — no streaming deltas.
        They use block_append (not block_start/end) because they appear as tool results,
        not as the primary streaming content. FE appends them to the message blocks list.
        """
        tool_name = event.get("name", "unknown")
        tool_output = event.get("data", {}).get("output", "")

        # Step 1 — emit legacy events via the existing handler
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
    ) -> None:
        """Persist conversation messages to DB and Redis cache."""
        if not full_response and not accumulated_messages:
            return

        new_messages = self._serialize_messages(
            [HumanMessage(content=message), *accumulated_messages],
        )
        # Fallback: if no accumulated messages, persist simple format
        if not accumulated_messages:
            new_messages = [
                {"role": "user", "content": message},
                {"role": "assistant", "content": full_response},
            ]

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
    def _serialize_messages(messages: list) -> list[dict]:
        """Convert LangChain message objects to persistable dicts.

        Preserves tool_calls on AIMessages and ToolMessages for full
        conversation replay.
        """
        result = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                result.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                d: dict = {"role": "assistant", "content": msg.content}
                if msg.tool_calls:
                    d["tool_calls"] = [
                        {"id": tc["id"], "name": tc["name"], "args": tc["args"]} for tc in msg.tool_calls
                    ]
                result.append(d)
            elif isinstance(msg, ToolMessage):
                result.append(
                    {
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
