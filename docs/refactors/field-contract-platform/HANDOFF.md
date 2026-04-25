# Handoff — siguiente sesión Claude

> Prompt listo para pegar y arrancar la próxima fase. Generado al cerrar
> Fase 08 (`e1f44284`). Sirve como anclaje para retomar el refactor sin
> reconstruir contexto desde cero.

## Cómo usar este doc

1. Pegá el prompt de **Fase 09** (abajo) en una nueva sesión Claude
   con working dir `/home/chris/AISALESHT`.
2. Claude lee `STATE.md` + protocolos + PRE_INVESTIGATION + SPEC de la
   fase activa antes de tocar código.
3. Cada commit atómico revertible. Commit final actualiza este HANDOFF
   con el prompt de la fase siguiente.

## Prompt — arrancar Fase 09 (Multi-channel projection)

```
Retomamos refactor field-contract-platform.

Workspace: docs/refactors/field-contract-platform/

Estado:
- Fase cerrada: 08-copilot-unification (commits 0d9ccc40 → e1f44284)
- Fase activa: 09-multi-channel-projection (ready-to-start)
- Last green commit: e1f44284
- Branch: development
- Working tree: limpio (3 ajenos: buyer-persona-ai-flow-verified.png,
  qa-extract-clean.png, docs/refactors/copilot-architecture/)
- Backend tests: 695 copilot pass · arch tests: 507 · acceptance copilot: 52
- 3 módulos migrados al FieldContract platform: offer + brand +
  buyer_persona. Copilot consume el registry unificado (Fase 08).

Protocolo de arranque obligatorio:

1. Leé en orden (5-10 min):
   - docs/refactors/field-contract-platform/STATE.md
   - docs/refactors/field-contract-platform/INVARIANTS.md
   - docs/refactors/field-contract-platform/PLAN.md §Fase 09
   - docs/refactors/field-contract-platform/DESIGN.md (escanear §2.5
     proyecciones por consumer + §2.8 multi-channel projection)
   - docs/refactors/field-contract-platform/LEARNINGS.md (cross-cutting
     + Fase 08 → Para Fase 09)
   - docs/refactors/field-contract-platform/DECISIONS.md (ADR-014
     copilot meta + ADR-015 multi-channel)
   - docs/refactors/field-contract-platform/phases/09-multi-channel-projection/STATUS.md
   - docs/refactors/field-contract-platform/protocol/RESUME.md

2. Pre-investigación obligatoria (sin saltar — ADR-017):
   Crear phases/09-multi-channel-projection/PRE_INVESTIGATION.md
   inventariando:
   - Estado actual del copilot conversacional cross-channel:
     · ¿Whatsapp adapter existe? ¿Cómo bind tools?
     · ¿Telegram adapter existe?
     · ¿Email/voice channels en roadmap?
   - Flujo actual de question selection en el copilot (qué decide
     qué preguntar, dónde vive el orden).
   - Trade-off determinístico (algoritmo selecciona candidate fields
     por priority/gate/missing) vs LLM creativo (LLM decide orden).
     Recomendado del DESIGN: híbrido — algoritmo filtra candidates,
     LLM formula la pregunta natural.
   - Compat web ↔ chat: form-runtime web sigue usando schemas existentes;
     el chat consume FieldContract metadata (human_question_es, expects,
     gate, redo_if_changes).
   - Tests acceptance existentes: chat E2E, sales-agent flow, copilot
     orchestrator tests.

3. Ejecutá protocol/PRE_FLIGHT.md (baseline tests + git status).

4. Crear phases/09-multi-channel-projection/SPEC.md con plan:
   - `copilot/application/orchestrator/conversational_questioning.py`:
     algoritmo `next_question(module, state)` que selecciona siguiente
     field por (priority, gate satisfied, missing). Probable sub-fases.
   - Integración con channel adapters existentes.
   - Tests E2E channel-agnostic: mismo flow funciona web + chat.

5. Escribir phases/09-multi-channel-projection/ACCEPTANCE.md con
   sub-steps atómicos y DoD per sub-step.

6. Scope Fase 09 (per PLAN.md):
   - Algoritmo question selection data-driven sobre FieldContract.
   - Channel adapters consumen `human_question_es` + `expects` + `gate`.
   - Tests channel-agnostic verifican mismo flow.
   - Documentación copilot conversacional pattern.

7. Out of scope:
   - Fases 04-08 cerradas (no reabrir).
   - Diferidos posibles (a tomar en sub-fases si scope lo permite):
     · Full data-driven `agent_identity.j2` loop (Fase 05 deferral).
     · Completion ↔ contract semantic alignment (Fase 05 deferral).
     · Landing aggregate migration (Fase 05 deferral).
     · Walker extension list[dict] item sub-keys (Fase 07 deferral).
   - Cambios en FE schemas (INVARIANT 9) — solo si la fase explícitamente
     necesita exposer nuevos campos al form-runtime.

8. Commits atómicos sugeridos (definitivo en SPEC + ACCEPTANCE):
   - a) PRE_INVESTIGATION + SPEC + ACCEPTANCE + baseline tests.
   - b) Algoritmo `next_question(module, state)` core + unit tests.
   - c) Integración con channel adapter (whatsapp first if exists).
   - d) Tests E2E channel-agnostic.
   - e) close: LEARNINGS + STATE/STATUS bump.

9. Al cerrar fase:
   - POST_FLIGHT.md
   - STATE.md → active_phase=10? (o cierre del refactor)
   - STATUS.md Fase 09 done
   - LEARNINGS.md append Fase 09
   - HANDOFF.md actualizado

Reglas inquebrantables:
- Cada commit revertible atómico · rama development · stage por nombre · no tocar ajenos
- Tech debt del scope = arreglar en la fase; tangencial a TODO.md
- Spanish neutro LATAM · TDD · UX byte-identical
- Multi-channel: producto y arquitectura interactúan. Riesgo ALTO.
  Probable spawn de sub-fases. Cada sub-fase con su PRE_INVESTIGATION.
- Si descubrís gap arquitectónico, ADR + replanteo, no hack.
- No reabrir Fases 04-08 (cerradas). Diferidos en LEARNINGS pueden
  tomarse en sub-fases dentro de Fase 09 si scope lo justifica.

Parallel sessions pueden estar corriendo — antes de commitear,
git status --short; si hay ajenos dejalos.

Empezá.
```

