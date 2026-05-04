# Product — SSoT vivo Nicolify

**Qué es:** estado actual del producto. Auto-actualizable. Cada PR mergeado modifica algo aquí.
**Qué NO es:** historial de proyectos (eso vive en `../projects/`). Documentos técnicos (esos viven en `../domains/`).

## Mapa

| Sub-dir | Contenido | Owner |
|---|---|---|
| `vision.md` · `roadmap.md` · `glossary.md` | North-stars + plan + términos | `/pm` |
| `modules/{module}.md` | Estado funcional por módulo. 1 archivo por módulo. | `/pm` mantiene; builders no tocan |
| `story-map/{backbone,walking-skeleton}.md` | User Story Map (Patton). Backbone = lifecycle horizontal. | `/pm` |
| `capabilities/{module}/{cap}.yaml` | Índice de stories agrupadas por capability. | auto-gen + `/pm` cura |
| `stories/{module}/{story-id}.yaml` | **SSoT atómico.** 1 story = 1 archivo. Tipos: ui/agentic/service. | `/po` redacta; `/pm` ratifica al merge |
| `opportunities/` | Discovery validado (JTBD claro, no implementado aún) | `/pm` + Chris |
| `ideas/` | Ideas raw (pre-validación) | Chris + `/pm` |

## Reglas de oro

- **NO duplicar info entre módulos**. Cross-module → frontmatter link.
- **Story YAML = SSoT** del comportamiento. Si el código diverge → bug, no excepción.
- **Capability** agrupa stories pero NO contiene scenarios. Los scenarios viven en story.
- **Status por story**: `planned | in-progress | live | deprecated`.
- **Status por capability** = derivado de stories: `live` si todas live, `in-progress` si alguna in-progress, `planned` si todas planned.

## Lectura para agents

`/po` lee: stories del módulo + capability index + módulo.md.
`/architect` lee: igual + domains/ técnico.
`/dev-team` lee: el ticket del sprint, NO toca product/ directamente (lectura referencia).
`/pm` lee: TODO. Es owner.

## Migración desde `pm-nico/`

`pm-nico/` queda intact. Migración gradual:
- `current-state/{m}.md` → `modules/{m}.md` (Phase 6 plan)
- `story-map/` ya replicado aquí
- `pis/active/` queda donde está; nuevos PIs en `../projects/active/`
- `opportunities/`+`ideas/` re-located cuando Chris pida

Ver `../process/migration-plan.md`.
