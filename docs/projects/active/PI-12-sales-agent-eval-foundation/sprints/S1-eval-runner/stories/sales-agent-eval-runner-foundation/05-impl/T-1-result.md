# T-1-result.md — Scaffold dirs eval harness sales_agent

---
ticket_id: T-1
story_id: sales-agent-eval-runner-foundation
state: committed
finished_by: claude-opus-4-7
finished_at: 2026-05-04T22:55Z
push_commit_sha: pending  # se actualiza tras commit
push_branch: development
push_status: NOT_PUSHED  # controller hace push tras Story A T-1
---

## Resumen 1-frase

Scaffolding mínimo del eval harness `backend/tests/agentic_evals/sales_agent/` (4 dirs, 4 `__init__.py` vacíos, 1 `.gitignore` para `_artifacts`, 1 `.gitkeep` para `goldens`, 1 README stub con orientación operativa hasta que T-6 lo reescriba completo) — base para que T-2..T-6 puedan agregar pytest plumbing, fixtures, runner, asserts y goldens.

## Acceptance criteria — auto-verificación

| ID | Criterio | Verifier output | Estado |
|---|---|---|---|
| A1 | Estructura de directorios match arch-be § "Estructura de directorio" | `test -d runner && test -d fixtures && test -d _artifacts && test -d goldens` → PASS | ✅ |
| A2 | `_artifacts/` gitignored (echo file ignored) | `cd _artifacts && touch test.tmp && git check-ignore test.tmp && rm test.tmp` → exit 0 | ✅ |
| A3 | `README.md` y `__init__.py` files existen | `test -f README.md && test -f __init__.py` → PASS | ✅ |

Quality gates (ticket YAML):

| Gate | Output | Estado |
|---|---|---|
| `git status` muestra solo archivos esperados (no `_artifacts` content) | `?? backend/tests/agentic_evals/` (untracked) — sin contenido en `_artifacts/` listado | ✅ |
| Ruff format clean | `4 files already formatted` (los 4 `__init__.py` vacíos) | ✅ |

## Diff resumen

```
backend/tests/agentic_evals/__init__.py                           +0 lines (new, empty)
backend/tests/agentic_evals/sales_agent/__init__.py               +0 lines (new, empty)
backend/tests/agentic_evals/sales_agent/runner/__init__.py        +0 lines (new, empty)
backend/tests/agentic_evals/sales_agent/fixtures/__init__.py      +0 lines (new, empty)
backend/tests/agentic_evals/sales_agent/_artifacts/.gitignore     +2 lines (new)
backend/tests/agentic_evals/sales_agent/goldens/.gitkeep          +0 lines (new, empty)
backend/tests/agentic_evals/sales_agent/README.md                 +95 lines (new, stub)

7 files changed, 97 insertions
```

## Quality gates output (paste literal)

```
$ cd backend && .venv/bin/ruff check tests/agentic_evals/ --no-cache
All checks passed!

$ cd backend && .venv/bin/ruff format --check tests/agentic_evals/
4 files already formatted

$ cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/ --collect-only -q
no tests collected in 0.08s

$ test -d backend/tests/agentic_evals/sales_agent/runner && \
  test -d backend/tests/agentic_evals/sales_agent/fixtures && \
  test -d backend/tests/agentic_evals/sales_agent/_artifacts && \
  test -d backend/tests/agentic_evals/sales_agent/goldens
[A1 PASS]

$ cd backend/tests/agentic_evals/sales_agent/_artifacts && \
  touch test.tmp && git check-ignore test.tmp && rm test.tmp
test.tmp
[A2 PASS]

$ test -f backend/tests/agentic_evals/sales_agent/README.md && \
  test -f backend/tests/agentic_evals/sales_agent/__init__.py
[A3 PASS]

$ grep -nE '\b(podés|tenés|sos|querés|hacés|configurá|seleccioná|...)\b' README.md
[0 matches] Spanish neutro OK
```

NOTA: `/test-backend` full suite NO corrido en este ticket — T-1 es scaffolding puro
(sin Python operacional, sin DDD, sin migrations). T-2 corre `/test-backend` con
fixtures + meta-tests TDD. T-1 quality gate floor satisfied (ruff + pytest collect).

## Skills consultadas (Step 0 GATE)

