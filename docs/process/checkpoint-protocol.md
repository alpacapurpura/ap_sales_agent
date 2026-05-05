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

## Crash recovery (R27 2026-05-05)

WSL2 hangs / computer crashes / network blip pueden interrumpir mid-pipeline.
Para que recovery sea trivial, cada agent + orchestrator MUST:

### Subagent contract (write artifacts EARLY)

Cada subagent escribe su output a disco apenas tiene contenido suficiente
— NO bufferea hasta el final. Pattern:

| Agent | Artifact | Write trigger |
|---|---|---|
| `context-builder` | `CONTEXT-BRIEF.md` | Skeleton at Step 0, fill Edits per Step. Crash mid-build → partial brief + audit log explica what's missing. |
| `context-validator` | `CONTEXT-BRIEF-validation.md` | Skeleton at Step 0, fill Edits per Step. |
| `gate-runner` | `gate-output.json` + `gate-logs/iter-N-*.log` | Raw log streamed via `tee` during execute. JSON written + verified post-condition (R22). |
| `builder-{be,fe,agentic}` | `T-{n}-impl-log.md` | Write skeleton at Step 1. Append per fase. `T-{n}-result.md` + commit hash AFTER push. |
| `auditor-{be,fe,agentic}` | `T-{n}-review.md` | Write skeleton early, fill cat scores incrementally. |

### Orchestrator contract (frequent commits + push)

`/dev-team` + `/auditor` orchestrator (Claude main session) MUST:

- Commit cada artefacto downstream apenas terminado (never batch ≥3 artefactos)
- `git push origin development` después de cada commit (no acumular >2 commits unpushed)
- Update `checkpoint.md` story-level con `last_artifact` + `last_modified` + `next_action`

Razón: crash recovery = `git pull || git fetch` + leer `checkpoint.md` =
contexto restaurado en <30 seconds. Sin push frecuente, perdés horas de
work si crash + machine no boots.

### Resume from crash workflow

Sesión nueva post-crash:

```bash
# 1. State estable
git status --short                                   # debe estar limpio
git log --oneline -5                                 # confirmar commits llegaron remoto

# 2. Identificar último ticket en progreso
ls docs/projects/active/                             # PIs activos
cat docs/projects/active/PI-N/checkpoint.md          # PI-level
ls docs/projects/active/PI-N/sprints/SN/stories/     # sprints + stories
cat docs/projects/active/PI-N/sprints/SN/stories/{id}/checkpoint.md

# 3. Verificar artefactos del ticket interrumpido
ls -lt docs/projects/active/PI-N/sprints/SN/stories/{id}/05-impl/  # builder outputs
ls -lt docs/projects/active/PI-N/sprints/SN/stories/{id}/06-audit/ # auditor outputs

# 4. Consultar gate-output.json freshness (R22 post-condition)
GATE=docs/projects/active/PI-N/sprints/SN/stories/{id}/gate-output.json
[ -f $GATE ] && jq '.overall.any_fail, .iter' $GATE

# 5. Re-run scoped tests para confirm state consistente
cd backend && .venv/bin/pytest <ticket scope tests> -v

# 6. Continue from `next_action` field of checkpoint.md
```

### Background tasks (Bash run_in_background)

Crash kills bg tasks. NUNCA confíes en bg task output sin re-verify:
- `pytest` corriendo en bg → re-run scoped suite post-crash
- `npm run test:e2e` corriendo en bg → re-run preflight + smoke

Mejor: usar `run_in_background: true` solo para tasks <5min wall-clock.
Tasks largas → use Monitor con persistent: true (sobrevive sesión, no
process crash).

### Tests state recovery

Si crash mid-pytest run, tests no escribieron coverage report ni quizá
.pytest_cache. Re-run desde scope mínimo (ticket-scoped) → escala scope
a downstream (R3) → escala scope a full suite si hay tiempo.

| Scope | Comando | Tiempo aprox |
|---|---|---|
| Ticket-scoped (verificar fix) | `pytest <ticket test paths>` | 10-30s |
| Downstream regression (R3) | `pytest <SSoT downstream targets>` | 1-3min |
| Module-scoped | `pytest tests/modules/{m}/` | 2-5min |
| Full backend | `pytest -x -q --tb=short` | 8-15min |

Empezar siempre por ticket-scoped. Solo escalas si red flag (memory
test pollution, unrelated cascade fail).

Origen R27: PI-12 T-1.bis 2026-05-05 — WSL2 crash mid-pytest pero commits
ya pushed → state recovery <2min via git log + scoped re-run. Lección:
commits pequeños + push frecuente = zero pérdida.
