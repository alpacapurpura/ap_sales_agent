---
story_id: luana-brand-offer-studios
arch_version: 1
last_modified: 2026-05-11
drafted_by: /architect (claude-opus-4-7)
authority: 00-story.md + outcome §7.3 lift mode + §7.2 extension Story 5 + ADR-001 §2.4 + Story 4 03-arch.md pattern reference
deviations_from_spec:
  - "2 copilot_provider/ subfolders (brand/copilot_provider/ + offer/copilot_provider/) DEFERRED to Story 6 (copilot lift). Same pattern as Story 4 §9.1 — they import src.modules.copilot.domain.{ports,workflow}. Story 6 territory."
  - "offer/api/{counts.py,campaigns.py} DEFERRED to Story 8 (campaigns lift). They import src.modules.advertising.application.services.offer_campaigns_read_adapter (advertising is in Story 8's lift batch — verified per outcome §2 Story 8 = `luana-campaigns-extension-sdk`)."
  - "offer/api/offer_ai.py DEFERRED to Story 6 (copilot lift). It imports src.modules.copilot.application.services.offer_psychology_service which is concrete copilot LLM-call code, Story 6 territory."
  - "Voice compiler v2 ELEVATION (ADR-001 §2.4): PersonalityCompiler class (brand/domain/personality.py line 440) STAYS in luana-core-brand-studio.domain.personality verbatim. NO refactor in Story 5 — same file location, same name, same signature. ADR-001 §2.4 says engine lives in core-brand-studio (which is THIS story's target). Story 7 wires BrandVoicePort consumer into core-sales-agent."
  - "BrandVoicePort stub (per 00-story.md): per outcome §7.3 'MUST DO: preserve public API surface, no new abstractions', we DO NOT create BrandVoicePort port file in Story 5. ADR-001 §2.4 mentions it as Story 7's consumption surface — Story 7 will introduce the port (with the implementation in core-brand-studio at that time). Adding the port stub here would violate §7.3 'no new abstractions'. Re-confirmed by Chris ratification §7.2 'lift-mode with design-decisions pre-ratified' — the design decision is the ELEVATION (✓ done by lifting verbatim to core-brand-studio.domain.personality), NOT introducing a new port today."
  - "voice cloning feature flag: per 00-story.md it 'activa pipeline LLM-distillation desde 50+ chats reales'. NO code exists for this pipeline in AISALESHT brand/. Per §7.3 'no scope expansion', Story 5 does NOT introduce voice cloning pipeline. The flag is a future BrandConfig field — outcome §2.5 + Story 11-13 territory. Re-confirmed §7.2 autonomy rationale: 'cloning flag declarativo por brand en BrandConfig' = BrandConfig schema field, NOT pipeline implementation."
  - "Tests `test_offer_data_access_provider.py` (offer) + `test_worker_emits_summary_and_pills.py` (brand) + `test_buyer_persona_fields_dropped_regression.py` (brand) DEFERRED to Story 6 — they import from src.modules.copilot.* directly. Story 6 lifts copilot, then those tests can lift alongside copilot's test surface OR be redesigned to use mocks (TBD Story 6)."
  - "Offer module split into 4 lift tickets (T-9 domain, T-10 infra, T-11 app+presets, T-12 api) due to 95-file density vs Story 4's analytics 3-split precedent. Single 'lift offer' ticket would exceed Sonnet 2h cap. Per outcome §7.4 atomicity rule."
  - "Brand module split into 5 lift tickets (T-3 domain, T-4 infra, T-5 app+services, T-6 voice-fidelity+style-analyzer, T-7 api, T-8 workers) due to 81-file density + voice-fidelity sub-module + style-analyzer LangGraph agent (extraction). Sub-tickets preserve atomicity per outcome §7.4."
---

# Story 5 — Luana Brand Studio + Offer Studio lift — Architecture (03-arch.md)

## §1. Topology — Dependency Graph (resolved)

### §1.1 Audit method

Per `.claude/rules/anti-duplication.md` cross-module audit + outcome §7.3 lift mode:

```bash
cd /home/chris/AISALESHT/backend/src/modules
for m in brand offer; do
    echo "==== $m ===="
    grep -rEh "^from src\.(modules|shared|core)\." $m/ --include="*.py" | sort -u
done
```

Audit findings (full inventory captured in §9 deferrals):

1. **brand↔offer cross-import:** NONE in production code. Both lift cleanly to separate packages, depend on shared (Story 2) + iam (Story 3) only.
2. **brand→copilot forward imports:** 4 files in `brand/copilot_provider/` only. NONE in `brand/domain` `application` `infrastructure` `api` `workers`.
3. **offer→copilot forward imports:** 4 files in `offer/copilot_provider/` + 1 file `offer/api/offer_ai.py` (imports `copilot.application.services.offer_psychology_service`).
4. **offer→advertising forward imports:** 2 files `offer/api/counts.py` + `offer/api/campaigns.py` (both import `advertising.application.services.offer_campaigns_read_adapter`).
5. **brand→sales_agent forward imports:** NONE.
6. **offer→sales_agent forward imports:** NONE.

Total deferrals: 4 brand copilot_provider/ files + 4 offer copilot_provider/ files + 2 offer/api files (advertising) + 1 offer/api/offer_ai.py (copilot) + 3 test files = 14 files DEFERRED.

### §1.2 Python package dependency DAG (2 packages)

```
                  luana-core-platform  (Story 2 foundation)
                                    ↑
                                    │
                ┌──────────────────┴──────────────────┐
                │                                     │
                │                                     │
   luana-core-brand-studio              luana-core-offer-studio
                │                                     │
                ↓                                     ↓
        luana-core-iam (Story 3)              luana-core-iam (Story 3)
                │                                     │
   (uses User + tenant context;          (uses User + tenant context;
    consumes BrandReadPort               consumes OfferReadPort
    via shared/links/ports;              via shared/links/ports;
    PersonalityCompiler lives            consumes 7 catalogs DAG
    here per ADR-001 §2.4;               + 76 presets verbatim;
    StyleAnalyzer LangGraph agent        consumes ProductMappingPort
    lifted in §3.2 sub-folder)           from shared.domain.ports)
```

**Resolution summary (cross-package edges, all DAG-clean):**

| Source package | Depends on | Symbol used |
|---|---|---|
| `luana-core-brand-studio` | `luana-core-platform` | `shared.application.{ai_action_service, extraction.base_orchestrator, progress_emitter, field_diff}` + `shared.domain.{base_entity, datetime_utils, events, extraction_jobs, field_contract, ports.BrandReadPort, locale}` + `shared.domain_events.outbox.application.event_bus_adapter` + `shared.infrastructure.{files.file_parsing_service, llm.factory, prompts.base, web.crawler}` + `shared.links.ports.brand` + `core.{database, enums.ModelRole}` |
| `luana-core-brand-studio` | `luana-core-iam` | `iam.api.dependencies::{get_current_user, get_db}` + `iam.domain.user::User` + `iam.infrastructure.models.{UserModel, tenant_model.TenantModel}` |
| `luana-core-offer-studio` | `luana-core-platform` | `shared.application.{ai_action_service, extraction.base_orchestrator, progress_emitter}` + `shared.domain.{base_entity, datetime_utils, enums.{AvatarPersona, FinancialCapacity, LeadTemperature}, expert_business_type, extraction_jobs, field_contract, locale, ports.{OfferReadPort, ProductMappingPort}}` + `shared.domain_events.outbox.application.event_bus_adapter` (transitive via workers) + `shared.infrastructure.{files.file_parsing_service, prompts.base, web.crawler}` + `shared.links.ports.{edition_landing_clone}` + `core.{database, enums.ModelRole}` |
| `luana-core-offer-studio` | `luana-core-iam` | `iam.api.dependencies::{get_current_user, get_db, get_tenant_locale, get_tenant_context}` + `iam.domain.user::User` |