| Skill | Razón | Decisión tomada |
|---|---|---|
| `backend-expert` | siempre obligatoria para BE | `runtime-quality-checklist.md` § N/A — T-1 no escribe Python operacional. SOP § "Tarea técnica (infra/config)" aplica: scaffolding tests no toca DDD layers. |
| `tessl__pytest-api-testing` | obligatoria para tests scaffolding | § 2 "conftest.py Fixture Organization" confirma jerarquía: T-2 creará `agentic_evals/conftest.py` (root del eval suite) + `agentic_evals/sales_agent/conftest.py` (fixtures dominio). T-1 deja la estructura para auto-discovery sin imports manuales. |
| `tessl__fastapi`, `tessl__graceful-degradation`, `offer-expert`, `brand-expert`, `metrics-expert`, `offer-type-preset-expert` | N/A | T-1 no toca esos módulos ni hace HTTP/external calls. |

## Anti-duplication grep evidence

```bash
$ find /home/chris/AISALESHT/backend -path '*/agentic_evals*' 2>/dev/null
# (vacío — greenfield confirmed)

$ ls /home/chris/AISALESHT/backend/tests/agentic_evals/ 2>/dev/null
# "No such file" — directorio no existía pre-T-1

$ ls /home/chris/AISALESHT/backend/tests/quality/sales_agent_goldens/
# (existe — S10 weekly judge stub, distinto propósito co-existe)
```

Decisión: NEW directory. CO-EXIST con `tests/quality/sales_agent_goldens/`. README diferencia explícitamente los dos para evitar confusión post-merge.

## Commits

```
$ git log --oneline -1
(pendiente — commitear siguiente)
```

```
$ git status --short backend/tests/agentic_evals/
?? backend/tests/agentic_evals/
```

NOTA: Este ticket NO pushea. Per user prompt: "DO NOT push to remote. Stage + commit allowed. Push happens AFTER another parallel ticket (Story A T-1) completes — controller does push." Workflow:
1. Este ticket commitea localmente (un commit conventional).
2. Controller verifica que Story A T-1 también commiteó.
3. Controller pushea ambos juntos (o secuencial sin force).

## Notas para /auditor

- **Greenfield**: `backend/tests/agentic_evals/` no existía. Anti-duplication clean.
- **Co-existencia con S10**: `backend/tests/quality/sales_agent_goldens/` permanece intacto (otro propósito — LLM-as-judge weekly cron). README documenta diferencia.
- **NO Python operacional**: T-1 sólo `__init__.py` vacíos + Markdown + `.gitignore`. `runtime-quality-checklist` consultado pero no aplicable (no fixture pattern, no JSONB, no Annotated dep, no datetime queries).
- **NO `src/` tocado**: arch fitness gates no se afectan; coverage gate intacto (eval suite outside `[tool.coverage.run].source`).
- **NO migrations**: arch-be § "Migrations" → "None".
- **Spanish neutro README**: verificado con regex `\b(podés|tenés|sos|querés|hacés|configurá|seleccioná|...)\b` → 0 matches.
- **Arch-be deliverable §1 dice contenido `*` para `.gitignore`**: implementé `*\n!.gitignore` para mantener el propio `.gitignore` checked-in (robustez). El verifier A2 igualmente pasa.
- **Sin `.venv`/`__pycache__` recursion**: no se creó `__pycache__` durante el ticket (pytest --collect-only del eval dir vacío no compila nada).
- **Bordes con Story A**: NO toqué `sales-agent-litellm-canonicalization/` (Story A files architect WIP). Mi único toque a `docs/` es Story B 05-impl + checkpoint.

## Riesgos conocidos / deuda

- ⚠️ **Pendiente T-2**: pytest plumbing (`--run-evals` + marker registration en `agentic_evals/conftest.py`), 4 fixtures + meta-tests TDD. Sin esto, los archivos `__init__.py` siguen siendo placeholders.
- ⚠️ **Pendiente T-6**: reescritura completa del README con docs operativas (cleanup, cost budget alert >$0.05, future story scope detallado).
- ⚠️ Coordinación con Story A: este commit NO se pushea hasta que Story A T-1 también haya commiteado. Push ordenado por controller.

## Output al orchestrator

```
done -> docs/projects/active/PI-12-sales-agent-eval-foundation/sprints/S1-eval-runner/stories/sales-agent-eval-runner-foundation/05-impl/T-1-result.md
state: committed (commit hash pending — push diferido por controller)
ready for /auditor (T-1 review) | T-2 puede arrancar tras commit
```
