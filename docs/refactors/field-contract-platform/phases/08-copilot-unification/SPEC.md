# Fase 08 — Copilot unification

## Objetivo

Eliminar duplicación interna del copilot. `editable_fields` port +
`schema_introspection` consumen `FieldContract` cross-module. Reduce
2 SSoT a 1 dentro del copilot.

## Scope

**Dentro**:
- `shared/links/ports/editable_fields.py` rewriteado: `get_catalog(domain)`
  proyecta de `get_module_contracts(domain)` con `can_propose=True` y
  `status=ACTIVE`.
- `copilot/domain/schema_introspection.py` simplificado: `get_model_sections`,
  `validate_field_path` consumen `FieldContract` registry. Introspección
  Pydantic queda como helper interno del registry, no API pública.
- `copilot/domain/offer_fields.py` evaluar drop si consumers migran.
- Tests acceptance copilot end-to-end: chat tests existentes pasan idéntico.

**Fuera**:
- Multi-channel (Fase 09).

## Riesgo

Alto. Copilot está en producción. Tests acceptance exhaustivos requeridos.

## DoD

- [ ] `editable_fields` port deriva.
- [ ] `schema_introspection` simplificado.
- [ ] Copilot acceptance tests verde.
- [ ] `propose_field_updates` valida idéntico.
