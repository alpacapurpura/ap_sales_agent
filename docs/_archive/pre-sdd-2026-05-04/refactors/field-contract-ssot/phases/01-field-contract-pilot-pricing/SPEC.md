# Fase 01 — FieldContract pilot (pricing)

## Objetivo

Introducir `FieldContract` BE + migrar sección **pricing** al patrón. Cerrar
Capa A pricing: los 3 fields huérfanos (`tax_included`,
`installments_available`, `accepted_payment_providers`) pasan a persistir y
propagarse downstream (sales-agent additive). Allowlist shrink-only:
`KNOWN_UNRESOLVED_PATHS.size` baja de 59 a 56.

## Scope

**Dentro**:
- Migration 062 idempotente (raw SQL `IF NOT EXISTS`) sobre `products`:
  `tax_included bool`, `installments_available text`,
  `accepted_payment_providers jsonb NOT NULL DEFAULT '[]'`.
- Pydantic `Offer` + `OfferPricingUpdate` + `ProductModel` extendidos con
  los 3 fields. Repositorio save/load mapea columnas.
- `backend/src/modules/offer/domain/field_contract.py`: `FieldContract`
  dataclass frozen + `PRICING_FIELD_CONTRACTS` tuple con entries de pricing.
- `GET /api/v1/offer/field-contract` versionado (versión en el payload).
- Nuevo extractor `_extract_pricing` en `OfferExtractionService` +
  template jinja2 `offer_extract_pricing.j2` + `PricingWaveOutput` en
  `extraction_schemas.py`. Orchestrator corre pricing en W2 junto a
  psychology/value_stack/closing.
- Codegen `scripts/generate_offer_field_paths.py` regenera
  `tests/architecture/fixtures/offer_field_paths.json` (123 → 126 paths).
- FE `pricing.schema.ts`: tipo `path` contra generated union
  `OfferFieldPath` (codegen TS). TSC error si se inventa.
- Arch test FE allowlist shrink 59 → 56 (removidas 3 entradas Fase 01).
  `ALLOWLIST_CAP` update + `toBeLessThanOrEqual(59)` baja a 56.
- Sales-agent prompt template `agent_identity.j2`: bloque pricing
  additive (condicional). Campo vacío → sin cambios en render.
- Golden fixture regenerada: baseline suma 3 keys con valores actuales
  (null / null / []). Test round-trip valida persistencia PATCH→GET.

**Fuera** (diferido):
- Otras secciones (Fase 02).
- `OFFER_FIELDS_BY_FE_SECTION` cleanup (Fase 04).
- Refactor `PricingStructure` VO.
- Landing builder consume de nuevos fields. Legacy consume `pricing`
  JSONB dict, no top-level offer fields → alineación se hace en Fase 05
  (downstream unify). INVARIANT 8 se preserva: offer sin data nueva =
  landing output byte-identical.
- Completion service rules para pricing (Fase 05).

## Decisiones arquitectónicas (ver DECISIONS.md)

- **ADR-008**: pricing extraction es wave W2 concurrente con psychology
  / value_stack / closing. Razón: LLM-inferible solo `tax_included` +
  `installments_available` (texto sobre precios). `accepted_payment_providers`
  NO se extrae (UI-config via Connections). Wave dedicada simplifica
  merge, separa responsabilidad de closing (garantías + urgencia).
- **ADR-009**: `accepted_payment_providers` persiste como `list[str]`
  (no enum) en domain/DTO. Validación runtime opcional contra catálogo
  en `shared/domain/`. Razón: `PaymentProvider` enum vive en
  `sales_agent.domain.enrollment`, importar cross-module viola DDD
  (INVARIANT 15, rule backend-ddd.md). Shrink path: Fase 02+ mueve enum
  a `shared/domain/` + offer usa vía port. Para Fase 01 evitamos la
  migración cross-module (scope creep).

## Sub-steps (commits atómicos ordenados)

| # | Commit (conventional) | Archivos |
|---|---|---|
| A | `docs(refactor-field-contract): open fase 01 — SPEC + ACCEPTANCE + ADRs` | `docs/refactors/field-contract-ssot/phases/01-*/SPEC.md`, `ACCEPTANCE.md`, `../../DECISIONS.md` (ADR-008, ADR-009), `STATUS.md` |
| B | `feat(offer): migration 062 pricing latam columns` | `backend/alembic/versions/062_offer_pricing_latam.py` |
| C | `feat(offer): domain + DTO + model pricing latam` | `backend/src/modules/offer/domain/offer.py`, `backend/src/modules/offer/infrastructure/models/product_model.py`, `backend/src/modules/offer/infrastructure/repositories/offer_repository.py` (mapping) |
| D | `feat(offer): FieldContract registry + /field-contract endpoint` | `backend/src/modules/offer/domain/field_contract.py`, `backend/src/modules/offer/api/offer_field_contract.py`, `backend/src/main.py` (mount router) |
| E | `feat(offer): extraction wave pricing + prompt + schema` | `backend/src/modules/copilot/infrastructure/prompts/templates/offer_extract_pricing.j2`, `backend/src/modules/offer/application/offer_extraction_service.py`, `backend/src/modules/offer/application/offer_extraction_orchestrator.py`, `backend/src/modules/offer/application/extraction_schemas.py` |
| F | `chore(offer): regen field-paths JSON + shrink FE allowlist` | `backend/tests/architecture/fixtures/offer_field_paths.json`, `frontend/src/__tests__/architecture/test-fe-schema-paths-resolve.test.ts` |
| G | `feat(offer-studio): type pricing schema paths against codegen` | `frontend/src/features/offer-studio/api/__generated__/offer-field-paths.ts` (new codegen TS), `frontend/src/features/offer-studio/schemas/pricing.schema.ts`, codegen script update |
| H | `feat(sales-agent): additive pricing block in agent identity prompt` | `backend/src/modules/sales_agent/infrastructure/prompts/templates/agent_identity.j2`, `backend/src/modules/sales_agent/application/knowledge_builder.py` (expose fields) |
| I | `test(offer): golden fixture roundtrip pricing latam` | `backend/tests/modules/offer/fixtures/offer_a96403b5_baseline.json`, `backend/tests/modules/offer/test_offer_a96403b5_baseline.py` (+ 3 field assertions), `backend/scripts/capture_offer_a96403b5_baseline.py` (if needed) |
| J | `chore(refactor-field-contract): close fase 01` | `docs/refactors/field-contract-ssot/STATE.md`, `LEARNINGS.md`, `STATUS.md`, Fase 02 STATUS new |

## Duración estimada

5-7 commits de código + 2 de docs. Scope 1 sprint.

## Riesgo

Medio. Primera migration real. Tests golden + round-trip protegen.
Mitigación: migration idempotente `IF NOT EXISTS`. Golden baseline
regenerada sin perder keys (INVARIANT 6).

## Definition of Done

Ver `ACCEPTANCE.md`.
