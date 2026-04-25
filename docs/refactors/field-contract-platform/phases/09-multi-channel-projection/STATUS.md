---
status: ready-to-start
opened_at: null
closed_at: null
baseline_green_commit: (TBD by 08.F close commit)
---

# Fase 09 — Multi-channel projection · Status

**Ready-to-start**. Fase 08 cerrada (5 commits). Copilot consume
`FieldContract` cross-module unificado. 507 arch tests + 52 copilot
acceptance verde como baseline.

## Scope (per PLAN.md §Fase 09)

El copilot conversacional whatsapp/telegram consume `FieldContract`
para preguntar naturalmente. Web sigue funcionando idéntico.

## Deliverables esperados

- `copilot/application/orchestrator/conversational_questioning.py`:
  algoritmo `next_question(module, state)` que selecciona siguiente
  field por (priority, gate, missing).
- Integración con whatsapp/telegram channel adapters.
- Tests E2E channel-agnostic: mismo flow funciona web + chat.

## Pre-investigación obligatoria (ADR-017)

- Estado del copilot conversacional en este momento (whatsapp ya
  integrado? telegram?).
- Trade-offs: ¿algoritmo determinístico decide preguntas o LLM
  creativo? Híbrido natural: algoritmo selecciona candidate fields,
  LLM formula la pregunta.
- Compat web ↔ chat: el form-runtime web sigue funcionando con la
  misma surface.

## Diferidos posibles para Fase 09 (de fases anteriores)

- **Diferidos Fase 05** (LEARNINGS Fase 05): full data-driven loop en
  `agent_identity.j2`, alineación completion ↔ contract semantics,
  migración landing builders al Offer aggregate. Fase 09 puede
  evaluarlos en una sub-fase dedicada.
- Walker extension para list[dict] item sub-keys (LEARNINGS Fase 07).

## Riesgo

**Alto**. Producto y arquitectura interactúan. Probable spawn de
sub-fases. Whatsapp/telegram en producción agrega presión.