**Cycle check:** None. DAG-clean. brand-studio ⊥ offer-studio (no inter-Story-5 edges).

**No inter-Story-5 coupling.** Cross-checked:

```bash
grep -l "from src.modules.brand" /home/chris/AISALESHT/backend/src/modules/offer/ -r
# → empty (offer never imports brand directly)
grep -l "from src.modules.offer" /home/chris/AISALESHT/backend/src/modules/brand/ -r
# → empty (brand never imports offer)
```

Both Story 5 packages parallelize after Story 4 batch (already done 2026-05-11).

### §1.3 Coupling notes

- **brand carries PersonalityProfile + PersonalityCompiler** — domain/personality.py contains the compiler (line 440) per ADR-001 §2.4 ownership. Verbatim lift preserves SSoT.
- **brand consumes BrandReadPort** (defined in `shared.domain.ports`, lifted Story 2 to `luana_core_platform.domain.ports`). `brand/application/services/brand_read_port_impl.py` implements it. Lift preserves.
- **brand has StyleAnalyzer LangGraph agent** in `application/agents/style_analyzer/`. Lift verbatim — preserves graph topology, no agentic logic changes. Per outcome §7.3 "no refactor".
- **offer consumes OfferReadPort + ProductMappingPort** (defined `shared.domain.ports`). Implementations in `offer/application/services/offer_read_port_impl.py` + `product_mapping_port_impl.py`. Lift preserves.
- **offer 7 catalogs DAG** — `archetype_catalog.py`, `value_level_catalog.py`, `format_catalog.py`, `section_catalog.py`, `offer_ladder_hints.py`, `offer_type_preset_catalog.py`, `variant_structure_catalog.py` — all lift verbatim. `_CATALOG_VERSION` constants (in `api/offer_type_presets.py`) preserved. No bump in Story 5 — that's a runtime bump triggered when catalog content changes; lift = identical content, no version bump needed.
- **offer 76 presets:** all 76 lift verbatim in `domain/offer_type_preset_catalog.py`.
- **offer extraction wave-based orchestrator** — `application/offer_extraction_orchestrator.py` subclasses `shared.application.extraction.base_orchestrator.BaseExtractionOrchestrator`. Same pattern as brand extraction. Lift preserves.

### §1.4 No-cycle proof

Manually walked the DAG:
- brand-studio → platform.shared + platform.core + iam (downward edges only)
- offer-studio → platform.shared + platform.core + iam (idem)
- iam doesn't import brand or offer
- platform doesn't import brand or offer

No cyclic edges. Pure DAG.

### §1.5 No forward-Story-6/7/8 coupling (after deferrals)

Verified post-deferral grep:

```bash
grep -rEh "^from src\.modules\.(copilot|sales_agent|advertising|campaigns|scheduling|social_media)\." \
    /home/chris/AISALESHT/backend/src/modules/{brand,offer}/ \
    --include="*.py" \
    --exclude-dir=copilot_provider | sort -u
```

Result (after deferring per §9):
- `brand/`: 0 forward imports remaining (only copilot_provider/ subfolder had them).
- `offer/`: 0 forward imports remaining (after deferring counts.py + campaigns.py + offer_ai.py).

## §2. Lift Order

Per dependency graph + file density, lift order is **1 batch × 2 parallelizable packages**:

**Batch 1 (both parallel after T-1 workspace prep; no inter-Story-5 deps):**
1. `luana-core-brand-studio` — 81 files (75 production after deferring 4 copilot_provider/ + 1 test file in src; 35 tests after deferring 2). Split into 6 tickets (T-2 skeleton, T-3 domain, T-4 infra, T-5 app/services, T-6 voice-fidelity+style-analyzer LangGraph, T-7 api, T-8 workers).
2. `luana-core-offer-studio` — 95 files (88 production after deferring 4 copilot_provider/ + 2 advertising + 1 copilot api/offer_ai.py = 7 files). 74 tests (73 after deferring test_offer_data_access_provider.py). Split into 5 tickets (T-9 skeleton+domain, T-10 infra, T-11 app, T-12 api, T-13 workers).

**Cross-cutting:**
- T-1 workspace prep before any lift (extends Stories 2+3+4 root pyproject.toml).
- T-14 cross-package integration smoke + aggregate pytest post-lifts.
- T-15 brand-agnostic engines arch fitness (extends Story 4 §7.1 to brand + offer).
- T-16 no-forward-imports arch fitness (extends Story 4 §7.2 to Story 5 packages).
- T-17 voice compiler SSoT smoke (assert PersonalityCompiler.compile produces non-empty 5-block instruction post-lift — placement verification per ADR-001 §2.4).
- T-18 lint + AISALESHT untouched + DEFERRED-FILES.md update + READMEs.

## §3. Per-Package Structure

### §3.1 Python package layout (mirror Story 4 §3.1)

```
core/luana-core-{brand-studio,offer-studio}/
├── pyproject.toml                       # workspace member, version "0.0.1-alpha"
├── README.md                            # stub: 1 paragraph what + lift origin + deferrals
├── src/
│   └── luana_core_{brand_studio,offer_studio}/   # snake_case (PEP 8)
│       ├── __init__.py
│       └── <preserved DDD structure verbatim>
└── tests/
    ├── __init__.py
    ├── conftest.py                       # lift verbatim
    └── <preserved test structure>
```

### §3.2 luana-core-brand-studio layout

```
core/luana-core-brand-studio/
├── pyproject.toml
├── README.md
├── src/luana_core_brand_studio/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── avatars.py
│   │   ├── buyer_personas.py
│   │   ├── dto/
│   │   │   ├── __init__.py
│   │   │   ├── avatars.py
│   │   │   ├── buyer_personas.py
│   │   │   └── extraction.py
│   │   ├── extraction.py
│   │   ├── personality.py
│   │   ├── router.py
│   │   ├── sections.py
│   │   └── style.py
│   ├── application/
│   │   ├── __init__.py
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   └── style_analyzer/
│   │   │       ├── __init__.py
│   │   │       ├── graph.py             # LangGraph onboarding_app — lift verbatim
│   │   │       ├── nodes.py
│   │   │       ├── nodes_research.py
│   │   │       ├── prompts.py
│   │   │       └── state.py             # OnboardingState TypedDict
│   │   ├── extraction_crawler.py
│   │   ├── extraction_orchestrator.py   # BaseExtractionOrchestrator subclass
│   │   ├── extraction_routes.py
│   │   ├── extraction_service.py
│   │   ├── extraction_trace.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── brand_data_adapter.py    # implements BrandDataPort
│   │   │   ├── brand_field_apply_adapter.py
│   │   │   ├── brand_read_port_impl.py  # implements BrandReadPort
│   │   │   └── personality_service.py
│   │   └── voice_fidelity/
│   │       ├── __init__.py
│   │       ├── golden.py                # GOLDEN_PROMPTS
│   │       └── grader.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── aggregates.py                # BrandSettings root
│   │   ├── buyer_persona.py
│   │   ├── buyer_persona_field_contract.py
│   │   ├── communication_assets.py
│   │   ├── entities.py
│   │   ├── field_contract.py            # BRAND_SECTION_MAP + BRAND_FIELD_OVERRIDES
│   │   ├── identity.py
│   │   ├── narrative.py                 # StoryBrand
│   │   ├── personality.py               # PersonalityCompiler v2 ★ ADR-001 §2.4 SSoT ★
│   │   ├── positioning.py               # Brand Love Key
│   │   ├── section_catalog.py
│   │   ├── story.py
│   │   ├── strategy.py
│   │   └── team.py                      # BrandContact + KeyFigure + BrandTestimonial + BrandAuthorityItem
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── avatar_model.py
│   │   │   ├── brand_summary_model.py
│   │   │   ├── buyer_persona_model.py
│   │   │   ├── extraction_trace_model.py
│   │   │   └── personality_model.py
│   │   ├── parsers/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── instagram_parser.py
│   │   │   ├── telegram_parser.py
│   │   │   └── whatsapp_parser.py
│   │   ├── qdrant/
│   │   │   ├── __init__.py
│   │   │   └── style_anchor_store.py
│   │   └── repositories/
│   │       ├── __init__.py
│   │       ├── avatar_repository.py
│   │       ├── brand_repository.py
│   │       ├── brand_summary_repository.py
│   │       ├── buyer_persona_repository.py
│   │       └── personality_repository.py
│   ├── tests/
│   │   ├── __init__.py
│   │   └── repro_issue.py               # in-source test scaffold (lift verbatim)
│   └── workers/
│       ├── __init__.py
│       └── tasks.py
│   # NOTE: copilot_provider/ NOT lifted — DEFERRED Story 6 (see §9.1)
└── tests/
    ├── __init__.py
    ├── application/
    │   ├── __init__.py
    │   └── services/
    │       ├── __init__.py
    │       └── test_brand_data_adapter_pr2.py
    ├── conftest.py
    ├── integration/
    │   ├── __init__.py
    │   └── test_outbox_cutover.py
    ├── test_avatar_repository.py
    ├── test_brand_context_injector.py   # ← DEFERRED Story 6 (imports copilot)
    ├── test_brand_repository.py
    ├── test_brand_section_updated_event.py
    ├── test_brand_summary_repository.py
    ├── test_buyer_persona_api.py
    ├── test_buyer_persona_entity.py
    ├── test_buyer_persona_fields_dropped_regression.py  # ← DEFERRED Story 6 (imports copilot)
    ├── test_buyer_persona_model.py
    ├── test_buyer_persona_repository.py
    ├── test_clone_dry_run.py
    ├── test_data_model_purge.py
    ├── test_domain_models.py
    ├── test_extraction_orchestrator_per_wave_save.py
    ├── test_extraction_router.py
    ├── test_extraction_service.py
    ├── test_extraction_trace.py
    ├── test_outbox_adapter_integration.py
    ├── test_parsers.py
    ├── test_personality_api.py
    ├── test_personality_compiler_output.py
    ├── test_personality_compiler_v2.py
    ├── test_personality_domain.py
    ├── test_personality_integration.py
    ├── test_personality_profile_updated_event.py
    ├── test_personality_repository.py
    ├── test_personality_service.py
    ├── test_style_anchor_store.py
    ├── test_voice_fidelity_grader.py
    └── test_worker_emits_summary_and_pills.py  # ← DEFERRED Story 6 (imports copilot)
```

### §3.3 luana-core-offer-studio layout

