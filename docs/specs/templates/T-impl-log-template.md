# T-{n}-impl-log.md — Template (developer bitácora viva)

> Owner: developer (qwen | opus | sonnet) ASIGNADO al ticket.
> Mantenelo VIVO durante el build (cada paso significativo). NO al final.
> Si la sesión muere, este es el archivo que lee la siguiente sesión para retomar.

---
ticket_id: T-1
story_id: STORY_ID
state: building                                  # ver process/ticket-states.md
assigned_to: qwen-opencode                       # qwen-opencode | claude-opus-4-7 | claude-sonnet-4-6
started_at: 2026-05-04T16:00Z
last_update: 2026-05-04T16:23Z
current_step: "Implementando service layer"
blocker: null                                    # si hay → state = blocked
---

## Plan inicial (antes tocar código)

1. [Paso 1: leer 01-spec, 03-arch, archivos a tocar]
2. [Paso 2: escribir test RED para A1 (happy path)]
3. [Paso 3: implementar mínimo para GREEN A1]
4. [Paso 4: test RED A2 (negative), implementar]
5. [Paso 5: ...]

## Bitácora paso-a-paso

### 16:00 — Setup
- Leí `01-spec.md`, `03-arch-be.md`, `T-1-handoff.md`.
- Cargué skill `backend-expert`.
- Verifiqué entorno: `cd backend && .venv/bin/pytest --collect-only tests/modules/{m}/` → OK.

### 16:05 — RED test happy path (A1)
- Creé `tests/modules/{m}/test_{name}_endpoint.py::test_happy_path`.
- Asserts: status=200, response shape, DB state.
- Run: pytest → falla (esperado, endpoint no existe). ✅ RED.

### 16:12 — GREEN A1: endpoint stub
- Agregué DTO `RequestDTO` + `ResponseDTO` en `dtos.py`.
- Agregué `@router.post(...)` en `routes.py`.
- Stub service.
- Run: pytest → pasa A1. ✅ GREEN.

### 16:23 — RED test tenant isolation (A2)
- Test: user A header T1 → recurso de T2 → debe 403.
- Run: falla (no hay filter). ✅ RED.

### [continuar...]

## Decisiones tomadas durante el build

- **2026-05-04 16:18** — Usé `idempotency-key` header en vez de natural key. Razón: payloads con timestamp variable.
- ...

## Bloqueos / Issues

- ❌ **2026-05-04 16:30** — `make extraction-contract` falla porque metric_catalog no tiene la nueva métrica.
  - Esperado vs actual: ...
  - Resolución: agregué entry en metric_catalog antes de re-correr.

## Tests corridos

| Cuándo | Comando | Resultado |
|---|---|---|
| 16:23 | `pytest tests/modules/{m}/ -x -q` | 3 pass / 1 fail (A2 RED esperado) |
| 16:35 | `pytest tests/modules/{m}/ -x -q` | 4 pass ✅ |
| 16:40 | `/test-backend` | gates verde, coverage 47% (>= 43%) |

## Commits

| SHA | Mensaje | Files |
|---|---|---|
| `abc1234` | `feat({m}): endpoint POST /{action}` | `dtos.py`, `routes.py`, `service.py`, tests |
| `def5678` | `feat({m}): tenant isolation in service` | `service.py`, test |

## Quality gates final (antes push)

```
$ /test-backend
[OK] ruff check
[OK] ruff format
[OK] arch fitness
[OK] pytest 247 pass / 0 fail
[OK] coverage 48%
[OK] mypy strict
[OK] migration idempotency
```

## Estado al cerrar

- ticket state: `tests-passing` → push imminente
- Próximo paso: `git push origin development` y mover state a `pushed`

## Si bloqueas

Si encontraste un bloqueo que NO podés resolver:
1. Estado ticket → `blocked` en `04-tickets.yaml`
2. Documentá razón en `blocker:` arriba
3. Salida al orchestrator: `blocked -> ver T-{n}-impl-log.md`
