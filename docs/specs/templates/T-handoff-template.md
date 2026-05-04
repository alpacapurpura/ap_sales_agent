# T-{n}-handoff.md — Template (input al developer)

> Owner: `/architect`. Lo que el dev (qwen|opus|sonnet) lee antes de codear.
> Self-contained — el dev NO debe leer otros archivos del story salvo los explícitos.

---
ticket_id: T-1
story_id: STORY_ID
sprint: SN-SLUG
pi: PI-N
type: backend                                    # backend | frontend | agentic | infra | migration
surface: BE
priority: 1
estimate_hours: 2

# ── Owner eligibility (CRITICAL) ──────────────
owner_eligibility:
  qwen_opencode: true                            # acepta opencode/qwen
  claude_sonnet: true                            # acepta Claude Code Sonnet
  claude_opus_required: false                    # FORZAR Opus 4.7 (true para AGENTIC)
assigned_to: null                                # rellena /dev-team al tomar
assigned_at: null
---

## Contexto en 5 frases

[1-2 párrafos cortos: qué hace el módulo, dónde encaja este ticket, qué outcome user-observable produce.]

## Inputs obligatorios (lectura previa)

- `01-spec.md` — acceptance criteria de la story (sólo scenarios relevantes a este ticket están listados abajo)
- `03-arch-{surface}.md` — diseño técnico de la capa
- Story YAML: `../../../../../product/stories/{module}/{story-id}.yaml` (sólo header + scenarios listados abajo)

**Reglas/skills cargar:**
- `.claude/rules/{rules-relevantes}.md`
- Tessl skills: `[lista]`
- Domain skills: `[backend-expert | brand-expert | ...]`

## Scope de ESTE ticket

### Hacer:
- [Deliverable 1 con path exacto]
- [Deliverable 2]

### NO hacer (out of scope):
- [Lo que NO toca este ticket — lo cubre T-X]

### Files que vas a tocar:
- `backend/src/modules/{m}/api/dtos.py` (modificar)
- `backend/src/modules/{m}/api/routes.py` (modificar — agregar endpoint)
- `backend/src/modules/{m}/application/services/{name}_service.py` (crear)
- `backend/src/modules/{m}/infrastructure/repositories/{name}_repo.py` (crear)
- `alembic/versions/XXXX_{description}.py` (crear)
- `backend/tests/modules/{m}/test_{name}_service.py` (crear)
- `backend/tests/modules/{m}/test_{name}_endpoint.py` (crear)

### Files que NO debes tocar:
- `frontend/src/**` (es ticket FE separado)
- `backend/src/modules/{otro_modulo}/**` (cross-module via puerto)

## Acceptance criteria (verificables)

| ID | Criterio | Verificador automático |
|---|---|---|
| A1 | POST /api/v1/{path} con payload válido → 200 | `pytest tests/modules/{m}/test_{name}_endpoint.py::test_happy_path` |
| A2 | Cross-tenant request → 403 | `pytest ... ::test_tenant_isolation` |
| A3 | Migration idempotente | `make verify-migration-idempotency` |
| A4 | Coverage del módulo no baja | `/test-backend` gate coverage |
| A5 | Spanish neutro en todos los strings user-facing | grep `voseo` patterns |

## Quality gates obligatorios (correr antes push)

```bash
cd backend
.venv/bin/ruff check src/modules/{m}/ tests/modules/{m}/
.venv/bin/ruff format --check src/modules/{m}/ tests/modules/{m}/
.venv/bin/pytest tests/architecture/ -v --override-ini="addopts="
.venv/bin/pytest tests/modules/{m}/ --cov=src/modules/{m} --cov-report=term-missing -x -q
docker exec visionarias_brain_dev alembic upgrade head
```

O atajo: `/test-backend` slash-skill.

## Conventions a respetar

- DDD inside-out: domain → infra → application → api
- SQLA 2.0 async. Cada query filtra `tenant_id`.
- DTOs Pydantic v2 con `model_config = ConfigDict(...)`.
- Errors explícitos (excepciones nombradas, no `None`).
- No `print` (usa `structlog`).
- No `datetime.utcnow()` (usa `utc_now()` shared).

## TDD obligatorio

1. RED: escribe test que falla (cubre acceptance criteria)
2. GREEN: implementa mínimo para pasar
3. REFACTOR: limpia + extrae helpers

NO escribas código sin test asociado.

## Resume protocol

Si la sesión muere mid-build:
1. `cat docs/projects/active/PI-N/sprints/SN/stories/{story-id}/05-impl/T-{n}-impl-log.md` ← bitácora viva
2. `git status` → ver work-in-progress
3. Continuar desde último checkpoint registrado en impl-log
4. Re-correr quality gates antes de declarar done

## Output esperado

Tras terminar, escribir `T-{n}-result.md` con:
- Diff resumen (archivos creados/modificados)
- Output de quality gates (paste)
- Commit SHA
- Estado final del ticket: `pushed`

Y respuesta al orchestrator (single line):
```
done -> docs/projects/active/PI-N/sprints/SN/stories/{story-id}/05-impl/T-{n}-result.md
```
