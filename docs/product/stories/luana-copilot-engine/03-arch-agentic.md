---
story_id: luana-copilot-engine
agentic_arch_version: 1
last_modified: 2026-05-11
drafted_by: /architect-orchestrator (claude-opus-4-7) — sub-architecture detail for agentic surface per architect skill mandate
authority: 03-arch.md §8 + copilot-expert SKILL.md F0-F11 + sales-agent-expert SKILL.md (cross-reference) + anti-duplication.md + ADR-001 §2.4
mandate: "Lift verbatim per outcome §7.3 — preserve LangGraph state, deepagents harness, Anthropic prompt cache slots, Qdrant RAG tenant filtering, 36 [COPILOT-*] anchors, registry public contracts (D-T1 FROZEN)"
---

# Story 6 — Copilot Agentic Surface — Architecture Detail

> Companion to `03-arch.md`. This file documents the agentic-specific structure: LangGraph state, subagent topology, prompt cache slots, ToolRegistry/WorkflowRegistry/ExtractorRegistry signatures (D-T1 frozen), observability writes, Qdrant RAG. **Builder-agentic Opus reads this file plus 03-arch.md as joint contract.**

## §1. LangGraph state (TypedDict — preserve verbatim)

File: `luana_core_copilot.application.orchestrator.state` — class `CopilotState(TypedDict)`.

**State keys (AISALESHT current — verbatim preserve):**

```python
class CopilotState(TypedDict, total=False):
    # Identity (cacheable cross-tenant per slot 1)
    tenant_id: str                              # MANDATORY every state — tenant isolation in graph
    conversation_id: str                         # turn-stable for checkpointer

    # Conversation (variable per turn)
    messages: Annotated[list[BaseMessage], add_messages]  # ★ add_messages reducer ★

    # Iteration guard (max-iter exit)
    iterations: Annotated[int, operator.add]    # increments per node visit; cap = COPILOT_RECURSION_LIMIT env (default 25)

    # Route resolver outputs (per turn)
    route: str                                   # "brand_studio" | "offer_studio" | "general" | etc.
    entity_id: str | None                        # offer_id / brand_id / etc.
    channel_type: str                            # "whatsapp" | "telegram" | "instagram" | "web"
    channel_intent: str | None                   # FP2 — channel_intent_detector regex output

    # Plan card (deepagents write_todos output)
    plan: list[dict]                             # F2 — plan_card SSoT (rendered as card via SSE v2)

    # Subagent isolation
    todos: list[dict]                            # deepagents native task tracking
    subagent_output: dict[str, Any]              # last subagent return

    # Tool execution
    tool_calls_seen: dict[str, int]              # F0 — anti-loop dedup tracker
    last_tool_result: Any

    # Lighthouse (slot 4 — cacheable per-tenant)
    brand_summary: dict[str, Any]                # F3 — brand_lighthouse pre-rendered

    # Inspirations (slot 8 — volatile per-turn)
    inspirations: list[dict]                    # F4 — fetched URLs + extractions

    # Workflow state (F12 — future, dual-read enabled)
    workflow_state: dict[str, Any] | None       # JSONB-backed via migration 071
    procedure_state: dict[str, Any] | None      # legacy — dual-read both during F12 cutover

    # Mutation journal accumulator (per turn)
    mutations_proposed: list[dict]

    # Observability + cost
    obs: CopilotObservabilityContext             # ★ CONSUMED from luana_core_copilot.observability.recording (which inherits BaseObservabilityContext from luana_core_observability)
    trace_event_recorder: callable               # best-effort write

    # Stream filters (SSE v2)
    streaming_enabled: bool                      # default True post-F8
    sse_block_ids: list[str]                     # block_start/block_end correlation

    # Workflow_handlers lazy-resolved (per F6)
    workflow_handler_cache: dict[str, callable]

    # Routing log (F8)
    routing_log_entry: dict | None               # tier + classifier + confidence + tools_available

    # Channel intent hint (FP2)
    channel_intent_hint: str | None

    # Voice (when transcription endpoint feeds messages)
    voice_input_meta: dict | None                # transcription metadata
```

