---
sprint_id: S3
slug: voice-fidelity-gate
pi: PI-12
started_at: 2026-05-26
target_end: 2026-06-01
status: planning                                  # planning | active | wrap-up | done
checkpoint: ./checkpoint.md
---

# Sprint S3 — Voice Fidelity Gate

## Goal del sprint

Al final del sprint: el grader de voice fidelity calibrado (vs juicio humano ±0.15) corre runtime contra los 12 goldens, devuelve un score 0-1 por output, y CI bloquea PRs que toquen `modules/sales_agent/` con score agregado <0.7.

## Stories incluidas

| Story ID | Type | Module | Estimate | Status | Tickets count (estimado) |
|---|---|---|---|---|---|
| `sales-agent-voice-fidelity-grader-runtime` | agentic | sales_agent | 3d | planning | 2 (T-1 grader + T-2 calibration) |
| `sales-agent-voice-fidelity-ci-gate` | service | sales_agent | 2d | planning | 1-2 |

**Total estimado:** 5d

## Tickets por owner pool (estimado pre-architect)

| Owner pool | Stories | Estimate |
|---|---|---|
| claude-opus (agentic, LLM-as-judge prompt design) | voice-fidelity-grader-runtime | 3d |
| claude-opus (CI wiring, env var, gate logic) | voice-fidelity-ci-gate | 2d |

## Dependencias entre stories

```
[S2] sales-agent-goldens-3-tenants-dataset
[S2] sales-agent-personas-instrumented-runtime
  ↓ (necesita goldens y personas para calibrar)
sales-agent-voice-fidelity-grader-runtime
  ↓ (necesita grader devolviendo scores)
sales-agent-voice-fidelity-ci-gate
```

## Orden ejecución sugerido

1. `sales-agent-voice-fidelity-grader-runtime` (claude-opus)
2. `sales-agent-voice-fidelity-ci-gate` (claude-opus)

## Cierre del sprint

Criterios:
- [ ] `grade_voice_fidelity(output, tenant_voice_profile) → float` operativo
- [ ] Calibración documentada: 10 outputs labeled manualmente Chris vs grader → variance ≤ 0.15
- [ ] Cache de resultados por `(output_hash, tenant_id)` evita rejecutar judge en cada CI
- [ ] Env var `SALES_AGENT_VOICE_FIDELITY_THRESHOLD=0.7` enforced
- [ ] CI gate corre en `/test-backend` o nuevo `/test-agentic-evals`
- [ ] PR sintético con voice drift simulado → bloqueado correctamente
- [ ] Modo "warning only" 1 semana antes de hard-block (rollout suave) — documentado en `process/learnings.md`
- [ ] `checkpoint.md` sprint marcado `done`
