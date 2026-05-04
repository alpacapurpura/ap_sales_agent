# Fase 05 — Downstream data-driven

## Objetivo

Sales-agent + landing + completion service consumen `FieldContract`
directamente. Un field nuevo agregado al contract → aparece automático
en prompt sales-agent + copy de landing + cálculo de completion, sin
tocar templates.

## Scope

**Dentro**:
- `sales_agent/application/knowledge_builder.py` consume
  `get_module_contracts("offer")` para iterar fields. Ordena por
  `(section, priority)`. Filtra `status == ACTIVE`. Skip valor vacío.
- `sales_agent/.../prompts/agent_identity.j2` render data-driven.
  Reemplaza `{% if offer.X %}` hardcoded por loop sobre contracts.
- `landing/application/services/landing_content_builders.py` consume
  contract para proyectar copy.
- `offer/application/services/offer_completion_service.py` calcula
  `% completed` con `is_required_semantic`.
- Tests golden: `agent_identity.j2` rendered + `landing/output`
  byte-identical para offer `a96403b5...` vs baseline pre-fase-05.

**Fuera**:
- Brand/buyer migration (Fase 06/07).
- Copilot unification (Fase 08).
- Multi-channel (Fase 09).
- Schemas FE no tocan.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Render data-driven cambia output sutilmente | Tests golden snapshot byte-identical |
| Templates sales-agent tienen lógica custom no expresable en data | Override mecanismo: `c.notes` + `human_question_es` cubren mayoría. Casos extremos: sub-template per section con loop interno |
| Completion service calculation cambia % | Tests existentes preservados + nuevo test golden completion |

## DoD

- [ ] Sales-agent render data-driven funciona.
- [ ] Landing render data-driven funciona.
- [ ] Completion calculation idéntico para offers existentes.
- [ ] Golden snapshot offer `a96403b5...` byte-identical.
- [ ] Tests verde (backend + frontend).
