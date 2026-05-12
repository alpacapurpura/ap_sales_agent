---
story_id: luana-sales-agent-engine
agentic_arch_version: 1
last_modified: 2026-05-11
drafted_by: /architect-orchestrator (claude-opus-4-7)
authority: 03-arch.md §8 + sales-agent-expert SKILL.md §3 protected surfaces + S0-S12 cement + ADR-001 §2.4 BrandVoicePort + anti-duplication.md
mandate: "Lift verbatim per outcome §7.3 — preserve LangGraph state, supervisor specialist routing, slot 5 BRAND_VOICE via D-T3 BrandVoicePort, observability subclass pattern, channel format consumption, follow_up_engine cadence, closer_studio API+WS, SmartBufferService, OutputManager chunking, §3 protected surfaces verbatim"
---

# Story 7 — Sales Agent Agentic Surface — Architecture Detail

> Companion to `03-arch.md`. Documents sales_agent agentic-specific structure: supervisor-pattern specialist routing, 5-slot prompt cache (slot 5 BRAND_VOICE via D-T3 BrandVoicePort), tool registry (scheduler/payment/qualification/knowledge/follow-up), closer_studio API+WS preserved verbatim, observability subclass pattern (D-T6), §3 protected surfaces preservation.

## §1. LangGraph state (TypedDict — preserve verbatim per S0-S12 cement)

File: `luana_core_sales_agent.application.orchestrator.state` — class `SalesAgentState(TypedDict)`.

**State keys (AISALESHT current — verbatim preserve):**

```python
class SalesAgentState(TypedDict, total=False):
    # Identity (cacheable cross-tenant)
    tenant_id: str
    conversation_id: str
    lead_id: str | None
    
    # Conversation
    messages: Annotated[list[BaseMessage], add_messages]
    
    # Iteration guard
    iterations: Annotated[int, operator.add]
    
    # Specialist routing (supervisor pattern)
    current_specialist: str  # qualifier | product_expert | closer | supervisor | tool_executor | safety | escalate
    routing_decision: dict   # last classifier output (tier + confidence + reason)
    
    # Channel context
    channel_type: str        # whatsapp | telegram | instagram | web
    channel_format_hint: str | None  # injected via luana_core_channels.format_for_channel
    intent_detected: str | None       # luana_core_channels.intent_detector output
    
    # Voice (D-T3 BrandVoicePort consumed)
    brand_voice_system_instruction: str  # slot 5 BRAND_VOICE cache prefix (filled by BrandVoicePort.compile_system_instruction)
    voice_metadata: dict                  # personality_profile_version + dimensions_summary
    
    # Tools
    tool_calls_seen: dict[str, int]      # ★§3 protected — anti-loop dedup
    last_tool_result: Any
    
    # Buffer service (SmartBufferService runner)
    buffer_state: dict                    # ★§3 protected — debounce window state
    
    # Output manager
    pending_outbound: list[dict]          # ★§3 protected — OutputManager.process_response chunked
    typing_simulation_cpm: float | None  # S12 per-channel override
    
    # Enrollment / payment state
    enrollment_state: dict | None         # ★§3 protected
    payment_state: dict | None
    
    # Audit emitter (tracing)
    audit_events: list[dict]
    
    # Observability + cost
    obs: SalesAgentObservabilityContext  # ★ D-T6 subclass — consumed from luana_core_sales_agent.observability.recording
    
    # Quality / judge (eval surface — but eval simulator NOT lifted per ratificación 2)
    quality_grade: dict | None
    
    # Compliance gates
    compliance_check_result: dict | None  # WABA 24h, opt-in, blacklist
    
    # Budget gating (PR-2 wired Story 2 — primitives available, sales_agent specialists consume)
    budget_decision: dict | None
```

**State path:** `luana_core_sales_agent/application/orchestrator/state.py` — FROZEN at lift moment.

## §2. Topology — Supervisor pattern with specialists (NOT deepagents subagents)

Per sales-agent-expert SKILL.md cemented post-S12. Selected topology: **supervisor pattern routing to specialists**.

### §2.1 Specialist nodes (StateGraph nodes preserved verbatim)