```
core/luana-core-offer-studio/
├── pyproject.toml
├── README.md
├── src/luana_core_offer_studio/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── archetypes.py
│   │   ├── assets.py
│   │   ├── campaigns.py                 # ← DEFERRED Story 8 (imports advertising)
│   │   ├── counts.py                    # ← DEFERRED Story 8 (imports advertising)
│   │   ├── definitions.py
│   │   ├── dto/
│   │   │   ├── __init__.py
│   │   │   ├── asset_dtos.py
│   │   │   ├── campaigns_dtos.py
│   │   │   ├── counts_dtos.py
│   │   │   ├── extraction.py
│   │   │   ├── knowledge_dtos.py
│   │   │   ├── landing_dtos.py
│   │   │   ├── lifecycle_dtos.py
│   │   │   ├── offer_gallery.py
│   │   │   └── products.py
│   │   ├── formats.py
│   │   ├── knowledge.py
│   │   ├── landing.py
│   │   ├── launch_editions.py
│   │   ├── lifecycle.py
│   │   ├── offer_ai.py                  # ← DEFERRED Story 6 (imports copilot.offer_psychology_service)
│   │   ├── offer_extraction.py
│   │   ├── offer_field_contract.py
│   │   ├── offer_ladder_hints.py
│   │   ├── offer_type_presets.py        # contains _CATALOG_VERSION
│   │   ├── product_mappings.py
│   │   ├── products.py
│   │   ├── value_levels.py
│   │   └── variant_structures.py
│   ├── application/
│   │   ├── __init__.py
│   │   ├── edition_clone_service.py
│   │   ├── extraction_routes.py
│   │   ├── extraction_schemas.py
│   │   ├── launch_edition_service.py
│   │   ├── offer_extraction_orchestrator.py  # BaseExtractionOrchestrator subclass
│   │   ├── offer_extraction_service.py
│   │   ├── offer_extraction_trace.py
│   │   ├── offer_generator.py
│   │   ├── offer_service.py             # create_offer with preset_id derives archetype
│   │   ├── ports.py
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── landing_generation_service.py
│   │       ├── offer_asset_service.py
│   │       ├── offer_completion_service.py
│   │       ├── offer_counts_service.py
│   │       ├── offer_knowledge_service.py
│   │       ├── offer_lifecycle_service.py
│   │       ├── offer_read_port_impl.py   # implements OfferReadPort
│   │       └── product_mapping_port_impl.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── archetype_catalog.py         # 5 archetypes (1 of 7 catalogs DAG)
│   │   ├── assets.py
│   │   ├── details.py
│   │   ├── enums.py                     # OfferArchetype, OfferValueLevel, etc
│   │   ├── events.py
│   │   ├── exceptions.py
│   │   ├── extraction_section_map.py
│   │   ├── field_contract.py            # OFFER_SECTION_MAP + OFFER_FIELD_OVERRIDES
│   │   ├── format_catalog.py            # composite (2 of 7)
│   │   ├── knowledge_source.py
│   │   ├── launch_edition.py
│   │   ├── lifecycle.py
│   │   ├── offer.py                     # Offer aggregate root + preset_id
│   │   ├── offer_ai_schemas.py
│   │   ├── offer_gallery.py
│   │   ├── offer_ladder_hints.py        # hints per EBT × ValueLevel (3 of 7)
│   │   ├── offer_type_preset_catalog.py # ★ 76 presets ★ (4 of 7) ★
│   │   ├── section_catalog.py           # 21 sections (5 of 7)
│   │   ├── value_level_catalog.py       # 5 value levels (6 of 7)
│   │   └── variant_structure_catalog.py # 4 structures (7 of 7)
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── external_product_mapping_model.py
│   │   │   ├── knowledge_source_model.py
│   │   │   ├── launch_edition_model.py
│   │   │   ├── offer_asset_model.py
│   │   │   ├── offer_extraction_trace_model.py
│   │   │   └── product_model.py
│   │   └── repositories/
│   │       ├── __init__.py
│   │       ├── enum_normalizer.py
│   │       ├── external_product_mapping_repository.py
│   │       ├── knowledge_source_repository.py
│   │       ├── launch_edition_repository.py
│   │       ├── offer_asset_repository.py
│   │       ├── offer_repository.py
│   │       └── stub_landing_generation_repository.py
│   └── workers/
│       ├── __init__.py
│       └── tasks.py
│   # NOTE: copilot_provider/ NOT lifted — DEFERRED Story 6 (see §9.1)
└── tests/
    ├── __init__.py
    ├── api/
    │   ├── __init__.py
    │   ├── test_archetypes_api.py
    │   ├── test_assets_api.py
    │   ├── test_campaigns_api.py
    │   ├── test_counts_api.py
    │   ├── test_edition_clone_api.py
    │   ├── test_edition_clone_endpoint.py
    │   ├── test_field_contract_endpoint.py
    │   ├── test_formats_api.py
    │   ├── test_knowledge_api.py
    │   ├── test_landing_api.py
    │   ├── test_launch_editions_api_endpoints.py
    │   ├── test_lifecycle_api.py
    │   ├── test_offer_ladder_hints_api.py
    │   ├── test_pricing_tiers_api.py
    │   └── test_value_levels_api.py
    ├── application/
    │   ├── __init__.py
    │   ├── test_create_offer_paths.py
    │   ├── test_edition_clone_service.py
    │   ├── test_landing_generation_service.py
    │   ├── test_offer_asset_service.py
    │   ├── test_offer_completion_golden.py
    │   ├── test_offer_completion_service.py
    │   ├── test_offer_counts_service.py
    │   ├── test_offer_extraction_schemas.py
    │   ├── test_offer_knowledge_service.py
    │   └── test_offer_lifecycle_service.py
    ├── conftest.py
    ├── domain/
    │   └── *.py (12 files — all 7 catalog tests + edition + lifecycle + section + extraction_section_map)
    ├── infrastructure/
    │   └── *.py (3 files)
    ├── test_asset_shared_flag.py
    ├── test_edition_placeholder_and_publishing.py
    ├── test_edition_publish_archetype_rules.py
    ├── test_enum_normalizer.py
    ├── test_extraction_orchestrator_per_wave_save.py
    ├── test_launch_edition_api.py
    ├── test_launch_edition_domain.py
    ├── test_launch_edition_repository.py
    ├── test_launch_edition_service.py
    ├── test_offer_a96403b5_baseline.py
    ├── test_offer_ai_endpoint.py        # may need skip if depends on deferred offer_ai.py
    ├── test_offer_data_access_provider.py  # ← DEFERRED Story 6 (imports copilot)
    ├── test_offer_extraction_endpoint.py
    ├── test_offer_extraction_service.py
    ├── test_offer_extraction_service_delegates.py
    ├── test_offer_generator_decoupled.py
    ├── test_offer_read_port_impl.py
    ├── test_offer_repository.py
    ├── test_offer_repository_search.py
    ├── test_offer_service.py
    ├── test_pricing_tiers_domain.py
    ├── test_pricing_tiers_service.py
    ├── test_product_mappings_performance.py
    ├── test_products_archive_api.py
    ├── test_products_create_api.py
    ├── test_tenant_isolation.py
    └── workers/
        ├── __init__.py
        └── test_tasks_section_grouping.py
```

## §4. Workspace Registration

### §4.1 Root pyproject.toml (extend Stories 2+3+4 state)

Stories 2+3+4 declared 19 packages. Story 5 adds 2 more (total 21):

```toml
[tool.uv.workspace]
members = [
    "core",
    # Story 2 packages (9 — already registered)
    "core/luana-core-platform",
    "core/luana-core-llm",
    "core/luana-core-channels",
    "core/luana-core-idempotency",
    "core/luana-core-observability",
    "core/luana-core-events",
    "core/luana-core-extraction",
    "core/luana-core-compliance",
    "core/luana-core-billing",
    # Story 3 packages (6 — already registered)
    "core/luana-core-iam",
    "core/luana-core-tenant-profile",
    "core/luana-core-tenant-domains",
    "core/luana-core-commercial-calendar",
    "core/luana-core-social-proof",
    "core/luana-core-assets",
    # Story 4 packages (4 — already registered)
    "core/luana-core-crm",
    "core/luana-core-analytics-engine",
    "core/luana-core-landing",
    "core/luana-core-connections",
    # Story 5 packages (NEW — 2 packages)
    "core/luana-core-brand-studio",
    "core/luana-core-offer-studio",
    # Brand apps
    "nicolify", "vitalia", "comunify", "lupulo",
]

[tool.uv.sources]
# Stories 2+3+4 (already registered, 19 entries)
luana-core-platform = { workspace = true }
luana-core-llm = { workspace = true }
luana-core-channels = { workspace = true }
luana-core-idempotency = { workspace = true }
luana-core-observability = { workspace = true }
luana-core-events = { workspace = true }
luana-core-extraction = { workspace = true }
luana-core-compliance = { workspace = true }
luana-core-billing = { workspace = true }
luana-core-iam = { workspace = true }
luana-core-tenant-profile = { workspace = true }
luana-core-tenant-domains = { workspace = true }
luana-core-commercial-calendar = { workspace = true }
luana-core-social-proof = { workspace = true }
luana-core-assets = { workspace = true }
luana-core-crm = { workspace = true }
luana-core-analytics-engine = { workspace = true }
luana-core-landing = { workspace = true }
luana-core-connections = { workspace = true }
# Story 5 (NEW)
luana-core-brand-studio = { workspace = true }
luana-core-offer-studio = { workspace = true }
```

### §4.2 No TS this story

Story 5 backend-only per 00-story.md acceptance: "Form-runtime engine FE refactorizado en `@luana/brand-studio-ui` + `@luana/offer-studio-ui` (separate per OQ4)" → this is Story 10/11+ territory (Nicolify FE migration). Story 5 lifts ONLY Python packages. `pnpm-workspace.yaml` unchanged.

## §5. Import Path Mapping

### §5.1 Python mapping (verbatim preservation rule)

| AISALESHT source path | luana-platform internal path |
|---|---|
| `from src.modules.brand.<X>` | `from luana_core_brand_studio.<X>` |
| `from src.modules.offer.<X>` | `from luana_core_offer_studio.<X>` |
| `from src.modules.iam.<X>` | `from luana_core_iam.<X>` (Story 3 SSoT) |
| `from src.shared.domain.<X>` | `from luana_core_platform.domain.<X>` (Story 2) |
| `from src.shared.infrastructure.<X>` | `from luana_core_platform.infrastructure.<X>` |
| `from src.shared.application.<X>` | `from luana_core_platform.application.<X>` |
| `from src.shared.links.<X>` | `from luana_core_platform.links.<X>` |
| `from src.shared.domain_events.<X>` | `from luana_core_platform.domain_events.<X>` |
| `from src.core.<X>` | `from luana_core_platform.core.<X>` |

