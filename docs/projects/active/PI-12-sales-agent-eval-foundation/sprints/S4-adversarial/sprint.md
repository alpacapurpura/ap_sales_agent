---
sprint_id: S4
slug: adversarial
pi: PI-12
started_at: 2026-06-02
target_end: 2026-06-08
status: planning                                  # planning | active | wrap-up | done
checkpoint: ./checkpoint.md
---

# Sprint S4 — Adversarial Coverage

## Goal del sprint

Al final del sprint: el eval suite tiene 8-10 goldens adversariales (jailbreak, prompt injection, hostile persona, overpromise coercion) instrumentados con threshold pass^3=1.0 (cero tolerancia a leaks de system prompt o promesas fuera de oferta).

## Stories incluidas

| Story ID | Type | Module | Estimate | Status | Tickets count (estimado) |
|---|---|---|---|---|---|
| `sales-agent-adversarial-jailbreak-suite` | agentic | sales_agent | 3d | planning | 2 (T-1 goldens curate + T-2 rubric wiring) |

**Total estimado:** 3d

## Tickets por owner pool (estimado pre-architect)

| Owner pool | Stories | Estimate |
|---|---|---|
| claude-opus (agentic, adversarial pattern design) + Chris (ratifica goldens) | adversarial-jailbreak-suite | 3d |

## Dependencias entre stories

```
[S3] sales-agent-voice-fidelity-grader-runtime
[S3] sales-agent-voice-fidelity-ci-gate
  ↓ (adversarial usa mismos rubrics + gate)
sales-agent-adversarial-jailbreak-suite
```

## Orden ejecución sugerido

1. `sales-agent-adversarial-jailbreak-suite` (única story del sprint)

## Cierre del sprint

Criterios:
- [ ] 8-10 goldens adversariales en `backend/tests/agentic_evals/sales_agent/goldens/adversarial/`
- [ ] Categorías cubiertas: jailbreak (3), prompt injection (2), hostile persona (2), overpromise coercion (2)
- [ ] Rubrics aplicados por golden: `no-hallucination`, `no-overpromise`, `voice-fidelity`
- [ ] Threshold `pass^3 = 1.0` enforced (cualquier leak = fail PR)
- [ ] CI gate ya enforced (Story 8 S3) cubre adversarial automático
- [ ] `process/learnings.md` documenta patterns adversariales descubiertos para futuros agents
- [ ] `checkpoint.md` sprint marcado `done`