| Node | Role | Tools accessible | Routing source |
|---|---|---|---|
| `supervisor` | route decision based on intent + lead state | (no LLM tool calls — routing only) | LLM classification (NANO) + semantic_router rules |
| `qualifier` | lead qualification specialist | qualification tools subset | supervisor → qualifier when lead unqualified |
| `product_expert` | product/offer info specialist | knowledge_search, offer_section_tools, offer_ladder_tools | supervisor → product_expert when info-seeking |
| `closer` | booking + payment closer | scheduling tools, payment tools | supervisor → closer when buy-intent + qualified |
| `tool_executor` | dispatches arbitrary tools | ALL tools (via budget guard) | supervisor → tool_executor on ambiguous |
| `safety` | content safety filter | SafetyService rules | every output passes through safety pre-emit |
| `escalate` | hand-off to human | (notifies operator via closer_studio WS) | safety FAIL or supervisor escalation |

### §2.2 Edges

- `START` → `supervisor` (every turn enters supervisor)
- `supervisor` → conditional: `qualifier | product_expert | closer | tool_executor | escalate`
- All specialists → `safety` (mandatory post-output gate)
- `safety` → conditional: `END` (PASS) OR `escalate` (FAIL)
- `escalate` → `END` (terminal — human takes over)

### §2.3 Checkpointer

`AsyncPostgresSaver` for `agent_state_checkpoints` table (★§3 protected — schema plural, do not modify).

## §3. Slot architecture (5 slots — preserve per S3 cemented)

File: `luana_core_sales_agent.application.prompts.compose` — function `compose_prompt(...)`.

**Slot order (verbatim sales-agent-expert SKILL.md + ADR-001 §2.4):**

```
SLOT 1 [cacheable cross-tenant]   AGENT_IDENTITY (specialist persona base)   ← TTL 1h
SLOT 2 [cacheable cross-tenant]   TOOLS_MANIFEST (per specialist)            ← TTL 1h
SLOT 3 [cacheable cross-tenant]   DOMAIN_CONTEXT (sales domain knowledge)    ← TTL 1h
SLOT 4 [cacheable per-tenant]     OFFER_CATALOG_CONTEXT (tenant's offers)    ← TTL 5min
SLOT 5 [cacheable per-tenant]     BRAND_VOICE                                ← TTL 5min ★ D-T3
                                  ┌─ cache_control breakpoint ─┐
SLOT 6 [volatile per-turn]        CONVERSATION_HISTORY + LEAD_CONTEXT + CURRENT_TURN
                                  + channel_format_hint (luana_core_channels) + intent_detected
```

**SLOT 5 BRAND_VOICE injection (D-T3 — KEY ARCHITECTURAL DECISION):**

Per ADR-001 §2.4 + Story 5 §9.4 deferral resolution:

```python
# In luana_core_sales_agent.application.prompts.compose:
from luana_core_brand_studio.application.ports.brand_voice_port import BrandVoicePort

async def compose_prompt(
    specialist: str,
    state: SalesAgentState,
    voice_port: BrandVoicePort,         # injected via DI
    ...
) -> list[ChatCompletionContentPartParam]:
    ...
    # Slot 5 BRAND_VOICE — D-T3 hexagonal consumption
    brand_voice_text = await voice_port.compile_system_instruction(state["tenant_id"])
    voice_metadata = await voice_port.get_voice_metadata(state["tenant_id"])
    state["voice_metadata"] = voice_metadata  # for cache invalidation logic
    
    slots[5] = {
        "type": "text",
        "text": brand_voice_text,
        "cache_control": {"type": "ephemeral"},  # TTL 5min default per tenant
    }
    ...
```

**TTL choice ratification:**
- Slots 1-3 cross-tenant invariants → `ttl: "1h"` (specialist + tools + domain shared across tenants).
- Slots 4-5 per-tenant invariants → 5min default (regen when tenant offer catalog or PersonalityProfile updates).
- Slot 6 volatile → no cache marker.

**Cache invalidation triggers (per F8 + ADR-001 §2.4):**
- PersonalityProfile bumped (tenant edits voice) → `get_voice_metadata.personality_profile_version` bumps → cache key prefix changes → slot 5 cache invalidates.
- Offer catalog mutation → slot 4 invalidates.
- Tool registry change → slot 2 invalidates (entire cache prefix).

**Validation:**
- Every LLM call records `cache_creation_input_tokens` + `cache_read_input_tokens` to module-scoped `sales_agent_llm_call` (Story 7 module-scoped repo) — separate from `copilot_llm_call`.
- Admin `/sales-routing` Streamlit page displays `avg_cache_hit_rate`.
- Target: ≥60% post-deploy (S12 cement).

