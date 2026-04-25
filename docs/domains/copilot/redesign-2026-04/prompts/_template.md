# Prompt para iniciar F# en nueva conversación

> Pegar este texto literal al abrir nueva sesión Claude Code en `/home/chris/AISALESHT`.

---

```
Estamos ejecutando la fase F# del Copilot Redesign 2026-04 ("Claude Code de Marketing").

Antes de tocar código, leé en orden:
1. docs/domains/copilot/redesign-2026-04/README.md
2. docs/domains/copilot/redesign-2026-04/00-vision-and-non-goals.md (atención a §3 — lo que NO se toca)
3. docs/domains/copilot/redesign-2026-04/01-master-plan.md
4. docs/domains/copilot/redesign-2026-04/02-architecture-target.md
5. docs/domains/copilot/redesign-2026-04/03-phase-protocol.md
6. docs/domains/copilot/redesign-2026-04/phases/F#-{slug}.md
7. docs/domains/copilot/redesign-2026-04/learnings/F{#-1}-{slug}.md (si existe)

Después seguí el protocolo del paso 03 sin saltarte ningún paso:
- Paso 2: pasada de research fresco (WebSearch + tessl-context, abril 2026).
- Paso 3: TaskCreate con tasks granulares.
- Paso 4: TDD obligatorio.
- Paso 5: quality gates native (nunca docker exec).
- Paso 6: verificación funcional + confirma que §3 sigue funcionando.
- Paso 7: learnings/F#-{slug}.md.
- Paso 8: prompts/F{#+1}-start.md.
- Paso 9: commit + push + reporte al usuario.

Brutal honestidad. No alucinar. No agregar features no listadas. Si descubris algo crítico no previsto → preguntar antes de actuar.

Branch único: development. Native dev tools (lint/tests/type-check WSL, nunca docker exec).

Empezá por el Paso 1 (re-lectura). Reportame en 3 líneas qué entendiste antes de avanzar al Paso 2.
```

---

## Hooks específicos de esta fase

(Esta sección la completa la fase ANTERIOR al cerrar, basándose en aprendizajes:)

- Cosas que aprendí en F{#-1} relevantes para F#:
- Tests baseline que F# debe correr antes de empezar:
- Archivos clave que F# modifica:
- Riesgos que vigilar:
