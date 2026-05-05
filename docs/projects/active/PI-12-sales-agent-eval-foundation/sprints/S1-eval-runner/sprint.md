---
sprint_id: S1
slug: eval-runner
pi: PI-12
started_at: 2026-05-04
target_end: 2026-05-18
status: planning                                  # planning | active | wrap-up | done
checkpoint: ./checkpoint.md
---

# Sprint S1 — Eval Runner Foundation

## Goal del sprint

Al final del sprint: existe `backend/tests/agentic_evals/sales_agent/`, dev puede correr el runner manualmente, cada golden corre 3 trials con pass^k tracking, runs >$5 son abortados, y el reporte de cost por trial es confiable (deepseek pricing fix aplicado).

## Stories incluidas

| Story ID | Type | Module | Estimate | Status | Tickets count (estimado) |
|---|---|---|---|---|---|
| `sales-agent-eval-runner-foundation` | service | sales_agent | 3d | planning | 2 (T-1 infra + T-2 smoke test) |
| `sales-agent-eval-pass-k-tracking` | service | sales_agent | 2d | planning | 1 |
| `sales-agent-eval-cost-budget-cap` | service | sales_agent | 1d | planning | 1 |
| `sales-agent-cost-tracking-deepseek-fix` | service | shared (cost) | 2d | planning | 1-2 (fix + repair migration) |

**Total estimado:** 8d

## Tickets por owner pool (estimado pre-architect)

| Owner pool | Stories | Estimate |
|---|---|---|
| claude-opus (eval infra agentic-adjacent) | runner-foundation, pass-k-tracking, budget-cap | 6d |
| qwen-opencode (BE non-agentic patch) | deepseek-fix | 2d |

## Dependencias entre stories

```
sales-agent-eval-runner-foundation
  ├──> sales-agent-eval-pass-k-tracking (necesita runner para iterar trials)
  └──> sales-agent-eval-cost-budget-cap (necesita runner para hookear cost recorder)

sales-agent-cost-tracking-deepseek-fix
  (independiente — puede ejecutarse en paralelo con cualquiera arriba)
```

## Orden ejecución sugerido

1. `sales-agent-cost-tracking-deepseek-fix` (qwen-opencode, paralelizable, desbloquea reporting confiable durante el resto del sprint)
2. `sales-agent-eval-runner-foundation` (claude-opus, bloquea 2 y 3)
3. `sales-agent-eval-pass-k-tracking` (claude-opus)
4. `sales-agent-eval-cost-budget-cap` (claude-opus)

## Cierre del sprint

Criterios:
- [ ] 4 stories `audit-passed` o movidas a próximo sprint
- [ ] `backend/tests/agentic_evals/sales_agent/` existe y tiene al menos 1 smoke golden corriendo verde
- [ ] `pass_k_last_run` reportado por golden + agregado por suite
- [ ] Run > $5 USD aborta con error claro
- [ ] `cost_usd != 0` para 100% trials con provider=deepseek (verificar contra `copilot_llm_call` table)
- [ ] `checkpoint.md` sprint marcado `done`
- [ ] Retrospective brief al final
