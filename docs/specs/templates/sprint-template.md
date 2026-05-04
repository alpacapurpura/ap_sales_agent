# sprint.md — Template (Sprint dentro de PI)

> Owner: `/pm`. Vive en `docs/projects/active/PI-N/sprints/SN-{slug}/sprint.md`.

---
sprint_id: SN
slug: SLUG
pi: PI-N
started_at: 2026-05-04
target_end: 2026-05-18
status: planning                                  # planning | active | wrap-up | done
checkpoint: ./checkpoint.md
---

## Goal del sprint

[1 frase: qué outcome user-observable se alcanza al final del sprint.]

## Stories incluidas

| Story ID | Type | Module | Status | Tickets count |
|---|---|---|---|---|
| `copilot-brand-audit` | agentic | copilot | planning | 3 (T-1 BE, T-2 agentic, T-3 FE) |
| `brand-completeness-score` | service | brand | planning | 1 |

## Tickets por owner pool

| Owner pool | Tickets | Estimate |
|---|---|---|
| qwen-opencode | T-1, T-3, T-4 | 6h |
| claude-opus (agentic) | T-2 | 3h |
| claude-sonnet | (vacío) | — |

## Dependencias entre stories

```
brand-completeness-score
  ↓ (capability requerida)
copilot-brand-audit
```

## Cierre del sprint

Criterios:
- [ ] Todas las stories `audit-passed` o movidas a próximo sprint
- [ ] Métricas: pass^k stories agentic >= threshold, coverage no bajó
- [ ] `checkpoint.md` sprint marcado `done`
- [ ] Retrospective brief al final
