# Sprint S{N} — {tema}

> Template. Copy a `pis/active/PI-X-{theme}/sprints/S{N}-{slug}/sprint.md`. Reemplazar placeholders.

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

## Plan PRs (folders)

> **Sprint sizing Opus 4.7[1M]:** target 1-3 PRs amplios cohesivos. Cada PR = carpeta. Cada PR ≈ 3 ejecuciones (architect + builder + auditor).

| PR | Folder | Descripción | Agentes/skills | Esfuerzo | Estado |
|---|---|---|---|---|---|
| PR-N | `prs/PR-N-{slug}/` | descripción 1 línea (scope cohesivo) | `nicolify-architect` → `nicolify-backend` → `nicolify-backend-auditor` | M/L | not-started |
| PR-N+1 | `prs/PR-{N+1}-{slug}/` | ... | ... | ... | ... |

Detalle de cada PR vive en `prs/PR-N-{slug}/PR.md`. Prompts pre-cocidos para handoffs en `prompts/`.

## Criterio éxito sprint

- [ ] Criterio 1 testeable
- [ ] Criterio 2 testeable
- [ ] Cero refactor necesario en sprint siguiente
- [ ] Todos los PRs tienen `RESULT.md` escrito (loop cerrado)
- [ ] `current-state/{m}.md` actualizado con capabilities lineage de todos los shipped

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
2. Llenar `handoff.md` (decisiones, surface, agentes recomendados S{N+1}).
3. Marcar sprint `done` en este `sprint.md`.
4. Verificar todos los `prs/PR-*/RESULT.md` escritos (loop cerrado).
5. Si learnings impactan proceso global → append `../../../../process/process-learnings.md`.
6. Si último sprint del PI → escribir `retro.md` + mover PI completo a `pis/archive/`.
