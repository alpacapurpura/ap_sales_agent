# CONTRACT — PR-7-outbound-orchestrator

> Owner: `nicolify-architect`. SSoT pre-implementación. Builders agentic + backend consumen este archivo en paralelo. Architect run on 2026-04-30.

## 0. Context summary

| Surface | Builder owner | Auditor owner | Skills consulted |
|---|---|---|---|
| `sales_agent/application/orchestrator/{outbound_orchestrator.py,state.py,conversation_pipeline.py}` | `nicolify-agentic` (Opus) | `nicolify-agentic-auditor` (Opus) | `sales-agent-expert`, `tessl__langgraph` |
| `sales_agent/application/prompts/compose.py` | `nicolify-agentic` (Opus) | `nicolify-agentic-auditor` (Opus) | `sales-agent-expert` (slot architecture, cache boundary) |
| `sales_agent/application/agents/sales/nodes.py` (supervisor branch only) | `nicolify-agentic` (Opus) | `nicolify-agentic-auditor` (Opus) | `sales-agent-expert` |
| `campaigns/infrastructure/external/sales_agent_adapter.py` (NEW) | `nicolify-backend` (Sonnet) | `nicolify-backend-auditor` (Opus) | `backend-expert` |
| `campaigns/workers/execution_task.py` + `campaigns/infrastructure/channels/{telegram.py,shared.py}` | `nicolify-backend` (Sonnet) | `nicolify-backend-auditor` (Opus) | `backend-expert`, `tessl__graceful-degradation` |
| `shared/links/ports/crm_repos.py` + `shared/billing/application/llm_guards.py` + `shared/domain/locale.py` lookup | `nicolify-backend` (Sonnet) | `nicolify-backend-auditor` (Opus) | `backend-expert` |
| `brand/application/{voice_fidelity,agents/style_analyzer,services/personality_service}.py` (helper wiring only) | `nicolify-backend` (Sonnet) | `nicolify-backend-auditor` (Opus) | `brand-expert` (no copy/voice changes — only LLMFactory→helper) |

**Skills consulted summary**:
- `sales-agent-expert`: voice SSoT preserved (no brand_voice_summary, no fine-tune); slot 6 POST slot 5 to keep cache prefix per-tenant invariant; output respects tenant voice (voseo OK si AR — `.claude/rules/spanish-text.md` exception applies); §3 SACRA NOT touched (Closer Studio, BufferService, OutputManager.process_response chunking, agent_state_checkpoint schema, webhook adapters, follow_up_engine, tool_call_dedup).
- `tessl__langgraph`: reuse `agent_app.ainvoke(state, config={callbacks: [...]})` — no new StateGraph; checkpoint via existing `state_repository`; supervisor branching via state field read (no new node).
- `backend-expert`: every query filters tenant_id; SA 2.0 select; AsyncSession new code; structlog only; soft delete preserved.
- `tessl__graceful-degradation`: `_resolve_tenant_locale` lookup wraps try/except → fallback `TenantLocale.default()` → never aborts send; LRU cache 5min for hot-path latency.
- `brand-expert`: helper wiring is mechanical (LLMFactory.get_service() → `_get_guarded_llm_service(tenant_id, "brand")`) — NO change to brand domain logic, voice extraction algorithms, or PersonalityCompiler.

**CONTEXT-BRIEF source**: self-ran greps + read of canonical files. PR-7 trabaja sobre architecture cementada S3 — context-builder Haiku no fue invocado para este PR (Opus 1M holds full surface in context).

**pm-nico/current-state files affected** (post-merge updates required):
- `docs/pm-nico/current-state/campaigns.md` — append "Outbound conversational dispatch via SalesAgentAdapter (PR-7)"
- `docs/pm-nico/current-state/sales-agent.md` — append "OutboundOrchestrator (PR-7) — paralelo a ChatOrchestrator inbound; reusa LangGraph + cache; voice fidelity prod ≥0.7"
- `docs/pm-nico/current-state/brand.md` — append "Voice fidelity grader + style_analyzer + personality_service guarded by BudgetGuard (PR-7 Sub-G)"

**Architecture gates that must keep passing**:
- `tests/architecture/test_budget_guard_pre_llm_call.py` (ratchet shrink 5→2)
- `tests/architecture/test_no_new_copilot_module_imports.py` (ratchet 22 frozen — sales_agent NOT touching copilot)
- `tests/architecture/test_response_model_required.py` (PR-7 zero new endpoints)
- `tests/architecture/test_no_cross_module_imports.py` (sales_agent → crm via port `crm_repos.py` only)
- `tests/architecture/test_system_prompt_order.py` (slot order CACHEABLE prefix slots 1-5 invariante)
- `tests/architecture/test_outbound_orchestrator_non_breaking.py` (NEW)
- `tests/architecture/test_campaign_state_additive.py` (NEW)

---

## 1. Existing systems audit (NO NEW LAYER rule)

### Audit cross-module ejecutado

```bash
grep -rn "agent_app\|StateGraph\|sales_app" backend/src/modules/sales_agent/
grep -rn "ChatOrchestrator\|ConversationPipeline\|build_initial_state" backend/src/modules/sales_agent/
grep -rn "BudgetGuardingLLMService\|BudgetGuardingChatModel" backend/src/shared/billing/
grep -rn "telegram_id" backend/src/shared/infrastructure/models/ backend/src/modules/crm/
grep -rn "TenantLocale\|format_message_for_tenant_locale" backend/src/shared/ backend/src/modules/campaigns/
grep -rn "PromptFragment\|compose_system_prompt\|CACHEABLE_FRAGMENTS" backend/src/modules/sales_agent/
grep -rn "step_type\|StepType\|CALL_SUBAGENT_BRIEF" backend/src/modules/campaigns/
```

### Sistemas existentes — todos EXTEND, cero NEW layer

| Sistema | Path:line | Decisión | Notas |
|---|---|---|---|
| `ConversationPipeline` static class | `sales_agent/application/orchestrator/conversation_pipeline.py:77` | EXTEND | `build_initial_state` ya tiene pattern `budget_guard: BudgetGuard | None = None` opcional → mismo pattern para `campaign_id`/`campaign_instructions`/`outbound_mode` |
| LangGraph `agent_app` | `sales_agent/application/orchestrator/graph.py:52` (`agent_app = workflow.compile()`) | REUSE no-op | invocado idéntico via `agent_app.ainvoke(initial_state, config={"callbacks": [handler]})` |
| Slot system v2 `compose.py` | `sales_agent/application/prompts/compose.py:53-90` (`PromptFragment` enum + `CACHEABLE_FRAGMENTS` + `VOLATILE_FRAGMENTS`) | EXTEND | append `CAMPAIGN_CONTEXT` enum value POST `BRAND_VOICE` slot 5 |
| `BudgetGuardingLLMService` + `BudgetGuardingChatModel` | `shared/billing/application/llm_guards.py:126,188` | EXTEND | nuevo helper `_get_guarded_llm_service(tenant_id, agent_kind, db, model_hint=None)` mismo archivo |
| `crm_repos.py` lazy port | `shared/links/ports/crm_repos.py:18-76` | EXTEND | nueva function `get_lead_telegram_id(db, tenant_id, lead_id)` mismo patrón lazy-import |
| `LeadModel.telegram_id` column | `shared/infrastructure/models/crm.py:160` | REUSE | columna `unique=True nullable=True`, indexed; cero migration |
| `TenantLocale` VO | `shared/domain/locale.py:11` | REUSE | dataclass frozen ya provee `default()` fallback |
| `_resolve_tenant_locale` placeholder | `campaigns/infrastructure/channels/shared.py:111` | EXTEND | reemplazar `TenantLocale.default()` placeholder por lookup real `TenantModel.config_json["tenant_locale"]` con LRU cache 5min |
| `build_sales_agent_callback_handler` | `sales_agent/observability/recording/factory.py:53` | REUSE no-op | invoke con `role="agent"` (default) outbound |
| `node_sales_supervisor` routing | `sales_agent/application/agents/sales/nodes.py:94` | EXTEND | branch outbound BEFORE LLM call: `if state.get("outbound_mode") and state.get("lead_score", 0) >= 40: return {"next_node": "closer"}` |
| `execution_task.py::_process_task` | `campaigns/workers/execution_task.py:68` | EXTEND | branch `step.step_type == StepType.CALL_SUBAGENT_BRIEF` → `SalesAgentAdapter.dispatch(...)`, else existing path |
| `TelegramChannelRouter._resolve_telegram_id` | `campaigns/infrastructure/channels/telegram.py:422` | EXTEND | wirea CRM port (cierra DR-7 STUB) |
| `KNOWN_UNGUARDED` ratchet | `tests/architecture/test_budget_guard_pre_llm_call.py:29` | SHRINK | brand 3 entries removed; `expected_max` 5 → 2 (o 0 si Sub-H) |
| `LeadRepository.get_by_channel_id` | `crm/infrastructure/repositories/lead_repository.py:90` | REUSE pattern | función nueva CRM port reusa mismo lookup pattern (`SELECT WHERE telegram_id = X AND tenant_id = Y`) |
| `CampaignStep.step_type StepType.CALL_SUBAGENT_BRIEF` | `campaigns/domain/enums.py:39` | REUSE | enum value ya existe + `step_config` JSONB shape `{"agent_kind": "sales_agent", "brief": str}` documentado en `campaign_step.py:30` |