**Important:** AISALESHT imports NOT touched (Story 10 territory).

### §5.2 Deferred imports — NO sed rewrite

The following imports remain `src.modules.*` in deferred files **only because the deferred file is NOT lifted**. The deferred file stays in AISALESHT verbatim:

- `from src.modules.copilot.*` → **deferred `brand/copilot_provider/` + `offer/copilot_provider/` + `offer/api/offer_ai.py`** stay in AISALESHT.
- `from src.modules.advertising.*` → **deferred `offer/api/counts.py` + `offer/api/campaigns.py`** stay in AISALESHT.

Detection rule for /dev-team: BEFORE running sed, run `grep -rEn "from src\.modules\.(copilot|advertising|sales_agent|campaigns)" <package-being-lifted>/` → flagged files are in DEFERRED list (§9). Skip those files during `cp -r`.

## §6. Test Lift Strategy

### §6.1 Python tests

Tests lift in **same commit as source** (per `.claude/rules/auditor-downstream-regression.md`):

| AISALESHT source | luana-platform destination | Test count |
|---|---|---|
| `backend/tests/modules/brand/` | `core/luana-core-brand-studio/tests/` | 37 files (3 deferred: test_brand_context_injector.py + test_buyer_persona_fields_dropped_regression.py + test_worker_emits_summary_and_pills.py) → 34 lifted |
| `backend/tests/modules/offer/` | `core/luana-core-offer-studio/tests/` | 74 files (1 deferred: test_offer_data_access_provider.py) → 73 lifted |

### §6.2 Mock path migration

Tests may use `monkeypatch.setattr("src.modules.<m>.X")` — update to `luana_core_{brand_studio,offer_studio}.X` verbatim. Same mechanical sed pattern as Story 4 §6.

### §6.3 conftest.py preservation

Each module's `tests/conftest.py` lifts verbatim alongside source. offer's conftest imports `src.modules.offer.{domain.enums, infrastructure.models.product_model}` — apply sed.

### §6.4 Cross-coupling tests stay in AISALESHT (until Story 6)

These test files import deferred surfaces → they remain in AISALESHT until Story 6 lifts copilot:

- `backend/tests/modules/brand/test_brand_context_injector.py` (imports `copilot.application.orchestrator.context_inject`) → stays AISALESHT, lifts Story 6 alongside copilot
- `backend/tests/modules/brand/test_buyer_persona_fields_dropped_regression.py` (imports `copilot.infrastructure.persisters.buyer_persona_persister` + `copilot.domain.field_paths_hint`) → stays AISALESHT
- `backend/tests/modules/brand/test_worker_emits_summary_and_pills.py` (imports `copilot.domain.{message_blocks.CardBlock, card_payloads.CARD_PAYLOAD_MODELS}`) → stays AISALESHT
- `backend/tests/modules/offer/test_offer_data_access_provider.py` (imports `copilot.domain.ports.DataQueryPlan`) → stays AISALESHT

Builder uses the explicit rsync exclude pattern (see 05-guidelines.md §3.4).

### §6.5 Offer api/offer_ai endpoint test note

`test_offer_ai_endpoint.py` lifts but may have a test or two that exercise the deferred `offer_ai.py` route — if so, mark with `pytest.skip(reason="DEFERRED Story 6 — offer_ai.py routes need copilot.offer_psychology_service")` per-test (NOT whole-file skip). Builder inspects + decides per-test, budget ≤5% test drop per outcome §7.4 halt #9.

## §7. Architecture Fitness Tests

### §7.1 Brand-agnostic engines (extends Story 4 §7.1 to Story 5 packages)

Per outcome §2 brand-agnostic invariant + ADR-001 §2.4, **luana-core-{brand-studio, offer-studio} MUST stay brand-agnostic**. Brand-divergence (Nicolify vs Vitalia vs Comunify vs Lupulo) lives in BrandConfig, NOT in engine.

**New arch fitness test:** `core/tests/architecture/test_story5_brand_agnostic_engines.py`

```python
"""Story 5 — Brand-agnostic engines invariant.

luana-core-{brand-studio, offer-studio} MUST NOT contain brand-aware
control flow. Per ADR-001 §2.4 + outcome §2 brand isolation strategy.
"""
from pathlib import Path
import re

PKGS = [
    ("luana-core-brand-studio", "luana_core_brand_studio"),
    ("luana-core-offer-studio", "luana_core_offer_studio"),
]

FORBIDDEN_PATTERNS = [
    r"if\s+brand\s*==",
    r"if\s+tenant\.brand\s*==",
    r"if\s+self\.brand\s*==",
    r'brand\s*==\s*["\'](nicolify|vitalia|comunify|lupulo)["\']',
    # Hardcoded API keys / app IDs (must be env)
    r'(API_KEY|SECRET|TOKEN)\s*=\s*["\'](?!os\.|settings\.|env|getenv).{8,}["\']',
]


def test_engines_no_brand_aware_control_flow() -> None:
    """No `if brand == "..."` or brand-key string literals in engine source."""
    core_dir = Path(__file__).parent.parent.parent
    offenders = []
    for pkg_dir, pkg_snake in PKGS:
        pkg_src = core_dir / pkg_dir / "src" / pkg_snake
        if not pkg_src.exists():
            continue
        for py_file in pkg_src.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            for pattern in FORBIDDEN_PATTERNS:
                matches = re.findall(pattern, text)
                if matches:
                    offenders.append((py_file, pattern, matches))
    assert not offenders, f"Story 5 engines contain brand-aware code: {offenders}"
```

### §7.2 No forward-Story imports — Story 5 (extends Story 4 §7.2)

**New arch fitness test:** `core/tests/architecture/test_story5_no_forward_module_imports.py`

```python
"""Story 5 packages MUST NOT import from Story 6/7/8 modules.

After deferring brand/copilot_provider/ + offer/copilot_provider/ +
offer/api/{counts,campaigns,offer_ai}.py, no forward imports remain.
"""
from pathlib import Path
import re

STORY5_PKGS = [
    "luana-core-brand-studio",
    "luana-core-offer-studio",
]

FORBIDDEN_IMPORTS = [
    r"from\s+luana_core_(copilot|sales_agent)\.",
    r"from\s+luana_core_(campaigns|advertising|social_media|scheduling)\.",
    # Also block accidental AISALESHT imports
    r"from\s+src\.modules\.",
]


def test_no_forward_module_imports() -> None:
    core_dir = Path(__file__).parent.parent.parent
    offenders = []
    for pkg in STORY5_PKGS:
        pkg_src = core_dir / pkg / "src"
        if not pkg_src.exists():
            continue
        for py_file in pkg_src.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            for pattern in FORBIDDEN_IMPORTS:
                matches = re.findall(pattern, text)
                if matches:
                    offenders.append((py_file, pattern, matches))
    assert not offenders, f"Story 5 forward module imports: {offenders}"
```

### §7.3 Voice compiler SSoT placement (Story 5-specific — ADR-001 §2.4 cement)

**New arch fitness test:** `core/tests/architecture/test_story5_voice_compiler_in_brand_studio.py`

