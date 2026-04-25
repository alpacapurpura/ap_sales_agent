# Plantilla — prompt de inicio de fase

> Cada fase usa este patrón. Copiar el bloque entre los `---` literal a una conversación nueva de Claude Code en `/home/chris/AISALESHT`.

---

```
Estamos ejecutando la fase F# del Copilot Redesign 2026-04 ("Claude Code de Marketing").

Objetivo único de esta fase: <pegar el §1 del doc phases/F#-{slug}.md, una sola línea>.

Antes de escribir código, leé en orden (sin saltarte ninguno):
1. docs/domains/copilot/redesign-2026-04/README.md
2. docs/domains/copilot/redesign-2026-04/00-vision-and-non-goals.md  (atención §3 — lista exhaustiva de lo que NO se toca)
3. docs/domains/copilot/redesign-2026-04/01-master-plan.md
4. docs/domains/copilot/redesign-2026-04/02-architecture-target.md
5. docs/domains/copilot/redesign-2026-04/03-phase-protocol.md
6. docs/domains/copilot/redesign-2026-04/phases/F#-{slug}.md
7. docs/domains/copilot/redesign-2026-04/learnings/F{#-1}-*.md  (aprendizajes de la fase anterior — OBLIGATORIO si existen)

Después seguí los 9 pasos del protocolo (03-phase-protocol.md). Énfasis especial:

- **Paso 2 — Research fresco abril 2026 (no skip).**
  - WebSearch: mínimo 2 queries del "Research mandate" del doc de la fase. Anotar fuentes que vayan al learnings.
  - Context7 / Tessl tiles: invocar el skill `tessl-context` para revisar documentación versionada de las libs centrales que la fase toca (ej. langgraph, deepagents, fastapi, react, qdrant). Si no hay tile y el tema es central, instalarlo con `tessl install`.
  - Cuando la fase introduce o bumpea una librería externa: confirmar versión latest + leer changelog del último año. Lo "que sabíamos" puede estar desactualizado.
  - Si el research sugiere que el plan cambió → **ajustar el plan antes de codear** y dejar nota en learnings; no implementar al ciego.

- **Foco — no scope creep.** Si en el research aparecen ideas tangenciales atractivas, anotarlas como recomendaciones para fase siguiente, pero NO meterlas en el código de esta fase. Una fase entrega una sola cosa.

- **Paso 4 — TDD obligatorio.** Tests primero, implementación después. Para refactors: golden snapshots de F0 deben seguir verdes (`cd backend && .venv/bin/pytest tests/modules/copilot/golden/ -q -o addopts=""`); si cambian intencionalmente, `UPDATE_GOLDEN=1` y diff revisable en el commit.

- **Paso 5 — Quality gates native (NUNCA `docker exec`).** Lint, format, tests, type-check todo desde WSL nativo. Migraciones idempotentes si aplica.

- **Paso 6 — Verificar §3 intacto.** Browser smoke o trace inspection si la fase toca algo cerca de UI / SSE / observability.

- **Paso 7 — Lecciones aprendidas: ÚTILES, no plantilla rellenada.**
  - Solo escribir lo que **una fase futura va a consultar**: decisiones con su razón, sorpresas reales (no "todo salió bien"), gotchas de versión, hooks listos para próximas fases, riesgos abiertos.
  - Prohibido relleno: NO listar archivos modificados con detalle exhaustivo (eso vive en `git diff` / `git log`). NO inventar métricas si no se midieron. NO repetir lo que ya está en los docs base.
  - Preferir 200 líneas densas vs 600 con campos vacíos. Si una sección del template no aplica a esta fase, eliminarla.
  - El criterio: ¿la fase F{#+1} sería más torpe sin esta nota? Si no, sobra.

- **Paso 8 — Generar `prompts/F{#+1}-start.md`** desde esta plantilla, completando los hooks específicos al final.

- **Paso 9 — Commit + push.** Conventional commit con scope `copilot-redesign-f#`. Stage por nombre (nunca `git add -A`). Reportar al usuario en 3 líneas + paths a learnings + prompt siguiente.

Reglas no negociables:
- Branch único: `development`. Si no estás ahí, checkout antes.
- Brutal honestidad. Si el plan F# no aplica por aprendizajes previos → flagear y preguntar antes de actuar.
- No alucinar paths/símbolos. Leer archivos, no inventar.
- No tocar §3 (00-vision-and-non-goals.md). Si parece necesario → parar, preguntar.
- Native dev tools (lint/tests/type-check WSL, NUNCA `docker exec`).
- Spanish neutro LatAm en todo lo user-facing (`.claude/rules/spanish-text.md`).
- Stage por nombre (`git add path/file`), nunca `git add -A` (parallel-safety).

Empezá por el Paso 1 (re-lectura, especialmente learnings de la fase anterior). Reportá en 3 líneas qué entendiste antes de avanzar al Paso 2.
```

---

## Hooks específicos para esta fase

(Esta sección la completa la fase ANTERIOR al cerrar, basándose en aprendizajes. Si no aplica, eliminar todo el bloque — no dejar bullets vacíos.)

### Aprendizajes de la fase F{#-1} que F# debe asumir

- (Solo entradas accionables. Lo que cambia decisiones de F#.)

### Tests baseline que F# debe correr ANTES de empezar

- (Comando exacto. Qué debería estar verde antes de tocar nada.)

### Archivos clave que F# modifica

- (Solo si conocido a priori. No exhaustivo.)

### Riesgos que vigilar en F#

- (Específicos, no genéricos.)
