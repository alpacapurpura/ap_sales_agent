---
status: in_progress
opened_at: 2026-04-24
closed_at: null
baseline_green_commit: fcef64a4
sub_step: 06.A
---

# Fase 06 — Brand migration · Status

**In progress**. Pre-investigación completa, ACCEPTANCE definido,
baseline tests verde (453 BE arch + 38 FE arch).

Sub-steps:
- 06.A docs alignment + golden brand snapshot — **active**.
- 06.B generic platform tests pre-brand.
- 06.C brand FieldContract module.
- 06.D BRAND_EDITABLE_FIELDS proyectado.
- 06.E MIGRATED_MODULES bumped.
- 06.F tech debt en scope.
- 06.G close fase.

Decisión clave (per PRE_INVESTIGATION.md):
- buyer-persona out of scope (Fase 07 separada).
- Walker config: composable_fields para 9 sub-models, depth = 1 level
  (matches offer pattern).
- Drift A/B (broken shorthand paths) cerrado por construcción — los
  paths broken nunca validaron en `propose_field_updates` así que
  removerlos no afecta UX.
- Drift C (Pydantic fields missing del catalog) cerrado por
  derivación — agrega capabilities, no regresión.
