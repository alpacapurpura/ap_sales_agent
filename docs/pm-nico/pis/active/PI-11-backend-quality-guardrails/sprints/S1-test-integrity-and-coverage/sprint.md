# Sprint S1 — Test Integrity & Coverage P0

> Sprint ID: S1-test-integrity-and-coverage
> PI padre: PI-11-backend-quality-guardrails
> Estado: **not-started**
> Owner PM: /pm

## Objetivo

Restaurar confianza en el CI backend: **0 tests fallidos** + cobertura P0 (`crm`, `scheduling`) sube a ≥75%.

## Pre-handoff

- N/A (primer sprint del PI).

## Plan PRs

| PR | Folder | Descripción | Agentes/skills | Esfuerzo | Estado |
|---|---|---|---|---|---|
| PR-1 | `prs/PR-1-fix-broken-tests-and-arch-snapshots/` | Fix 10+ tests fallidos + arch snapshots + imports DDD + outbox flags | `nicolify-backend` + `nicolify-agentic` (paralelo) → auditores cruzados | L | not-started |
| PR-2 | `prs/PR-2-coverage-p0-modules/` | Cobertura ≥75% en `crm` y `scheduling` (servicios + repos + DTOs sin test) | `nicolify-backend` → `nicolify-backend-auditor` | L | not-started |

Detalle de cada PR vive en `prs/PR-*/PR.md`.

## Criterio éxito sprint

- [ ] `pytest` pasa 100% (0 failed, 0 deselected obligatorios).
- [ ] Arch fitness 78/78 verde.
- [ ] Cobertura `crm` ≥75%, `scheduling` ≥75%.
- [ ] Todos los PRs tienen `RESULT.md`.
- [ ] `/test-backend` verde end-to-end.

## Out of scope

| Item | Razón | Sprint destino |
|---|---|---|
| Cobertura `sales_agent`/`copilot` ≥80% | Scope limitado a P0 primero | S2 |
| Cobertura `shared/links/ports` | Transversal, mejor en batch S2 | S2 |
| Tests de integración con DB real (verify/integration markers) | Requieren Postgres up; son gate separado | No programado (ya existen, solo requieren env) |

## Riesgos

| Riesgo | Mitigación | Owner |
|---|---|---|
| PR-1 toca business + agentic → conflictos de surface | Builders paralelos por surface; paths excluyentes en prompts | PM |
| Fix de test descubre bug real de código (no solo test roto) | Escalate a PM; si es crítico → mini-PI hotfix separado | PM |

## Cierre

Al cerrar:
1. Llenar `learnings.md`.
2. Llenar `handoff.md`.
3. Marcar sprint `done`.
4. Verificar `RESULT.md` de PR-1 y PR-2.
