# Gap report — Group A (brand, offer, landing, assets) — 2026-05-04

> Auto-generado por agente mapper durante migración SDD Level 3.
> Cada gap representa un área que necesita atención (test missing, coverage bajo, eval missing, etc).
> Agente: module-mapper Group A — paths verificados contra repo en `last_audit: 2026-05-04`.

## Resumen

| Module | Capabilities mapped | Stories mapped | E2E coverage | Unit/Integration coverage (BE) | Status |
|---|---|---|---|---|---|
| brand | 5 | 6 | parcial (smoke only) | sólido | needs e2e regression |
| offer | 5 | 9 | parcial (smoke + 1 regression) | sólido | needs e2e regression + cohort archetype tests |
| landing | 3 | 5 | parcial (visual + public) | sólido | needs xss/load tests |
| assets | 4 | 4 | sin coverage e2e | sólido | needs flyer pipeline + voice fidelity grader |
| **Total** | **17** | **24** | — | — | — |

## Gaps por módulo

### brand

#### brand-identity-edit (story)
- E2E test missing — solo `brand-crud.smoke.spec.ts` cubre superficie genérica. Falta regression dedicado.
- State_check graders apuntan a tests inexistentes (`null` en path)
- Domain event BrandSectionUpdated emitted via outbox: feature live (PR-6 Sub-D), pero no hay test E2E que valide consumer downstream (sales_agent cache invalidation)

#### brand-visuals-edit (story)
- E2E test missing
- Upload de logos a R2: state_check para verificar persistencia en R2 no implementado
- Sin coverage para oversized files / invalid MIME

#### brand-personality-edit (story)
- E2E `personality.smoke.spec.ts` solo valida render — no flow completo (edit → save → sales_agent picks up)
- Voice fidelity grader (`voice_fidelity/grader.py`) tiene tests pero no en CI gate de PRs que tocan personality
- DR-7 abierto: 7 callsites brand sin BudgetGuard wrap activo (`tests/architecture/test_budget_guard_pre_llm_call.py KNOWN_UNGUARDED`)

#### brand-style-clone-from-chat (agentic-story)
- Sin eval suite dedicada (no rubrics, no personas, no pass^k tracking)
- LLM cost no surface a user después del cloning
- No personas ni rubrics implementados — `eval_suite_path: null`

#### brand-buyer-persona-create (story)
- E2E `buyer-personas.smoke.spec.ts` cubre solo render inicial — falta regression de create/edit completo
- Test regression `test_buyer_persona_fields_dropped_regression.py` evidencia historial de bugs, coverage para cross-section persistence sigue thin

#### brand-extract-from-website (service-story)
- No hay E2E del flujo "subo URL → veo brand poblada en UI"
- Worker `brand_summary_regen` usa LLM sin BudgetGuard activo (DR-7)
- Cost monitoring del pipeline (tokens/USD por extraction) no surface en UI ni en alerting

#### brand-credentials (capability — partial coverage)
- Solo `brand-team-manage` tiene story YAML; `brand-testimonials-manage` y `brand-authority-vault-manage` están planned pero sin YAML escrito
- Upload de fotos a R2 sin state_check graders
- Copilot operability: bajo — no hay tools para agregar testimonio/credencial conversacionalmente

### offer

#### offer-ladder-view (story)
- E2E `offer-list.spec.ts` cubre listado pero no flujos completos del ladder
- Empty state y many-offers performance sin coverage explícito

#### offer-create-from-ladder (story)
- E2E smoke `offer-crud.smoke.spec.ts` cubre create básico — falta regression con preset selection completo
- State_check de DB post-create no implementado en grader

#### offer-blueprint-edit (story)
- Sin E2E regression dedicado
- Conditional questions per preset: no test que verifique cambio de preset surface/oculta secciones esperadas
- Cross-module integration LOCATION→scheduling y INSTRUCTORS→brand sin contract test E2E

#### offer-pricing-tiers-edit (story)
- Multi-currency: arch test enforces DTO `currency` field, pero no hay E2E que valide FE display correcto
- Test backend sólido (`test_pricing_tiers_service.py`)

#### offer-variants-polymorphic (story)
- E2E regression existe (`offer-variants-polymorphic.regression.spec.ts`)
- Variant invalid for archetype: sin contract test exhaustivo per archetype
- Variant deletion cascade (con editions activas) sin test

#### offer-extract-from-document (service-story)
- No hay E2E del flujo "subo PDF → veo oferta poblada con archetype correcto"
- Cost monitoring del pipeline no surface
- Endpoint scraping desde URL para offer existe parcial pero sin stable test