**Cero NEW layer detectada. Cero archivo orphan. Cero ratchet break.**

---

## 2. AgentState extension diff (Sub-A)

**File**: `backend/src/modules/sales_agent/application/orchestrator/state.py`

### Added fields (additive, opcionales)

```python
class AgentState(TypedDict):
    # ... existing fields preserved verbatim ...

    # PR-7: Outbound campaign context (additive, opt-in via outbound_mode)
    campaign_id: UUID | None  # campaigns.id when dispatched from CampaignTask
    campaign_instructions: str | None  # CampaignStep.step_config["brief"] verbatim
    outbound_mode: bool  # default False — inbound chat path; True only via OutboundOrchestrator
```

### `create_initial_state` signature additive

```python
def create_initial_state(
    user_id: str,
    tenant_id: str,
    # ... existing params verbatim ...
    _llm_service: object | None = None,
    # PR-7: outbound additive
    campaign_id: UUID | None = None,
    campaign_instructions: str | None = None,
    outbound_mode: bool = False,
) -> AgentState:
    # ... existing body verbatim ...
    return {
        # ... existing dict verbatim ...
        "_llm_service": _llm_service,
        # PR-7: outbound additive (always set, defaults preserve inbound behavior)
        "campaign_id": campaign_id,
        "campaign_instructions": campaign_instructions,
        "outbound_mode": outbound_mode,
        "error": None,
    }
```

**Invariant**: `outbound_mode=False` (default) → AgentState dict shape backward-compatible. Existing inbound calls pass through unchanged. Test `test_campaign_state_additive.py` enforces.

---

## 3. Slot 6 CAMPAIGN_CONTEXT signature (Sub-A)

**File**: `backend/src/modules/sales_agent/application/prompts/compose.py`

### Enum + ordering changes

```python
class PromptFragment(StrEnum):
    # ── Cacheable prefix (stable across turns) ────────────────────────
    STATIC_IDENTITY = "static_identity"          # Slot 1 cross-tenant invariant
    STATIC_TOOLS_HINT = "static_tools_hint"      # Slot 2 cross-tenant invariant
    SALES_PLAYBOOK_HINT = "sales_playbook_hint"  # Slot 3 per-specialist invariant
    AGENT_IDENTITY = "agent_identity"            # Slot 4 per-tenant invariant (WHO+WHAT)
    BRAND_VOICE = "brand_voice"                  # Slot 5 per-tenant invariant (HOW — SSoT)
    CHANNEL_FORMAT_HINT = "channel_format_hint"  # Slot 6 per-tenant invariant (channel chat/wa/tg)
    CAMPAIGN_CONTEXT = "campaign_context"        # Slot 7 NEW — per-campaign invariant (within turn)
    # ── Volatile tail (changes per turn) ──────────────────────────────
    STAGE_HINT = "stage_hint"
    LEAD_SIGNALS = "lead_signals"
    SESSION_CONTINUITY = "session_continuity"
    TOOL_REQUEST_FORMAT = "tool_request_format"


CACHEABLE_FRAGMENTS: tuple[PromptFragment, ...] = (
    PromptFragment.STATIC_IDENTITY,
    PromptFragment.STATIC_TOOLS_HINT,
    PromptFragment.SALES_PLAYBOOK_HINT,
    PromptFragment.AGENT_IDENTITY,
    PromptFragment.BRAND_VOICE,
    PromptFragment.CHANNEL_FORMAT_HINT,
    PromptFragment.CAMPAIGN_CONTEXT,  # PR-7: per-campaign invariant within turn
)
```

### Slot 7 builder (Decisión 35 — slot order — POST slot 6 channel; cache prefix slots 1-6 per-tenant invariante)

```python
def _campaign_context(state: AgentState) -> str:
    """PR-7 — slot 7 per-campaign invariant.

    Emitted ONLY when ``outbound_mode=True``. Preserves cache prefix per-tenant:
    slots 1-6 (STATIC_IDENTITY → CHANNEL_FORMAT_HINT) remain invariant for the
    tenant whether inbound chat or outbound campaign — campaign-specific
    instructions go AFTER channel format. Cache hit rate ≥60% per-tenant
    preserved across inbound/outbound.

    NEVER inject {tenant_name} or {campaign_name} mid-block (cache prefix
    invalidation rule from sales-agent-brand-voice.md SACRA).
    """
    if not state.get("outbound_mode"):
        return ""

    instructions = (state.get("campaign_instructions") or "").strip()
    if not instructions:
        return ""

    return (
        "# Contexto de campaña\n\n"
        "Estás iniciando una conversación outbound. El usuario aún no respondió. "
        "Tu primer turno debe abrir la conversación según las siguientes "
        "instrucciones de campaña, manteniendo la voz de marca declarada arriba.\n\n"
        f"## Instrucciones de campaña\n\n{instructions}"
    )


def build_specialist_system_prompt(state: AgentState, role: SpecialistRole) -> str:
    fragments: dict[PromptFragment, str] = {
        PromptFragment.STATIC_IDENTITY: _BASE_IDENTITY,
        PromptFragment.STATIC_TOOLS_HINT: _TOOLS_HINT,
        PromptFragment.SALES_PLAYBOOK_HINT: _render_static_specialist_body(role),
        PromptFragment.AGENT_IDENTITY: state.get("agent_identity") or "",
        PromptFragment.BRAND_VOICE: state.get("brand_voice") or "",
        PromptFragment.CHANNEL_FORMAT_HINT: _channel_format_hint(state),
        PromptFragment.CAMPAIGN_CONTEXT: _campaign_context(state),  # PR-7
        PromptFragment.STAGE_HINT: _stage_hint(state),
        PromptFragment.LEAD_SIGNALS: _lead_signals(state),
        PromptFragment.SESSION_CONTINUITY: _session_continuity(state),
        PromptFragment.TOOL_REQUEST_FORMAT: _tool_request_format(),
    }
    return compose_system_prompt(fragments)
```

