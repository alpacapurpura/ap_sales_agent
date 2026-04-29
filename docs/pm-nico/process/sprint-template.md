# Sprint S{N} — {tema}

> Template. Copy a `pis/PI-X/sprints/S{N}-{slug}/sprint.md`. Reemplazar placeholders.

## Meta

| Campo | Valor |
|---|---|
| Sprint ID | S{N}-{slug} |
| PI padre | PI-X-{theme} |
| Estado | not-started \| in-progress \| done |
| Inicio | YYYY-MM-DD |
| Cierre estimado | YYYY-MM-DD |
| Cierre real | — |
| Owner PM | /pm |

## Objetivo (1 línea)

{Qué entrega este sprint que NINGÚN sprint posterior tenga que reconstruir.}

## Pre-handoff (input desde sprint anterior)

- Decisiones tomadas: link a `../S{N-1}-*/handoff.md`
- Surface disponible: APIs/types/tablas que ya existen
- Riesgos abiertos: lo que sprint anterior no pudo resolver
- Skills/agentes recomendados: lista exacta

## Plan PRs

| PR | Descripción | Agentes/skills | Esfuerzo | Estado |
|---|---|---|---|---|
| PR-N | descripción 1 línea | `nicolify-architect` → `nicolify-backend` | S/M/L | not-started |
| PR-N+1 | ... | ... | ... | ... |

Detalle de cada PR vive en `prs/PR-N-{slug}.md`.

## Criterio éxito sprint

- [ ] Criterio 1 testeable
- [ ] Criterio 2 testeable
- [ ] Cero refactor necesario en sprint siguiente

## Out of scope

| Item | Razón | Sprint destino |
|---|---|---|
| ... | ... | ... |

## Decisiones a tomar durante sprint

(append-only conforme aparezcan)

| Fecha | Decisión | PR |
|---|---|---|
| ... | ... | ... |

## Riesgos

| Riesgo | Mitigación | Owner |
|---|---|---|
| ... | ... | ... |

## Cierre

Al cerrar:
1. Llenar `learnings.md` (qué funcionó, qué no, sorpresas).
2. Llenar `handoff.md` (decisiones, surface, agentes recomendados).
3. Marcar sprint `done` en este `sprint.md`.
4. Si learnings impactan proceso global → append `../../../../process/process-learnings.md`.
