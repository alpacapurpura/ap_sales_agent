---
status: done
opened_at: 2026-04-24
closed_at: 2026-04-24
baseline_green_commit: 2e0f1cc7
last_green_commit: f866cd17
---

# Fase 09 — Multi-channel projection · Status

**Done**. 7 sub-pasos atómicos commiteados:

| Sub-paso | Commit | Descripción |
|---|---|---|
| 09.A | `a61aea16` | docs PRE_INVESTIGATION + SPEC + ACCEPTANCE |
| 09.B | `3691fd62` | next_question algorithm + 40 unit tests |
| 09.C | `eaa73708` | guided advance suggested_question + 16 unit tests |
| 09.D | `08ad7312` | ConversationalChannelPort + InMemoryConversationalChannel + 6 unit tests |
| 09.E | `bbfb5974` | E2E channel-agnostic + 6 tests |
| 09.F | `7e00b300` | human_question_es enrichment brand 12 + buyer 12 + baseline update |
| 09.fix | `f866cd17` | synthetic registry isolation (teardown_module) |
| 09.G | (this commit) | LEARNINGS + STATE/STATUS bump + close |

**Refactor field-contract-platform CIERRA con Fase 09.** 6 fases (04-09)
completadas según plan original. 3 módulos migrados (offer + brand +
buyer_persona). Copilot read+write unificado. Algoritmo conversational
data-driven channel-agnostic operativo.

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