**Invariant**: `outbound_mode=False` → `_campaign_context` returns `""` → `_take` drops empty fragment → assembled prompt identical to pre-PR-7 inbound. Cache prefix slots 1-6 byte-equal across inbound/outbound for same tenant. Verified by arch test `test_no_cache_prefix_break` (extends existing `test_system_prompt_order.py`).

---

## 4. OutboundOrchestrator class signature + flow (Sub-B)

**File** (NEW): `backend/src/modules/sales_agent/application/orchestrator/outbound_orchestrator.py`

```python
"""OutboundOrchestrator — outbound campaign dispatch via sales_agent.

Static class paralelo a ChatOrchestrator. Reusa ConversationPipeline
helpers + agent_app LangGraph + slot system v2 + voice SSoT.

Boundary: invoked by SalesAgentAdapter (campaigns/infrastructure/external/),
which is invoked by execution_task.py ARQ worker for steps with
step_type=CALL_SUBAGENT_BRIEF. NO webhook entry — outbound is cron-driven.

Continuity invariant: if checkpoint already active for (tenant, lead),
DO NOT create new session — resume existing (avoids dual-conversation drift).

# [SALES-AGENT-OUTBOUND-PR7] -> docs/pm-nico/pis/active/PI-1-campaigns-module/
#                                sprints/S3-mvp-telegram/prs/PR-7-outbound-orchestrator/CONTRACT.md
"""

from __future__ import annotations

import contextlib
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING

import structlog

from src.modules.sales_agent.application.orchestrator.audit_emitter import AuditEmitter
from src.modules.sales_agent.application.orchestrator.conversation_pipeline import (
    ConversationPipeline,
)
from src.modules.sales_agent.application.orchestrator.graph import agent_app
from src.modules.sales_agent.observability.recording.factory import (
    build_sales_agent_callback_handler,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

    from src.shared.billing.application.budget_guard import BudgetGuard
    from src.shared.infrastructure.channels.base import BaseChannel

logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class OutboundResult:
    """Result of an outbound campaign send.

    Returned to SalesAgentAdapter, which translates to ChannelSendResult
    for the worker.
    """

    success: bool
    tenant_id: UUID
    lead_id: UUID
    campaign_id: UUID
    session_id: str
    external_message_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    voice_fidelity_score: float | None = None  # populated when grader runs sync (golden test path)


class OutboundOrchestrator:
    """Static class — single async entrypoint ``send_outbound``."""

    @staticmethod
    async def send_outbound(  # noqa: PLR0913 — explicit DI is the contract
        *,
        db: Session,
        tenant_id: UUID,
        lead_id: UUID,
        campaign_id: UUID,
        campaign_instructions: str,
        channel_type: str,
        channel_adapter: BaseChannel,
        budget_guard: BudgetGuard | None = None,
        idempotency_key: str | None = None,
    ) -> OutboundResult:
        """Run one outbound turn through the sales_agent graph.

        Steps (mirror ChatOrchestrator.handle_message inbound pattern):
          1. Resolve tenant config + tenant UUID.
          2. Resolve lead via biz_repo (tenant-scoped).
          3. Load checkpoint — if active, REUSE (continuity invariant).
          4. Build agent_identity (slot 4) + brand_voice (slot 5).
          5. Build initial AgentState with outbound_mode=True + campaign fields.
          6. Build callback handler (best-effort observability).
          7. ainvoke agent_app with config={callbacks: [handler]}.
          8. Save checkpoint.
          9. Deliver via channel_adapter (Telegram bot).
          10. Audit + return OutboundResult.

        Best-effort: every observability + audit write wraps try/except
        with structlog.warning + db.rollback fallback. Never aborts send.
        """
        from src.modules.iam.infrastructure.models.tenant_model import TenantModel
        from src.modules.sales_agent.infrastructure.memory.audit_repository import (
            AuditRepository,
        )
        from src.modules.sales_agent.infrastructure.repositories.state_repository import (
            StateRepository,
        )
        from src.modules.sales_agent.infrastructure.repositories.business_repository import (
            BusinessRepository,
        )

        tenant_uuid, tenant_config = ConversationPipeline.fetch_tenant_config(db, str(tenant_id))
        if tenant_uuid is None:
            return OutboundResult(
                success=False,
                tenant_id=tenant_id,
                lead_id=lead_id,
                campaign_id=campaign_id,
                session_id="",
                error_code="tenant_not_found",
            )

        # --- Repos (same instances ChatOrchestrator uses) ---
        audit_repo = AuditRepository(db)
        state_repo = StateRepository(db)
        biz_repo = BusinessRepository(db, tenant_uuid)

        # --- Lead lookup (tenant-scoped) ---
        from sqlalchemy import select

        from src.shared.infrastructure.models.crm import LeadModel

        lead_row = (
            db.execute(
                select(LeadModel).where(
                    LeadModel.id == lead_id,
                    LeadModel.tenant_id == tenant_uuid,
                ),
            )
            .scalars()
            .first()
        )
        if lead_row is None:
            return OutboundResult(
                success=False,
                tenant_id=tenant_id,
                lead_id=lead_id,
                campaign_id=campaign_id,
                session_id="",
                error_code="lead_not_found",
            )

        # --- Customer placeholder (outbound has no customer in chat sense; reuse lead.customer if linked) ---
        customer = lead_row.customer  # may be None — biz_repo handles

        # --- Checkpoint continuity ---
        checkpoint = ConversationPipeline.load_checkpoint(db, state_repo, tenant_uuid, lead_row.id)

        # --- Identity + voice (slots 4-5) ---
        agent_identity = ConversationPipeline.build_agent_identity(db, tenant_uuid)
        brand_voice = ConversationPipeline.build_brand_voice(db, tenant_uuid)

        # --- Session state (outbound: always 'new' — no last_msg) ---
        session_state = {
            "session_active": True,
            "last_intent": None,
            "session_gap_hours": None,
            "is_returning_user": checkpoint is not None,
        }

        # --- Build initial AgentState with outbound flag ---
        initial_state, last_session_summary = ConversationPipeline.build_initial_state(
            db=db,
            biz_repo=biz_repo,
            audit_repo=audit_repo,
            user=lead_row,
            customer=customer,
            tenant_id=str(tenant_uuid),
            tenant_uuid=tenant_uuid,
            tenant_config=tenant_config,
            incoming=_OutboundIncoming(channel_type=channel_type),  # synthetic
            session_state=session_state,
            agent_identity=agent_identity,
            brand_voice=brand_voice,
            checkpoint=checkpoint,
            state_repo=state_repo,
            budget_guard=budget_guard,
            # PR-7: outbound additive
            campaign_id=campaign_id,
            campaign_instructions=campaign_instructions,
            outbound_mode=True,
        )

        # First-turn outbound: no user message — supervisor + closer compose opener.
        # Inject synthetic system "trigger" so graph has a starting message.
        initial_state["messages"] = [
            {"role": "system", "content": "[OUTBOUND_TRIGGER] Apertura outbound — el usuario aún no respondió."}
        ]

        # --- Observability handler ---
        turn_id = uuid.uuid4()
        handler = build_sales_agent_callback_handler(
            db=db,
            tenant_id=tenant_uuid,
            lead_id=lead_row.id,
            channel_type=channel_type,
            turn_id=turn_id,
            role="agent",
        )

        # --- Dispatch via LangGraph ---
        try:
            config = {"callbacks": [handler]} if handler is not None else {}
            result = await agent_app.ainvoke(initial_state, config=config)
        except Exception as exc:  # noqa: BLE001 — orchestrator resilience
            logger.exception(
                "outbound_orchestrator_graph_failed",
                tenant_id=str(tenant_uuid),
                lead_id=str(lead_row.id),
                campaign_id=str(campaign_id),
            )
            return OutboundResult(
                success=False,
                tenant_id=tenant_id,
                lead_id=lead_row.id,
                campaign_id=campaign_id,
                session_id=initial_state.get("session_id", ""),
                error_code="graph_invocation_failed",
                error_message=str(exc),
            )

        # --- Persist checkpoint ---
        ConversationPipeline.save_checkpoint(
            db,
            state_repo,
            tenant_uuid,
            lead_row,
            customer,
            channel_type,
            initial_state,
            result,
            last_session_summary,
        )

        # --- Deliver via channel adapter (Telegram) ---
        last_msg = result["messages"][-1] if result.get("messages") else {}
        bot_text = last_msg.get("content", "") if isinstance(last_msg, dict) else str(last_msg)
        bot_text = await ConversationPipeline.sanitize_text(bot_text, "bot_output")

        if not bot_text.strip():
            return OutboundResult(
                success=False,
                tenant_id=tenant_id,
                lead_id=lead_row.id,
                campaign_id=campaign_id,
                session_id=initial_state.get("session_id", ""),
                error_code="empty_response",
            )

        # Audit + send
        audit_repo.log_message(
            user_id=lead_row.id,
            role="assistant",
            content=bot_text,
            channel=channel_type,
            tenant_id=tenant_uuid,
        )

        from src.modules.sales_agent.infrastructure.external.output_manager import OutputManager

        try:
            external_id = await OutputManager.process_response(
                lead_row.telegram_id or "",  # outbound → telegram_id resolved by adapter
                bot_text,
                channel_adapter,
                channel_type=channel_type,
            )
        except Exception as exc:  # noqa: BLE001 — channel resilience
            logger.exception(
                "outbound_orchestrator_channel_send_failed",
                tenant_id=str(tenant_uuid),
                lead_id=str(lead_row.id),
                campaign_id=str(campaign_id),
            )
            return OutboundResult(
                success=False,
                tenant_id=tenant_id,
                lead_id=lead_row.id,
                campaign_id=campaign_id,
                session_id=initial_state.get("session_id", ""),
                error_code="channel_send_failed",
                error_message=str(exc),
            )

        with contextlib.suppress(Exception):
            await AuditEmitter.emit_assistant_message(tenant_uuid, lead_row, bot_text, result)

        return OutboundResult(
            success=True,
            tenant_id=tenant_id,
            lead_id=lead_row.id,
            campaign_id=campaign_id,
            session_id=initial_state.get("session_id", ""),
            external_message_id=external_id if isinstance(external_id, str) else None,
        )


@dataclass(frozen=True, slots=True)
class _OutboundIncoming:
    """Synthetic IncomingMessage shape for outbound (no real webhook)."""

    channel_type: str
    text: str = ""
    user_id: str = ""
    metadata: dict = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        # frozen + dataclass workaround
        object.__setattr__(self, "metadata", {})


__all__ = ["OutboundOrchestrator", "OutboundResult"]
```

