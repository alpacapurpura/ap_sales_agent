# Prompt F0 — Foundation cleanup

> Copiar TODO el bloque entre los `---` y pegarlo como primer mensaje de una **conversación nueva** de Claude Code en `/home/chris/AISALESHT` (working dir del repo).

---

```
Estamos arrancando la fase F0 del Copilot Redesign 2026-04 ("Claude Code de Marketing").

Es la primera fase del plan. Tu trabajo: limpieza + baseline + dep ready, sin refactor de arquitectura.

Antes de tocar código, leé en orden:
1. docs/domains/copilot/redesign-2026-04/README.md
2. docs/domains/copilot/redesign-2026-04/00-vision-and-non-goals.md  (atención §3 — lo que NO se toca)
3. docs/domains/copilot/redesign-2026-04/01-master-plan.md
4. docs/domains/copilot/redesign-2026-04/02-architecture-target.md
5. docs/domains/copilot/redesign-2026-04/03-phase-protocol.md
6. docs/domains/copilot/redesign-2026-04/phases/F0-foundation-cleanup.md

Después seguí el protocolo del paso 03 sin saltarte ningún paso:
- Paso 2: pasada de research fresco (WebSearch + skill tessl-context, abril 2026). Queries del §3 del doc F0.
- Paso 3: TaskCreate con tasks granulares.
- Paso 4: TDD obligatorio (golden tests baseline son TDD para F1+).
- Paso 5: quality gates native (NUNCA docker exec).
- Paso 6: verificación funcional + confirma que §3 sigue funcionando.
- Paso 7: docs/domains/copilot/redesign-2026-04/learnings/F0-foundation.md.
- Paso 8: docs/domains/copilot/redesign-2026-04/prompts/F1-start.md.
- Paso 9: commit + push + reporte al usuario.

Reglas no negociables:
- Branch único: development. Si no estás ahí, checkout antes de arrancar.
- Brutal honestidad. Si algo del plan F0 no aplica por descubrimiento → flagealo y preguntá antes de actuar.
- No alucinar paths/símbolos. Leer archivos, no inventar.
- No tocar §3 (lista exhaustiva de NO tocar).
- Native dev tools (lint/tests/type-check WSL, NUNCA docker exec).
- Spanish neutro LatAm en user-facing (no aplica acá pero recordá).
- Stage por nombre (git add path), nunca git add -A (parallel-safety).

Empezá por el Paso 1 (re-lectura). Reportame en 3 líneas qué entendiste antes de avanzar al Paso 2.
```

---

## Estado esperado al arrancar F0

- Branch: `development`.
- Working tree: limpio (commit `976123cd` o posterior).
- Carpeta `docs/domains/copilot/redesign-2026-04/` ya creada con todos los docs base + plantillas.
- Sin learnings previos (F0 es la primera fase).

## Qué espera el usuario al cerrar F0

- Resumen 3 líneas + paths a `learnings/F0-foundation.md` y `prompts/F1-start.md`.
- Lista archivos eliminados.
- Versión `langchain-deepagents` fijada.
- Comando rápido para correr golden tests.
- Confirmación que `§3 (no tocar)` sigue funcionando (browser smoke + tests).