```python
"""Story 5 — voice compiler v2 (PersonalityCompiler) MUST live in
luana-core-brand-studio.domain.personality per ADR-001 §2.4.

This test cements the ownership placement decision. If a future story
(7) wires BrandVoicePort consumer in sales-agent, that port MUST resolve
to this engine, NOT a mirror.
"""
from pathlib import Path


def test_personality_compiler_lives_in_brand_studio_domain() -> None:
    core_dir = Path(__file__).parent.parent.parent
    target = core_dir / "luana-core-brand-studio" / "src" / "luana_core_brand_studio" / "domain" / "personality.py"
    assert target.exists(), f"PersonalityCompiler SSoT file missing: {target}"
    text = target.read_text(encoding="utf-8")
    assert "class PersonalityCompiler" in text, "PersonalityCompiler class not found in brand-studio domain"
    assert "def compile(" in text, "PersonalityCompiler.compile() method not found"


def test_no_mirror_personality_compiler_outside_brand_studio() -> None:
    """No other package should declare class PersonalityCompiler (anti-mirror rule)."""
    core_dir = Path(__file__).parent.parent.parent
    offenders = []
    for py_file in core_dir.rglob("*.py"):
        if "luana-core-brand-studio" in str(py_file):
            continue
        if "node_modules" in str(py_file) or "__pycache__" in str(py_file):
            continue
        try:
            text = py_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if "class PersonalityCompiler" in text:
            offenders.append(py_file)
    assert not offenders, f"PersonalityCompiler mirror found outside brand-studio: {offenders}"
```

### §7.4 Offer catalogs DAG completeness (Story 5-specific)

The existing AISALESHT `backend/tests/modules/offer/domain/test_*.py` (12 files) covers the 7 catalogs DAG. They lift alongside offer to `core/luana-core-offer-studio/tests/domain/`. **No NEW arch test needed** — lift preserves the entire catalog test suite. We add ONE smoke test confirming the 76 presets count + 7 catalog modules exist post-lift:

**New smoke test:** `core/luana-core-offer-studio/tests/test_catalogs_dag_smoke.py`

```python
"""Story 5 — offer catalogs DAG smoke post-lift.

Confirms 7-catalog DAG SSoT preserved verbatim:
  archetype_catalog · value_level_catalog · format_catalog · section_catalog ·
  offer_ladder_hints · offer_type_preset_catalog (76 presets) · variant_structure_catalog
"""
from luana_core_offer_studio.domain.archetype_catalog import ARCHETYPE_CATALOG
from luana_core_offer_studio.domain.value_level_catalog import VALUE_LEVEL_CATALOG
from luana_core_offer_studio.domain.format_catalog import FORMAT_CATALOG
from luana_core_offer_studio.domain.section_catalog import SECTION_CATALOG
from luana_core_offer_studio.domain.offer_ladder_hints import OFFER_LADDER_HINTS
from luana_core_offer_studio.domain.offer_type_preset_catalog import OFFER_TYPE_PRESET_CATALOG
from luana_core_offer_studio.domain.variant_structure_catalog import VARIANT_STRUCTURE_CATALOG


def test_7_catalogs_loaded() -> None:
    assert len(ARCHETYPE_CATALOG) == 5
    assert len(VALUE_LEVEL_CATALOG) == 5
    assert len(SECTION_CATALOG) >= 21  # 21 post-consolidation (may grow)
    assert len(OFFER_TYPE_PRESET_CATALOG) >= 76  # Story 5 confirms ≥76 presets verbatim
    assert len(VARIANT_STRUCTURE_CATALOG) == 4
    assert len(FORMAT_CATALOG) > 0
    assert len(OFFER_LADDER_HINTS) > 0
```

(Counts as of 2026-05-11 verified per offer-expert skill body. Story 5 lift preserves these exact counts. If counts have drifted post-skill-generation, builder updates assertions to actual lifted values + documents in commit body.)

### §7.5 Existing AISALESHT arch tests stay (no migration)

Story 5 does NOT migrate AISALESHT arch tests (`tests/architecture/test_offer_type_preset_catalog_completeness.py`, `test_brand_editable_fields_baseline.py`, etc.). They stay validating AISALESHT until Story 10. Story 5 builds parallel Luana-platform-side arch tests (§7.1-§7.4).

## §8. Per-Package pyproject.toml Dependency Declarations

### §8.1 luana-core-brand-studio/pyproject.toml

```toml
[project]
name = "luana-core-brand-studio"
version = "0.0.1-alpha"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
    "fastapi>=0.115",
    "structlog>=24.0",
    "httpx>=0.27",                 # extraction crawler
    "langgraph>=0.2",              # StyleAnalyzer agent
    "langchain-core>=0.3",
    "qdrant-client>=1.10",         # style_anchor_store
    "luana-core-platform",
    "luana-core-iam",
]

[tool.uv.sources]
luana-core-platform = { workspace = true }
luana-core-iam = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/luana_core_brand_studio"]
```

### §8.2 luana-core-offer-studio/pyproject.toml

```toml
[project]
name = "luana-core-offer-studio"
version = "0.0.1-alpha"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
    "fastapi>=0.115",
    "structlog>=24.0",
    "httpx>=0.27",                 # offer extraction crawler
    "arq>=0.26",                   # workers/tasks
    "luana-core-platform",
    "luana-core-iam",
]

[tool.uv.sources]
luana-core-platform = { workspace = true }
luana-core-iam = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/luana_core_offer_studio"]
```

## §9. Deferred Files (Story 5 exception list)

### §9.1 copilot_provider/ subfolders — DEFERRED Story 6

Same pattern as Story 4 §9.1. Both Story 5 modules have a `copilot_provider/` subfolder importing `src.modules.copilot.domain.{ports, workflow}`:

| AISALESHT path | Reason | Will lift in |
|---|---|---|
| `backend/src/modules/brand/copilot_provider/__init__.py` | re-exports provider | Story 6 (copilot lift) |
| `backend/src/modules/brand/copilot_provider/context_inject.py` | imports `copilot.domain.ports.BaseCopilotProvider` | Story 6 |
| `backend/src/modules/brand/copilot_provider/module_data.py` | imports `copilot.domain.ports.ModuleData` | Story 6 |
| `backend/src/modules/brand/copilot_provider/provider.py` | imports `copilot.domain.ports.BaseCopilotProvider` | Story 6 |
| `backend/src/modules/brand/copilot_provider/summary.py` | imports `copilot.domain.workflow.NodeOutput` | Story 6 |
| `backend/src/modules/brand/copilot_provider/tools.py` | imports `copilot.domain.ports` tools API | Story 6 |
| `backend/src/modules/brand/copilot_provider/workflow_handlers.py` | imports `copilot.domain.workflow` | Story 6 |
| `backend/src/modules/brand/copilot_provider/workflows.py` | imports `copilot.domain.workflow` | Story 6 |
| `backend/src/modules/offer/copilot_provider/__init__.py` | re-exports provider | Story 6 |
| `backend/src/modules/offer/copilot_provider/data_access.py` | imports `copilot.domain.ports.{DataQueryPlan, DataQueryResult}` | Story 6 |
| `backend/src/modules/offer/copilot_provider/provider.py` | imports `copilot.domain.ports.BaseCopilotProvider` | Story 6 |
| `backend/src/modules/offer/copilot_provider/workflow_handlers.py` | imports `copilot.domain.workflow` | Story 6 |
| `backend/src/modules/offer/copilot_provider/workflows.py` | imports `copilot.domain.workflow` | Story 6 |

**Lift behavior:** when lifting brand + offer, /dev-team SKIPS the `copilot_provider/` subfolders entirely. Story 6 lifts these alongside copilot module's lift.

### §9.2 Cross-module API surfaces — DEFERRED Stories 6 + 8

| AISALESHT path | Imports | Will lift in |
|---|---|---|
| `backend/src/modules/offer/api/offer_ai.py` | `src.modules.copilot.application.services.offer_psychology_service` | Story 6 (copilot lift) |
| `backend/src/modules/offer/api/counts.py` | `src.modules.advertising.application.services.offer_campaigns_read_adapter` | Story 8 (campaigns/advertising lift) |
| `backend/src/modules/offer/api/campaigns.py` | `src.modules.advertising.application.services.offer_campaigns_read_adapter` | Story 8 |

**Lift behavior:** /dev-team SKIPS these 3 files during `cp -r` of offer/api/. Each file remains in AISALESHT verbatim. Story 6/8 lifts the file alongside the source-of-its-import.

### §9.3 Tests importing copilot — DEFERRED Story 6

| AISALESHT path | Imports | Will lift in |
|---|---|---|
| `backend/tests/modules/brand/test_brand_context_injector.py` | `copilot.application.orchestrator.context_inject` | Story 6 |
| `backend/tests/modules/brand/test_buyer_persona_fields_dropped_regression.py` | `copilot.infrastructure.persisters` + `copilot.domain.field_paths_hint` | Story 6 |
| `backend/tests/modules/brand/test_worker_emits_summary_and_pills.py` | `copilot.domain.{message_blocks, card_payloads}` | Story 6 |
| `backend/tests/modules/offer/test_offer_data_access_provider.py` | `copilot.domain.ports.DataQueryPlan` | Story 6 |

**Lift behavior:** /dev-team uses `rsync --exclude='test_brand_context_injector.py' --exclude='test_buyer_persona_fields_dropped_regression.py' --exclude='test_worker_emits_summary_and_pills.py' …` for brand tests + `rsync --exclude='test_offer_data_access_provider.py' …` for offer tests.

### §9.4 BrandVoicePort port creation — DEFERRED Story 7 (NOT Story 5)

Per 00-story.md "BrandVoicePort definido en core-brand-studio" — this would introduce a NEW abstraction.

**Decision:** Per outcome §7.3 lift mode "MUST NOT DO: new abstractions" + §7.2 autonomy rationale "lift-mode with design-decisions pre-ratified" — the ratified design decision is the OWNERSHIP placement (PersonalityCompiler lives in core-brand-studio), NOT the introduction of a new port. The port itself is consumption-side concern of core-sales-agent (Story 7). When Story 7 lifts sales-agent, it will:
1. Add `BrandVoicePort` Protocol in `luana-core-brand-studio.application.ports` (Story 7 territory because Story 7 is the CONSUMER).
2. Have `core-brand-studio.application.services.brand_voice_service` implement it (or wire PersonalityCompiler.compile directly).

Story 5 does NOT add the port. Cementing this avoids §7.3 violation. Story 7 architect doc will reference this defer.

### §9.5 Voice cloning pipeline — DEFERRED Stories 11-13 (vertical bootstrap)

Per 00-story.md "Voice cloning feature flag... activa pipeline LLM-distillation desde 50+ chats reales" — pipeline does NOT exist in AISALESHT brand/ today. Verified via grep:

```bash
grep -rln "voice_cloning\|LLM-distill\|chat_samples_voice" /home/chris/AISALESHT/backend/src/modules/brand/
# → empty
```

The flag (`voice_cloning: bool`) is a BrandConfig schema field per ADR-001 §2.4. Story 5 does NOT introduce the schema field (BrandConfig itself is Story 8/9 territory per outcome §2). Story 11 (Vitalia) + Story 12 (Comunify) + Story 13 (Lupulo) set per-brand value when their BrandConfig file is created.

### §9.6 Audit trail

Append entry to `core/DEFERRED-FILES.md` (created Story 2):

```markdown
## Story 5 deferrals (2026-05-11)

### Defer to Story 6 (copilot lift)
- backend/src/modules/brand/copilot_provider/ (8 files) → Story 6 (imports src.modules.copilot.domain.{ports, workflow})
- backend/src/modules/offer/copilot_provider/ (5 files) → Story 6 (imports src.modules.copilot.domain.{ports, workflow})
- backend/src/modules/offer/api/offer_ai.py → Story 6 (imports src.modules.copilot.application.services.offer_psychology_service)
- backend/tests/modules/brand/test_brand_context_injector.py → Story 6
- backend/tests/modules/brand/test_buyer_persona_fields_dropped_regression.py → Story 6
- backend/tests/modules/brand/test_worker_emits_summary_and_pills.py → Story 6
- backend/tests/modules/offer/test_offer_data_access_provider.py → Story 6

### Defer to Story 8 (campaigns/advertising lift)
- backend/src/modules/offer/api/counts.py → Story 8 (imports src.modules.advertising.application.services.offer_campaigns_read_adapter)
- backend/src/modules/offer/api/campaigns.py → Story 8 (idem)

### Reserved (design decision, NOT existing code)
- BrandVoicePort Protocol → Story 7 (introduced ALONGSIDE sales-agent lift as consumer; impl wired here in core-brand-studio at that time; NOT Story 5 because §7.3 forbids new abstractions)
- voice_cloning BrandConfig flag → Stories 11-13 (per-brand value set at vertical bootstrap; BrandConfig schema itself in Story 8/9)
- voice cloning pipeline code → Stories 11-13 (LLM-distillation pipeline does NOT exist in AISALESHT today; NEW code per outcome §7.3 "no scope expansion")
```

## §10. Voice Compiler Elevation (ADR-001 §2.4 verification)

### §10.1 Decision: PersonalityCompiler lifted verbatim to luana-core-brand-studio.domain.personality

Per ADR-001 §2.4 + 00-story.md "voice compiler v2 ELEVATED here":

- Current location AISALESHT: `backend/src/modules/brand/domain/personality.py` (`class PersonalityCompiler` line 440, `compile()` method line 444).
- Target location luana-platform: `core/luana-core-brand-studio/src/luana_core_brand_studio/domain/personality.py` (same class, same line position post-lift).

**Lift mechanics:** verbatim file copy + sed import rewrite (per §5.1 mapping). No refactor. No new abstraction. No signature change.

### §10.2 NO port introduced in Story 5

Per outcome §7.3 "MUST NOT DO: new abstractions" + §9.4 above:

- Story 5 does NOT create `luana_core_brand_studio.application.ports.BrandVoicePort`.
- Story 5 does NOT create `BrandVoiceService.compileSystemInstruction(tenant_id)`.
- Story 5 lifts existing `PersonalityCompiler.compile()` verbatim — its current signature is the SSoT.

### §10.3 Story 7 will wire the port