**Reducers (preserved verbatim):**
- `messages`: `langgraph.graph.message.add_messages` (append, dedup by id)
- `iterations`: `operator.add` (accumulator)
- All other dict/list keys: default overwrite (no reducer — last-write-wins)

**State path:** `luana_core_copilot/application/orchestrator/state.py` — class signature FROZEN at lift moment.

## §2. Topology — single graph + deepagents harness + 4 subagents

Selected topology: **deepagents `task` tool with explicit subagents** (NOT supervisor pattern). Reason: copilot's domain is "guided exploration + extraction + mutation" — sub-agents handle context-isolated heavy tasks (URL analysis, data query, audit). Single supervisor would over-route.

**Per F2 + copilot-expert SKILL.md** — `build_deep_agent_graph` constructs LangGraph 2.0 StateGraph with deepagents middleware injected. Lift verbatim from `luana_core_copilot/application/orchestrator/deep_agent.py` + `graph.py`.

### §2.1 Graph nodes (preserved verbatim)

| Node | Async fn signature | Returns | Edge type |
|---|---|---|---|
| `START` → `route` | `async def route_node(state) -> dict` | `{"route": str, "entity_id": str, "channel_type": str, "iterations": 1}` | conditional |
| `route` → `agent` | direct edge | — | direct |
| `agent` (ReAct loop) | LLM call + tool decision | `{"messages": [response]}` | conditional via `should_continue` |
| `tools` (ToolNode prebuilt) | `langgraph.prebuilt.ToolNode(tools)` | `{"messages": tool_messages, "last_tool_result": Any}` | direct → agent |
| `subagent_task` (deepagents `task` tool entry) | spawns isolated SubAgent state | `{"subagent_output": dict, "messages": [synth]}` | direct → agent |
| `mutation_apply` | applies proposed mutations via `MutationApplyService` | `{"mutations_applied": [...]}`  | conditional |
| `synth` | final response composition | `{"messages": [final], "iterations": +1}` | → END |
| max-iter guard in `should_continue` | `if state["iterations"] > settings.COPILOT_RECURSION_LIMIT: return END` | — | explicit cap |

### §2.2 Subagents (deepagents — 4 explicit, tools= explicit list per F2 pattern)

Verbatim lift from `luana_core_copilot/application/orchestrator/subagents/`:

| SubAgent name | File | Tools (explicit list, F2 sandbox rule) | Allowed state keys IN | Allowed state keys OUT |
|---|---|---|---|---|
| `URL_ANALYZER_SUBAGENT` | `subagents/url_analyzer.py` | `[fetch_url, pin_to_memory]` (F4 sandbox) | `messages`, `tenant_id`, `route` | `messages`, `inspirations` |
| `DATA_QUERY_SUBAGENT` | `subagents/data_query.py` | `[ask_tenant_data, knowledge_search]` (F5 — internal data query) | `messages`, `tenant_id`, `entity_id`, `route` | `messages`, `subagent_output` |
| `AUDIT_INSPECTOR_SUBAGENT` | `subagents/audit_inspector.py` | `[mutation_apply, knowledge_search]` (debugging mutations) | `messages`, `tenant_id`, `mutations_proposed` | `messages` |
| (deepagents native `task` tool) | injected via `deepagents.SubAgentMiddleware` | — | — | — |

**deepagents version pinned: `>=0.5.3`** (matches AISALESHT current). `SubAgentMiddleware(subagents=[URL_ANALYZER_SUBAGENT, DATA_QUERY_SUBAGENT, AUDIT_INSPECTOR_SUBAGENT])` registered at graph compile time.

### §2.3 Routing (NANO classifier + rule classifier + ModelRouter — F8)