**Forbidden in slot 5 BRAND_VOICE prefix:**
- `{tenant_name}` interpolation mid-block — voice compiler emits whole block as cacheable unit; injecting tenant_name mid-block invalidates cache every turn (S12 §"NO inyectar `{tenant_name}` mid-block cache prefix").
- Timestamps, conversation IDs, turn counters.

## §4. Tool registry — 5 base tool groups (scheduler/payment/knowledge/qualification/follow-up)

File: `luana_core_sales_agent.application.tools.registry` — ToolRegistry SSoT for sales_agent.

**Tool groups + STAGE_TOOL_SCOPE per S12:**

| Group | Tools | Stage scope |
|---|---|---|
| `qualification` | qualify_lead, ask_qualification_questions, update_lead_state | qualifier specialist |
| `knowledge` | knowledge_search, offer_section_lookup, offer_ladder_query | product_expert |
| `scheduling` | book_meeting, list_available_slots, get_booking_status, reschedule | closer (via tools/scheduling/providers.py strategy pattern) |
| `payment` | create_payment_link, verify_payment_status, grant_access, list_payment_methods | closer (via tools/payment/providers.py strategy pattern) |
| `follow_up` | schedule_followup, check_followup_due, mark_followup_done | follow_up_engine worker |
| `safety` | check_compliance, escalate_to_human | safety + escalate specialists |

**Tool registry pattern:** Tools register with explicit `groups=("qualification",)` etc. STAGE_TOOL_SCOPE maps specialist → allowed groups. Verified at tool dispatch time.

