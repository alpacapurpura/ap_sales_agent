---
story_id: luana-copilot-engine
arch_version: 1
last_modified: 2026-05-11
drafted_by: /architect-orchestrator (claude-opus-4-7) — single spawn for Stories 6+7 per D-T4
authority: 00-story.md + outcome §7.2 + §7.3 lift mode + ADR-001 §2.4 + 6 D-T decisiones + 3 ratificaciones Chris 2026-05-11
combined_with: luana-sales-agent-engine (Story 7) — separate 03-arch-agentic.md per story; 06-tickets.yaml independent (Story 7 blocked_by Story 6 done)
deviations_from_spec:
  - "AISALESHT modules/copilot has NO copilot_provider/ subfolder (it consumes others' providers via module_registry — provider pattern). Story 6 lifts the FULL copilot module including domain/module_registry + ports + workflow base classes."
  - "Stories 2-5 copilot_provider/ deferrals (commercial_calendar, social_proof, crm, analytics, landing, connections, brand, offer — 22 files total) UNLIFT Story 6: now that luana-core-copilot exists with ports + workflow base classes, each lifted package's deferred copilot_provider/ subfolder lifts back to its home package via sed rewrite from `src.modules.copilot.domain.*` → `luana_core_copilot.domain.*`. T-X dedicated."
  - "MessageModel SQLA stub in offer-studio conftest.py (Story 5 lines 145-157) MIGRATES to real `luana_core_copilot.persistence.models.MessageModel` import — Story 5 deuda técnica residual cleared per D-T2."
  - "AppointmentModel SQLA stub in offer-studio conftest.py (Story 5 lines 160-172) STAYS — scheduling module NOT lifted until Story 8 per outcome §2 DAG (scheduling is part of campaigns-extension-sdk lift batch). Stub remains until then."
  - "Tool/workflow/extractor/module/suggestion registry public contracts FROZEN at lift moment per D-T1 — Story 8 wraps as EP-1..EP-5 SDK formal layer. Arch fitness V-AG-3 enforces stable signatures via golden snapshot of registry public API."
  - "copilot module has NO Streamlit admin subfolder (admin lives in backend/src/admin/ root with pages consuming copilot via API — confirmed grep). Story 6 lifts copilot module proper; Streamlit admin pages stay in AISALESHT until Story 10 (nicolify migration)."
  - "AISALESHT copilot module = 243 .py files (incl. 35 evals/* + 13 utils + observability/* already lifted to luana-core-observability Story 2). After deduping observability (lifted) → ~210 src files + ~213 test files net to lift Story 6."
  - "Voice transcription endpoint (copilot/infrastructure/voice/whisper_transcriber.py) lifts verbatim — single self-contained file, no external deps beyond shared/llm + httpx already in luana-core-llm."
  - "Channel format registry consumption: copilot/infrastructure/channels/ has only 2 files (telegram_bot + in_memory_channel). Cross-checked: `format_for_channel` registry already in luana-core-channels (Story 2). copilot lifts the CHANNEL ADAPTER classes (TelegramBotChannel, InMemoryChannel implementing OutputChannel protocol), not the registry."
  - "marketing_kb Qdrant store (copilot/infrastructure/qdrant/marketing_kb_store.py) is tenant-agnostic global KB (per copilot-expert §F10). Collection `nicolify_marketing_kb` slug stays — Story 6 lifts verbatim. Per-brand KB collections (`vitalia_marketing_kb` etc.) are Stories 11-13 territory."
  - "[COPILOT-*] anchor registry (36 anchors per copilot-expert) preserves count post-lift. Arch test test_copilot_anchors_count_stable.py verifies exactly 36 anchors after lift — bumping requires architect ratification."
  - "Story 7 split-by-design — sales_agent runtime lifts WITHOUT eval framework (simulator/MAJ-EVAL grader/personas/goldens) per ratificación 2 + 00-story.md acceptance + outcome §2 OQ1. Eval stays in nicolify repo until Luana v0.2.0. Arch fitness V-AG-5 (Story 7) cements absence."
---

# Story 6 — Copilot Engine Lift — Architecture

## §1. Topology — Dependency Graph

### §1.1 Audit method (NO-NEW-LAYER per anti-duplication.md)

Cross-codebase grep executed against AISALESHT modules/copilot + luana-platform existing 21 packages:

```bash
# What copilot imports from peer modules
grep -rhE "^from src\.modules\.[a-z_]+" backend/src/modules/copilot/ \
  | awk -F"from src.modules." '{print $2}' | awk -F"[ .]" '{print $1}' | sort -u
# → assets, brand, copilot, iam, offer

# What copilot imports from shared
grep -rhE "^from src\.(shared|core)\." backend/src/modules/copilot/ | sort -u | wc -l
# → 87 distinct shared/core imports (all lifted to luana-core-platform via Story 2)

# What already exists in luana-platform that copilot would touch
find /home/chris/luana-platform/core/luana-core-observability/src -name "*.py" -type f | wc -l
# → 33 (full agent_observability lifted Story 2 — copilot consumes via inheritance NEVER mirrors)
```

### §1.2 Existing systems audit (cross-module NO-NEW-LAYER + ANTI-DUPLICATION)

Per `.claude/rules/anti-duplication.md` shared abstractions inventory + Story 2 lift status:

| Subsystem detected pre-existing | Path canónico | luana-platform location | Story 6 decision |
|---|---|---|---|
| BaseObservabilityContext / BaseAgentCallbackHandler / FXResolver / CostCalculator / PricingResolver / sanitize_payload / base_trace_event_repo / base_llm_call_repo / tenant_billing_config_repository | shared/agent_observability/* | `luana_core_observability.{recording,cost,pricing,persistence,reporting,workers}` (33 files Story 2 lift) | **EXTEND/CONSUME** — copilot subclasses `BaseAgentCallbackHandler` as `CopilotCallbackHandler` + subclasses `BaseObservabilityContext` as `CopilotObservabilityContext`. NEVER mirror. Existing AISALESHT copilot/observability/recording/{callback_handler.py, turn_envelope.py} lift verbatim with sed rewrite — they already inherit from shared base. |
| Channel format registry + format_for_channel + intent_detector | shared/agent_observability/channels/* → lifted Story 2 | `luana_core_channels.{format,format_for_channel,intent_detector,channel_registry}` | **CONSUME** — copilot tools (knowledge_search, navigation, etc.) call `format_for_channel` via lifted package import. NEVER re-register channels. |
| LLM router + LiteLLM service + provider adapters | shared/infrastructure/llm/* → lifted Story 2 | `luana_core_llm.{router,factory,providers.litellm,_kwargs,_chat_model_resolver}` | **CONSUME** — copilot/application/router/model_router.py imports from luana_core_llm. |
| Outbox pattern + event bus adapter + domain events | shared/domain_events/outbox/* → lifted Story 2 | `luana_core_events.outbox.*` | **CONSUME** — copilot/domain/events.py classes inherit `DomainEvent` from luana_core_platform.domain.events. |
| Idempotency keys | shared/idempotency/* → lifted Story 2 | `luana_core_idempotency.*` | **CONSUME** — copilot workers (telegram_worker) use `IdempotencyService` from luana_core_idempotency. |
| BudgetGuard + RateLimiter (billing guards) | shared/billing/* → lifted Story 2 | `luana_core_billing.*` | **CONSUME** — pre-LLM-call check per Budget Gating PR-2 anchor (copilot-expert SKILL.md). |
| BrandReadPort + OfferReadPort + ProductMappingPort (cross-module ports) | shared/links/ports/* → lifted Story 2 | `luana_core_platform.links.ports.{brand,offer,scheduling,domain_lookup,edition_landing_clone}` | **CONSUME** — copilot/application/tools/{landing,offer_*,connections,analytics,assets,crm}_tools.py call these read ports. |
| TenantLocale VO + currency catalog | shared/domain/{locale,currency,currency_catalog} → lifted Story 2 | `luana_core_platform.domain.{locale,currency,currency_catalog}` | **CONSUME** — date/money formatting in copilot tools. |
| FieldContract platform + section catalogs | shared/domain/field_contract → lifted Story 2 | `luana_core_platform.domain.field_contract` | **CONSUME** — copilot persisters (brand_persister, offer_persister, buyer_persona_persister) call `FieldContract.walk_paths()`. |
| BrandSettings + BRAND_SECTION_MAP + BRAND_FIELD_OVERRIDES + PersonalityCompiler v2 | brand/* → lifted Story 5 | `luana_core_brand_studio.domain.*` | **CONSUME** — copilot persisters (brand_persister) + extraction + tools/extraction_tools call brand-studio domain. |
| Offer aggregate + 7 catalogs DAG + 84 presets + OfferReadPort impl | offer/* → lifted Story 5 | `luana_core_offer_studio.domain.*` | **CONSUME** — copilot persisters (offer_persister, buyer_persona_persister) + tools/offer_section_tools + offer_ladder_tools + tools/extraction_tools. |
| User + Tenant + dependencies | iam/* → lifted Story 3 | `luana_core_iam.*` | **CONSUME** — copilot/api/* routes use `get_current_user`, `get_db`, `get_tenant_locale`, `get_tenant_context` from luana_core_iam.api.dependencies. |
| Asset gallery / OfferGallery | assets/* → lifted Story 3 | `luana_core_assets.*` | **CONSUME** — copilot/application/tools/assets_tools.py calls AssetService + OfferGalleryService. |
| **NO EXISTING LAYER for: copilot module_registry + tool/workflow/extractor registries + suggestion engine + mutation_journal + marketing_kb_store + copilot deep_agent harness + LangGraph orchestrator + 36 [COPILOT-*] anchors** | — | — | **NEW (lift verbatim from AISALESHT)** — these ARE the copilot module. luana-core-copilot package is born here. |

**NO NEW LAYER created cross-module.** Story 6 lifts the copilot module proper; all dependencies resolve to existing luana-platform packages (21 already + 1 new = 22 total post-Story 6).

### §1.3 Python package dependency DAG (1 package + cleanup of 22 previously-deferred copilot_provider/ subfolders)

```
        luana-core-platform (Story 2 SSoT)
                ↑
                │
        luana-core-{events, idempotency, billing, channels, llm,
                    observability, compliance, extraction}  (Story 2)
                ↑
                │
        luana-core-iam (Story 3)
                ↑
                │
        luana-core-{tenant-profile, commercial-calendar,
                    social-proof, assets, tenant-domains}  (Story 3)
                ↑
                │
        luana-core-{crm, analytics-engine, landing, connections}  (Story 4)
                ↑
                │
        luana-core-{brand-studio, offer-studio}  (Story 5)
                ↑
                │
        luana-core-copilot  ★ NEW STORY 6 ★
                ↑
                ┌─ consumed by ─┐
                │ Stories 2-5 deferred copilot_provider/ unlift back to their packages
                │   (22 files cumulative — Stories 2,3,4,5 deferred lists in DEFERRED-FILES.md):
                │   - commercial-calendar/copilot_provider/ (Story 3 deferral, 2 files)
                │   - social-proof/copilot_provider/ (Story 3, 2 files)
                │   - crm/copilot_provider/ (Story 4, 2 files)
                │   - analytics-engine/copilot_provider/ (Story 4, 2 files)
                │   - landing/copilot_provider/ (Story 4, 2 files)
                │   - connections/copilot_provider/ (Story 4, 2 files)
                │   - brand-studio/copilot_provider/ (Story 5, 8 files)
                │   - offer-studio/copilot_provider/ (Story 5, 5 files; + offer_ai.py route 1 file)
                └─────────────────┘
```

**Cycle check:** None. copilot_provider/ subfolders import FROM luana-core-copilot but copilot does NOT import them back (registry pattern — copilot discovers providers at runtime via `module_registry`).

**Resolution summary cross-package edges:**

| Source package | Depends on | Symbol used |
|---|---|---|
| `luana-core-copilot` | `luana-core-platform` | `shared.application.{ai_action_service, extraction.base_orchestrator}` + `shared.domain.{base_entity, datetime_utils, events, field_contract, locale, ports.{BrandReadPort, OfferReadPort, scheduling, domain_lookup, edition_landing_clone}}` + `shared.domain_events.outbox` + `shared.infrastructure.{files, llm, web, prompts}` + `shared.links.ports.*` + `core.{database, enums.ModelRole, config}` |
| `luana-core-copilot` | `luana-core-iam` | `iam.api.dependencies.{get_current_user, get_db, get_tenant_locale, get_tenant_context}` + `iam.domain.user.User` + `iam.infrastructure.models.{UserModel, tenant_model.TenantModel}` |
| `luana-core-copilot` | `luana-core-observability` | `recording.{BaseAgentCallbackHandler, BaseObservabilityContext, sanitize_payload}` + `cost.{CostCalculator, FXResolver}` + `pricing.{PricingResolver, PricingSnapshotRepository}` + `persistence.{BaseTraceEventRepoProtocol, BaseLLMCallRepoProtocol, TenantBillingConfigRepository}` |
| `luana-core-copilot` | `luana-core-llm` | `router.LLMRouter` + `factory.build_provider_service` + `providers.litellm.LiteLLMService` |
| `luana-core-copilot` | `luana-core-channels` | `channel_registry` + `format.get_channel_format` + `format_for_channel` (LangChain tool) + `intent_detector` |
| `luana-core-copilot` | `luana-core-events` | `outbox.application.event_bus_adapter.adapter_bus` + outbox domain events |
| `luana-core-copilot` | `luana-core-idempotency` | `application.service.IdempotencyService` |
| `luana-core-copilot` | `luana-core-billing` | `application.llm_guards.BudgetGuardingLLMService` + `budget_guard.BudgetGuard` (per Budget Gating PR-2 — wiring deferred per anchor) |
| `luana-core-copilot` | `luana-core-brand-studio` | `domain.{aggregates.BrandSettings, personality.PersonalityCompiler, buyer_persona.BuyerPersona, field_contract.BRAND_SECTION_MAP}` + `application.services.brand_read_port_impl` (read-only consumption) |
| `luana-core-copilot` | `luana-core-offer-studio` | `domain.{offer.Offer, enums.{OfferArchetype, OfferValueLevel}, archetype_catalog, offer_type_preset_catalog, section_catalog, field_contract.OFFER_SECTION_MAP}` + `application.services.offer_read_port_impl` |
| `luana-core-copilot` | `luana-core-assets` | `application.assets_service.AssetService` + gallery service |
| `luana-core-copilot` | `luana-core-crm` | `domain.lead.Lead` (read-only for crm_tools) |
| `luana-core-copilot` | `luana-core-analytics-engine` | metrics_service (read-only for analytics_tools) |
| `luana-core-copilot` | `luana-core-landing` | landing_service (read-only for landing_tools) |
| `luana-core-copilot` | `luana-core-connections` | connection adapters (read-only for connections_tools, telegram_bot channel) |

**No inter-Story-6/7 coupling:** copilot does NOT import sales_agent — verified empty grep `from src.modules.sales_agent` in modules/copilot/.

## §2. Lift Order — 21 tickets per outcome §7.4 atomicity

**Batch 1: Workspace prep + skeleton (T-1, T-2)**
- T-1 (15min): workspace pyproject.toml + Story 6 section
- T-2 (20min): luana-core-copilot package skeleton + pyproject + README

**Batch 2: Domain (T-3..T-5) — registries + ports + types**
- T-3 (75min): domain core (28 files): module_registry, ports, workflow base, message, events, mutation_journal, schema_introspection, field_paths_hint, hooks/, rules/, skills/, message_blocks, card_payloads, etc.
- T-4 (45min): domain hooks/rules/skills extension API (already counted T-3 — split for granularity)
- T-5 — merged into T-3 if file count permits

**Batch 3: Infrastructure (T-6..T-8) — 4 sub-batches**
- T-6 (60min): infrastructure/repositories/ (10 repos) + infrastructure/models/ (11 SQLA models)
- T-7 (45min): infrastructure/persisters/ (5 files: brand, buyer_persona, offer, persister_registry)
- T-8 (60min): infrastructure/{channels, voice, qdrant, cache, prompts, web, workers} (~14 files)

**Batch 4: Application — 5 sub-batches due to density (T-9..T-13)**
- T-9 (60min): application/orchestrator/ (16 files: graph, deep_agent, system_prompt_composer, state, chat, conversational_questioning, subagents/, etc.)
- T-10 (60min): application/tools/ (28 files in 4 subfolders: tools/, tools/ask_tenant_data/, tools/guided/, tools/shared_tools/)
- T-11 (60min): application/{router, suggestions, workflows, procedures, data_access, extraction, guided, memory, observability} (~30 files)
- T-12 (60min): application/services/ (10 files including handlers/) + application/discovery + extraction_card_flow
- T-13 (45min): observability subfolder verbatim lift (copilot/observability/{recording, persistence, api} — these inherit luana-core-observability bases; NOT a mirror, distinct module-scoped repos + handlers)

**Batch 5: API + workers + evals (T-14..T-15)**
- T-14 (60min): api/ (22 files: chat, conversations, voice, telegram, plan, suggestions, etc. + dto/)
- T-15 (45min): evals/ (4 files: golden_dataset, runner, scorers/) + utils/

**Batch 6: Story 2-5 copilot_provider/ unlift (T-16)**
- T-16 (60min): UNLIFT 22 deferred copilot_provider/ files from Stories 2-5 lifted packages. Each subfolder copies back from AISALESHT, sed-rewrites `src.modules.copilot.*` → `luana_core_copilot.*`. Re-test affected packages.

**Batch 7: Cross-Story-5 stub cleanup per D-T2 (T-17)**
- T-17 (30min): Remove `MessageModel` stub from `core/luana-core-offer-studio/tests/conftest.py` (lines 145-157). Replace with `from luana_core_copilot.persistence.models.message_model import MessageModel  # noqa: F401`. Run offer-studio aggregate pytest GREEN. NOTE: `AppointmentModel` stub STAYS (scheduling = Story 8 territory).

**Batch 8: Integration + arch fitness (T-18..T-21)**
- T-18 (30min): Cross-package smoke + aggregate pytest GREEN (Stories 2+3+4+5+6 = 22 packages).
- T-19 (35min): NEW arch fitness `test_story6_brand_agnostic_engine.py` + `test_story6_no_forward_module_imports.py`.
- T-20 (45min): NEW arch fitness `test_copilot_registry_contracts_stable.py` (D-T1) + `test_no_residual_test_stubs_post_story_6.py` (D-T2) + `test_no_mirror_observability_in_copilot.py` (D-T6) + `test_module_descriptor_complete_for_lifted_packages.py` (D-T6) + `test_voice_compiler_ssot_still_intact.py` (regression Story 5).
- T-21 (30min): Finalization — lint + AISALESHT untouched verifier + DEFERRED-FILES.md update + README.md polish.

## §3. Per-Package Structure

### §3.1 luana-core-copilot layout

```
core/luana-core-copilot/
├── pyproject.toml                      # workspace member, version 0.0.6-alpha
├── README.md                           # SSoT + lift origin + deferrals
├── src/luana_core_copilot/
│   ├── __init__.py
│   ├── domain/                         # 28 files — registries + ports + base classes
│   │   ├── __init__.py
│   │   ├── module_registry.py          # ★ ModuleDescriptor registry (D-T6 SSoT)
│   │   ├── ports.py                    # ★ BaseCopilotProvider + ModuleData + DataQueryPlan ports (D-T1 FROZEN)
│   │   ├── workflow.py                 # ★ Workflow + WorkflowEngine + handler_ref base (D-T1 FROZEN)
│   │   ├── extraction_domain_registry.py # ★ ExtractorRegistry (D-T1 FROZEN)
│   │   ├── events.py, message.py, message_blocks.py, card_payloads.py
│   │   ├── mutation_journal.py, plan_state.py, procedure_state.py
│   │   ├── schema_introspection.py, field_paths_hint.py, offer_fields.py
│   │   ├── navigation_map.py, routing_policy.py, context_window.py
│   │   ├── suggestion.py, tenant_limits.py, telegram.py, voice.py
│   │   ├── hooks/{hook_registry, copilot_events}.py
│   │   ├── rules/{rule_definition, rule_registry, rule_metadata}.py
│   │   └── skills/{skill_definition, skill_registry, skill_metadata}.py
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── models/                     # 11 SQLA models verbatim (MessageModel HERE — D-T2 cleanup target)
│   │   │   ├── conversation_model.py
│   │   │   ├── message_model.py        # ★ D-T2 — offer-studio conftest now imports from here
│   │   │   ├── inspiration_model.py, mutation_journal_model.py
│   │   │   ├── pinned_memory_model.py, routing_log_model.py
│   │   │   ├── tenant_limits_model.py, tenant_limits_audit_model.py
│   │   │   ├── event_model.py, trace_event_model.py
│   │   │   ├── workflow_metric_model.py, telegram_models.py
│   │   ├── repositories/                # 10 repos
│   │   ├── persisters/                  # 5 persisters (brand, buyer_persona, offer + registry)
│   │   ├── channels/                    # TelegramBotChannel + InMemoryChannel adapters
│   │   ├── voice/                       # WhisperTranscriber endpoint
│   │   ├── qdrant/                      # MarketingKbStore (tenant-agnostic collection)
│   │   ├── cache/                       # DataQueryCache
│   │   ├── prompts/                     # PromptBase + sanitizer + templates/ + brand_extraction/
│   │   ├── web/                         # TrafilaturaClient + TavilySearch
│   │   ├── workers/                     # TelegramWorker
│   │   └── {in_memory_hook,in_memory_rule,in_memory_skill}_registry.py
│   ├── application/
│   │   ├── __init__.py
│   │   ├── orchestrator/                # 16 files — LangGraph deep_agent harness
│   │   │   ├── graph.py                 # ★ build_deep_agent_graph (LangGraph 2.0 StateGraph)
│   │   │   ├── deep_agent.py            # ★ deepagents subagent harness (preserve verbatim per D-T6)
│   │   │   ├── system_prompt_composer.py # ★ compose_system_prompt (slot 1-11 cache-friendly)
│   │   │   ├── system_prompt_layout.py
│   │   │   ├── chat.py, state.py, conversational_questioning.py
│   │   │   ├── inspirations_layer.py, block_adapters.py, stream_filters.py
│   │   │   ├── stream_provenance.py, output_sanitizer.py
│   │   │   ├── tool_call_dedup.py, context_budget.py, subagent_budget.py
│   │   │   ├── invoke_result.py
│   │   │   └── subagents/               # data_query, url_analyzer, audit_inspector
│   │   ├── tools/                       # 28 files — tool registry + 4 subfolders
│   │   │   ├── registry.py              # ★ ToolRegistry (D-T1 FROZEN signature)
│   │   │   ├── awareness, navigation, mutations, analytics_tools, assets_tools,
│   │   │   │   connections_tools, crm_tools, document_tools, extract_from_doc,
│   │   │   │   extraction_tools, fetch_url, knowledge_search, knowledge_tools,
│   │   │   │   landing_tools, module_tools, offer_ladder_tools, offer_section_tools,
│   │   │   │   pin_to_memory, procedure_tools, research, sales_agent_tools,
│   │   │   │   telegram_redirect, url_inspiration_analyzer, _analytics_inputs.py
│   │   │   ├── ask_tenant_data/         # 7 files: tool, intent_classifier, query_builder, synthesizer, state_check, executor, date_parser
│   │   │   ├── guided/                  # 4 files: start, advance, extract, end
│   │   │   └── shared_tools/            # clarify, web_research
│   │   ├── workflows/                   # WorkflowEngine + WorkflowRegistry (D-T1 FROZEN)
│   │   ├── suggestions/                 # SuggestionEngine + SuggestionRegistry + providers/
│   │   ├── router/                      # NANO LLMClassifier + RuleClassifier + ModelRouter
│   │   ├── procedures/                  # Procedure base + brand_setup + offer_creation + first_setup
│   │   ├── observability/               # CopilotJudge + RagGoldens (eval surface)
│   │   ├── extraction/                  # ActiveJobState + ActiveJobPersistence
│   │   ├── data_access/                 # Conversation reader
│   │   ├── memory/                      # ContextWindowBuilder + RollingSummarizer + TitleGenerator + TokenCounter
│   │   ├── guided/                      # GuidedStateReader + Persistence + BlockGenerator + QuestionHint
│   │   ├── services/                    # 10 services (telegram_link, mutation_apply, limits_resolver, document_processor, etc.) + handlers/
│   │   ├── discovery.py                 # ★ pkgutil-based provider auto-discovery
│   │   └── extraction_card_flow.py
│   ├── api/                             # 22 routers + DTOs
│   │   ├── __init__.py, _dependencies.py
│   │   ├── chat.py, conversations.py, voice.py, telegram.py, plan.py
│   │   ├── suggestions.py, actions.py, events.py, media.py, knowledge.py
│   │   ├── nudge.py
│   │   └── (DTOs co-located: conversation_dto, document_dto, suggestions_dto, etc.)
│   ├── observability/                   # MODULE-SCOPED observability (NOT mirror — extends luana-core-observability)
│   │   ├── __init__.py
│   │   ├── persistence/
│   │   │   ├── llm_call_repository.py   # extends BaseLLMCallRepoProtocol
│   │   │   └── trace_event_repository.py # extends BaseTraceEventRepoProtocol
│   │   ├── recording/
│   │   │   ├── callback_handler.py      # CopilotCallbackHandler(BaseAgentCallbackHandler)
│   │   │   ├── turn_envelope.py         # CopilotObservabilityContext(BaseObservabilityContext)
│   │   │   └── domain_subscribers.py
│   │   └── api/                         # observability admin endpoints
│   ├── evals/                           # 4 files — golden runner + classifier/summarizer scorers
│   │   ├── golden_dataset.py, runner.py
│   │   └── scorers/{base, classifier, summarizer}.py
│   └── utils/                           # 1 file
└── tests/
    ├── __init__.py
    ├── conftest.py                       # lift verbatim + sed for cross-module mocks
    ├── (213 test files lift — see §6)
    └── architecture/                     # NEW Story 6 arch tests live in core/tests/architecture/
```

### §3.2 pyproject.toml (Story 6)

```toml
[project]
name = "luana-core-copilot"
version = "0.0.6-alpha"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
    "fastapi>=0.115",
    "structlog>=24.0",
    "httpx>=0.27",
    "langgraph>=0.2",              # StateGraph + checkpointers
    "langchain-core>=0.3",
    "langchain-openai>=0.2",       # for OpenAI-protocol providers
    "deepagents>=0.5.3",           # subagent harness
    "qdrant-client>=1.10",         # marketing_kb_store
    "arq>=0.26",                   # workers/telegram_worker
    "jinja2>=3.1",                 # prompts templates
    "tiktoken>=0.7",               # token counter
    "trafilatura>=1.12",           # web crawl
    "litellm>=1.40",
    "luana-core-platform",
    "luana-core-iam",
    "luana-core-observability",
    "luana-core-llm",
    "luana-core-channels",
    "luana-core-events",
    "luana-core-idempotency",
    "luana-core-billing",
    "luana-core-extraction",
    "luana-core-brand-studio",
    "luana-core-offer-studio",
    "luana-core-assets",
    "luana-core-crm",
    "luana-core-analytics-engine",
    "luana-core-landing",
    "luana-core-connections",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/luana_core_copilot"]

[tool.pytest.ini_options]
pythonpath = ["."]
asyncio_mode = "auto"
```

## §4. Workspace Registration

Root `pyproject.toml`:
```toml
[tool.uv.workspace]
members = [
    "core",
    # (Stories 2-5 packages — 21 already registered)
    # Story 6 (NEW — 1 package)
    "core/luana-core-copilot",
    # Brand apps
    "nicolify", "vitalia", "comunify", "lupulo",
]

[tool.uv.sources]
# (Stories 2-5 — 21 entries already registered)
# Story 6 (NEW)
luana-core-copilot = { workspace = true }
```

## §5. Import Path Mapping (sed mechanical rewrites)

| AISALESHT source path | luana-platform internal path |
|---|---|
| `from src.modules.copilot.<X>` | `from luana_core_copilot.<X>` |
| `from src.modules.brand.<X>` | `from luana_core_brand_studio.<X>` |
| `from src.modules.offer.<X>` | `from luana_core_offer_studio.<X>` |
| `from src.modules.iam.<X>` | `from luana_core_iam.<X>` |
| `from src.modules.assets.<X>` | `from luana_core_assets.<X>` |
| `from src.modules.crm.<X>` | `from luana_core_crm.<X>` |
| `from src.modules.analytics.<X>` | `from luana_core_analytics_engine.<X>` |
| `from src.modules.landing.<X>` | `from luana_core_landing.<X>` |
| `from src.modules.connections.<X>` | `from luana_core_connections.<X>` |
| `from src.shared.agent_observability.<X>` | `from luana_core_observability.<X>` |
| `from src.shared.domain.<X>` | `from luana_core_platform.domain.<X>` |
| `from src.shared.infrastructure.<X>` | `from luana_core_platform.infrastructure.<X>` |
| `from src.shared.application.<X>` | `from luana_core_platform.application.<X>` |
| `from src.shared.links.<X>` | `from luana_core_platform.links.<X>` |
| `from src.shared.domain_events.<X>` | `from luana_core_events.<X>` |
| `from src.shared.idempotency.<X>` | `from luana_core_idempotency.<X>` |
| `from src.shared.billing.<X>` | `from luana_core_billing.<X>` |
| `from src.shared.infrastructure.llm.<X>` | `from luana_core_llm.<X>` |
| `from src.core.<X>` | `from luana_core_platform.core.<X>` |

## §6. Test Lift Strategy

213 test files in `backend/tests/modules/copilot/` lift verbatim to `core/luana-core-copilot/tests/`. Apply sed per §5. **None are deferred** — all copilot tests lift WITH the lift.

Cross-coupling tests that previously stayed in AISALESHT (Story 5 deferred 4 tests) now lift in T-16 alongside the copilot_provider/ subfolders:
- `test_brand_context_injector.py` (Story 5 deferral) → lifts to `core/luana-core-brand-studio/tests/`
- `test_buyer_persona_fields_dropped_regression.py` → `core/luana-core-brand-studio/tests/`
- `test_worker_emits_summary_and_pills.py` → `core/luana-core-brand-studio/tests/`
- `test_offer_data_access_provider.py` → `core/luana-core-offer-studio/tests/`

## §7. Architecture Fitness Tests (NEW Story 6)

### §7.1 Brand-agnostic engine invariant (extends Stories 4+5 §7.1)

`core/tests/architecture/test_story6_brand_agnostic_engine.py` — scans `luana_core_copilot` for `if brand ==`, brand-key literals, hardcoded API keys. Same regex template as Stories 4+5. PKGS = [("luana-core-copilot", "luana_core_copilot")].

### §7.2 No forward-Story imports

`core/tests/architecture/test_story6_no_forward_module_imports.py` — luana_core_copilot MUST NOT import from `luana_core_sales_agent` or `luana_core_campaigns` or `luana_core_{advertising, scheduling, social_media}`. Also blocks accidental `from src.modules.`.

### §7.3 Registry contract stability (D-T1)

`core/tests/architecture/test_copilot_registry_contracts_stable.py` — golden-snapshot the public signature of:
- `luana_core_copilot.domain.module_registry.ModuleRegistry` + `register/get/list_modules` + `ModuleDescriptor` dataclass fields
- `luana_core_copilot.application.tools.registry.ToolRegistry` + `register/get/list/groups` + `Tool` shape
- `luana_core_copilot.application.workflows.registry.WorkflowRegistry` + `Workflow` shape + `handler_ref` mechanism
- `luana_core_copilot.domain.extraction_domain_registry.ExtractorRegistry` + entries

Snapshot file: `core/tests/architecture/_snapshots/copilot_registry_v1.json`. Mismatch → FAIL with diff. Bump = arch fitness change requires architect ratification (Story 8 EP-1..EP-5 introduction is the next allowed bump occasion).

### §7.4 No residual test stubs post-Story 6 (D-T2)

`core/tests/architecture/test_no_residual_test_stubs_post_story_6.py`:
- Asserts `core/luana-core-offer-studio/tests/conftest.py` does NOT contain `class MessageModel(_Base)` declaration (must `import` from luana_core_copilot post-T-17).
- AppointmentModel stub may persist (scheduling = Story 8 territory) — documented allowlist.

### §7.5 No mirror observability in copilot (D-T6 + anti-duplication)

`core/tests/architecture/test_no_mirror_observability_in_copilot.py`:
- Scans `luana_core_copilot.observability.recording.callback_handler` — must `from luana_core_observability.recording.base_callback_handler import BaseAgentCallbackHandler` AND subclass it (NOT redefine).
- Same for `turn_envelope.py` → `BaseObservabilityContext`.
- Same for `cost_recorder` consumption — NEVER imported from `luana_core_copilot.observability` (cost_recorder lives in luana_core_observability).
- Verify no class declarations of: `FXResolver`, `PricingResolver`, `CostCalculator`, `sanitize_payload` function — these must be imports.

### §7.6 ModuleDescriptor complete for lifted packages (D-T6)

`core/tests/architecture/test_module_descriptor_complete_for_lifted_packages.py`:
- Asserts `module_registry.discover()` finds ModuleDescriptor entries for: brand, offer, crm, analytics, landing, connections, commercial_calendar, social_proof, assets, iam, tenant_profile, tenant_domains — all Stories 2-5 packages.
- Validates ModuleDescriptor fields populated: `module_key`, `display_name`, `data_access_kinds`, `tools`, `workflows`.

### §7.7 Voice compiler SSoT still intact (regression Story 5)

`core/tests/architecture/test_voice_compiler_ssot_still_intact.py`:
- Re-runs Story 5 V-AG-3 assertion in Story 6 context: only `luana-core-brand-studio.domain.personality` declares `class PersonalityCompiler`. Story 6 must NOT introduce mirror.

### §7.8 [COPILOT-*] anchor registry stability

`core/tests/architecture/test_copilot_anchors_count_stable.py` — counts anchors with regex `r"\[COPILOT-[A-Z0-9-]+\]"` in `luana_core_copilot/**/*.py`. Asserts exactly 36 (post-F11 per copilot-expert §"Anchors"). Bump requires explicit registry update.

## §8. Agentic Surfaces (deep-dive in 03-arch-agentic.md)

See companion file `03-arch-agentic.md` for full LangGraph state shape, deepagents subagent topology, prompt cache slot 1-11 architecture, ToolRegistry/WorkflowRegistry/ExtractorRegistry signatures (D-T1 FROZEN), observability writes flow, Qdrant RAG marketing_kb tenant-agnostic invariant, 36 [COPILOT-*] anchor map.

**Architecture decisions baked here (NOT in 03-arch-agentic.md — those are runtime-spec details):**

- **D-T1 registry contracts FROZEN** — `ToolRegistry.register/get/list/groups`, `WorkflowRegistry.register/get`, `ExtractorRegistry.register/get`, `ModuleRegistry.discover/get/list_modules` public signatures lock at lift moment. Golden snapshot test V-AG-3 enforces. Story 8 EP-1..EP-5 wrap these as formal SDK without changing internals.
- **D-T2 cleanup** — T-17 dedicated ticket removes `MessageModel` stub from offer-studio conftest. AppointmentModel stub stays.
- **D-T6 ModuleDescriptor cement** — module_registry.discover() pre-populates entries for all Stories 2-5 lifted packages. Each lifted package's `copilot_provider/provider.py` registers via convention.
- **D-T6 anti-mirror observability** — copilot/observability/recording/{callback_handler, turn_envelope} are SUBCLASSES of luana-core-observability bases. arch test V-AG-5 enforces.
- **D-T6 LangGraph + Anthropic cache + Qdrant verbatim** — orchestrator/graph.py + system_prompt_composer.py + marketing_kb_store.py lift verbatim. Versions match (langgraph>=0.2, deepagents>=0.5.3 per AISALESHT current).

## §9. Deferred Files (Story 6)

### §9.1 Streamlit admin pages → DEFER to Story 10 (nicolify migration)

| AISALESHT path | Reason | Lifts at |
|---|---|---|
| `backend/src/admin/pages/{trazas,copilot-routing,costo-copilot,copilot-limits,copilot-quality,marketing-kb,...}.py` | These are Streamlit pages CONSUMING copilot via API. Live in nicolify shell, not core engine. | Story 10 (nicolify migration moves admin shell) |

### §9.2 Cross-package adapter wiring for connections.api/dependencies (Story 4 deferral resolution partial)

Per Story 4 DEFERRED-FILES.md, `backend/src/modules/connections/api/dependencies/__init__.py` wires `ChatOrchestrator` from copilot. Story 6 provides `ChatOrchestrator`; but full wiring requires Story 7 (sales_agent's MessageHandlerPort impl). **Story 6 DOES NOT fully unblock connections/api/dependencies.** Stub stays until Story 7.

### §9.3 Reserved (NOT existing, NOT deferred)

- **EP-1..EP-5 Extension SDK formal wrapping** → Story 8. Stories 6+7 freeze registries; Story 8 wraps them as SDK.

### §9.4 Audit trail (append to core/DEFERRED-FILES.md)

```markdown
## Story 6 deferrals (2026-05-11) + unlifts