File: `luana_core_copilot/application/router/`

- `LLMClassifier` (NANO model `gpt-4o-mini` per F8 — env override `COPILOT_NANO_MODEL`). Threshold 0.7 auto-act vs fallback.
- `RuleClassifier` deterministic rules (regex pattern matchers).
- `ModelRouter.classify()` dispatches based on tier (NANO/FAST/REASONING/AGENT).
- Routing decisions logged to `copilot_routing_log` table (admin/copilot-routing Streamlit page consumes).

## §3. Prompt cache architecture (Anthropic — 11-slot order per F8 + F10)

File: `luana_core_copilot/application/orchestrator/system_prompt_composer.py` — function `compose_system_prompt(fragments) -> list[dict]`.

**Slot order (verbatim from copilot-expert SKILL.md §"System prompt order"):**

```
SLOT 1 [cacheable cross-tenant]   static_identity                  ← TTL 1h, change ≤weekly
SLOT 2 [cacheable cross-tenant]   tools_hint                       ← TTL 1h, changes when ToolRegistry changes
SLOT 3 [cacheable cross-tenant]   marketing_kb_hint                ← F10 — TTL 1h, changes when KB doc adds/removes
SLOT 4 [cacheable per-tenant]     lighthouse (brand_summary)       ← F3 — TTL 5min, regen via ARQ worker
SLOT 5 [cacheable per-tenant]     editable_catalog                 ← TTL 5min, derived from FieldContract
SLOT 6 [cacheable per-tenant]     modules_list                     ← TTL 5min, from module_registry
                                  ┌─ cache_control breakpoint ─┐
SLOT 7 [volatile per-turn]        completion_snapshot + behavior + guided + studio  ← F0/F8 per-turn
SLOT 8 [volatile per-turn]        inspirations_layer                ← F4 state-aware
SLOT 9 [volatile per-turn]        workflow_state hint               ← F12 future
SLOT 10 [volatile per-turn]       channel_intent_hint               ← FP2 — regex middleware output
SLOT 11 [volatile per-turn]       deep_agent_suffix                 ← F2 — always last (deepagents anchor)
```

**TTL choice ratification:**
- Slots 1-3 cross-tenant invariants → **`ttl: "1h"`** (rationale: shared across all tenants, write cost amortized over many reads). Per F8 cache hit rate target ≥60%.
- Slots 4-6 per-tenant invariants per-turn → **5min default** (rationale: within turn 5-10 multi-turn flow, regen via brand_summary_regen ARQ worker on brand event).
- Slots 7-11 volatile → NO cache_control marker (rebuilt per turn).

**Min cacheable tokens: 4096 (Claude Opus 4.7).** F8 enforces prefix ≥1024 tokens for Sonnet (legacy floor), but Opus 4.7 requires 4096. **Per F8 cement:** lighthouse (slot 4) populated for tenant + editable_catalog (slot 5) + modules_list (slot 6) → prefix size 8-12k tokens → comfortably above 4096 floor.

**Cache invalidation triggers (preserve per F8):**
- Tool definition change (ToolRegistry mutation) → entire cache invalidates (slots 1-6 ✘). Acceptable — tool changes are rare.
- Lighthouse regen → slot 4 onward ✘. Acceptable — driven by brand event.
- Editable catalog change (FieldContract bump) → slot 5 onward ✘.

**Validation (mandatory observability writes):**
- Every LLM call records `cache_creation_input_tokens` + `cache_read_input_tokens` to `copilot_llm_call` table.
- Admin `/copilot-routing` dashboard (Streamlit) displays `avg_cache_hit_rate` aggregate.
- Target: **≥60% cache read rate post-deploy** (per F8 cost guard).
- Forbidden in cacheable prefix: timestamps, conv IDs, turn counters, random IDs, `{tenant_name}` interpolation mid-block (use slot boundary instead).