**Flow steps**:
1. `fetch_tenant_config` (reused).
2. Resolve `LeadModel` via `select` tenant-scoped.
3. `load_checkpoint` (reused — REUSES if active).
4. `build_agent_identity` + `build_brand_voice` (reused).
5. `build_initial_state(... outbound_mode=True, campaign_id=..., campaign_instructions=...)`.
6. `build_sales_agent_callback_handler(role="agent")` for observability.
7. `await agent_app.ainvoke(state, config={"callbacks": [handler]})`.
8. `save_checkpoint` (reused).
9. Deliver via `OutputManager.process_response(channel_adapter)`.
10. `AuditEmitter.emit_assistant_message`.

---

## 5. SalesAgentAdapter signature (Sub-D)

**File** (NEW): `backend/src/modules/campaigns/infrastructure/external/sales_agent_adapter.py`

**Decisión 31 — location**: `campaigns/infrastructure/external/`. Reasoning: the adapter is `campaigns`-owned (translates campaign domain to sales_agent invocation); putting it in `sales_agent/` would force `sales_agent → campaigns` cross-module import (DDD violation). Adapter pattern in infrastructure layer is canonical for downstream adapters per backend-ddd.md.

```python
"""SalesAgentAdapter — bridges CampaignTask + CampaignStep → OutboundOrchestrator.

Cross-module port: campaigns/infrastructure → sales_agent.application.
Lazy-imports OutboundOrchestrator + ChannelRouter so the campaigns module
does NOT take a top-level dependency on sales_agent (DDD: sales_agent is
the LangGraph runtime; campaigns owns the cron + DAG).

Invoked from: ``campaigns/workers/execution_task.py::_process_task`` when
``step.step_type == StepType.CALL_SUBAGENT_BRIEF``.

Compliance + RateLimit + Idempotency stay applied PRE-dispatch via the
worker's existing pipeline (heredado del worker — NO se duplica aquí).

# [CAMPAIGNS-OUTBOUND-ADAPTER-PR7]
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    from src.modules.campaigns.domain.campaign_step import CampaignStep
    from src.modules.campaigns.domain.campaign_task import CampaignTask
    from src.shared.billing.application.budget_guard import BudgetGuard

logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class SalesAgentDispatchResult:
    """Result of adapter dispatch — translates to ChannelSendResult by worker."""

    success: bool
    external_message_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class SalesAgentAdapter:
    """Static adapter — single async entrypoint ``dispatch``."""

    @staticmethod
    async def dispatch(
        *,
        session: AsyncSession,
        task: CampaignTask,
        step: CampaignStep,
        budget_guard: BudgetGuard | None = None,
    ) -> SalesAgentDispatchResult:
        """Dispatch CampaignTask via OutboundOrchestrator.

        Pre-conditions (caller-enforced — execution_task.py):
        - ``step.step_type == StepType.CALL_SUBAGENT_BRIEF``
        - Compliance, RateLimit, Idempotency already gated by worker
        - SELECT FOR UPDATE row lock held on CampaignTask

        Args:
            session: AsyncSession (worker-scoped, txn open).
            task: CampaignTask (locked).
            step: CampaignStep with step_config = {"agent_kind", "brief"}.
            budget_guard: Optional — when set, OutboundOrchestrator wraps LLM.

        Returns:
            SalesAgentDispatchResult with ``success`` + external_message_id.

        Raises:
            ValueError: step_type mismatch (caller bug).
        """
        from src.modules.campaigns.domain.enums import StepType

        if step.step_type != StepType.CALL_SUBAGENT_BRIEF:
            msg = f"SalesAgentAdapter requires CALL_SUBAGENT_BRIEF; got {step.step_type}"
            raise ValueError(msg)

        # Lazy imports to keep DDD boundary clean
        from src.modules.campaigns.infrastructure.channels.registry import ChannelRouterRegistry
        from src.modules.sales_agent.application.orchestrator.outbound_orchestrator import (
            OutboundOrchestrator,
        )

        # Bridge AsyncSession → sync Session for OutboundOrchestrator
        # (sales_agent uses sync Session in ConversationPipeline). Reuse worker's
        # bind via sync_session under the hood. Pattern documented in PR-6.
        from src.shared.infrastructure.db import sync_session_from_async

        sync_db = sync_session_from_async(session)

        brief = (step.step_config or {}).get("brief") or step.label or "Iniciá la conversación outbound."
        agent_kind = (step.step_config or {}).get("agent_kind", "sales_agent")
        if agent_kind != "sales_agent":
            return SalesAgentDispatchResult(
                success=False,
                error_code="unsupported_agent_kind",
                error_message=f"agent_kind={agent_kind} not supported (only sales_agent in S3)",
            )

        channel_type = "telegram"  # S3 MVP — multi-canal en S4
        registry = ChannelRouterRegistry()
        channel_router = registry.get(channel_type)
        # ChannelRouter has channel_adapter under .send — adapter wraps Telegram Bot API
        # OutboundOrchestrator uses the same router for delivery to keep ONE path

        try:
            result = await OutboundOrchestrator.send_outbound(
                db=sync_db,
                tenant_id=task.tenant_id,
                lead_id=task.lead_id,
                campaign_id=task.campaign_id,
                campaign_instructions=brief,
                channel_type=channel_type,
                channel_adapter=channel_router,  # type: ignore[arg-type] — protocol-compatible
                budget_guard=budget_guard,
                idempotency_key=task.idempotency_key,
            )
        except Exception as exc:  # noqa: BLE001 — adapter resilience
            logger.exception(
                "sales_agent_adapter_dispatch_failed",
                task_id=str(task.id),
                tenant_id=str(task.tenant_id),
                campaign_id=str(task.campaign_id),
            )
            return SalesAgentDispatchResult(
                success=False,
                error_code="adapter_failure",
                error_message=str(exc),
            )

        return SalesAgentDispatchResult(
            success=result.success,
            external_message_id=result.external_message_id,
            error_code=result.error_code,
            error_message=result.error_message,
        )


__all__ = ["SalesAgentAdapter", "SalesAgentDispatchResult"]
```

