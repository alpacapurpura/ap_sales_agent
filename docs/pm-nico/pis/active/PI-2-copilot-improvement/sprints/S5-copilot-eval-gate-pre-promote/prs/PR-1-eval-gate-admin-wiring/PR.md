# PR-1-eval-gate-admin-wiring

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-1-eval-gate-admin-wiring |
| Sprint padre | S5-copilot-eval-gate-pre-promote |
| PI padre | PI-2-copilot-improvement |
| Estado | ready (depends S4 shipped) |
| Tipo | infra (eval gate integration admin UI + CI) |
| Esfuerzo | M-L (~12 archivos) |
| Owner PM | /pm |

## Problema

Post-S4, swap modelo es hot-swap admin UI. Pero NO hay gate de calidad. Riesgo: admin activa modelo broken → all turns fail / regresión silenciosa. Costo escala 1000+ tenants × N requests × calidad mala = catastrófico.

JTBD Chris: "Antes de cambiar a un modelo, quiero estar seguro de que no rompe lo que ya funciona."

## Outcome esperado

- Admin UI `/admin/llm-models` botón "Test candidate" disponible per role/model.
- Click → eval gate runner ejecuta inline async (50 goldens) + score reportado en UI.
- Botón "Promote to active" bloqueado si score <0.95 (per-role threshold configurable).
- CI integration: PR commit que toca `llm_role_binding` table o `.env AI_MODEL_*` → marker `@pytest.mark.eval_gate` corre + bloque merge si fail.
- Audit trail: cada eval gate run → row en `llm_eval_gate_runs` (immutable).

## Walking skeleton

1. **Eval gate UI integration** `admin/pages/llm_models.py`:
   - Button "Test candidate" → spawn async task `LLMEvalRunner.run_for_role(role, candidate_model)`
   - Progress indicator + score display
   - Block "Promote" button if `score < threshold[role]` (default 0.95)
2. **`LLMEvalRunner` async orchestrator**:
   - Wraps existing `evals/runner.py` (S2 PR-3 shipped)
   - Concurrent goldens execution (50 parallel async client calls)
   - Aggregate score + per-golden detail
3. **Migration `119_llm_eval_gate_runs`**: tabla audit `(role, candidate_model, baseline_model, score, passed, threshold, ran_at, ran_by)`.
4. **CI integration** `.github/workflows/llm-eval-gate.yml`:
   - Trigger: PR diff toca `llm_role_binding` migration data o `.env` AI_MODEL_*
   - Job: runs `pytest -m eval_gate` con threshold configurable
   - Block merge si fail
5. **Per-role threshold config**: tabla `llm_eval_gate_threshold (role PRIMARY KEY, threshold NUMERIC)` con seed (NANO=0.95, FAST=0.95, REASONING=0.93, AGENT=0.95, VISION=0.90, EMBEDDING=0.95). Admin UI editable.

## Existing systems audit

```bash
grep -rn "evals\|eval_gate" backend/src/
find backend/src/modules/copilot/evals/ -name "*.py"
ls backend/tests/evals/
```

**Sistemas:**
- ✅ Sistema A (EXTEND): `backend/src/modules/copilot/evals/{runner, scorers, goldens}` shipped S2 PR-3 (mantenido en S3 cleanup) — wrap async + UI integration.
- ✅ Sistema B (EXTEND admin Streamlit): `admin/pages/llm_models.py` shipped S4 PR-1 — agregar buttons + progress.
- 🆕 Sistema C (NEW DB layer): `llm_eval_gate_runs` audit + `llm_eval_gate_threshold` config table. Justificación: audit trail compliance + per-role threshold.

## Surface impactada

| Tipo | Path | Cambio |
|---|---|---|
| Migration | `alembic/versions/119_llm_eval_gate.py` | NEW idempotente |
| BE service | `src/modules/copilot/evals/runner_async.py` | NEW (wrap existing runner) |
| Admin extend | `admin/pages/llm_models.py` | EXTEND buttons "Test candidate" + "Promote" gated |
| Admin new | `admin/pages/llm_eval_thresholds.py` | NEW per-role threshold CRUD |
| CI | `.github/workflows/llm-eval-gate.yml` | NEW workflow |
| Tests | `tests/modules/copilot/evals/test_runner_async.py` | NEW |
| Tests | `tests/admin/test_llm_models_eval_gate.py` | NEW |
| current-state | `current-state/copilot.md` | append cap "Eval gate pre-promote enforced" |

## Tests requeridos

- Async runner: 50 goldens parallel < 5min
- Score aggregation correct vs sync runner reference
- Promote button gated correctly (score 0.96 → enabled, 0.85 → disabled)
- CI workflow: PR diff con .env AI_MODEL_NANO change → workflow runs → fail bloquea merge
- Audit table: cada run grabado correctamente

## Aceptación

- [ ] Tests verde
- [ ] Manual: admin UI workflow completo (test → score → promote/block)
- [ ] CI workflow tested vía PR de prueba (toca .env AI_MODEL_NANO → eval gate runs)
- [ ] current-state updated
- [ ] Migration idempotente

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Eval gate inline lento → admin UX poor | Async background + progress indicator + ETA |
| Goldens stale (calidad models cambia) | Admin UI "Refresh goldens from prod" feature S5+ futuro |
| Per-role threshold demasiado estricto/laxo | Configurable + audit log when admin updates threshold |
| CI workflow falla por API key DEEPSEEK_API_KEY ausente en CI | Repo secret + skip if missing en CI test (run only on tagged PRs) |
