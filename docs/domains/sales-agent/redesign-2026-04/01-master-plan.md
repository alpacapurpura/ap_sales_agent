# 01 · Master Plan — DAG de fases

> **Actualizado 2026-04-28**: agregada S00 pre-fase (codebase audit + cleanup deprecated). S4 scope recortado (ChatModelSpec + multi-provider per-role ya existen post-commits abril, sales_agent solo adopta).

## Lectura del DAG

```
                                    ┌─────────────────────┐
                                    │ S00: codebase audit │
                                    │ + cleanup deprecated│
                                    │ + admin migration   │
                                    │ prep                │
                                    └──────────┬──────────┘
                                               │
                                               ▼
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
                                    │ parity + PII +      │
                                    │ tool_call_dedup     │
                                    └──────────┬──────────┘
                                               │
                                ┌──────────────┼──────────────┐
                                ▼              ▼              ▼
                  ┌──────────────────┐ ┌─────────────┐ ┌────────────┐
                  │ S2: cost         │ │ S4: ADOPT   │ │ S5: channel│
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
                                       │ ratchet + drop legacy   │
                                       │ agent_trace_model       │
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
| **S00** | — | Pre-fase. Snapshot estado limpio antes de tocar arq. |
| S0 | S00 | Audit map identifica callers que extract no debe romper. |
| S1 | S0 | Necesita módulo shared. Adopta `tool_call_dedup` + pricing/aliases. |
| S2 | S1 | Necesita `sales_agent_llm_call` poblado. |
| S3 | S4 | Cache_boundary necesita modelos NANO/MINI/REASONING/AGENT/HEAVY. |
| S4 | S1 | Callback handler graba `provider`/`model_responded` para validar resolver. |
| S5 | S1 | Channel registry consumer de observability. |
| S6 | S0, S1, S2, S4, S5 | Ratchet congela infra estable. Drop `agent_trace_model` legacy. |
| S7 | S3, S6 | Lighthouse cae slot cacheable. Ratchet evita drift. |
| S8 | S7 | Scheduler tools deben hablar voz de marca. |
| S9 | S7, S8 | Payment hereda voz; flows mezclan booking + payment. |
| S10 | S7, S8, S9 | Goldens cubren features completas. |

---

## Cronograma estimado

| Fase | Esfuerzo | Sprint sugerido |
|---|---|---|
| **S00** | 2-3 días | 0 |
| S0 | 3-5 días | 1 |
| S1 | 8-10 días | 2 (incluye dual-write 4 semanas observación) |
| S2 | 3-4 días | 3 |
| S3 | 5-7 días | 4 |
| **S4** | **1-2 días** (recortado) | 4 (paralelo S3) |
| S5 | 3-4 días | 5 |
| S6 | 2-3 días | 5 |
| S7 | 5-7 días | 6 |
| S8 | 7-10 días | 7 |
| S9 | 7-10 días | 8 |
| S10 | 5-7 días | 9 |

**Total ~50-65 días desarrollador** (paralelizable S2/S3/S4/S5).

---

## Branch strategy

`development` siempre. Cada fase = N commits conventional con scope `sales-agent-redesign-s{N}`. Ejemplo:

```
chore(sales-agent-redesign-s00): cleanup deprecated /sales/resumen + audit map
feat(sales-agent-redesign-s1): callback handler + dual-write
feat(sales-agent-redesign-s1): tool_call_dedup mirror + PII LATAM
test(sales-agent-redesign-s1): callback handler invariants
docs(sales-agent-redesign-s1): learnings + s2 handoff prompt
```

NO feature branches. NO worktrees. Ver `.claude/rules/parallel-safety.md`.

---

## Cuándo NO seguir el plan al pie de la letra

Si durante research fresco descubres:
- Librería pivot tuvo breaking change
- Stack añadió capa nativa que reemplaza decisión del plan
- Análisis revela sub-decisión subóptima
- **Realidad post-abril 2026 ya implementó** parte del plan (caso S4)

**ENTONCES:** Pausa, documenta en `phases/S{N}-*.md` sección "Ajustes vs plan original", pregunta al usuario si confirma antes de codear.

NO seguir ciego. NO desviar sin documentar.