**File: `system_prompt_composer.py` FROZEN public API:**
```python
def compose_system_prompt(
    static_fragments: list[str],         # slots 1-3
    per_tenant_fragments: list[str],     # slots 4-6 (cacheable per-tenant)
    volatile_fragments: list[str],       # slots 7-11
    cache_breakpoint_after: int = 6,    # boundary slot index (default 6)
    ttl_long_hours: bool = True,         # slots 1-3 use 1h cache
) -> list[ChatCompletionContentPartParam]: ...
```

Reorder = breaking change. Arch fitness V-AG-3 golden snapshot enforces signature stability.

## §4. ToolRegistry / WorkflowRegistry / ExtractorRegistry (D-T1 FROZEN public contracts)

### §4.1 ToolRegistry

File: `luana_core_copilot/application/tools/registry.py`

```python
@dataclass(frozen=True)
class Tool:
    """LangChain @tool — frozen public API."""
    name: str
    description: str
    function: Callable
    groups: tuple[str, ...]                     # e.g. ("brand", "always_available")
    schema: type[BaseModel] | None              # Pydantic input schema
    tenant_scoped: bool = True                  # MANDATORY for state queries
    external_calls: bool = False                # if True, wrap with timeout+fallback per tessl__graceful-degradation

class ToolRegistry:
    @classmethod
    def register(cls, tool: Tool, /) -> None: ...
    @classmethod
    def get(cls, name: str) -> Tool | None: ...
    @classmethod
    def list(cls) -> list[Tool]: ...
    @classmethod
    def groups(cls) -> dict[str, list[Tool]]: ...
    @classmethod
    def reset(cls) -> None: ...                 # test-only

# Module-level constants (FROZEN — V-AG-3 snapshot):
_BASE_TOOL_GROUPS: dict[str, list[Tool]] = {...}
ALWAYS_AVAILABLE_GROUPS: tuple[str, ...] = ("always_available", "navigation", "memory")
ROUTE_TOOL_MAP: dict[str, list[str]] = {...}   # F7 + F8 — per-route tool budget
```

### §4.2 WorkflowRegistry

File: `luana_core_copilot/application/workflows/registry.py`

```python
@dataclass(frozen=True)
class Workflow:
    """Declarative workflow definition — F6."""
    id: str
    name: str
    steps: list[WorkflowStep]
    handler_ref: str                            # lazy ref to handler_handlers.py — F6 anti-circular-import pattern
    domain: str                                 # "brand" | "offer" | "campaigns" | ...

class WorkflowRegistry:
    @classmethod
    def register(cls, wf: Workflow, /) -> None: ...
    @classmethod
    def get(cls, wf_id: str) -> Workflow | None: ...
    @classmethod
    def list_by_domain(cls, domain: str) -> list[Workflow]: ...
    @classmethod
    def reset(cls) -> None: ...
```

### §4.3 ExtractorRegistry

File: `luana_core_copilot/domain/extraction_domain_registry.py`

```python
@dataclass(frozen=True)
class ExtractorDomain:
    """Field-contract-platform extractor domain — F9 + Fase-09."""
    domain_key: str                             # "brand" | "offer" | "buyer_persona" | "landing"
    field_contract_module: str                  # module path to FieldContract subclass
    persister_class: type                       # subclass of FieldPersister

class ExtractorRegistry:
    @classmethod
    def register(cls, ext: ExtractorDomain, /) -> None: ...
    @classmethod
    def get(cls, domain_key: str) -> ExtractorDomain | None: ...
    @classmethod
    def list(cls) -> list[ExtractorDomain]: ...
```

### §4.4 ModuleRegistry

File: `luana_core_copilot/domain/module_registry.py`

```python
@dataclass(frozen=True)
class ModuleDescriptor:
    """Per-package descriptor — F1."""
    module_key: str
    display_name: str
    package_path: str                           # e.g. "luana_core_brand_studio"
    data_access_kinds: tuple[str, ...]          # kinds the module exposes for ask_tenant_data
    tools: tuple[str, ...]                      # tool names the module contributes
    workflows: tuple[str, ...]                  # workflow IDs the module exposes

class ModuleRegistry:
    @classmethod
    def discover(cls) -> None: ...              # pkgutil scan for copilot_provider/ subfolders
    @classmethod
    def get(cls, module_key: str) -> ModuleDescriptor | None: ...
    @classmethod
    def list_modules(cls) -> list[ModuleDescriptor]: ...
```

### §4.5 SuggestionRegistry

File: `luana_core_copilot/application/suggestions/registry.py`

```python
class SuggestionProvider(Protocol):
    """F0 — pure-expansion provider pattern."""
    async def suggestions_for(self, tenant_id: UUID, context: dict) -> list[Suggestion]: ...

class SuggestionRegistry:
    @classmethod
    def register(cls, provider: SuggestionProvider, /) -> None: ...
    @classmethod
    def all_providers(cls) -> list[SuggestionProvider]: ...
```

**All 5 registries FROZEN at Story 6 lift moment.** Golden snapshot test `test_copilot_registry_contracts_stable.py` (V-AG-3) hashes class signatures + dataclass fields → JSON snapshot. Mismatch on subsequent stories = FAIL. Story 8 EP-1..EP-5 WRAPS these (no signature change inside; EP layer is composition).

## §5. Checkpointer (production)

**Per copilot-expert SKILL.md + LangGraph 2.0 docs:**

