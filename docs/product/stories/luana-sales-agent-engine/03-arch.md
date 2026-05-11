---
story_id: luana-sales-agent-engine
arch_version: 1
last_modified: 2026-05-11
drafted_by: /architect-orchestrator (claude-opus-4-7) — single spawn for Stories 6+7 per D-T4
authority: 00-story.md + outcome §7.2 + §7.3 lift mode + ADR-001 §2.4 voice + 6 D-T decisiones + 3 ratificaciones Chris 2026-05-11 (Story E eval gate WAIVED to v0.2.0)
blocked_by: luana-copilot-engine (Story 6) done
deviations_from_spec:
  - "Story 7 lifts sales_agent runtime VERBATIM but EXCLUDES eval framework (simulator + MAJ-EVAL grader + personas catalog + goldens dataset) per ratificación 2 + outcome §2 OQ1 + 00-story.md acceptance. Eval stays in nicolify repo until Luana v0.2.0 (~Sem 9). Arch fitness V-AG-5 cements absence."
  - "Story 7 introduces D-T3 BrandVoicePort hexagonal — NEW abstraction in luana-core-brand-studio.application.ports + concrete adapter in luana-core-brand-studio.application.services + DI consumer in luana-core-sales-agent. Per ADR-001 §2.4 + Story 5 §9.4 deferral. THIS is the canonical voice compiler integration point sales_agent consumes."
  - "PersonalityCompiler SSoT stays in luana-core-brand-studio.domain.personality (Story 5 placement). BrandVoicePort wraps it. Story 7 does NOT mirror or move PersonalityCompiler. Arch test V-AG-7 regression Story 5 verifies."
  - "AISALESHT sales_agent module = 153 .py files (incl. observability/eval_simulator/* — DEFERRED). Net to lift Story 7 ≈ 130 src files + ~82 test files (some eval tests stay in nicolify)."
  - "Story 7 lifts §3 protected surfaces verbatim per sales-agent-expert SKILL.md (closer_studio API+WS, SmartBufferService smart_debounce_runner, OutputManager.process_response chunking, enrollment_*, agent_state_checkpoints schema, webhook adapters, follow_up_engine, PromptVersionModel, model_pricing_snapshot — already lifted to luana-core-observability Story 2)."
  - "Connections/api/dependencies/__init__.py real ChatOrchestrator wiring (Story 4+6 deferral) UNLIFTS in Story 7 ticket T-X. After Story 7 done, luana-core-connections has full MessageHandlerPort impl wired."
  - "Sales agent observability/recording/* (CALLBACK_HANDLER + TURN_ENVELOPE + FACTORY + 1 module-scoped repo) SUBCLASS luana-core-observability bases per D-T6 + anti-duplication.md cardinal. NEVER mirror — same pattern as Story 6 copilot."
  - "Story 7 sales_agent has NO copilot_provider/ subfolder in AISALESHT (verified — sales_agent doesn't expose itself to copilot; copilot expects sales_agent_tools via sales-agent-tools tool in copilot). Sales agent itself imports brand (style_anchor_retriever consumes BrandReadPort) + scheduling.application via tools/scheduling/providers.py runtime deferred imports + crm (LeadModel SQLA mapper resolution only)."
  - "tools/scheduling/providers.py has runtime `from src.shared.links.ports.scheduling import ...` + `from src.modules.iam.infrastructure.models.tenant_model import TenantModel` inside method bodies (TYPE_CHECKING + deferred imports). Per Story 2 lift, shared.links.ports already at luana_core_platform.links.ports. Per Story 3 lift, iam.* at luana_core_iam.*. sed handles both. NO additional deferrals required."
  - "Scheduling concrete adapter integration: scheduling module NOT lifted until Story 8. Sales agent's `InternalSchedulerProvider` references `BookingLink` + `AvailabilityService` via deferred imports — those classes live in scheduling/. **Lift-time decision:** Sales agent's `tools/scheduling/providers.py` lifts verbatim with deferred-import pattern preserved. If/when scheduling lifts Story 8, the imports resolve. Until then, sales agent runtime fails on scheduler tool invocation in Luana standalone — acceptable because nicolify shell wires scheduling (Story 10 brings scheduling lift OR keep scheduling in nicolify shell)."
  - "Eval framework files NOT lifted (per ratificación 2 + 00-story.md): observability/eval_simulator/, observability/eval_simulator/persistence/, observability/eval_simulator/persistence/models/ (5 model files), spec.py — stays in AISALESHT until Luana v0.2.0. Sales agent runtime works WITHOUT eval simulator (eval is separate process; production runtime doesn't import eval simulator)."
  - "All sales_agent tests files (~82) EXCEPT eval simulator tests + eval scheduling tests lift. Eval tests deferred — listed in §9 + DEFERRED-FILES."
---

# Story 7 — Sales Agent Engine Lift — Architecture

## §1. Topology — Dependency Graph

### §1.1 Audit method (NO-NEW-LAYER per anti-duplication.md)

```bash
# Sales agent peer module imports
grep -rhE "^from src\.modules\.[a-z_]+" backend/src/modules/sales_agent/ \
  | awk -F"from src.modules." '{print $2}' | awk -F"[ .]" '{print $1}' | sort -u
# → copilot (via copilot_provider/ subfolder ONLY), iam, sales_agent (self)
# NOTE: brand consumed via BrandReadPort (shared.links.ports) — no direct import.
# NOTE: scheduling consumed via deferred imports inside method bodies (TYPE_CHECKING).

# Sales agent shared imports
grep -rhE "^from src\.(shared|core)\." backend/src/modules/sales_agent/ | wc -l
# → ~100+ shared imports (all lifted Stories 2 via luana-core-platform + luana-core-observability + luana-core-llm + luana-core-channels + luana-core-events + luana-core-billing + luana-core-compliance + luana-core-idempotency + luana-core-extraction).
```

### §1.2 Existing systems audit (cross-module NO-NEW-LAYER + ANTI-DUPLICATION)

Per `.claude/rules/anti-duplication.md` shared abstractions inventory + Stories 2-6 lift status:

| Subsystem detected pre-existing | Path canónico | luana-platform location | Story 7 decision |
|---|---|---|---|
| BaseObservabilityContext / BaseAgentCallbackHandler / FXResolver / CostCalculator / PricingResolver / sanitize_payload / base_trace_event_repo / base_llm_call_repo / tenant_billing_config_repository | shared/agent_observability/* | `luana_core_observability.*` (Story 2) | **EXTEND/CONSUME** — sales_agent subclasses bases as `SalesAgentCallbackHandler` + `SalesAgentObservabilityContext`. NEVER mirror. Existing AISALESHT sales_agent/observability/recording/{callback_handler.py, turn_envelope.py, factory.py} lift verbatim — they already inherit from shared bases per Story 2 prior work. |
| Channel format registry + format_for_channel + intent_detector | shared/agent_observability/channels/* → Story 2 | `luana_core_channels.*` | **CONSUME** — sales_agent/infrastructure/external/output_manager.py + application/prompts/compose.py call get_channel_format. NEVER re-register channels. |
| LLM router + LiteLLM service | shared/infrastructure/llm/* → Story 2 | `luana_core_llm.*` | **CONSUME** — sales_agent specialists call via router. |
| Outbox pattern + event bus adapter | shared/domain_events/outbox/* → Story 2 | `luana_core_events.outbox.*` | **CONSUME** — sales_agent events (USE_OUTBOX_PATTERN_SALES_AGENT=True per anti-default-flip-audit). |
| Idempotency keys | shared/idempotency/* → Story 2 | `luana_core_idempotency.*` | **CONSUME** — sales_agent workers (verify_pending_*, follow_up_engine) use idempotency keys. |
| BudgetGuard + RateLimiter | shared/billing/* → Story 2 | `luana_core_billing.*` | **CONSUME** — per Budget Gating PR-2 anchor in sales-agent-expert SKILL.md, sales_agent specialists wire `BudgetGuard.check(agent_kind="sales_agent")` pre-LLM-call. Wiring deferred per anchor — primitives ready. |
| ComplianceService | shared/compliance/* → Story 2 | `luana_core_compliance.*` | **CONSUME** — sales_agent compliance gates (WABA 24h, opt-in, blacklist, country block). |
| BrandReadPort (read-only via port — NOT direct brand import) | shared/links/ports/brand → lifted Story 2 to luana_core_platform | `luana_core_platform.links.ports.brand` | **CONSUME** — sales_agent/application/services/style_anchor_retriever.py reads BrandReadPort. |
| PersonalityCompiler v2 (voice compiler SSoT) | brand/domain/personality.py → Story 5 | `luana_core_brand_studio.domain.personality.PersonalityCompiler` | **CONSUME via D-T3 BrandVoicePort** — Story 7 introduces port + adapter pattern. NEVER imports PersonalityCompiler directly. |
| User + Tenant + dependencies | iam/* → Story 3 | `luana_core_iam.*` | **CONSUME** — sales_agent/api/* routes use iam dependencies. |
| LeadModel + sales repositories (cross-module SQLA mapper resolution) | crm/* → Story 4 | `luana_core_crm.*` | **CONSUME (LeadModel SQLA only)** — sales_agent infrastructure imports LeadModel for relationship resolution. |
| OfferRead + offer catalogs | offer/* → Story 5 | `luana_core_offer_studio.*` | **CONSUME** — sales_agent/application/services/offer_prompt_renderer.py + application/agents/sales/tools.py read offer data via OfferReadPort impl OR direct offer-studio domain. |
| Copilot ports + workflow base classes (for sales_agent's copilot_provider/) | copilot/* → Story 6 | `luana_core_copilot.*` | **CONSUME** — sales_agent's `copilot_provider/provider.py` (1 file — sales_agent IS a registered copilot module) subclasses BaseCopilotProvider from luana_core_copilot.domain.ports. |
| BaseExtractionOrchestrator | shared/application/extraction → Story 2 | `luana_core_extraction.base_orchestrator` | **CONSUME** (not used by sales_agent runtime — by brand/offer/landing extractors; sales_agent doesn't subclass). |
| **NO EXISTING LAYER for: sales_agent module orchestrator + state graph + specialists + SmartBufferService + OutputManager + CloserStudio API+WS + follow_up_engine + enrollment_* + tools registry + slot architecture compose.py + judge + personality compiler integration consumer** | — | — | **NEW (lift verbatim from AISALESHT)** — these ARE the sales_agent module. luana-core-sales-agent package born here. **PLUS D-T3 introduces BrandVoicePort + BrandVoiceService adapter in luana-core-brand-studio.** |

### §1.3 D-T3 BrandVoicePort introduction (NEW abstraction this story)

Per ADR-001 §2.4 + 00-story.md acceptance + Story 5 §9.4 deferral + outcome §7.2 ratificación.

**Files to create (NEW abstractions):**

1. **Port (in luana-core-brand-studio)** — `core/luana-core-brand-studio/src/luana_core_brand_studio/application/ports/brand_voice_port.py`:
   ```python
   from __future__ import annotations
   from typing import Protocol, runtime_checkable
   from uuid import UUID

   @runtime_checkable
   class BrandVoicePort(Protocol):
       """Voice compiler port — consumed by luana-core-sales-agent slot 5 BRAND_VOICE prefix.

       Per ADR-001 §2.4: PersonalityCompiler lives in luana-core-brand-studio.domain.personality.
       BrandVoicePort wraps it for cross-module consumption — sales-agent never imports
       PersonalityCompiler directly (hexagonal DDD boundary).

       Public methods (FROZEN at Story 7 introduction):
       """

       async def compile_system_instruction(self, tenant_id: UUID) -> str:
           """Compile tenant's PersonalityProfile to 5-block system_instruction.

           Returns empty string if tenant has no PersonalityProfile (fallback to default voice).
           """
           ...

       async def get_voice_metadata(self, tenant_id: UUID) -> dict:
           """Return voice metadata for prompt cache invalidation:
           - personality_profile_version: int (bumps on profile update)
           - last_compiled_at: datetime
           - dimensions_summary: dict (energy, warmth, humor — for routing decisions)
           """
           ...
   ```

2. **Adapter (in luana-core-brand-studio)** — `core/luana-core-brand-studio/src/luana_core_brand_studio/application/services/brand_voice_service.py`:
   ```python
   from __future__ import annotations
   from uuid import UUID

   from luana_core_brand_studio.domain.personality import PersonalityCompiler
   from luana_core_brand_studio.infrastructure.repositories.personality_repository import PersonalityRepository
   from luana_core_brand_studio.application.ports.brand_voice_port import BrandVoicePort

   class BrandVoiceService(BrandVoicePort):
       """Concrete adapter — wraps PersonalityCompiler + PersonalityRepository.

       Per ADR-001 §2.4 — engine lives here in core-brand-studio. Consumer
       (luana-core-sales-agent) injects this via DI.
       """

       def __init__(self, repo: PersonalityRepository, compiler: PersonalityCompiler):
           self._repo = repo
           self._compiler = compiler

       async def compile_system_instruction(self, tenant_id: UUID) -> str:
           profile = await self._repo.get_for_tenant(tenant_id)
           if profile is None:
               return ""  # fallback to specialist default voice
           return self._compiler.compile(profile)

       async def get_voice_metadata(self, tenant_id: UUID) -> dict:
           profile = await self._repo.get_for_tenant(tenant_id)
           if profile is None:
               return {"personality_profile_version": 0, "last_compiled_at": None, "dimensions_summary": {}}
           return {
               "personality_profile_version": profile.version,
               "last_compiled_at": profile.last_compiled_at,
               "dimensions_summary": profile.dimensions.summary(),
           }
   ```

3. **Consumer wiring (in luana-core-sales-agent)** — sales_agent specialists receive `BrandVoicePort` via DI factory pattern.
   - In `luana_core_sales_agent.application.services.knowledge_builder.build_identity()`: replace direct PersonalityCompiler invocation with `voice_port.compile_system_instruction(tenant_id)` call.
   - In `luana_core_sales_agent.application.prompts.compose.compose_prompt()`: slot 5 BRAND_VOICE prefix populated via `voice_port.compile_system_instruction(tenant_id)`.
   - DI: `BrandVoiceService` instantiated at app bootstrap (nicolify shell wiring), injected via FastAPI Depends.

4. **Arch fitness test V-AG-3 (NEW Story 7):** `test_sales_agent_uses_voice_port_no_direct_compiler_import.py`:
   ```python
   def test_sales_agent_never_imports_personality_compiler_directly():
       """Per D-T3 + ADR-001 §2.4 — hexagonal DDD boundary."""
       pkg_dir = Path("core/luana-core-sales-agent/src/luana_core_sales_agent")
       offenders = []
       for py in pkg_dir.rglob("*.py"):
           text = py.read_text(encoding="utf-8")
           if "PersonalityCompiler" in text:
               # Only allowed: type hint with BrandVoicePort (no actual import)
               if "from luana_core_brand_studio.domain.personality import PersonalityCompiler" in text:
                   offenders.append(py)
           if "from luana_core_brand_studio.domain.personality" in text:
               offenders.append(py)
       assert not offenders, f"sales-agent imports PersonalityCompiler directly (D-T3 violation): {offenders}"
   ```

5. **Arch fitness test V-AG-4 (NEW Story 7):** `test_voice_port_interface_complete.py`:
   ```python
   def test_voice_port_methods_cover_personality_compiler_consumed_surface():
       """Per D-T3 — port surface MUST cover ALL PersonalityCompiler consumption sites in sales_agent.

       Audit script: grep AISALESHT sales_agent for calls to compiler methods, assert port has equivalents.
       """
       from luana_core_brand_studio.application.ports.brand_voice_port import BrandVoicePort
       # Port must expose: compile_system_instruction + get_voice_metadata
       assert hasattr(BrandVoicePort, "compile_system_instruction")
       assert hasattr(BrandVoicePort, "get_voice_metadata")
       # Both async (Protocol)
       import inspect
       assert inspect.iscoroutinefunction(BrandVoicePort.compile_system_instruction)
       assert inspect.iscoroutinefunction(BrandVoicePort.get_voice_metadata)
   ```

### §1.4 Python package dependency DAG (1 package + brand-studio port-introduction edits + connections wiring resolution)

```
        luana-core-platform (Story 2)
                ↑
        Stories 2-5 packages
                ↑
        luana-core-copilot (Story 6) ★ blocked_by
                ↑
        luana-core-sales-agent  ★ NEW STORY 7 ★
                ↑
        ┌─ also touched Story 7 ─┐
        │  luana-core-brand-studio (Story 5) — ADD BrandVoicePort + BrandVoiceService (D-T3)
        │  luana-core-connections (Stories 4+6 deferral) — REPLACE ChatOrchestrator stub with real wiring
        └──────────────────────────┘
```

**Cross-package edges:**

| Source package | Depends on | Symbol used |
|---|---|---|
| `luana-core-sales-agent` | `luana-core-platform` | `shared.application.{ai_action_service}` + `shared.domain.{base_entity, datetime_utils, events, locale, ports.{scheduling, domain_lookup}}` + `shared.domain_events.outbox` + `shared.infrastructure.{llm.factory, prompts.base, files}` + `shared.links.ports.{scheduling, domain_lookup, brand}` + `core.{database, enums.ModelRole, config}` |
| `luana-core-sales-agent` | `luana-core-iam` | iam dependencies + User + TenantModel |
| `luana-core-sales-agent` | `luana-core-observability` | `recording.{BaseAgentCallbackHandler, BaseObservabilityContext, sanitize_payload, cost_recorder.pop_cost}` + `cost.{CostCalculator, FXResolver}` + `pricing.{PricingResolver}` + `persistence.{BaseTraceEventRepoProtocol, BaseLLMCallRepoProtocol}` |
| `luana-core-sales-agent` | `luana-core-llm` | `router.LLMRouter` + `providers.litellm.LiteLLMService` + factory |
| `luana-core-sales-agent` | `luana-core-channels` | `channel_registry` + `format.get_channel_format` + `format_for_channel` + `intent_detector` |
| `luana-core-sales-agent` | `luana-core-events` | `outbox.application.event_bus_adapter.adapter_bus` |
| `luana-core-sales-agent` | `luana-core-idempotency` | `IdempotencyService` |
| `luana-core-sales-agent` | `luana-core-billing` | `BudgetGuard` + `OutboundRateLimiter` (per Budget Gating PR-2 anchor) |
| `luana-core-sales-agent` | `luana-core-compliance` | `ComplianceService` |
| `luana-core-sales-agent` | `luana-core-brand-studio` | `application.ports.brand_voice_port.BrandVoicePort` (D-T3 — port only, NEVER PersonalityCompiler direct) |
| `luana-core-sales-agent` | `luana-core-copilot` | `domain.ports.BaseCopilotProvider` (for sales_agent's own copilot_provider/provider.py subclass) |
| `luana-core-sales-agent` | `luana-core-offer-studio` | `domain.offer.Offer` (read-only) + via OfferReadPort impl |
| `luana-core-sales-agent` | `luana-core-crm` | `domain.lead.Lead` + LeadModel for SQLA mapper resolution (relationship to MessageModel) |

**Crucially: cycle check OK.**
- sales_agent does NOT import copilot orchestrator (consumes BaseCopilotProvider port only).
- copilot does NOT import sales_agent (verified Story 6 empty grep).
- DAG-clean.

### §1.5 No inter-Story-7 internal cycles

Sales agent internal modules — no cycles. Verified per AISALESHT current state.

## §2. Lift Order — 19 tickets per outcome §7.4 atomicity

**Batch 1: Workspace + skeleton (T-1, T-2)**
- T-1 (15min): workspace pyproject.toml + Story 7 section
- T-2 (20min): luana-core-sales-agent skeleton

**Batch 2: D-T3 BrandVoicePort introduction (T-3) — DOES touch luana-core-brand-studio**
- T-3 (45min): Create port + adapter in luana-core-brand-studio + arch tests V-AG-3 + V-AG-4 stubs. **This is the ONLY ticket in Story 7 that modifies luana-core-brand-studio package** — per ADR-001 §2.4 design decision pre-ratified.

**Batch 3: Domain (T-4)**
- T-4 (45min): sales_agent domain (10 files: model_tier, events, message, base_entity, semantic_routes, exceptions, enums, tuning, enrollment, memory/repository)

**Batch 4: Infrastructure (T-5..T-7)**
- T-5 (45min): infrastructure/models/ (13 SQLA models + db/{base, database, repositories/business_repository, models})
- T-6 (60min): infrastructure/repositories/ (4 repos) + infrastructure/memory/ + infrastructure/monitoring/ + infrastructure/prompts/
- T-7 (45min): infrastructure/external/ (output_manager, buffer_service, safety_service) + ws_manager

**Batch 5: Application — 5 sub-batches due to density (T-8..T-12)**
- T-8 (60min): application/orchestrator/ (10 files — graph + smart_debounce_runner + chat + state + conversation_pipeline + identity_resolver + outbound_orchestrator + tool_call_dedup + audit_emitter)
- T-9 (45min): application/agents/sales/ (4 files — graph + nodes + tools + enrollment_tools) — sales-agent specialist subgraph
- T-10 (60min): application/tools/ (3 subfolders: payment, scheduling + registry) — tool registry + payment provider + scheduling provider strategy pattern
- T-11 (45min): application/quality/judge.py + application/prompts/compose.py + slot architecture cement (D-T3 consumer wire) — slot 5 BRAND_VOICE via BrandVoicePort
- T-12 (60min): application/services/ (16 files — knowledge_builder + closer_studio service + closer_studio/ subfolder + style_anchor_retriever + offer_prompt_renderer + semantic_router + etc.)

**Batch 6: API + workers (T-13)**
- T-13 (60min): api/ (8 files: closer_studio + enrollments + audit + scheduler_webhooks + payment_webhooks + ws + dto/) + workers/ (7 files: follow_up_engine + appointment_reminder_engine + frozen_detection + payment_reminder_engine + verify_pending_*)

**Batch 7: Observability subfolder (T-14)**
- T-14 (45min): observability/recording/ (callback_handler + turn_envelope + factory — D-T6 subclass pattern) + observability/persistence/ (llm_call_repo + trace_event_repo + routing_log_repo) + observability/workers/ (dual_write_reconciliation_task) + observability/domain_events/subscribers.py — **EXCLUDE observability/eval_simulator/ (NOT lifted per ratificación 2)**

**Batch 8: copilot_provider lift (T-15)**
- T-15 (20min): sales_agent's own copilot_provider/provider.py (1 file — sales-agent IS a registered copilot module via convention) — subclasses luana_core_copilot.domain.ports.BaseCopilotProvider

**Batch 9: connections wiring resolution (T-16) — Story 4+6 deferral resolved**
- T-16 (30min): replace `NotImplementedError` stub in `luana_core_connections.api.dependencies.__init__.py` with real `ChatOrchestrator` wiring per Story 4 §9 deferral. Per Story 4 + Story 6 deferral notes, this required both luana_core_copilot + luana_core_sales_agent — both now exist.

**Batch 10: Integration + arch fitness (T-17..T-19)**
- T-17 (30min): Cross-package smoke + aggregate pytest GREEN (Stories 2+3+4+5+6+7 = 23 packages)
- T-18 (60min): NEW arch fitness Story 7 — V-AG-1..V-AG-8 (8 tests including D-T3 V-AG-3 + V-AG-4)
- T-19 (35min): Finalization — lint + AISALESHT untouched + DEFERRED-FILES.md update (eval framework + scheduling concrete deps + Story E waiver) + README

## §3. Per-Package Structure

### §3.1 luana-core-sales-agent layout

```
core/luana-core-sales-agent/
├── pyproject.toml                      # workspace member, version 0.0.7-alpha
├── README.md
├── src/luana_core_sales_agent/
│   ├── __init__.py
│   ├── domain/                         # 10 files
│   │   ├── __init__.py
│   │   ├── model_tier.py               # ★ ModelRole + LLM_ROLE_BY_SITE + SPECIALIST_TO_ROLE (SSoT per S12)
│   │   ├── events.py, message.py, base_entity.py
│   │   ├── semantic_routes.py, exceptions.py, enums.py, tuning.py, enrollment.py
│   │   └── memory/{__init__,repository}.py
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── models/                      # 13 SQLA models
│   │   │   ├── message_model.py         # NOTE: NOT same as luana_core_copilot.message_model (sales has different schema for sales messages)
│   │   │   ├── enrollment_model.py, payment_link_model.py, scheduler_webhook_event_model.py
│   │   │   ├── payment_grant_audit_model.py, agent_trace_model.py, prompt_version_model.py
│   │   │   ├── sensitive_data_model.py, workflow_metric_model.py, llm_log_model.py
│   │   │   ├── payment_webhook_event_model.py, agent_state_checkpoint_model.py
│   │   ├── repositories/{enrollment, message, state, workflow_metric}_repository.py
│   │   ├── memory/{vector_store, audit_repository}.py
│   │   ├── monitoring/tracing.py
│   │   ├── prompts/{base, semantic}.py + templates/{specialist_*, supervisor_routing.j2, legacy/}
│   │   ├── external/                    # ★§3 protected — output_manager, buffer_service, safety_service
│   │   ├── db/{base, database}.py + repositories/business_repository.py + models/
│   │   └── ws_manager.py
│   ├── application/
│   │   ├── __init__.py
│   │   ├── event_bus.py
│   │   ├── payment_event_handlers.py, scheduling_event_handlers.py
│   │   ├── orchestrator/                # 10 files — LangGraph + smart_debounce + chat + state
│   │   │   ├── graph.py                 # ★ Sales agent specialist routing graph (StateGraph)
│   │   │   ├── smart_debounce_runner.py # ★§3 protected — SmartBufferService
│   │   │   ├── chat.py, state.py
│   │   │   ├── conversation_pipeline.py # main entry — BudgetGuard.check pre-LLM-call (PR-2 wiring sites)
│   │   │   ├── identity_resolver.py, audit_emitter.py, outbound_orchestrator.py
│   │   │   ├── tool_call_dedup.py       # ★§3 protected — anti-loop guard
│   │   ├── agents/sales/                # 4 files — specialist sub-agents
│   │   │   ├── graph.py, nodes.py, tools.py, enrollment_tools.py
│   │   ├── tools/                       # tool registry + 2 subfolders
│   │   │   ├── __init__.py, registry.py
│   │   │   ├── payment/{__init__,tools,providers,webhook_providers}.py
│   │   │   └── scheduling/{__init__,tools,providers,webhook_providers}.py
│   │   ├── quality/{__init__,judge}.py  # SalesAgentJudge — 4-dim NANO
│   │   ├── prompts/                     # compose.py — slot architecture (slot 5 BRAND_VOICE via D-T3 BrandVoicePort)
│   │   │   ├── __init__.py
│   │   │   └── compose.py
│   │   ├── services/                    # 16 files
│   │   │   ├── knowledge_builder.py     # ★ build_identity — consumes BrandVoicePort
│   │   │   ├── closer_studio_service.py
│   │   │   ├── closer_studio/{command_service,query_service,kpi_service,lead_helpers}.py
│   │   │   ├── style_anchor_retriever.py # consumes BrandReadPort
│   │   │   ├── offer_prompt_renderer.py
│   │   │   ├── semantic_router.py, payment_state_service.py
│   │   │   ├── inbox_campaign_enrichment.py, enrollment_service.py
│   │   │   ├── observability_adapter.py, meeting_state_service.py
│   │   │   ├── tenant_route_overlay.py
│   │   │   ├── channel_resolver.py, message_service.py
│   ├── observability/                   # MODULE-SCOPED — extends luana-core-observability
│   │   ├── __init__.py
│   │   ├── recording/                   # ★ D-T6 subclasses
│   │   │   ├── callback_handler.py      # SalesAgentCallbackHandler(BaseAgentCallbackHandler)
│   │   │   ├── turn_envelope.py         # SalesAgentObservabilityContext(BaseObservabilityContext)
│   │   │   └── factory.py
│   │   ├── persistence/                 # 4 module-scoped repos
│   │   │   ├── llm_call_repository.py, trace_event_repository.py, routing_log_repository.py
│   │   │   └── models/{llm_call_model, trace_event_model, routing_log_model}.py
│   │   ├── workers/dual_write_reconciliation_task.py
│   │   ├── domain_events/subscribers.py
│   │   # NOTE: eval_simulator/ NOT lifted — DEFERRED Luana v0.2.0 per ratificación 2
│   ├── workers/                         # ★§3 protected
│   │   ├── follow_up_engine.py, appointment_reminder_engine.py, frozen_detection.py
│   │   ├── payment_reminder_engine.py, verify_pending_payments.py, verify_pending_bookings.py
│   ├── api/                             # ★§3 protected
│   │   ├── closer_studio.py             # ★§3 — Live ops + Streamlit + FE dependen
│   │   ├── enrollments.py, audit.py, scheduler_webhooks.py, payment_webhooks.py
│   │   ├── ws.py                        # ★§3 — WS for closer_studio
│   │   └── dto/{closer_studio, enrollments, public_links, telegram, gmail, calendar, audit}.py
│   └── copilot_provider/                # 1 file — sales-agent IS a copilot module
│       └── provider.py                  # extends BaseCopilotProvider from luana_core_copilot.domain.ports
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── (~82 test files — EXCLUDE eval simulator tests per §9)
    │   - test_agent_observability_* tests EXCLUDED if they reference eval_simulator
    │   - test_*_personas_* EXCLUDED
    │   - test_*_goldens_* EXCLUDED
    │   - test_*_grader_* EXCLUDED (MAJ-EVAL grader = Luana v0.2.0)
    └── (NEW arch fitness tests live in core/tests/architecture/)
```

### §3.2 pyproject.toml (Story 7)

```toml
[project]
name = "luana-core-sales-agent"
version = "0.0.7-alpha"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
    "fastapi>=0.115",
    "structlog>=24.0",
    "httpx>=0.27",
    "langgraph>=0.2",
    "langchain-core>=0.3",
    "langchain-openai>=0.2",
    "arq>=0.26",                  # workers
    "jinja2>=3.1",                # prompts templates
    "tiktoken>=0.7",
    "litellm>=1.40",
    "luana-core-platform",
    "luana-core-iam",
    "luana-core-observability",
    "luana-core-llm",
    "luana-core-channels",
    "luana-core-events",
    "luana-core-idempotency",
    "luana-core-billing",
    "luana-core-compliance",
    "luana-core-extraction",
    "luana-core-brand-studio",     # D-T3 BrandVoicePort consumer
    "luana-core-offer-studio",
    "luana-core-crm",
    "luana-core-copilot",          # for copilot_provider/provider.py subclass
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/luana_core_sales_agent"]

[tool.pytest.ini_options]
pythonpath = ["."]
asyncio_mode = "auto"
```

## §4. Workspace Registration

```toml
[tool.uv.workspace]
members = [
    "core",
    # (Stories 2-6 packages — 22 already registered)
    # Story 7 (NEW — 1 package)
    "core/luana-core-sales-agent",
    # Brand apps
    "nicolify", "vitalia", "comunify", "lupulo",
]

[tool.uv.sources]
# (Stories 2-6 — 22 entries)
# Story 7 (NEW)
luana-core-sales-agent = { workspace = true }
```

## §5. Import Path Mapping (sed)

Same template as Story 6 §5 — `from src.modules.sales_agent.X` → `from luana_core_sales_agent.X`. Plus all cross-module patterns.

## §6. Test Lift Strategy

82 test files in `backend/tests/modules/sales_agent/`. Lift ~75 — DEFER 7 eval-framework tests per §9.

## §7. Architecture Fitness Tests (NEW Story 7)

### §7.1 Brand-agnostic engine invariant
`test_story7_brand_agnostic_engine.py` — same template Stories 4-6 extended to luana-core-sales-agent.

### §7.2 No forward Story imports
`test_story7_no_forward_module_imports.py` — luana-core-sales-agent MUST NOT import from luana_core_{campaigns, advertising, social_media}. luana_core_scheduling allowed only via deferred imports (TYPE_CHECKING) inside method bodies — separate arch test verifies via AST that no top-level scheduling imports.

### §7.3 D-T3 — Sales agent uses BrandVoicePort, NEVER PersonalityCompiler direct
`test_sales_agent_uses_voice_port_no_direct_compiler_import.py` — scans `luana_core_sales_agent` for forbidden `from luana_core_brand_studio.domain.personality import PersonalityCompiler` or `class PersonalityCompiler` declarations.

### §7.4 D-T3 — BrandVoicePort interface complete
`test_voice_port_interface_complete.py` — verifies BrandVoicePort has compile_system_instruction + get_voice_metadata public methods, both async (Protocol).

### §7.5 No eval framework lifted (per ratificación 2 + §9)
`test_no_eval_framework_lifted.py`:
```python
def test_eval_simulator_not_in_luana_core_sales_agent():
    """Per Session 3 ratificación 2 + outcome §2 OQ1 — eval framework stays in nicolify
    until Luana v0.2.0. Sales agent runtime works WITHOUT eval simulator."""
    forbidden_paths = [
        "core/luana-core-sales-agent/src/luana_core_sales_agent/observability/eval_simulator",
        "core/luana-core-sales-agent/tests/eval_simulator",
    ]
    for fp in forbidden_paths:
        assert not Path(fp).exists(), f"Eval framework leaked into Story 7: {fp} (must defer to Luana v0.2.0)"
```

### §7.6 D-T6 — Sales agent observability subclass invariant (anti-mirror)
`test_no_mirror_observability_in_sales_agent.py`:
- SalesAgentCallbackHandler subclasses BaseAgentCallbackHandler from luana_core_observability.
- SalesAgentObservabilityContext subclasses BaseObservabilityContext.
- NEVER declares class FXResolver, CostCalculator, PricingResolver, sanitize_payload function.

### §7.7 Voice compiler SSoT regression Story 5+6
`test_voice_compiler_ssot_still_intact_story7.py` — re-run V-AG-7 invariant: only luana-core-brand-studio.domain.personality declares PersonalityCompiler. Stories 6+7 must NOT introduce mirror.

### §7.8 §3 protected surfaces NOT refactored
`test_sales_agent_protected_surfaces_intact.py`:
- closer_studio.py API + WS routes lifted verbatim — signature unchanged
- SmartBufferService.smart_debounce_runner unchanged
- OutputManager.process_response chunking unchanged
- enrollment_* unchanged
- agent_state_checkpoints schema unchanged
- webhook adapters (telegram/whatsapp/IG) unchanged
- follow_up_engine cadence unchanged
- PromptVersionModel unchanged
- tool_call_dedup.py unchanged

Verified via file hashes (sha256 manifest snapshot at lift moment vs AISALESHT source).

## §8. Agentic Surfaces (deep-dive in 03-arch-agentic.md)

See `03-arch-agentic.md` for full sales_agent LangGraph state, specialist routing topology, slot architecture (5 slots with slot 5 BRAND_VOICE via D-T3 BrandVoicePort), tool registry (scheduler/payment/knowledge/qualification/follow-up base), observability subclass pattern, channel format consumption (luana_core_channels), PII sanitization (luana_core_observability.recording.sanitization).

## §9. Deferred Files (Story 7 exception list)

### §9.1 Eval framework — DEFERRED to Luana v0.2.0 per ratificación 2

| AISALESHT path | Reason | Lifts at |
|---|---|---|
| `backend/src/modules/sales_agent/observability/eval_simulator/__init__.py` | Eval simulator dual-LLM runtime — Story E (sales-agent-voice-fidelity-grader-runtime) WAIVED to v0.2.0 per session 3 mandate | Luana v0.2.0 |
| `backend/src/modules/sales_agent/observability/eval_simulator/spec.py` | Eval simulator spec | Luana v0.2.0 |
| `backend/src/modules/sales_agent/observability/eval_simulator/persistence/__init__.py` | Eval simulator persistence | Luana v0.2.0 |
| `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_llm_call.py` | Cost-bucket separated eval LLM call table | Luana v0.2.0 |
| `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_trace_event.py` | Cost-bucket separated eval trace table | Luana v0.2.0 |
| `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_synthetic_tenants.py` | Synthetic tenant fixtures | Luana v0.2.0 |
| `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_grade.py` | Grade record table | Luana v0.2.0 |
| `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_grade_cache.py` | Grader cache table | Luana v0.2.0 |
| `backend/tests/agentic_evals/sales_agent/` (entire tree) | Eval test suite + simulator smoke + property + schema regression + MAJ-EVAL grader + judge prompts + goldens dataset + personas catalog + adversarial jailbreak | Luana v0.2.0 |

**Decision rationale (per ratificación 2):**
- Story E (`sales-agent-voice-fidelity-grader-runtime`) WAIVED to Luana v0.2.0
- Eval framework not production-runtime — separate process invoked weekly via ARQ cron
- Sales agent runtime (specialists + orchestrator + observability) works WITHOUT eval simulator
- Lifting eval framework requires shared/agent_observability.eval-related infra not yet in luana-core-observability (Story 2 lifted only production observability, not eval-specific cost-bucket tables)
- Cost-bucket separation invariant (H7 per `auditor-downstream-regression.md` simulator schema-mirror downstream) requires care — defer until v0.2.0 eval foundation complete

### §9.2 Scheduling concrete provider integration — DEFERRED Story 8 (scheduling lift)

| AISALESHT path | Lifts in Story 7 | Notes |
|---|---|---|
| `backend/src/modules/sales_agent/application/tools/scheduling/providers.py` | **YES** (verbatim lift) | Has runtime deferred imports inside method bodies. After sed → `from luana_core_platform.links.ports.scheduling import ...` (Story 2 SSoT) + `from luana_core_iam.infrastructure.models.tenant_model import TenantModel` (Story 3). Sales agent runtime fails on scheduler tool invocation in Luana standalone UNTIL Story 8 lifts scheduling module — acceptable because nicolify shell wires scheduling pre-Story 8. |

### §9.3 Connections api/dependencies real wiring — UNLIFT Story 7

Per Story 4 + Story 6 deferral notes, `luana-core-connections/api/dependencies/__init__.py` has `NotImplementedError` stub for ChatOrchestrator. Story 7 has both luana-core-copilot + luana-core-sales-agent — wiring resolves. T-16 ticket dedicated.

### §9.4 Streamlit admin pages — DEFERRED Story 10 (nicolify migration)

| AISALESHT path | Reason | Lifts at |
|---|---|---|
| `backend/src/admin/pages/{sales-routing,sales-agent-quality,costo-agentes,llm-virtual-keys,llm-models,...}.py` | Streamlit admin shell migrates with nicolify | Story 10 |

### §9.5 Reserved (NEW abstractions THIS story or future)

| Reserved item | Story | Notes |
|---|---|---|
| `BrandVoicePort` Protocol | **THIS Story 7 (D-T3 — INTRODUCED)** | Created in luana-core-brand-studio.application.ports per ADR-001 §2.4. Stories 5+ defer pre-existed; Story 7 INTRODUCES |
| `BrandVoiceService` adapter | **THIS Story 7 (D-T3 — INTRODUCED)** | Created in luana-core-brand-studio.application.services. Wraps PersonalityCompiler + PersonalityRepository |
| voice_cloning BrandConfig flag | Stories 11-13 | Per-brand value (per Story 5 §9.5) |
| Voice cloning pipeline (LLM-distillation from chat samples) | Stories 11-13 | NEW code, not in AISALESHT |
| sales_agent eval framework (Story E) lift | Luana v0.2.0 (~Sem 9) | Per session 3 ratificación 2 |
| MAJ-EVAL grader runtime | Luana v0.2.0 | Idem |
| Personas catalog Story C | Luana v0.2.0 | Idem |
| Goldens dataset Story D infra | Luana v0.2.0 | Idem |
| Adversarial jailbreak suite Story I | Luana v0.2.0 | Idem |

### §9.6 Audit trail (append to core/DEFERRED-FILES.md)

```markdown
## Story 7 deferrals (2026-05-11) + INTRODUCED abstractions

### INTRODUCED Story 7 (D-T3 per ADR-001 §2.4):
- core/luana-core-brand-studio/src/luana_core_brand_studio/application/ports/brand_voice_port.py (BrandVoicePort Protocol)
- core/luana-core-brand-studio/src/luana_core_brand_studio/application/services/brand_voice_service.py (BrandVoiceService adapter)

### UNLIFTED Story 7 (Story 4+6 deferral):
- luana-core-connections/api/dependencies/__init__.py ChatOrchestrator real wiring — NotImplementedError stub REPLACED

### NEW Story 7 deferrals:

#### Defer to Luana v0.2.0 (eval framework — per Session 3 ratificación 2)
- backend/src/modules/sales_agent/observability/eval_simulator/ (entire subfolder — 8 files src + persistence models)
- backend/tests/agentic_evals/sales_agent/ (entire tree — simulator + grader + personas + goldens + adversarial)
- Story E (sales-agent-voice-fidelity-grader-runtime) blocked PI-12 eval-foundation incompleta → waived to v0.2.0

#### Defer to Story 8 (campaigns/scheduling lift)
- scheduling concrete provider integration — sales_agent/application/tools/scheduling/providers.py lifts WITH deferred-import pattern; runtime depends on scheduling module lifting Story 8

#### Defer to Story 10 (nicolify migration)
- backend/src/admin/pages/{sales-routing,sales-agent-quality,costo-agentes,llm-virtual-keys,llm-models}.py
```

## §10. Architecture Fitness Gates

| Gate | Layer | Owner |
|---|---|---|
| `uv sync --all-packages` GREEN (23 packages) | luana-platform root | gate-runner |
| `uv run pytest core/luana-core-sales-agent/tests/` GREEN (~75 tests) | per-package | gate-runner |
| `uv run pytest core/luana-core-brand-studio/tests/` GREEN (with new D-T3 port + adapter) | per-package | gate-runner |
| `uv run pytest core/luana-core-connections/tests/` GREEN (with real ChatOrchestrator wiring) | per-package | gate-runner |
| `uv run ruff check core/luana-core-sales-agent` GREEN | luana-platform root | gate-runner |
| 8 NEW arch tests V-AG-1..V-AG-8 GREEN | luana-platform | gate-runner |
| AISALESHT untouched verifier | AISALESHT repo | gate-runner |
| No-publish verifier | luana-platform | gate-runner |
| core/DEFERRED-FILES.md updated | luana-platform | gate-runner |
| Connections `NotImplementedError` stub replaced with real wiring | luana-core-connections | gate-runner |

## §11. Research Notes (state-of-the-art as of 2026-05-11)

| Source | Accessed | Key takeaway |
|---|---|---|
| Anthropic prompt caching https://platform.claude.com/docs/en/build-with-claude/prompt-caching | 2026-05-11 | Sales-agent slot 5 BRAND_VOICE: per-tenant cacheable 5min, invariant within tenant turn flow. Cache invalidates on personality_profile_version bump (D-T3 get_voice_metadata provides version for invalidation logic). |
| LangGraph workflows https://docs.langchain.com/oss/python/langgraph/workflows-agents | 2026-05-11 | Sales agent specialist routing = supervisor pattern (qualifier → product_expert → closer → supervisor → tool_executor → safety → escalate). StateGraph + AsyncPostgresSaver checkpointer + stream `messages` mode. |
| sales-agent-expert SKILL.md (internal) | 2026-05-11 | §3 protected surfaces: closer_studio API+WS, SmartBufferService smart_debounce_runner, OutputManager.process_response chunking, enrollment_*, agent_state_checkpoints schema (plural), webhook adapters, follow_up_engine cadence, PromptVersionModel, model_pricing_snapshot (cross-agent shared), tool_call_dedup.py. Voice = personality_profiles.system_instruction = slot 5 cache prefix. Compiler v2 (6 bloques: ASÍ HABLAS / ASÍ NO). |
| copilot-expert SKILL.md (internal) | 2026-05-11 | Sales agent IS a copilot module (registered via copilot_provider/provider.py). Subclasses BaseCopilotProvider — sales_agent tools available via `sales_agent_tools` in copilot tool registry. |
| ADR-001 §2.4 (internal) | 2026-05-11 | Voice compiler v2 elevated to luana-core-brand-studio.domain.personality. Story 7 introduces consumer-side port (BrandVoicePort) + adapter. PersonalityCompiler NEVER imported directly by sales_agent. |
| outcome §7.2 + §7.3 + Session 3 ratificación 2 (internal) | 2026-05-11 | Story 7 autonomy rationale: lift-mode + D-T3 voice port (single design decision pre-ratified ADR-001 §2.4). Eval framework WAIVED to v0.2.0. |
| `.claude/rules/anti-default-flip-audit.md` (internal) | 2026-05-11 | Sales-agent flag flips: USE_OUTBOX_PATTERN_SALES_AGENT=True default. LiteLLM Proxy enabled. Sales agent imports outbox via luana_core_events (Story 2 lift). |
| `.claude/rules/anti-duplication.md` (internal) | 2026-05-11 | Sales-agent observability subclass pattern cemented post-PI-1.1 PR-1 revert. D-T6 enforces. |

**Knowledge cutoff disclosure:** Opus 4.7 cutoff Jan 2026. Anthropic prompt caching post-cutoff (workspace isolation Feb 2026, multi-TTL mixing) verified live on 2026-05-11. LangGraph + deepagents APIs verified against AISALESHT working code (S12 close 2026-04-17).

## §12. Cross-Cutting Concerns

- **Tenant isolation:** every query `tenant_id` filter — sales_agent already complies (S0-S12 cement). Slot 5 BrandVoicePort per-tenant.
- **PII sanitization:** `sanitize_payload` from luana_core_observability used on every observability write (S0-S11A Template Method). Routes use `response_model=`. Lift preserves.
- **Spanish neutro EXCEPTION:** sales_agent output respects tenant voice (voseo OK if tenant AR per personality_profile). Other user-facing strings (error messages, tool descriptions visible to operator in closer_studio) follow Spanish neutro LatAm. Per `.claude/rules/spanish-text.md` § Excepción sales_agent.
- **Master data:** UTC store, tenant locale. Already complies.
- **Currency:** sales_agent monetary fields include `currency` per shared catalog.
- **Native-first:** uv run pytest / ruff. No Docker.
- **R23 Opus mandatory:** ALL Story 7 tickets owner = builder-agentic Opus 4.7. NO Sonnet eligibility (production agentic code per ratificación 3).

## §13. capability YAML + modules/ Updates Required

**None Story 7.** Mechanical lift + D-T3 NEW abstraction. Outcome `luana-platform-migration.md` § progress log updated by /pm at story close. Capability `luana-core/multi-brand-platform.yaml` adds `sales-agent-engine` capability mention at merge.

## §14. Open Questions for PM (none blocking)

All scope decisions resolved per outcome §7.2 + §7.3 + ADR-001 + 6 D-T decisiones + 3 ratificaciones:

- **D-T3 BrandVoicePort INTRODUCED in Story 7** — single design decision pre-ratified ADR-001 §2.4. Port + adapter in luana-core-brand-studio (touches that package — acceptable per ratificación). Sales-agent consumes via DI.
- **D-T6 observability subclass** — Story 7 cement (extends Stories 2+6 cement).
- **Eval framework WAIVED to v0.2.0** — per ratificación 2 + 00-story.md acceptance. §9.1 documents 8+ files + tests deferred.
- **§3 protected surfaces preserved** — V-AG-8 arch test verifies file hashes.
- **Scheduling deferred imports preserved** — sales_agent/application/tools/scheduling/providers.py lifts with TYPE_CHECKING + method-body deferred imports verbatim. Story 8 scheduling lift resolves runtime imports.
- **Connections wiring resolved** — T-16 replaces NotImplementedError stub with real ChatOrchestrator using luana_core_copilot + luana_core_sales_agent.

If Chris reads this and wants to INCLUDE eval framework in Story 7 → STOP, ratificación 2 explicit. v0.2.0 territory.

If Chris reads this and wants BrandVoicePort with MORE methods than `compile_system_instruction` + `get_voice_metadata` (e.g., add `get_personality_dimensions()` for routing) → that's port API surface expansion. Story 7 architect cements 2-method surface per audit of AISALESHT sales_agent consumption sites. If gap detected → escalate, evaluate adding method to port + adapter + arch test.
