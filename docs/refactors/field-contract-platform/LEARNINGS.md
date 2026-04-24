# Aprendizajes acumulados

Append-only. Cada fase suma entries. Cross-cutting arriba. Per-fase abajo.

---

## Cross-cutting (aplica a todo Nicolify)

### Heredados del workspace anterior (field-contract-ssot)

- **Pydantic default `extra="ignore"` es silent data loss trap.**
  `BaseEntity` config no declara `extra=`. Considerar `forbid` con
  arch test que permite legacy via migration `metadata_info`.

- **Schemas FE sin enforcement de paths contra BE domain = drift garantizado.**
  Capa A (9 paths huérfanos en field-contract-ssot Fase 00) lo demostró.

- **Allowlists de arch tests deben medirse, no estimarse.** Fase 00 SPEC
  predijo 9 paths y la realidad fue 59. Antes de fijar cap en ADR,
  correr el test contra el repo y contar.

- **Polling cap hardcoded 120s** rompió offer extraction >2min. Safety
  caps arbitrarios son frágiles. Poll hasta terminal con cap alto +
  backoff.

- **Scripts standalone que tocan SA deben importar `model_registry`
  primero**. Sin eso, primer query falla.

- **Fixtures golden de BE que necesitan DB corren dentro del container,
  no en WSL native.** Docker publica en Windows host, WSL2 no llega
  por `localhost`.

### Nuevos (descubiertos al pivotar a field-contract-platform)

- **Allowlist shrink no es proxy suficiente para cobertura de FieldContract
  registry.** Fase 02 del refactor anterior cerró sin notar 41 fields gap
  porque la métrica era "shrink de allowlist `KNOWN_UNRESOLVED_PATHS`",
  que mide paths huérfanos en codegen JSON (Pydantic-derived). Los 41
  fields legacy nunca aparecieron en la allowlist porque sus paths
  resolvían en el codegen. Solución: arch test independiente
  `Pydantic.model_fields ⊆ FieldContract paths` por módulo migrado.

- **Refactors estructurales empiezan con inventario completo de SSoT
  paralelos.** Antes de definir scope: grep cross-module por todos los
  registries que mencionan "field" o "section". Los 5 fuentes paralelas
  descubiertas en Fase 04 deberían haber sido inventario inicial.

- **`copilot/domain/schema_introspection.py` ya hace introspección
  Pydantic robusta** (`unwrap_optional`, `get_model_sections`,
  `validate_field_path`). Reutilizable en cualquier walker nuevo —
  no inventar.

- **Drift confirmado entre `OFFER_EDITABLE_FIELDS` y `FIELD_CONTRACT_REGISTRY`**
  al abrir Fase 04. Los nuevos pricing LATAM (tax_included,
  installments_available, accepted_payment_providers), authority fields,
  total_perceived_value_anchor, stack_positioning_statement viven en
  un registry pero no en el otro. Sin arch test que fuerce paridad,
  drift entre registries paralelos es inevitable.

- **`OFFER_FIELDS_BY_FE_SECTION` y similares dicts manuales son trampa
  recurrente.** Cualquier dict `{section: tuple[fields]}` que no se
  derive automáticamente acumula drift. Patrón evitar: si el dict tiene
  más de 5 entries y no está auto-generado, está mal.

---

## Fase 04 — Platform foundation

**Status**: in-progress (2026-04-24)

### Pre-fase expectations

- Promover `FieldContract` a `shared/domain/`.
- Offer migra completo end-to-end (closes drift entre 5 registries
  paralelos).
- Brand/buyer/copilot intactos.
- UX byte-identical via golden snapshots.
- Arch tests cross-cutting que fuerzan cobertura.

### Descubrimientos (en curso)

- (Sub-paso A) Inventario confirma 5 fuentes paralelas + 1 dict legacy.
  Drift entre `OFFER_EDITABLE_FIELDS` (~36 entries) y
  `FIELD_CONTRACT_REGISTRY` (~40 entries con mucho overlap pero
  distintos campos). Total Pydantic Offer top-level: ~50 fields +
  PlatformDetails (14) + 5 polymorphic specific_details classes.

(continuará)

---

## Fase 05 — Downstream data-driven

**Status**: pending

---

## Fase 06 — Brand migration

**Status**: pending

---

## Fase 07 — Buyer-persona migration

**Status**: pending

---

## Fase 08 — Copilot unification

**Status**: pending

---

## Fase 09 — Multi-channel projection

**Status**: pending