**Worker dispatch branch** (`execution_task.py::_process_task` after `step` is loaded, BEFORE channel resolution):

```python
# After step lookup (existing line ~123):
if step is not None and step.step_type == StepType.CALL_SUBAGENT_BRIEF:
    # PR-7: dispatch via SalesAgentAdapter; channel + LLM owned by OutboundOrchestrator
    from src.modules.campaigns.infrastructure.external.sales_agent_adapter import (
        SalesAgentAdapter,
    )

    sa_result = await SalesAgentAdapter.dispatch(
        session=session,
        task=_task_to_domain(row),
        step=step,
        budget_guard=ctx.get("budget_guard"),
    )

    if sa_result.success:
        await task_repo.mark_sent(
            task_id, tenant_id,
            external_message_id=sa_result.external_message_id,
            channel_used="telegram",
            session=session,
        )
        await _audit(audit_svc, session, ..., event_type=AuditEventType.TASK_SENT, ...)
        return {"id": str(task_id), "status": "sent", "external_id": sa_result.external_message_id or ""}

    await task_repo.mark_failed(
        task_id, tenant_id,
        error_code=sa_result.error_code or "sales_agent_dispatch_failed",
        error_message=sa_result.error_message or "",
        session=session,
    )
    return {"id": str(task_id), "status": "failed", "external_id": ""}

# else: existing SEND_MESSAGE / channel router path unchanged
```

---

## 6. CRM port `get_lead_telegram_id` signature (Sub-E)

**Decisión 32 — extend `crm_repos.py` lazy port (NOT new `LeadChannelPort`)**.

Reasoning (1000 clientes):
- `LeadModel.telegram_id` is a single column on the existing leads table — not a separate channel registry.
- `crm_repos.py` already exposes lazy-import factories for cross-module CRM access (existing pattern). Extending it adds 1 function vs creating new file with 0 net abstraction.
- A new `LeadChannelPort` would be premature abstraction: WhatsApp/IG/TikTok all use the same shape (`LeadModel.{whatsapp,instagram,tiktok}_id` columns) — the lookup is mechanical per-column. If S4 adds 3 more channels, we can refactor THEN; YAGNI today.
- Alternative rejected: separate `LeadChannelPort` ABC + impl — adds 2 files for 1 single-column lookup. Wasted abstraction.

**File extended**: `backend/src/shared/links/ports/crm_repos.py`

```python
def get_lead_telegram_id(db: Session, tenant_id: UUID, lead_id: UUID) -> str | None:
    """Resolve telegram_id for a lead (tenant-scoped). Lazy-imports LeadModel.

    PR-7 — closes DR-7 (TelegramChannelRouter._resolve_telegram_id STUB).
    Returns None when lead has no telegram_id OR doesn't belong to tenant.
    """
    from sqlalchemy import select

    from src.shared.infrastructure.models.crm import LeadModel

    stmt = select(LeadModel.telegram_id).where(
        LeadModel.id == lead_id,
        LeadModel.tenant_id == tenant_id,
    )
    return db.execute(stmt).scalar_one_or_none()


# Async variant for AsyncSession callers (workers)
async def get_lead_telegram_id_async(
    session: AsyncSession,
    tenant_id: UUID,
    lead_id: UUID,
) -> str | None:
    """Async variant of ``get_lead_telegram_id`` for AsyncSession callers."""
    from sqlalchemy import select

    from src.shared.infrastructure.models.crm import LeadModel

    stmt = select(LeadModel.telegram_id).where(
        LeadModel.id == lead_id,
        LeadModel.tenant_id == tenant_id,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
```

**Wire in `TelegramChannelRouter._resolve_telegram_id`**:

```python
async def _resolve_telegram_id(self, lead_id: UUID, tenant_id: UUID) -> str | None:
    """Resolve telegram_id for a lead via CRM port. PR-7 cierra DR-7."""
    from src.shared.links.ports.crm_repos import get_lead_telegram_id_async

    # Worker passes session via __init__ DI (PR-7 wiring); fallback returns None
    session = getattr(self, "_session", None)
    if session is None:
        return None
    return await get_lead_telegram_id_async(session, tenant_id, lead_id)
```

---

## 7. BudgetGuard helper signature (Sub-G)

**Decisión 33 — helper centralizado en `shared/billing/application/llm_guards.py`** (extend, NOT new file).

Reasoning (1000 clientes):
- Single SSoT for all guarded LLM access. New brand callsites added by future devs invoke helper → automatic guard. Single point of enforcement.
- Helper returns `BudgetGuardingLLMService` wrapping `LLMFactory.get_service()` when `tenant_id` provided. Returns plain `LLMFactory.get_service()` when `tenant_id is None` (test path) — backward-compatible.
- Alternative rejected: per-callsite manual `BudgetGuardingLLMService(...)` instantiation × 7 brand sites = 7 places to maintain, drift-prone, easy to forget. Helper = 1 place.

**File extended**: `backend/src/shared/billing/application/llm_guards.py`

```python
def get_guarded_llm_service(
    *,
    tenant_id: UUID | None,
    agent_kind: str,
    db: Session | None = None,
    model_hint: str | None = None,
) -> Any:
    """Return a BudgetGuard-wrapped LLM service for the given tenant.

    Returns ``LLMFactory.get_service()`` (unguarded) when ``tenant_id`` is None
    (test path) or when BudgetGuard cannot be resolved (DI absent).

    Caller pattern (replaces ``LLMFactory.get_service()``):

        llm = get_guarded_llm_service(tenant_id=tenant_id, agent_kind="brand", db=db)
        response = llm.generate_response(prompt=..., system_prompt=..., ...)

    PR-7 Sub-G — closes DR-7 brand callsites (3 files, 7 sites).

    Args:
        tenant_id: tenant UUID; None disables guarding (returns plain service).
        agent_kind: bucket key for BudgetGuard (``"brand"``, ``"copilot"``,
                    ``"sales_agent"``). NEVER ``"others"`` literal — let BudgetGuard
                    map agent_kind to pool internally.
        db: Session for BudgetGuard repo construction; required when tenant_id set.
        model_hint: optional model SKU hint for cost estimation.

    Returns:
        ``BudgetGuardingLLMService`` if guard available, else plain LLM service.
    """
    from src.shared.infrastructure.llm.factory import LLMFactory

    inner = LLMFactory.get_service()

    if tenant_id is None or db is None:
        return inner

    try:
        from src.shared.billing.application.budget_guard import BudgetGuard
        from src.shared.billing.application.plan_service import PlanService
        from src.shared.billing.infrastructure.budget_repository_impl import (
            BudgetRepositoryImpl,
        )

        guard = BudgetGuard(
            budget_repo=BudgetRepositoryImpl(db),
            plan_service=PlanService(db),
        )
        return BudgetGuardingLLMService(
            inner=inner,
            budget_guard=guard,
            tenant_id=tenant_id,
            agent_kind=agent_kind,
            model_hint=model_hint,
        )
    except Exception as exc:  # noqa: BLE001 — guard infra failure → fail-open
        logger.warning(
            "get_guarded_llm_service_unavailable_fail_open",
            tenant_id=str(tenant_id) if tenant_id else None,
            agent_kind=agent_kind,
            error=str(exc),
        )
        return inner
```

