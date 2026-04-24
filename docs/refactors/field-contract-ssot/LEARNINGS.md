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

---

## Fase 00 — Guardrail

**Status**: pending (2026-04-24)

### Pre-fase expectations
- Arch test simple (AST parse + JSON compare). 2-3h realista.
- Allowlist inicial 9 paths.
- Golden fixture captura limitada a lo verificable hoy (Wave 1 completada, Wave 2/3 dudoso por bug polling ya fixed).

### Descubrimientos
- [ ] _pendiente ejecución_

### Decisiones nuevas
- [ ] _pendiente ejecución_

### Deuda técnica encontrada
- [ ] _pendiente ejecución_

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