### UNLIFTED Story 6 (previously deferred Stories 2-5):
- commercial-calendar/copilot_provider/ (Story 3 deferral) — 2 files
- social-proof/copilot_provider/ (Story 3) — 2 files
- crm/copilot_provider/ (Story 4) — 2 files
- analytics-engine/copilot_provider/ (Story 4) — 2 files
- landing/copilot_provider/ (Story 4) — 2 files
- connections/copilot_provider/ (Story 4) — 2 files
- brand-studio/copilot_provider/ (Story 5) — 8 files
- offer-studio/copilot_provider/ (Story 5) — 5 files
- offer-studio/api/offer_ai.py (Story 5) — 1 file
- brand-studio tests: test_brand_context_injector + test_buyer_persona_fields_dropped_regression + test_worker_emits_summary_and_pills (Story 5) — 3 files
- offer-studio tests: test_offer_data_access_provider (Story 5) — 1 file
- **Total UNLIFTED: 30 files**

### NEW Story 6 deferrals:
- backend/src/admin/pages/{trazas,copilot-routing,costo-copilot,...} → Story 10 (nicolify shell migration)
- connections/api/dependencies/__init__.py real wiring → Story 7 (sales_agent's MessageHandlerPort needed for ChatOrchestrator full instantiation)
- AppointmentModel stub in offer-studio conftest → Story 8 (scheduling lift)
```

## §10. Architecture Fitness Gates (test surfaces)

| Gate | Layer | Owner |
|---|---|---|
| `uv sync --all-packages` GREEN (22 packages) | luana-platform root | gate-runner |
| `uv run pytest core/luana-core-copilot/tests/` GREEN | per-package | gate-runner |
| `uv run ruff check core/luana-core-copilot/` GREEN | root | gate-runner |
| Stories 2-5 packages still GREEN after copilot_provider/ unlift (T-16) | luana-platform | gate-runner |
| 7 NEW arch tests V-AG-1..V-AG-8 GREEN | luana-platform | gate-runner |
| AISALESHT untouched verifier | AISALESHT repo | gate-runner |
| No-publish verifier | luana-platform | gate-runner |
| core/DEFERRED-FILES.md updated | luana-platform | gate-runner |
| MessageModel stub removed from offer-studio conftest.py (T-17) | luana-platform | gate-runner |

## §11. Research Notes (state-of-the-art as of 2026-05-11)

| Source | Accessed | Key takeaway |
|---|---|---|
| Anthropic prompt caching https://platform.claude.com/docs/en/build-with-claude/prompt-caching | 2026-05-11 | TTL 5min default (1.25x base write / 0.1x read) vs 1h (2x write / 0.1x read). Min cacheable tokens Claude Opus 4.7 = **4096**. Place cache_control on LAST stable block. Lookback 20 blocks. `cache_creation_input_tokens` + `cache_read_input_tokens` measure hit rate. **Workspace-isolated caches as of 2026-02-05.** Multi-TTL mixing supported (longer TTL first). |
| LangGraph workflows https://docs.langchain.com/oss/python/langgraph/workflows-agents | 2026-05-11 | StateGraph + reducers (add_messages, operator.add). Stream modes: values, updates, messages, tasks, checkpoints, custom. ToolNode prebuilt. AsyncPostgresSaver checkpointer mandatory for production (NEVER MemorySaver). Stream mode `updates` recommended for production UI per-node deltas. |
| deepagents docs https://docs.langchain.com/oss/python/deepagents/overview | 2026-05-11 | `task` tool spawns subagents with context isolation. SubAgent dict shape: name + description + prompt + tools (explicit list) + model override. Per-subagent state scoping via SubAgentMiddleware `allowed_keys_to_subagent`/`allowed_keys_from_subagent`. AISALESHT current version: 0.5.3 (verified in copilot pyproject — preserve). |
| copilot-expert SKILL.md (internal) | 2026-05-11 | 11 fases F0-F11 cemented. 36 [COPILOT-*] anchors capped. Ratchet `copilot → módulo` import = 22 frozen. System prompt slot order 1-11 (slot 3 marketing_kb_hint, slot 4 lighthouse, slot 7+ volatile). Cache hit rate target ≥60% post-deploy. |
| sales-agent-expert SKILL.md (internal) | 2026-05-11 | §3 NO-TOCAR surfaces: closer_studio API+WS, SmartBufferService, OutputManager chunking, enrollment, agent_state_checkpoints schema, webhook adapters, follow_up_engine cadence, PromptVersionModel, model_pricing_snapshot, tool_call_dedup. PersonalityProfile.system_instruction = voz SSoT slot 5. |
| anti-duplication.md (internal) | 2026-05-11 | Inventory SSoT shared abstractions — BaseObservabilityContext, BaseAgentCallbackHandler, FXResolver.default, PricingResolver, sanitize_payload, base_trace_event_repo, base_llm_call_repo, channel format registry. CARDINAL rule: copilot inherits/consumes, NEVER mirrors. |
| auditor-downstream-regression.md (internal) | 2026-05-11 | Surface→downstream test map. shared/agent_observability changes ripple to modules/{copilot,sales_agent}/observability/. Story 6 lift = downstream regression scope = full copilot tests + Stories 2-5 packages re-run post-unlift. |

**Knowledge cutoff disclosure:** Opus 4.7 cutoff Jan 2026. Anthropic prompt caching post-cutoff details (Feb 2026 workspace isolation) verified live via canonical URL above on 2026-05-11. LangGraph 2.0 + deepagents 0.5.3 APIs verified against AISALESHT's working code (which has been in production since F11 close 2026-Q1).

## §12. Cross-Cutting Concerns

- **Tenant isolation:** every query `tenant_id` filter — copilot already complies in AISALESHT. Marketing_kb is tenant-agnostic (global collection per F10 design). All other queries tenant-scoped.
- **PII sanitization:** `sanitize_payload` from luana_core_observability used on every observability write. response_model= on routes. Lift preserves.
- **Spanish neutro:** copilot user-facing strings (tools descriptions, system prompts, channel format hints, error messages) — lift verbatim. NO voseo violations expected per Story 5 precedent.
- **Master data:** UTC store, tenant locale display. Already complies.
- **Native-first:** validators use `uv run pytest` / `uv run ruff` — no Docker.
- **Currency:** copilot monetary fields (when applicable in tools/analytics_tools) include `currency` per shared catalog.
- **Migrations:** copilot uses Alembic in AISALESHT; lifts NOT applicable here (Stories 2-5 don't lift migrations — migrations stay in brand apps).

## §13. capability YAML + modules/ Updates Required

**None Story 6.** Mechanical lift. Outcome `luana-platform-migration.md` § progress log updated by /pm at story close. Capability `luana-core/multi-brand-platform.yaml` exists already (Story 1) — Story 6 adds `copilot-engine` capability mention via /pm capability promotion at merge.

## §14. Open Questions for PM (none blocking)

All scope decisions resolved per outcome §7.2 + §7.3 + ADR-001 + 6 D-T decisiones técnicas + 3 ratificaciones business:

- **D-T1 registry contracts FROZEN at lift moment** — ratified.
- **D-T2 MessageModel stub cleanup in T-17** — AppointmentModel stub stays per scheduling = Story 8 territory.
- **D-T6 module_registry + tool/workflow/extractor registries lift verbatim** — public API surface frozen via golden snapshot V-AG-3.
- **D-T6 observability anti-mirror** — copilot/observability/{recording, persistence} = subclasses NOT mirrors.
- **D-T6 LangGraph + Anthropic cache + Qdrant verbatim** — versions in pyproject match AISALESHT.
- **D-T6 36 anchors cap stable** — arch test V-AG-8 cements.

If Chris reads this and wants to PRE-introduce EP-1..EP-5 SDK formalization in Story 6 (instead of Story 8) → that's NEW abstractions, scope expansion, escalate.

If Chris reads this and finds the Streamlit admin pages SHOULD lift in Story 6 (instead of Story 10) → Streamlit shell is part of nicolify app, not core engine. Lifting now duplicates work post-Story 10. Escalate if disagreement.
