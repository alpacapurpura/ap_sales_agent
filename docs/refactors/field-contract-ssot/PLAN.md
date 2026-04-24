# Plan — 6 fases frozen

Cambios al plan requieren entry en [DECISIONS.md](DECISIONS.md) con razón fuerte.

## Overview

```
Fase 00  Guardrail           Arch test paths resolve + allowlist + golden fixture
Fase 01  Pilot pricing       FieldContract BE + migration + 3 LATAM fields funcionan
Fase 02  Migrate sections    Otras 8 secciones bajo FieldContract
Fase 03  Section catalog     FE consume BE catalog, dedup lista 21 secciones
Fase 04  Drop legacy map     OFFER_FIELDS_BY_FE_SECTION derivado de FieldContract
Fase 05  Downstream unify    sales-agent + landing + completion consumen contract
```

## Fase 00 — Guardrail

**Objetivo**: evitar drift futuro. Arch test que rechaza PR con FE path inexistente.

**Deliverables**:
- `frontend/src/__tests__/architecture/test-fe-schema-paths-resolve.test.ts`
- `backend/scripts/generate_offer_field_paths.py` (dump Pydantic paths a JSON)
- `frontend/src/features/offer-studio/api/__generated__/offer-field-paths.json`
- Allowlist inicial 9 paths conocidos
- Golden fixture `fixtures/offer_a96403b5_baseline.md`

**Out of scope**: no migration, no domain change, no UX change.

**Duración estimada**: 2-3h. Un PR atómico.

**Riesgo**: bajo. Solo CI gate.

## Fase 01 — FieldContract pilot (pricing)

**Objetivo**: introducir `FieldContract` BE + migrar pricing + cerrar Capa A pricing (3 fields).

**Deliverables**:
- `backend/src/modules/offer/domain/field_contract.py` con dataclass + registry
- Migration idempotente: `+tax_included bool, +installments_available text, +accepted_payment_providers jsonb[]`
- Pydantic `Offer` agrega los 3 fields
- `OfferPricingUpdate` DTO incluye
- Prompt jinja2 `offer_extract_closing.j2` actualizado (pricing vive con closing wave)
- `extraction_schemas.py` wave output extiende
- Endpoint `GET /api/v1/offer/field-contract` versionado
- Codegen `offer-field-paths.json` con nuevos paths
- `pricing.schema.ts` tipa `path` contra codegen
- Arch test shrinks allowlist (3 paths removidos)
- Sales-agent prompt template agrega bloque pricing si seteado
- Landing builder consume nuevos fields si presentes
- Golden fixture: persistencia round-trip testing

**Out of scope**: otras secciones, `OFFER_FIELDS_BY_FE_SECTION` cleanup.

**Duración**: 1 sprint.

**Riesgo**: medio. Migration real. Tests golden protegen.

## Fase 02 — Migrar resto secciones

**Objetivo**: aplicar patrón Fase 01 a las 8 secciones restantes.

**Secciones a migrar** (una PR por bloque semántico):
1. Authority block — `authority_positioning_for_sales`, `authority_notes` (instructors section)
2. Value-stack anchor — `total_perceived_value_anchor`, `stack_positioning_statement`
3. Program-details narrativos — `weekly_time_commitment_hours`, `prerequisites_text` (JSONB)
4. Extract prompts restantes (Capa B coverage: fulfillment_note, etc.)
5. FieldContract para secciones sin Capa A pending (identity, promise, strategy, psychology, closing) — ya tienen domain, solo formalizar

**Deliverables por bloque**:
- Migration si aplica
- Fields en Pydantic
- Extraction prompt + schema update
- `FieldContract` registry entries
- Schema FE tipado
- Arch test allowlist shrinks
- Snapshot tests golden

**Duración**: 2 sprints. ~1 PR por semana.

**Riesgo**: bajo (patrón validado en Fase 01).

## Fase 03 — Section catalog dedup

**Objetivo**: FE no duplica lista de secciones. Consume del endpoint `/catalog` existente.

**Deliverables**:
- FE hook `useSectionCatalog()` reemplaza hardcoded `OFFER_SECTIONS`
- `icon_name` string en BE → componente Lucide via `icon-name-resolver.ts` (ya existe)
- `kind` (singleton/collection) se mueve a BE `SectionMetadata`
- Brand-studio mismo patrón (DRY cross-studio)
- Arch test: FE no puede hardcodear section list

**Duración**: 0.5 sprint.

**Riesgo**: bajo. Refactor mecánico.

## Fase 04 — Drop `OFFER_FIELDS_BY_FE_SECTION`

**Objetivo**: eliminar el mapping legacy, reemplazar por derivación pura desde `FieldContract`.

**Deliverables**:
- Util `fields_by_section(contract, section_key) -> tuple[str, ...]`
- Extraction worker consume util
- Tests extraction se adaptan
- Se borra `OFFER_FIELDS_BY_FE_SECTION` dict
- Arch test: el dict no puede reaparecer

**Duración**: 0.5 sprint.

**Riesgo**: bajo. Paridad tested.

## Fase 05 — Sales-agent + landing consumen contract

**Objetivo**: downstream unified. Nuevos fields agregados a contrato aparecen **auto** en sales-agent prompt + landing sin tocar templates.

**Deliverables**:
- `knowledge_builder.py` consume `FieldContract` para iterar fields user-facing
- `agent_identity.j2` render data-driven (no hardcoded `{% if offer.x %}` por cada field)
- `landing_content_builders.py` consume `FieldContract` para proyectar copy
- Completion service consume `FieldContract.required` → % real
- Golden snapshot test: `a96403b5...` prompt rendered + landing output diff vs baseline

**Duración**: 1 sprint.

**Riesgo**: medio. Tests golden protegen outputs críticos.

## Out of scope global

- Copy UX/labels iteration (separado — trabajo de producto)
- Refactor `PricingStructure` VO o edition model
- Nuevos catálogos (VariantStructure, LadderHints actualizaciones)
- Migración brand-studio a `FieldContract` (patrón disponible para hacerlo después si querés)
- Enum dinámico por preset (pendiente, design separado)

## Reglas inquebrantables

Ver [INVARIANTS.md](INVARIANTS.md).

## Tech debt discovery

Si durante cualquier fase encontrás deuda técnica **relacionada al scope**, la arreglás en la misma PR (o PR vecina de misma fase). Si es tangencial, entry en [TODO.md](TODO.md) y [docs/mejoras-proceso/to-do.md](../../mejoras-proceso/to-do.md).

**Nunca** dejar deuda técnica descubierta para "después del refactor". Crea compounding.