**Lift verbatim** — registry public API FROZEN at lift moment per D-T1 (sales_agent registry parallels copilot's per Story 6 — same Tool dataclass shape).

## §5. Channel format consumption (luana_core_channels — Story 2 SSoT)

Sales agent consumes (NEVER re-registers):

```python
# luana_core_sales_agent.infrastructure.external.output_manager:
from luana_core_channels.format import get_channel_format

async def process_response(self, channel_type: str, message: str) -> list[ChunkedMessage]:
    fmt = get_channel_format(channel_type)
    # ★§3 protected — CPM_SPEED + cap calibrated. typing_simulation_cpm per-channel override (S12 registry).
    cpm = fmt.typing_simulation_cpm or self.CPM_SPEED_DEFAULT
    ...
```

**S12 cement:** `typing_simulation_cpm` per-channel override via registry. Fallback `CPM_SPEED_DEFAULT` global.

## §6. Observability (consume luana-core-observability, NEVER mirror — D-T6)

### §6.1 Subclass pattern (parallels copilot Story 6 §7)

`luana_core_sales_agent/observability/recording/callback_handler.py`:
```python
from luana_core_observability.recording.base_callback_handler import BaseAgentCallbackHandler
from luana_core_observability.recording.sanitization import sanitize_payload
from luana_core_observability.recording.cost_recorder import pop_cost

class SalesAgentCallbackHandler(BaseAgentCallbackHandler):
    """Per S0/S11A Template Method — implement 2 hooks only."""
    
    async def _persist_llm_call_row(self, row: dict) -> None: ...
    async def _persist_trace_event_row(self, row: dict) -> None: ...
```

`turn_envelope.py` → `SalesAgentObservabilityContext(BaseObservabilityContext)`.

### §6.2 Module-scoped tables

| Table | Module-scoped repo | Schema source |
|---|---|---|
| `sales_agent_llm_call` | `SalesAgentLLMCallRepository` | Story 2 — schema in luana_core_observability migration (parallel to copilot_llm_call) |
| `sales_agent_trace_event` | `SalesAgentTraceEventRepository` | idem |
| `sales_agent_routing_log` | `RoutingLogRepository` | sales-agent-local table |
| `agent_state_checkpoints` | (AsyncPostgresSaver native) | ★§3 protected — schema plural |

### §6.3 Cost recording (S12 + PI-12 S1 T-1 cement)

- `cost_usd` via `pop_cost(litellm_call_id)` — CustomLogger bridge. NEVER `calculate_cost()` runtime.
- Tier pricing (Kimi K2.6 input_cost_per_token_above_200k_tokens): split at 200_000 threshold per S12.
- `provider_canonical` resolved via shared `_canonical_provider()`.
- Best-effort writes: try/except + structlog warning + db.rollback.

### §6.4 Eval-related observability — DEFERRED Luana v0.2.0

Per Session 3 ratificación 2 + outcome §2 OQ1:
- `eval_simulator_llm_call` table — DEFERRED
- `eval_simulator_trace_event` — DEFERRED
- `eval_simulator_grade` + `eval_simulator_grade_cache` — DEFERRED
- `eval_synthetic_tenants` — DEFERRED

**Cost-bucket invariant preserved at architecture level:** when v0.2.0 lifts eval framework, the cost-bucket separation table layout (eval_simulator_* writes are NOT mixed with sales_agent_llm_call production cost) lifts WITH it. Until then, eval framework lives in nicolify shell separately.

## §7. §3 protected surfaces — preservation verification

Per sales-agent-expert SKILL.md §3 "NO TOCAR":

| Surface | File | Preservation strategy |
|---|---|---|
| Closer Studio API | `api/closer_studio.py` | Lift verbatim — line-level. Live ops + Streamlit FE + WS depend. Hash snapshot. |
| Closer Studio WS | `api/ws.py` | Lift verbatim. Hash snapshot. |
| SmartBufferService | `application/orchestrator/smart_debounce_runner.py` | Lift verbatim. CPM/canales LATAM tuned. Hash snapshot. |
| OutputManager.process_response | `infrastructure/external/output_manager.py` | Lift verbatim. CPM_SPEED + cap calibrated. typing_simulation_cpm registry override (S12) preserved. Hash snapshot. |
| Enrollment end-to-end | `application/services/enrollment_service.py` + `domain/enrollment.py` + `infrastructure/models/enrollment_model.py` + `api/enrollments.py` | Lift verbatim. Production. S9 extension hooks preserved. |
| agent_state_checkpoints schema | (Alembic migration — stays in AISALESHT until Story 10) | DO NOT TOUCH. Plural table name (per S0 cement). |
| Webhook adapters | `application/tools/payment/webhook_providers.py` + `application/tools/scheduling/webhook_providers.py` | Lift verbatim. Auth + signature frágiles. |
| Follow-up engine cadence | `workers/follow_up_engine.py` | Lift verbatim. Timing horario + tz tenant. |
| PromptVersionModel | `infrastructure/models/prompt_version_model.py` | Lift verbatim. Sales needs override DB-backed per tenant. |
| model_pricing_snapshot | Story 2 lifted to luana_core_observability | NO touch. Cross-agent reference data. |
| tool_call_dedup.py | `application/orchestrator/tool_call_dedup.py` | Lift verbatim. Anti-loop post fbc79125. |

**V-AG-8 arch test computes sha256 of each file at lift moment vs AISALESHT source.** Mismatch FAIL.

## §8. Skill decisions referenced

| Skill | Decision |
|---|---|
| `sales-agent-expert` | §3 protected surfaces preserved (12 files). Voice = PersonalityProfile.system_instruction. Slot 5 BRAND_VOICE. typing_simulation_cpm registry (S12). LLM_ROLE_BY_SITE SSoT. Channel registry consumption. Spanish voseo allowed in output (tenant voice) — exception to .claude/rules/spanish-text.md. |
| `copilot-expert` | Sales agent IS a copilot module via copilot_provider/provider.py — subclasses BaseCopilotProvider from luana_core_copilot. |
| `tessl__langgraph` | Supervisor specialist routing. StateGraph + AsyncPostgresSaver. Stream `messages` mode. |
| `claude-api` prompt caching | 5-slot order. Slot 5 BRAND_VOICE TTL 5min per-tenant. cache_control breakpoint after slot 5. Min 4096 tokens Opus 4.7. |
| `anti-duplication.md` | D-T6 anti-mirror observability. Sales-agent subclasses BaseAgentCallbackHandler + BaseObservabilityContext from luana_core_observability. |
| `auditor-downstream-regression.md` | Surface→downstream test map. Sales agent lift = scope all ~75 sales_agent tests (excluding eval simulator) + Stories 2-6 packages re-test post brand-studio port introduction + connections wiring update. |
| `tessl__graceful-degradation` | Every external call (LLM, payment provider, scheduler provider, webhook delivery) has timeout + fallback per sales-agent-expert SKILL.md. |
| `ADR-001 §2.4` | BrandVoicePort hexagonal — Story 7 introduces port + adapter. PersonalityCompiler stays SSoT in luana-core-brand-studio.domain.personality. Sales-agent NEVER imports PersonalityCompiler directly. |
