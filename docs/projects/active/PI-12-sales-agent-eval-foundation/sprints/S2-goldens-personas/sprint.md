---
sprint_id: S2
slug: goldens-personas
pi: PI-12
started_at: 2026-05-19
target_end: 2026-05-25
status: planning                                  # planning | active | wrap-up | done
checkpoint: ./checkpoint.md
---

# Sprint S2 — Goldens & Personas

## Goal del sprint

Al final del sprint: el eval runner tiene 12 goldens reales checked-in (3 tenants × 4 escenarios) con PII anonymizada, y las 5 personas declaradas en `docs/specs/personas/` están instrumentadas como simuladores activos en el runner.

## Stories incluidas

| Story ID | Type | Module | Estimate | Status | Tickets count (estimado) |
|---|---|---|---|---|---|
| `sales-agent-goldens-3-tenants-dataset` | service | sales_agent | 5d | planning | 3 (T-1 extract script + T-2 sanitize + T-3 curate manual) |
| `sales-agent-personas-instrumented-runtime` | agentic | sales_agent | 2d | planning | 1-2 |

**Total estimado:** 7d

## Tickets por owner pool (estimado pre-architect)

| Owner pool | Stories | Estimate |
|---|---|---|
| agent-helper + Chris (curation híbrida) | goldens-3-tenants-dataset | 5d (mostly Chris time gating) |
| claude-opus (agentic, persona simulator wiring) | personas-instrumented-runtime | 2d |

## Dependencias entre stories

```
[S1] sales-agent-eval-runner-foundation
  ↓ (runner debe existir)
sales-agent-personas-instrumented-runtime

(goldens-3-tenants-dataset es independiente del runner — solo necesita estructura YAML decidida)
```

## Orden ejecución sugerido

1. `sales-agent-goldens-3-tenants-dataset` (paralelizable — agent extrae candidatos, Chris cura mientras corre `personas-instrumented-runtime`)
2. `sales-agent-personas-instrumented-runtime` (claude-opus, requiere S1 completo)

## Cierre del sprint

Criterios:
- [ ] 12 goldens YAML checked-in en `backend/tests/agentic_evals/sales_agent/goldens/{tenant_slug}/`
- [ ] PII verificada vía `sanitize_payload` (cero emails/teléfonos/nombres reales)
- [ ] README en goldens/ documenta criterios de selección + cómo agregar nuevos
- [ ] 5 personas cargables como simulators desde `docs/specs/personas/*.yaml`
- [ ] Tests parametrizados por persona (5 tests cada uno corre los 12 goldens)
- [ ] Métricas pass^k separadas por persona (no agregadas)
- [ ] `checkpoint.md` sprint marcado `done`
