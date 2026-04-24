# Aprendizajes acumulados

Append-only. Cada fase suma entries. Cross-cutting arriba. Per-fase abajo.

---

## Cross-cutting (aplica a todo Nicolify)

- **Pydantic default `extra="ignore"` es silent data loss trap.** `BaseEntity` config en `shared/domain/base_entity.py` no declara `extra=`. Post-refactor considerar `forbid` con arch test que permite solo legacy via migration `metadata_info`.

- **Schemas FE sin enforcement de paths contra BE domain = drift garantizado.** Capa A (9 paths huérfanos) fue consecuencia predecible. Arch test desde Fase 0 lo impide a futuro.

- **`OFFER_FIELDS_BY_FE_SECTION` es mapeo parcial que nadie tiene incentivo a completar.** Dict paralelo al FE schema. Solución de fondo = derivación de contrato, no completar lista manual.

- **Section catalog ya existe BE** (`section_catalog.py`) con metadata rica (label_es, subtitle_es, help_text_es, icon_name, scope, weight). FE no lo consume. Duplicación legacy.

- **Brand-studio tiene mismo patrón** que offer-studio (schemas FE + section-catalog.ts). Cualquier mejora en offer debe plantear replica en brand.

- **Polling cap hardcoded 120s** rompió offer extraction >2min. Fixed in `e8dd4bd5`. Lección: safety caps arbitrarios son frágiles ante cambios BE. Poll hasta terminal con cap alto + backoff escalonado.

- **Scripts standalone que tocan SA deben importar `model_registry` primero.** Sin eso, al primer query SA intenta resolver nombres de relaciones string (`LeadModel`, etc.) y falla porque el módulo no fue importado. Patrón: `from src.shared.infrastructure import model_registry  # noqa: F401` arriba de cualquier `db.execute`.

- **Allowlists de arch tests deben medirse, no estimarse.** Fase 00 SPEC predijo 9 paths y la realidad fue 59. Lección: antes de fijar un cap en ADR, corré el test contra el repo y contá. Sub-estimar lleva a red CI o a ADR reactivos.

- **Fixtures golden de BE que necesitan DB corren dentro del container, no en WSL native.** Docker publica en Windows host, WSL2 no llega por `localhost`. Patrón documentado en `docs/refactors/field-contract-ssot/fixtures/offer_a96403b5_baseline.md`.

---

## Fase 00 — Guardrail

**Status**: done (2026-04-24)

### Pre-fase expectations
- Arch test simple (AST parse + JSON compare). 2-3h realista.
- Allowlist inicial 9 paths.
- Golden fixture captura limitada a lo verificable hoy (Wave 1 completada, Wave 2/3 dudoso por bug polling ya fixed).

### Descubrimientos
- Allowlist real arrancó en **59**, no 9. Audit completo de
  `OFFER_SCHEMA_REGISTRY` con filtro `scope !== "edition_level"` + `owner !== "edition"`
  surfacó brecha mayor de lo previsto. Se documenta en ADR-007.
- `SubscriptionDetails` sufre rename drift: FE usa `billing_frequency` /
  `content_update_frequency`, BE declara `billing_cycle` / `content_update_freq`.
  Arreglable en Fase 02 (rename BE para alinear con terminología neutra).
- PLATFORM archetype (14 paths en `platform-details.schema.ts`) no tiene
  contraparte `PlatformDetails` en BE. Fase 02 debe introducir la 6ta entry
  en `ARCHETYPE_TO_DETAILS_MAPPING`.
- Cross-module federado (21 paths en `assets`, `testimonials`, `portfolio`,
  `knowledge`, `scheduling`, `gallery`, `faq`, `location.venues`) exige
  que el resolver Fase 05 consulte múltiples JSONs BE, no solo `Offer`.
- `LandingService.generate_landing_for_offer` persiste — replicamos el
  resolver puro (`_resolve_content` + SQL) en `scripts/capture_offer_a96403b5_baseline.py`
  para snapshot dry-run.
- Postgres bind sale por 127.0.0.1:5432 desde Windows, pero WSL2 no rutea
  al bridge Docker; scripts que necesitan DB local tienen que correr dentro
  de `visionarias_brain_dev` y copiar el output con `docker cp`.
- `from src.shared.infrastructure import model_registry` debe preceder
  cualquier consulta SA en scripts standalone para evitar
  `InvalidRequestError: expression 'LeadModel' failed to locate a name`.

### Decisiones nuevas
- ADR-007 — allowlist cap Fase 00 = 59, shrink-only desde ahí.

### Deuda técnica encontrada
- Rename `billing_cycle` → `billing_frequency` + `content_update_freq` →
  `content_update_frequency` en `SubscriptionDetails` (incluye migration
  + update repositorio). Programado Fase 02.
- Modelar `PlatformDetails` en `offer/domain/details.py` + 6ta entry de
  `ARCHETYPE_TO_DETAILS_MAPPING`. Programado Fase 02.
- Extender resolver de `test-fe-schema-paths-resolve` a paths federados
  (assets/social-proof/scheduling/knowledge) en Fase 05.
- Item-level (itemSchema.fields[].path) validation no enforzado — solo
  se excluyen de top-level. Fase 01+ debe extender la resolución a tipos
  `PricingStructure`/`ObjectionItem`/`DeliverableItem`/etc.

---

## Fase 01 — FieldContract pilot (pricing)

**Status**: pending

### Descubrimientos
- [ ] _pendiente_

---

## Fase 02 — Migrate remaining sections

**Status**: pending

---

## Fase 03 — Section catalog dedup

**Status**: pending

---

## Fase 04 — Drop OFFER_FIELDS_BY_FE_SECTION

**Status**: pending

---

## Fase 05 — Downstream unify

**Status**: pending