#### offer-edition-create-from-clone (story)
- Test backend `test_clone_dry_run.py` y `test_edition_placeholder_and_publishing.py` sólidos
- Sin E2E para flow create→edit→publish→archive

#### offer-edition-publish (service-story)
- Test `test_edition_publish_archetype_rules.py` cubre validation pero no exhaustivo per archetype variation
- Sin saga/transactional test de "edition publish + landing publish atomicity"

#### offer-preset-pick-on-wizard (story)
- Arch test enforces invariante "agregar preset nuevo no rompe wizard", pero no hay e2e
- Hardcoded preset metadata leak detection corre solo en arch tests
- BE→FE sync: catalog version mismatch sin test

### landing

#### landing-create-from-offer (service-story)
- Idempotent retry: contract test no implementado
- Cross-tenant event leak: sin test que valide handler discard de event mismatch

#### landing-section-edit (story)
- Sin E2E regression
- Tokenizer test backend existe (`test_landing_tokenizer.py`) pero sin fuzz/XSS coverage
- Edit while published (race condition): sin test

#### landing-publish (service-story)
- Test `test_public_edition_api.py` sólido para publish básico
- Sin contract test para publish without slug + idempotent republish edge cases

#### landing-slug-edit (story)
- Sin E2E test
- Duplicate slug 409: sin contract test exhaustivo
- Slug change while published: redirect strategy no implementada (TODO en story)

#### landing-public-render (service-story)
- E2E `landing.public.spec.ts` cubre render básico
- XSS via token injection: sin test específico
- Performance bajo carga (1000 GETs/min): sin load test
- Cross-tenant slug collision via custom domain: sin test

### assets

#### assets-generate-copy-for-channel (service-story)
- Test backend `test_assets_service.py` cubre service pero no eval LLM con voice fidelity
- Voice fidelity grader no integrado a tests del módulo
- Sin eval suite dedicada al module assets — copies generadas no se evalúan post-generation

#### assets-upload (service-story)
- Test backend `test_asset_repository.py` + `test_detect_type.py` sólidos
- Idempotent upload (mismo hash) sin test
- Cuotas/storage limits per tenant no implementado (TODO general del módulo)

#### assets-promote (service-story)
- Test `test_promote_endpoint.py` cubre happy path + cross-tenant
- Sin test idempotent re-promote (timestamp preservation)

#### assets-offer-gallery-list (service-story)
- Test backend `test_gallery_repository.py` sólido
- Sin test de performance bajo gallery con >100 items
- Filter por canal (Instagram only) no implementado

#### assets-flyer-image-gen (capability — placeholder)
- **Estado: in-progress** — sin story YAML
- Image gen pipeline no tiene provider production-ready definido
- Brochures = placeholder (no implementado)
- Sin contract tests dedicados al pipeline de generación visual

## Priorización sugerida (top 5)

1. **brand-style-clone-from-chat** — eval suite missing en agentic story que ya está live. Riesgo: drift de voice fidelity sin medición. Acción: escribir rubrics + personas + integrar a CI.

2. **landing-public-render xss-via-token-injection** — gap de seguridad en endpoint público. Acción: agregar fuzz test al tokenizer + e2e con script tags.

3. **brand DR-7 BudgetGuard wiring** — 7 callsites brand emiten LLM sin guard. Riesgo: cost runaway. Acción: cerrar S4 sub-D-2 con FastAPI provider + ARQ worker startup DI.

4. **offer-blueprint-edit conditional questions per preset** — regresión histórica común (cambio preset rompe sections). Acción: e2e que itere todos los presets y valide section invariants.

5. **assets voice fidelity** — copies generated no medidos contra voz tenant. Riesgo: assets fuera de marca a escala. Acción: integrar voice_fidelity grader a `test_assets_service.py`.

## Notas de migración

- **Stories pendientes de YAML**: `brand-testimonials-manage`, `brand-authority-vault-manage` (referenciadas en capability brand-credentials pero sin file aún). Próxima iteración del mapper o /po al refinar.
- **Capability flyer-image-gen**: in-progress — sin story; documentado para no perder rastro.
- **Cross-module event flow** (BrandSectionUpdated → sales_agent cache invalidation) no tiene E2E verifying contract — pattern aplicable a todos los modules.
- Los archivos YAML producidos por este mapper son SSoT atómicos; cualquier modificación de capability/story debe pasar por `/po` para ratificar y `/pm` para mergear.