**Brand callsites wired** (mechanical — 3 files, 7 sites):

| File | Pattern before | Pattern after |
|---|---|---|
| `brand/application/voice_fidelity/grader.py:105` | `llm = LLMFactory.get_service()` | `llm = get_guarded_llm_service(tenant_id=tenant_id, agent_kind="brand", db=db)` |
| `brand/application/agents/style_analyzer/nodes.py` (5 callsites at lines 165, 196, 230, 320, 343) | `LLMFactory.get_service().generate_response(...)` | `get_guarded_llm_service(tenant_id=tenant_id, agent_kind="brand", db=db).generate_response(...)` |
| `brand/application/services/personality_service.py:717` | `llm_service = LLMFactory.get_service()` | `llm_service = get_guarded_llm_service(tenant_id=tenant_id, agent_kind="brand", db=db)` |

`tenant_id` + `db` flow into these callsites is already available in the call stacks (per skill brand-expert read of nodes.py + grader.py + personality_service.py — they receive `db: Session` and tenant context). If a callsite truly lacks tenant_id, it's a tenant-isolation bug pre-existing — fix at call-stack root in same PR.

**Ratchet update** (`tests/architecture/test_budget_guard_pre_llm_call.py:29`):
```python
KNOWN_UNGUARDED: frozenset[tuple[str, str]] = frozenset(
    {
        # Sub-H pending — quality_eval workers (defer to S4 if Sub-H not included)
        (
            "src/shared/workers/sales_agent_quality_eval.py",
            "weekly eval cron worker — separate path from ConversationPipeline",
        ),
        (
            "src/shared/workers/copilot_quality_eval.py",
            "weekly eval cron worker — separate path from deep_agent",
        ),
    }
)

# expected_max bumped 5 → 2
expected_max = 2  # PR-7 closed brand 3 entries
```

If Sub-H included: `expected_max = 0` and frozenset empty.

---

## 8. quality_eval workers BudgetGuard (Sub-H — decision build-time)

**Decisión 34 — confirm based on complexity at build time**.

Read of `src/shared/workers/sales_agent_quality_eval.py` and `copilot_quality_eval.py` reveals:
- Cron-only path (weekly Mondays).
- LLMFactory invocations in eval grader inner loop.
- DI pattern: workers receive `db` via `WorkerSettings.on_startup` async session factory.

**Decision rule**: If callsites are ≤2 simple `LLMFactory.get_service()` invocations per worker → wire helper inline (same pattern as brand). Ratchet 5 → 0. **Default: include in PR-7**.

If wiring requires materially refactoring the worker's DI surface (e.g., needs new repos) → defer. Ratchet 5 → 2.

Builder `nicolify-agentic` decides at build step Sub-H based on real callsite shape. CONTRACT exposes both options; IMPL-LOG records which path taken.

---

## 9. Voice fidelity grader prod threshold (Sub-I)

**Decisión 30 — global ENV, NOT per-tenant**.

Reasoning (1000 clientes):
- Voice fidelity is an invariant quality gate (production target). Per-tenant tunable threshold = configuration sprawl, drift-prone, hard to audit. 1000 tenants × per-tenant threshold = ops nightmare.
- Single global threshold = single SSoT, single observability dashboard, single gate. If a specific tenant routinely fails 0.7 → fix the personality_profile (root cause), not the threshold.
- Alternative rejected: `tenant_subscription.custom_overrides["voice_fidelity_threshold"]` → opens door to "lower threshold per tenant" anti-pattern; voice fidelity is brand promise, not negotiable per-tenant.

**Implementation**:
- ENV: `SALES_AGENT_VOICE_FIDELITY_THRESHOLD`
- Default: `0.7` (Decimal/float — read as float)
- Consumed in: `tests/quality/golden/test_voice_fidelity_outbound.py` (golden gate) + future `weekly_sales_agent_quality_eval` cron alarm threshold.
- Loaded via `os.environ.get("SALES_AGENT_VOICE_FIDELITY_THRESHOLD", "0.7")` cast to `float`.

---

## 10. CampaignStep step_type discriminator: AGENT_CONVERSATION vs PLAIN_MESSAGE

**Drift detected and resolved**: sprint.md uses `action_type` as field name; actual codebase uses `step_type` enum on `CampaignStep` model. The values `AGENT_CONVERSATION` vs `PLAIN_MESSAGE` from the prompt map to:

| Prompt term | Real codebase term | Path |
|---|---|---|
| `action_type` | `step_type` (Pydantic field on `CampaignStep`) | `campaigns/domain/campaign_step.py:45` |
| `AGENT_CONVERSATION` | `StepType.CALL_SUBAGENT_BRIEF = "call_subagent_brief"` | `campaigns/domain/enums.py:39` |
| `PLAIN_MESSAGE` | `StepType.SEND_MESSAGE = "send_message"` | `campaigns/domain/enums.py:36` |

PR-7 uses `step_type == StepType.CALL_SUBAGENT_BRIEF` as discriminator. CampaignType `AGENT_CONVERSATION` (top-level campaign type) is the ENTIRE campaign category; `step_type` is the per-step polymorphic discriminator.

CampaignStep `step_config` contract (per `campaign_step.py:30-40`):
```
CALL_SUBAGENT_BRIEF -> {"agent_kind": "sales_agent", "brief": str}
```

PR-7 reads `step.step_config["agent_kind"]` (asserted `== "sales_agent"`) and `step.step_config["brief"]` as `campaign_instructions` for slot 6.

---

## 11. Decisiones 28-36 — todas resueltas en CONTRACT