- Library: `langgraph.checkpoint.postgres.aio.AsyncPostgresSaver` — **NEVER MemorySaver** (that's tutorial-only).
- Connection: `settings.postgres_dsn` (from luana_core_platform.core.config).
- Checkpoint table: `copilot_graph_checkpoints` (preserve from AISALESHT — Alembic migration).
- Async-first (`AsyncPostgresSaver.aenter` context).

## §6. Stream modes (SSE v2 — F8 cemented)

Production stream mode: **`updates`** (per-node deltas) + **`messages`** (token streaming via model events for chat UX).

SSE event types (preserve from F8 + post-rewrite, NO `text_chunk` legacy):
```
status (state: streaming|done) → message_start (msg_id) → block_start | block_delta | block_end | block_append (cards)
→ tool_start → tool_result → ui_action (legacy compat) → message_end → done | error
```

Block kinds: `text`, `image`, `audio`, `document`, `video`, `citation`, `tool_call`, `card` (kinds: `plan_card`, `inspiration_saved`, `memory_pinned`, `proposal_card`, `clarify`).

**Preserve verbatim.** Builder MUST grep FE consumer (already in nicolify shell — Story 10 territory) before changing protocol.

## §7. Observability (consume luana-core-observability, NEVER mirror — D-T6)

### §7.1 Subclass pattern

`luana_core_copilot/observability/recording/callback_handler.py`:
```python
from luana_core_observability.recording.base_callback_handler import BaseAgentCallbackHandler
from luana_core_observability.recording.sanitization import sanitize_payload
from luana_core_observability.recording.cost_recorder import pop_cost
from luana_core_copilot.observability.persistence.llm_call_repository import CopilotLLMCallRepository
from luana_core_copilot.observability.persistence.trace_event_repository import CopilotTraceEventRepository

class CopilotCallbackHandler(BaseAgentCallbackHandler):
    """Copilot-specific subclass. Implements 2 hooks per Template Method (S0/S11A)."""
    
    async def _persist_llm_call_row(self, row: dict) -> None:
        try:
            await self._llm_repo.insert(row)
        except Exception as e:
            logger.warning("copilot_llm_call_persist_failed", exc_info=e)
            await self._llm_repo.rollback()
    
    async def _persist_trace_event_row(self, row: dict) -> None:
        # idempotent insert + best-effort
        ...
```

Equivalent `CopilotObservabilityContext(BaseObservabilityContext)` in `turn_envelope.py`.

### §7.2 Tables (preserve from AISALESHT post-Story 2 lift)

| Table | Module-scoped repo | Schema source |
|---|---|---|
| `copilot_llm_call` | `CopilotLLMCallRepository` | Story 2 — schema lifted to luana_core_observability migration |
| `copilot_trace_event` | `CopilotTraceEventRepository` | idem |
| `copilot_routing_log` | `RoutingLogRepository` | copilot-local table for F8 routing telemetry |
| `model_pricing_snapshot` | `PricingSnapshotRepository` (luana_core_observability) | cross-agent SSoT — shared with sales_agent |

### §7.3 Cost recording (litellm canonicalization preserved — per Story PI-12 S1 T-1 + T-4)

- `cost_usd` populated via `pop_cost(litellm_call_id)` from CustomLogger bridge (S12 cemented). NEVER `calculate_cost()` runtime fallback.
- `provider_canonical` resolved via `_canonical_provider(model, hint)` — handles aliases (kimi-k2.6, deepseek-v4-flash, gemini-2.5-pro, gpt-4o-mini).
- Best-effort writes: `try/except` + structlog warning + `db.rollback()` per recording.

### §7.4 Cost target

Per copilot-expert SKILL.md cost guards:
- **≥60% cache_read_tokens** hit rate post-deploy.
- **2 LLM calls FAST max** per question (F5 pattern).
- **NANO routing classifier** with threshold 0.7.
- Cumulative cost target: budget per tenant per cycle (admin `/costo-copilot` page consumes `compute_cycle_start` function from luana_core_observability.reporting).

## §8. Qdrant RAG — marketing_kb_store (F10 — tenant-agnostic global KB)

File: `luana_core_copilot/infrastructure/qdrant/marketing_kb_store.py`

**Preserve invariants:**
- Collection: `nicolify_marketing_kb` (slug stays — per-brand collections future Story 11-13).
- Tenant filter: NONE (global tenant-agnostic KB per F10).
- Embedding dim: 3072.
- `chunk_markdown` breadcrumb-aware chunker (F10 pattern).
- `knowledge_search` tool (luana_core_copilot.application.tools.knowledge_search) calls `MarketingKbStore.search(query, top_k=5)`.

**Lift verbatim.** Qdrant client version `>=1.10`.

## §9. Module discovery + registries auto-population (F1)

`luana_core_copilot.application.discovery.discover_providers()`:
1. `pkgutil.walk_packages` over installed luana-core-* packages (Stories 2-5 registered packages).
2. For each, attempt `from luana_core_<X>.copilot_provider import provider` — if exists, register.
3. Provider conforms to `BaseCopilotProvider` (luana_core_copilot.domain.ports).
4. Filesystem fallback scan for namespace packages.

**Post-T-16 unlift:** discovery picks up:
- luana_core_brand_studio.copilot_provider
- luana_core_offer_studio.copilot_provider
- luana_core_crm.copilot_provider
- luana_core_analytics_engine.copilot_provider
- luana_core_landing.copilot_provider
- luana_core_connections.copilot_provider
- luana_core_commercial_calendar.copilot_provider
- luana_core_social_proof.copilot_provider

V-AG-6 arch test `test_module_descriptor_complete_for_lifted_packages.py` asserts all 8 + iam + tenant_profile + tenant_domains + assets register on discovery.

## §10. Eval goldens + judge (F9 — preserve)

File: `luana_core_copilot/evals/runner.py` + `golden_dataset.py`.

- 20 golden conversations (classifier + summarizer).
- `CopilotJudge` 4-dim multi-rubric NANO single JSON.
- Default: stub scoring (RUN_LLM_JUDGE=0).
- Opt-in: `RUN_LLM_JUDGE=1` env triggers real LLM judge.
- Cron: `weekly_copilot_quality_eval` ARQ lunes 05:00 UTC.

**Story 6 lifts these eval surfaces** (copilot evals are SMALL — 20 goldens; unlike sales_agent which has full simulator framework deferred to v0.2.0).

## §11. Migrations (NOT in scope Story 6)

Stories 2-5 didn't lift migrations. Same for Story 6. Migrations stay in `backend/alembic/` until Story 10 (nicolify migration moves Alembic config to brand app).

**Per Stories 2 lift:** all observability tables (copilot_llm_call, copilot_trace_event, model_pricing_snapshot) already have schema lifted to `luana_core_observability` Alembic. Module-scoped tables (copilot_routing_log, copilot_graph_checkpoints, copilot_conversations, copilot_messages, copilot_inspirations, copilot_pinned_memory, copilot_mutation_journal, copilot_workflow_metric, copilot_telegram_*) — schema preserved in AISALESHT migrations directory.

## §12. Test surfaces (TDD RED-first per layer)

| Layer | Test files lifted from AISALESHT |
|---|---|
| Domain | tests/modules/copilot/test_message.py, test_module_registry.py, test_field_paths_hint.py, test_workflow_*.py, test_mutation_journal.py, etc. |
| Infrastructure | test_*_repository.py (10 repos), test_*_persister.py (3 persisters), test_marketing_kb_store.py, test_qdrant_*.py, test_workflow_metric_repo.py, test_in_memory_*_registry.py |
| Application | test_orchestrator_*.py, test_tools_*.py (28 tool tests), test_workflow_*.py, test_suggestions_*.py, test_router_*.py, test_procedures_*.py, test_extraction_*.py, test_memory_*.py, test_observability_judge.py, test_rag_goldens.py, test_discovery.py |
| API | test_chat_api.py, test_conversations_api.py, test_voice_api.py, test_telegram_api.py, test_plan_api.py, test_suggestions_api.py, test_events_api.py, test_actions_api.py |
| Evals | golden_dataset tests + runner smoke |
| Observability subfolder | test_callback_handler_*.py, test_turn_envelope.py, test_domain_subscribers.py, test_trace_event_repo.py, test_llm_call_repo.py |

**Plus 4 cross-coupling tests UNLIFTED from Story 5 (T-16):**
- test_brand_context_injector.py → core/luana-core-brand-studio/tests/
- test_buyer_persona_fields_dropped_regression.py → core/luana-core-brand-studio/tests/
- test_worker_emits_summary_and_pills.py → core/luana-core-brand-studio/tests/
- test_offer_data_access_provider.py → core/luana-core-offer-studio/tests/

## §13. Skill decisions referenced

| Skill | Decision |
|---|---|
| `copilot-expert` | F0-F11 phases preserved, 36 [COPILOT-*] anchors capped, NO-SKIP debug protocol (trazas first), slot order 1-11, registries SSoT, cache hit rate ≥60% target, F5 NANO+FAST 2-call pipeline, F9 stub+opt-in judge |
| `tessl__langgraph` | StateGraph + add_messages reducer + ToolNode + conditional edges + AsyncPostgresSaver + stream modes updates/messages |
| `claude-api` prompt caching | 11-slot order + cache_control breakpoint after slot 6 + TTL 1h for slots 1-3 + 5min for slots 4-6 + min 4096 tokens Opus 4.7 + workspace isolation post 2026-02-05 |
| `anti-duplication.md` | NEVER mirror BaseObservabilityContext, FXResolver, sanitize_payload, etc. — inherit/consume from luana-core-observability |
| `auditor-downstream-regression.md` | Surface→downstream test map — copilot lift = scope all 213 copilot tests + Stories 2-5 packages re-test post-unlift |
| `tessl__graceful-degradation` | Every external call (httpx fetch_url, Qdrant search, LLM call) has timeout + fallback |
