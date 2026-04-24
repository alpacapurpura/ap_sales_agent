# Fase 09 — Multi-channel projection

## Objetivo

El copilot conversacional whatsapp/telegram consume `FieldContract`
para preguntar naturalmente. La web sigue funcionando igual.

## Scope

**Dentro**:
- `copilot/application/orchestrator/conversational_questioning.py`:
  algoritmo `next_question(module, state)` que selecciona siguiente
  field por `(priority, gate satisfied, missing value, status=ACTIVE)`.
- Integración con channel adapters (whatsapp/telegram).
- Tests E2E channel-agnostic: mismo flow funciona en web + chat.
- Documentación pattern conversacional.

**Fuera**:
- Channel infrastructure (whatsapp/telegram integration en sí).
  Esta fase asume infraestructura existe — solo agrega el algoritmo
  data-driven.

## Riesgo

Alto. Producto y arquitectura interactúan. Probable spawn de sub-fases.

## DoD

- [ ] `next_question` algoritmo funciona.
- [ ] Channel adapter web + chat ejercitan misma lógica.
- [ ] Tests E2E.