| # | Decisión | Resolución (1000 clientes lens) | Alternativa rechazada |
|---|---|---|---|
| 28 | AgentState additive vs dataclass separado | **additive (TypedDict)**. Existing pattern (`_llm_service: object | None`) + zero migration + arch test enforces additive. | Dataclass separado: requeriría dual schema, duplicación projection logic, drift between inbound/outbound state shape. |
| 29 | `outbound_mode` flag explícito vs derivado | **flag explícito**. Derivado (e.g., `bool(state.get("campaign_id"))`) is implicit coupling — breaks if state initialised with campaign_id but inbound semantics. Explicit flag = explicit invariant. | Derivado: implicit coupling; future test confusion when `campaign_id` set but `outbound_mode=False` (theoretical legitimate state). |
| 30 | Voice fidelity threshold prod | **0.7 default ENV `SALES_AGENT_VOICE_FIDELITY_THRESHOLD`, NO per-tenant**. Global invariant. | Per-tenant: drift-prone; opens door to "lower threshold for difficult tenant" anti-pattern. |
| 31 | sales_agent_adapter location | **`campaigns/infrastructure/external/`**. Adapter is campaigns-owned (translates campaign domain to sales_agent invocation). Putting in sales_agent forces sales_agent → campaigns DDD violation. | `sales_agent/api/`: DDD violation; `shared/links/`: shared is for ports, adapters live in implementing module's infrastructure. |
| 32 | CRM port — extend `LeadQueryService` vs new `LeadChannelPort` | **extend `crm_repos.py` lazy port** (`get_lead_telegram_id` + async variant). Single column lookup; `LeadChannelPort` is premature abstraction. WhatsApp/IG/TikTok lookups are mechanical per-column variants — refactor THEN if S4 needs. | New `LeadChannelPort` ABC + impl: 2 files for 1 column lookup; YAGNI. |
| 33 | Brand BudgetGuard wiring — helper centralizado | **helper `get_guarded_llm_service` en `shared/billing/application/llm_guards.py`**. Single SSoT; new brand callsites by future devs auto-guarded. | Per-callsite manual `BudgetGuardingLLMService(...)` × 7 sites: drift-prone, easy to forget, 7 places to maintain. |
| 34 | quality_eval workers — incluir PR-7 | **default include if callsites ≤2 simple per worker**; defer if material refactor. Ratchet 5→0 (include) or 5→2 (defer). Builder decides at Sub-H based on real callsite shape. IMPL-LOG records path taken. | Always defer: leaves DR-8 open longer; always include: risks scope creep if workers need refactor. Conditional = right cost-benefit. |
| 35 | Slot 6 CAMPAIGN_CONTEXT cache boundary | **POST slot 5 BRAND_VOICE AND POST slot 6 CHANNEL_FORMAT_HINT** (effectively becomes slot 7 cacheable). Slots 1-6 cache prefix per-tenant invariante across inbound/outbound; campaign-specific instructions go AFTER channel format. Cache hit rate ≥60% per-tenant preserved. | PRE slot 5: rompe cache prefix per-tenant; PRE slot 6: rompe cache prefix per-tenant per-channel; volatile (after marker): no cache benefit despite stable per-campaign-turn. |
| 36 | Outbound supervisor skip-qualifier umbral | **`lead_score >= 40`** (sprint.md tentative confirmed). NOT per-tenant tunable (1000 invariant). If telemetry shows false positives → ENV `SALES_AGENT_OUTBOUND_CLOSER_MIN_SCORE` follow-up adjustment. | Per-tenant: drift; <40: too aggressive (premature closer); ≥60: too conservative (re-qualifier on warm leads = burns turn). |

---

## 12. Invariants (auditor enforces)

1. **Chat path inbound NO rompe**: `outbound_mode=False` (default) → AgentState shape backward-compatible; slot 6 ausente; supervisor routing baseline. Test `test_outbound_orchestrator_non_breaking.py` asserts.
2. **Cache prefix per-tenant NO rompe**: slots 1-6 byte-equal across inbound/outbound for same tenant. `compose.py` arch test `test_system_prompt_order` extended with slot 7 ordering invariant.
3. **Voice fidelity outbound ≥0.7**: golden test ENV-driven gate. Cron weekly reports drift.
4. **Cero direct emit `event_bus.publish`**: outbound flow uses existing audit pattern (AuditEmitter); ratchet preserved.
5. **Tenant isolation en `_resolve_telegram_id`**: query MUST filter `tenant_id` AND `lead_id` (no tenant_id alone, no lead_id alone). Test `test_telegram_resolve_real.py` asserts cross-tenant lookup returns None.
6. **SA pool reservation 50% invariant respected outbound**: `OutboundOrchestrator.send_outbound(budget_guard=...)` propagates to `BudgetGuardingLLMService(... agent_kind="sales_agent")` — consumes SA reserved pool (PR-2 contract). Cero leak Others pool.
7. **Brand `KNOWN_UNGUARDED` shrink 5→2** (or 5→0 if Sub-H included). Ratchet test enforces shrink-only.
8. **Voice SSoT preserved**: NO `brand_voice_summary` table, NO fine-tuning, NO voice-rewriter LLM pass post-gen, NO hardcode voz. Slot 6 contains ONLY campaign instructions, NOT voice rewrite. `personality_profile.system_instruction` remains SSoT.
9. **`{tenant_name}` mid-block forbidden**: `_campaign_context` builder must NOT interpolate tenant identifiers into the cacheable prefix (slot 7 cacheable per-campaign within turn — but across campaigns mid-block injection breaks cache invalidation).
10. **§3 SACRA UNTOUCHED**: Closer Studio API + WS, BufferService.smart_debounce, OutputManager.process_response chunking + CPM_SPEED, agent_state_checkpoint schema, webhook adapters, follow_up_engine cadence, tool_call_dedup. PR-7 reuses without modification.

---

## 13. Tests requeridos

### Unit (with mocks)

| Path | What it covers |
|---|---|
| `tests/modules/sales_agent/application/orchestrator/test_outbound_orchestrator.py` | Happy path; checkpoint reuse; voice/identity wiring; budget guard pass-through; empty-response path; lead_not_found; tenant_not_found |
| `tests/modules/sales_agent/application/prompts/test_compose_slot_campaign_context.py` | `outbound_mode=True` → slot 7 emitted POST slot 6; `outbound_mode=False` → slot 7 absent; cache prefix slots 1-6 byte-equal across modes |
| `tests/modules/sales_agent/application/orchestrator/test_state_additive.py` | `create_initial_state` defaults preserve inbound shape; new fields opt-in |
| `tests/modules/sales_agent/application/agents/sales/test_supervisor_outbound_skip.py` | `outbound_mode=True` + `lead_score=45` → `next_node="closer"`; `outbound_mode=True` + `lead_score=30` → routing normal LLM call; `outbound_mode=False` + lead_score=99 → routing baseline (no skip) |
| `tests/modules/campaigns/infrastructure/external/test_sales_agent_adapter.py` | dispatch happy; rejects non-CALL_SUBAGENT_BRIEF; unsupported agent_kind error code |
| `tests/modules/campaigns/infrastructure/channels/test_telegram_resolve_real.py` | `_resolve_telegram_id` real CRM lookup; tenant isolation; None when no telegram_id |
| `tests/modules/campaigns/infrastructure/channels/test_shared_locale_real.py` | `_resolve_tenant_locale` returns real `(currency, timezone)` from TenantModel.config_json; LRU cache hit; fallback on error |
| `tests/modules/brand/application/test_brand_budget_guard_wiring.py` | grader.py + style_analyzer/nodes.py + personality_service.py invoke `get_guarded_llm_service`; helper returns BudgetGuardingLLMService when tenant_id+db; plain LLMFactory when None |
| `tests/shared/billing/test_get_guarded_llm_service_helper.py` | helper happy + fail-open when guard infra fails |

### Integration F-7 (sin mocks — política PR-4)

| Path | What it covers |
|---|---|
| `tests/integration/test_outbound_orchestrator_e2e.py` | Real DB fixture (tenant + lead with telegram_id + offer + personality_profile) → OutboundOrchestrator dispatch → checkpoint persisted + audit log row + LLM mock returns canned + Telegram channel mock receives formatted text |
| `tests/integration/test_sales_agent_adapter_e2e.py` | Real DB fixture (campaign DAG with CALL_SUBAGENT_BRIEF step + task) → ARQ worker → adapter → orchestrator → channel mock → task marked SENT |
| `tests/integration/test_brand_budget_guard_e2e.py` | Real DB fixture (tenant subscription with brand bucket cap=0.10, mv refresh) → grader invocation → BudgetExceeded raised; cap=10.00 → grader runs successfully |