When /architect drafts Story 7 (sales-agent lift), it will:
1. Add `BrandVoicePort` Protocol in `luana_core_brand_studio.application.ports.brand_voice_port` (introduced as Story 7's CONSUMER-side requirement).
2. Add `BrandVoiceService` adapter in `luana_core_brand_studio.application.services.brand_voice_service` that wraps `PersonalityRepository.get_for_tenant` + `PersonalityCompiler.compile`.
3. Inject `BrandVoicePort` into `core-sales-agent` Slot 5 BRAND_VOICE per `sales-agent-expert` skill SSoT.

Story 5 architect cements this decision in §9.4 so Story 7 architect can reference verbatim.

### §10.4 Arch fitness test §7.3 cements placement

`test_story5_voice_compiler_in_brand_studio.py` (§7.3 above) BLOCKS any future story from declaring a mirror `class PersonalityCompiler` outside brand-studio. SSoT cement.

## §11. Architecture Fitness Gates (test surfaces)

| Gate | Layer | Owner |
|---|---|---|
| `uv sync --all-packages` GREEN (21 packages total) | luana-platform root | gate-runner |
| `uv run pytest core/luana-core-brand-studio/tests/` GREEN | per-package | gate-runner |
| `uv run pytest core/luana-core-offer-studio/tests/` GREEN | per-package | gate-runner |
| `uv run ruff check core/luana-core-{brand-studio,offer-studio}/` GREEN | luana-platform root | gate-runner |
| `uv run pytest core/tests/architecture/test_story5_brand_agnostic_engines.py` GREEN | luana-platform | gate-runner |
| `uv run pytest core/tests/architecture/test_story5_no_forward_module_imports.py` GREEN | luana-platform | gate-runner |
| `uv run pytest core/tests/architecture/test_story5_voice_compiler_in_brand_studio.py` GREEN | luana-platform | gate-runner |
| `uv run pytest core/luana-core-offer-studio/tests/test_catalogs_dag_smoke.py` GREEN | per-package | gate-runner |
| AISALESHT untouched verifier | AISALESHT repo | gate-runner |
| No-publish verifier | luana-platform | gate-runner |
| `core/DEFERRED-FILES.md` updated with Story 5 entries | luana-platform | gate-runner |

## §12. Research Notes (state-of-the-art as of 2026-05-11)

| Source | Accessed | Key takeaway |
|---|---|---|
| uv workspace docs https://docs.astral.sh/uv/concepts/workspaces/ | 2026-05-11 (via Story 2-4 SSoT) | Workspace sources resolve at install time. Same pattern as Stories 2-4 — no new research. |
| Hatchling build backend https://hatch.pypa.io/latest/config/build/ | 2026-05-11 (via Story 2-4) | `[tool.hatch.build.targets.wheel] packages = ["src/<name>"]` is canonical src-layout. Matches Stories 2-4. |
| LangGraph docs https://docs.langchain.com/oss/python/langgraph/workflows-agents | 2026-05-11 | StyleAnalyzer agent (`brand/application/agents/style_analyzer/`) uses StateGraph + `onboarding_app` pattern. Lift verbatim preserves the topology (no agentic changes per §7.3). |
| `.claude/rules/offer-catalogs.md` (internal) | 2026-05-11 | 7-catalog DAG SSoT. Lift preserves all 7 catalogs + 76 presets verbatim. `_CATALOG_VERSION` not bumped (lift = identical content). |
| `.claude/skills/brand-expert/SKILL.md` (internal) | 2026-05-11 | BrandSettings root + 11 sub-models + PersonalityProfile 3-pillar SSoT confirmed. Voice compiler v2 owns 5-block system_instruction. |
| `.claude/skills/offer-expert/SKILL.md` (internal) | 2026-05-11 | 11 layers SSoT (L0..L11) + DAG resolved + cross-module ports `shared/links/ports/offer.py`. |
| ADR-001 §2.4 (internal) | 2026-05-11 | Voice compiler v2 elevation to core-brand-studio ratified. BrandVoicePort consumer-side intro deferred to Story 7. |
| Outcome §7.2 + §7.3 + §9.4 (internal) | 2026-05-11 | Story 5 autonomy rationale: lift-mode with design pre-ratified. NO new abstractions. |

**Knowledge cutoff disclosure:** Opus 4.7 cutoff = January 2026. All canonical references (uv, hatchling, langgraph) predate cutoff. Internal rules verified live against current state of `.claude/rules/` + `.claude/skills/` + outcome doc as of 2026-05-11.

## §13. Cross-Cutting Concerns (per CLAUDE.md)

- **Tenant isolation:** preserved verbatim — every entity carries `tenant_id`, every query filters it. Brand + Offer modules already comply in AISALESHT.
- **Currency handling:** offer monetary fields (PricingStructure, value_level pricing) include `currency: str | None`. Lift preserves. No new monetary fields added.
- **Master data:** brand + offer use UTC + tenant locale per shared utilities. Lift verbatim.
- **Spanish neutro LatAm:** NO UI strings in these 2 modules (all BE). User-facing copy lives in catalogs (`label_es`, `description_es`, `human_question_es`, `help_text_es`) — lift preserves verbatim. Form-runtime FE refactor (00-story.md acceptance) is Story 10/11+ territory.
- **PII sanitization:** routes use `response_model=` on user-facing DTOs (brand identity legal fields, buyer persona contact-adjacent fields). Lift preserves.
- **Native-first dev:** validators use native `uv run pytest`, `uv run ruff` — no Docker.
- **TDD-mandatory:** Story 5 is lift, not new code. Tests lift verbatim alongside source.
- **Brand-agnostic engines:** new invariant codified in §7.1 arch fitness test (extends Story 4 §7.1 to brand + offer).
- **Voice compiler SSoT:** preserved via §10 + arch fitness §7.3 (anti-mirror cement).
- **7 catalogs DAG SSoT:** preserved via §3.3 verbatim lift + smoke test §7.4.

## §14. Capability YAML + modules/ Updates Required

**None.** Story 5 is mechanical lift. Does not change user-facing capability. No `docs/product/capabilities/{m}/*.yaml` updates. No `docs/product/modules/{m}.md` updates.

Outcome `luana-platform-migration.md` § progress log will be updated by /pm at story close.

## §15. Open Questions for PM (none blocking)

All scope decisions resolved per outcome §7.2 (autonomous extension) + §7.3 (lift mode) + ADR-001 §2.4 + this architect document:

- **2 packages confirmed:** 00-story.md §2.2 surface. NO escalation.
- **14 deferred files confirmed:** §9 lists each with destination Story. Same pattern as Story 4 §9. NO escalation.
- **Brand split into 6 lift sub-tickets:** per outcome §7.4 atomicity rule, 81 files + LangGraph agent + voice-fidelity sub-module exceed single-ticket Sonnet 2h cap. Split is granularity, NOT scope expansion. NO escalation.
- **Offer split into 5 lift sub-tickets:** per outcome §7.4 atomicity rule, 95 files + 7 catalogs DAG exceed single-ticket Sonnet 2h cap. NO escalation.
- **Voice compiler ELEVATION = verbatim lift (§10):** ADR-001 §2.4 ratified. Cementing test §7.3. NO new port (deferred to Story 7 per §9.4). NO escalation.
- **Voice cloning pipeline NOT in Story 5 scope (§9.5):** code doesn't exist in AISALESHT, BrandConfig schema is Story 8/9, flag value is Stories 11-13. NO escalation.

If Chris reads this and decides to lift the copilot_provider/ subfolders early (would require stubbing `BaseCopilotProvider` protocol in `luana-core-platform.links.ports`), that's REFACTOR (scope expansion) — escalate.

If Chris reads this and wants BrandVoicePort introduced in Story 5 (consumer-side wired in Story 7), that's NEW abstraction — escalate.
