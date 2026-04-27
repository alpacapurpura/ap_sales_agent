# 01 · Master Plan — DAG de fases

## Lectura del DAG

```
                                    ┌─────────────────────┐
                                    │ S0: shared/agent_   │
                                    │ observability/      │
                                    │ (extract de copilot)│
                                    └──────────┬──────────┘
                                               │
                                               ▼
                                    ┌─────────────────────┐
                                    │ S1: sales_agent     │
                                    │ observability       │
                                    │ parity + PII        │
                                    └──────────┬──────────┘
                                               │
                                ┌──────────────┼──────────────┐
                                ▼              ▼              ▼
                  ┌──────────────────┐ ┌─────────────┐ ┌────────────┐
                  │ S2: cost         │ │ S4:         │ │ S5: channel│
                  │ guardrails +     │ │ ChatModel   │ │ registry   │
                  │ cycle 25-25      │ │ Spec + tier │ │ shared     │
                  └──────────────────┘ └──────┬──────┘ └─────┬──────┘
                                              │              │
                                              ▼              ▼
                                       ┌─────────────────────────┐
                                       │ S3: prompt cache        │
                                       │ boundary refactor       │
                                       │ (NEEDS S4 para tier)    │
                                       └────────────┬────────────┘
                                                    │
                                                    ▼
                                       ┌─────────────────────────┐
                                       │ S6: fitness tests       │
                                       │ ratchet (frozen state)  │
                                       └────────────┬────────────┘
                                                    │
                                                    ▼
                                       ┌─────────────────────────┐
                                       │ S7: brand voice         │
                                       │ (Estilo Comunicacional) │
                                       │ → lighthouse render     │
                                       └────────────┬────────────┘
                                                    │
                                       ┌────────────┴────────────┐
                                       ▼                         ▼
                            ┌──────────────────┐      ┌──────────────────┐
                            │ S8: scheduler    │      │ S9: payment      │
                            │ tools (booking)  │      │ lifecycle        │
                            └────────┬─────────┘      └────────┬─────────┘
                                     │                         │
                                     └────────────┬────────────┘
                                                  ▼
                                       ┌─────────────────────────┐
                                       │ S10: quality eval loop  │
                                       │ (judge + goldens)       │
                                       └─────────────────────────┘
```

---

## Tabla de dependencias

| Fase | Depende de | Razón |
|---|---|---|
| S0 | — | Foundation. |
| S1 | S0 | Necesita módulo shared. |
| S2 | S1 | Necesita `sales_agent_llm_call` poblado. |
| S3 | S4 | El cache_boundary necesita modelos NANO/MINI/REASONING/HEAVY definidos. |
| S4 | S1 | El callback handler ya graba `provider`/`model_responded` — verificar consistencia. |
| S5 | S1 | Channel registry es consumer de observability (registra `channel_intent` en trace). |
| S6 | S0, S1, S2, S4, S5 | Ratchet congela estado tras infra estable. |
| S7 | S3, S6 | Lighthouse de brand cae en slot cacheable; ratchet evita drift. |
| S8 | S7 | Scheduler tools deben hablar voz de marca. |
| S9 | S7, S8 | Payment hereda voz; algunos flows mezclan booking + payment. |
| S10 | S7, S8, S9 | Goldens cubren features completas. |

---

## Cronograma estimado (orientativo)

| Fase | Esfuerzo | Sprint sugerido |
|---|---|---|
| S0 | 3-5 días | 1 |
| S1 | 8-10 días | 2 (incluye dual-write 4 semanas observación) |
| S2 | 3-4 días | 3 |
| S3 | 5-7 días | 4 |
| S4 | 2-3 días | 4 (paralelo con S3 si recursos) |
| S5 | 3-4 días | 5 |
| S6 | 2-3 días | 5 |
| S7 | 5-7 días | 6 |
| S8 | 7-10 días | 7 |
| S9 | 7-10 días | 8 |
| S10 | 5-7 días | 9 |

**Total ~50-70 días desarrollador** (puede paralelizarse S2/S3/S4/S5).

---

## Branch strategy

Trabajo en `development` siempre. Cada fase = N commits conventional con scope `sales-agent-redesign-s{N}`. Ejemplo:

```
feat(sales-agent-redesign-s1): callback handler + dual-write
feat(sales-agent-redesign-s1): pii sanitization in trace recorder
test(sales-agent-redesign-s1): callback handler invariants
docs(sales-agent-redesign-s1): learnings + s2 handoff prompt
```

NO feature branches. NO worktrees. Ver `.claude/rules/parallel-safety.md`.

---

## Cuándo NO seguir el plan al pie de la letra

Si durante research fresco de una fase descubres que:

- Una librería pivot tuvo breaking change (ej. `langgraph` 0.3 cambió `astream_events`)
- El stack añadió una capa nativa que reemplaza una decisión del plan
- Un análisis revela que una sub-decisión es subóptima

**ENTONCES:** Pausa, documenta el hallazgo en el `phases/S{N}-*.md` (sección "Ajustes vs plan original"), pregunta al usuario si confirma el ajuste antes de codear.

NO seguir ciego un plan de 6 meses atrás. NO desviarse sin documentar.