### Architecture (NEW)

| Path | What it enforces |
|---|---|
| `tests/architecture/test_outbound_orchestrator_non_breaking.py` | AgentState shape pre-PR-7 ⊆ post-PR-7; new fields all `\| None` or have defaults; `create_initial_state(...)` callable with pre-PR-7 args only and produces valid state with `outbound_mode=False`; supervisor routing identical when `outbound_mode=False` |
| `tests/architecture/test_campaign_state_additive.py` | `AgentState.__annotations__` superset of frozen baseline; `create_initial_state` signature additive (only new params with defaults); zero new fields without `\| None` or default; zero existing fields modified or removed |

### Voice fidelity goldens

| Path | What it asserts |
|---|---|
| `tests/quality/golden/test_voice_fidelity_outbound.py` | Real `personality_profile.system_instruction` fixture + outbound conversation (3 turns) → grader score ≥ ENV `SALES_AGENT_VOICE_FIDELITY_THRESHOLD` (default 0.7). Skipped under `RUN_LLM_JUDGE!=1` (matches existing pattern) |

---

## 14. Migrations

**NINGUNA esperada. Confirmed.**

Audit:
- `AgentState` is TypedDict in-memory — no DB column.
- `CampaignStep.step_type StepType.CALL_SUBAGENT_BRIEF` already exists (`enums.py:39`).
- `LeadModel.telegram_id` already exists (`shared/infrastructure/models/crm.py:160`, `unique=True nullable=True`, indexed).
- `TenantModel.config_json` JSONB already exists; `_resolve_tenant_locale` reads `config_json["tenant_locale"]` if set.
- ENV `SALES_AGENT_VOICE_FIDELITY_THRESHOLD` is process-level, not DB.

If during build a migration is discovered necessary: STOP, escalate to PM. Migration in PR-7 = scope violation.

---

## 15. Files affected

### NEW (3)

| Path | Type |
|---|---|
| `backend/src/modules/sales_agent/application/orchestrator/outbound_orchestrator.py` | application/static class |
| `backend/src/modules/campaigns/infrastructure/external/sales_agent_adapter.py` | infrastructure/adapter |
| `backend/src/modules/campaigns/infrastructure/external/__init__.py` | (likely already exists; create if missing) |

### MODIFY (12)

| Path | What changes |
|---|---|
| `backend/src/modules/sales_agent/application/orchestrator/state.py` | `AgentState` + 3 fields; `create_initial_state` + 3 params |
| `backend/src/modules/sales_agent/application/orchestrator/conversation_pipeline.py` | `build_initial_state` accepts campaign fields |
| `backend/src/modules/sales_agent/application/agents/sales/nodes.py` | `node_sales_supervisor` — outbound skip-qualifier branch (5 lines pre-LLM) |
| `backend/src/modules/sales_agent/application/prompts/compose.py` | Slot 7 `CAMPAIGN_CONTEXT` enum + builder + ordering |
| `backend/src/modules/campaigns/workers/execution_task.py` | step_type branch dispatching to SalesAgentAdapter |
| `backend/src/modules/campaigns/infrastructure/channels/telegram.py` | `_resolve_telegram_id` real CRM port wire |
| `backend/src/modules/campaigns/infrastructure/channels/shared.py` | `_resolve_tenant_locale` real lookup with LRU cache |
| `backend/src/shared/links/ports/crm_repos.py` | + `get_lead_telegram_id` + `get_lead_telegram_id_async` |
| `backend/src/shared/billing/application/llm_guards.py` | + `get_guarded_llm_service` helper |
| `backend/src/modules/brand/application/voice_fidelity/grader.py` | LLMFactory → helper (1 site) |
| `backend/src/modules/brand/application/agents/style_analyzer/nodes.py` | LLMFactory → helper (5 sites) |
| `backend/src/modules/brand/application/services/personality_service.py` | LLMFactory → helper (1 site) |
| `backend/tests/architecture/test_budget_guard_pre_llm_call.py` | Ratchet shrink 5→2 (or 5→0) |

### NEW tests (~12)

See §13.

### MODIFY tests

- `tests/architecture/test_system_prompt_order.py` — extend with slot 7 ordering assertion (ratchet)
- Existing `compose.py` tests — assert slot 7 absent when outbound_mode=False

**Total impacted files**: ~30 (3 NEW source + 12 MODIFY source + 12 NEW tests + 3 MODIFY tests + 0 migrations).

---

## 16. Sub-deliverable order (A→K) + dependencies

| Order | Sub | What | Depends on |
|---|---|---|---|
| 1 | Sub-A | AgentState extension + `create_initial_state` + Slot 7 enum/builder | none |
| 2 | Sub-A.5 | `compose.py` `_campaign_context` builder + ordering + tests | Sub-A |
| 3 | Sub-B | `OutboundOrchestrator.send_outbound` + tests | Sub-A |
| 4 | Sub-C | Supervisor `outbound_mode` skip-qualifier branch + tests | Sub-A, Sub-B |
| 5 | Sub-E | CRM port `get_lead_telegram_id` + Telegram wire + tests | none |
| 6 | Sub-F | `_resolve_tenant_locale` real lookup + tests | none |
| 7 | Sub-D | `SalesAgentAdapter` + worker dispatch branch + tests | Sub-B, Sub-E |
| 8 | Sub-G | `get_guarded_llm_service` helper + brand wiring + ratchet shrink | none (parallel to A-F) |
| 9 | Sub-H | quality_eval workers wiring (decision build-time) | Sub-G |
| 10 | Sub-I | Voice fidelity ENV + golden test | Sub-A, Sub-B |
| 11 | Sub-J | All tests final pass + arch tests +2 | Sub-A through I |
| 12 | Sub-K | IMPL-LOG.md + current-state updates | all |

Sub-A through Sub-F can be parallelized within `nicolify-agentic` build; Sub-G can be picked up by `nicolify-backend` builder in parallel session (helper is independent of agentic surface). Convergence at Sub-J for full test suite + arch ratchet.

---

## 17. Research notes

No novel patterns. Architecture cementada in `docs/domains/sales-agent/redesign-2026-04/` (S0-S12 closed) + PR-2 + PR-5 + PR-6 of PI-1 S0/S2. Sources:
- LangGraph subgraph reuse pattern: `tessl__langgraph` skill (state-aware nodes, callback handler propagation via config).
- Anthropic prompt cache prefix stability: `https://platform.claude.com/docs/en/build-with-claude/prompt-caching` (accessed 2026-04-30) — confirms cache prefix invariance requirement; OpenAI prompt cache contract (April 2026) requires ≥1024 contiguous tokens of unchanged prefix; Kimi K2.6 + DeepSeek V3/V4 same auto-cache contract.
- DDD adapter pattern in infrastructure layer: backend-ddd.md + Eric Evans' DDD; campaigns owns adapter, lazy-imports sales_agent.
- Tenant isolation invariant: `.claude/rules/tenant-isolation.md` — every query filters tenant_id including get_by_id.
- Voice SSoT preserved: `.claude/rules/sales-agent-brand-voice.md` SACRA — slot 5 BRAND_VOICE = `personality_profile.system_instruction`; slot 6 CHANNEL_FORMAT_HINT cacheable per-channel; slot 7 CAMPAIGN_CONTEXT cacheable per-campaign within turn.
- Knowledge cutoff disclosure: Opus 4.7 cutoff Jan 2026; PR-7 architecture is internal codebase work (no post-cutoff library research needed beyond canonical docs above).

---

## 18. Open questions

ZERO. Todas las decisiones 28-36 resueltas en este CONTRACT con razón "1000 clientes" + alternativa rechazada documentada.