## Notas para futuras sesiones

- **Cada fase tiene `PRE_INVESTIGATION.md` obligatorio** (ADR-017). No
  saltar — la lección de Fase 02 del workspace anterior está en el
  ADN del refactor.
- **Cada commit atómico revertible**. INVARIANT 3.
- **UX byte-identical durante migración**. INVARIANT 4. Si rompe golden
  snapshot, no es Fase 04+, es un bug.
- **No introducir nuevos registries paralelos**. INVARIANT 1. Cualquier
  consumer nuevo proyecta del FieldContract registry.
- **Tech debt en scope se arregla en la misma fase**. INVARIANT 16.
- **Lifecycle versionado** (status/deprecated_in/replaced_by) para
  evitar breaking changes durante deprecaciones. ADR-013.
- **Diferidos de Fase 05** (loop data-driven full, completion alignment,
  landing aggregate) viven en LEARNINGS Fase 05 — pueden tomarse en
  sub-fase dedicada de Fase 09.
- **Walker `dict_subkeys` arg** (Fase 07) habilita cualquier módulo
  futuro con JSONB sub-keys sin tocar shared. Pattern Patrón B
  validado.
- **Copilot read+write surface unificada** (Fase 08): port +
  schema_introspection consumen el registry. Todos los catalog files
  per-módulo dropeados. Cualquier nuevo dominio migrado entra
  automático al port via `get_module_contracts(domain)`.

## Contacto

Si necesitás contexto extra, todo está en
`docs/refactors/field-contract-platform/`. STATE.md siempre tiene la
verdad actual. LEARNINGS.md acumula descubrimientos. DECISIONS.md
acumula ADRs. PLAN.md es frozen — cambios requieren nueva ADR.
