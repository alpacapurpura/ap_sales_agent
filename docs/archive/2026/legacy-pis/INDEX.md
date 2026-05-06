# Projects — Iniciativas en curso

**Qué es:** PIs activos + sprints + stories en ejecución. **Migraciones** que cuando mergean modifican `../product/`.
**Qué NO es:** estado del producto (vive en `../product/`).

## Estructura

```
projects/
├── active/PI-{N}-{theme}/
│   ├── PI.md                          # alcance + outcome esperado
│   ├── decisions.md                   # decisions log
│   ├── checkpoint.md                  # ⭐ resume protocol PI-level
│   └── sprints/S{N}-{slug}/
│       ├── sprint.md                  # alcance sprint
│       ├── checkpoint.md              # ⭐ resume protocol sprint-level
│       └── stories/{story-id}/
│           ├── checkpoint.md          # ⭐ resume protocol story-level
│           ├── 00-story.md            # PM: qué + porqué + JTBD
│           ├── 01-spec.md             # PO: gherkin AI-resistant
│           ├── 02-design-ui.md        # /ux-ui (si ui-story o mixed)
│           ├── 02-design-agentic.md   # /ux-agentico (si agentic-story o mixed)
│           ├── 03-arch-be.md          # /architect-be
│           ├── 03-arch-fe.md          # /architect-fe
│           ├── 03-arch-agentic.md     # /architect-agentic
│           ├── 04-tickets.yaml        # pila tickets ordenada
│           ├── 05-impl/T-{n}-{handoff,impl-log,result}.md
│           ├── 06-audit/T-{n}-review.md + REVIEW-final.md
│           └── 07-merge.md            # diff aplicado a product/
└── archive/PI-{N}-{theme}/            # PI cerrado, read-only
```

## Lifecycle PI

1. `/pm` crea folder PI con `PI.md` + `checkpoint.md`
2. Sprints internos: `S1`, `S2`, ...
3. Stories internas a sprint: 1 folder por story con artefactos versionados
4. Story passes audit → `07-merge.md` aplica diff a `../product/`
5. Sprint completa → checkpoint sprint = done
6. PI completa → mover a `archive/`

## Resume protocol

Cualquier sesión nueva:
1. `cat docs/projects/active/*/checkpoint.md` → ver PIs activos
2. `cat ./sprints/*/checkpoint.md` → ver sprint activo
3. `cat ./stories/*/checkpoint.md` → ver story activa + `phase` + `next_action`
4. Continuar desde `next_action`

## Reglas

- Cada artefacto tiene template en `../specs/templates/`.
- Los archivos tienen prefijo numérico (`00-`, `01-`, `02-`, ...) para forzar orden lectura.
- `checkpoint.md` único en cada nivel — no duplicar.
- NO editar artefactos de stories cerradas (post-merge). Agregar nuevo PR/sprint.

## In-flight legacy (pm-nico/pis/active/)

PI-3, PI-4, PI-5, PI-9, PI-10, PI-11 cierran en `pm-nico/pis/active/`. Cuando mergeen, `/pm` opcional translatea sus learnings a `../product/`. Después de cierre PI legacy → mover manual a `pm-nico/pis/archive/` por convención vieja.
