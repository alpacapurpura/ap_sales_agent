# Checkpoint Protocol — Resume sessions

> Cada nivel (PI / sprint / story) tiene `checkpoint.md` propio.
> Cualquier sesión nueva lee checkpoints PRIMERO antes de hacer nada.

## Por qué existe

Multi-instancia Claude Code (Chris) + sesiones que mueren mid-build + 6+ PIs activos = perder contexto es caro.

`checkpoint.md` resuelve:
1. Qué sesión está activa en este nivel
2. Qué fue lo último escrito
3. Qué se debe hacer next
4. Si hay bloqueos / si es seguro tocar

## Estructura

Ver `../specs/templates/checkpoint-template.md`.

Campos críticos:
- `phase` — fase actual del nivel
- `status` — pending | in-progress | done | blocked
- `last_artifact` — último archivo escrito
- `last_modified` — timestamp
- `next_action` — qué hace la próxima sesión / agent
- `parallel_safe` — ¿otra sesión puede tocar?
- `audit_iterations` — para cap (story-level)

## Niveles + ubicación

```
docs/projects/active/PI-12-{theme}/
├── checkpoint.md                          ← PI-level
└── sprints/S1-{slug}/
    ├── checkpoint.md                       ← sprint-level
    └── stories/{story-id}/
        └── checkpoint.md                   ← story-level
```

## Reglas de update

| Quién toca | Cuándo updatea |
|---|---|
| `/pm` | Crear PI/sprint/story. Cerrar phases. Aplicar merge. |
| `/po` | Tras aprobar `01-spec.md`. |
| `/ux-{ui,agentico}` | Tras escribir `02-design-*.md`. |
| `/architect` | Tras escribir `04-tickets.yaml`. |
| `/dev-team` | Por ticket: cambio state. |
| `/auditor` | Tras escribir `T-{n}-review.md` y `REVIEW-final.md`. |
| Hook `post-edit-checkpoint.sh` | Auto: `last_artifact` + `last_modified`. |

## Resume protocol — paso a paso

Cuando cualquier agent/sesión arranca o retoma:

```bash
# 1. Identificar trabajo activo
ls docs/projects/active/                   # PIs activos
cat docs/projects/active/PI-{N}/checkpoint.md  # PI-level state

# 2. Identificar sprint activo
ls docs/projects/active/PI-{N}/sprints/    # sprints del PI
cat docs/projects/active/PI-{N}/sprints/S{n}/checkpoint.md

# 3. Identificar story activa
ls docs/projects/active/PI-{N}/sprints/S{n}/stories/
cat docs/projects/active/PI-{N}/sprints/S{n}/stories/{id}/checkpoint.md

# 4. Verificar parallel_safe
# si parallel_safe=false → otra sesión está activa, NO TOCAR sin coordinar

# 5. Verificar blocked_reason
# si blocked → escala a Chris, no proceder

# 6. Ejecutar next_action
# leer artefacto previo (last_artifact) → producir siguiente
```

## Estados conflict

- 2 sesiones tocan misma story → `parallel_safe=false` + última sesión espera
- Si `parallel_safe=true` y dos artefactos diferentes (story tiene varios archivos), OK paralelo

## Anti-patterns

- ❌ Empezar trabajo sin leer checkpoint
- ❌ Saltarse phases (ej. /architect sin spec ratificada)
- ❌ No actualizar checkpoint tras escribir artefacto
- ❌ Ignorar `blocked_reason`
