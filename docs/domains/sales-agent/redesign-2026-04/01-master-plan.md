# 01 · Master Plan — DAG de fases

> **Actualizado 2026-04-28** (post-S6 close): agregadas 3 fases para garantizar que **al cerrar S12 el `05-tech-debt-log.md` queda con cero entries DEFERRED flotantes** (decisión CTO 2026-04-28). El plan es ahora autocontenido — cada deuda apunta a fase del plan o WONT-FIX con razón documentada.
>
> Cambios: agregada **S00** pre-fase (codebase audit + cleanup deprecated). S4 scope recortado (ChatModelSpec + multi-provider per-role ya existen post-commits abril, sales_agent solo adopta). Agregadas **S6.5** (legacy drop post dual-write window), **S11** (shared base lift + orchestrator decomposition Stranger Fig), **S12** (final hardening + cero deuda flotante).

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
                                       │ ratchet (sweeps S4/S5)  │
                                       └────────────┬────────────┘
                                                    │
                                                    ▼
                                       ┌─────────────────────────┐
                                       │ S6.5: legacy drop +     │
                                       │ admin cutover           │
                                       │ (post 2026-05-26 win.)  │
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
                                       │ (judge + goldens +      │
                                       │  DeepSeek alias guard + │
                                       │  Kimi 0.6 conv monitor) │
                                       └────────────┬────────────┘
                                                    │
                                                    ▼
                                       ┌─────────────────────────┐
                                       │ S11: shared base lift + │
                                       │ orchestrator decomp     │
                                       │ (Stranger Fig chat.py + │
                                       │  closer_studio_service +│
                                       │  semantic_router)       │
                                       └────────────┬────────────┘
                                                    │
                                                    ▼
                                       ┌─────────────────────────┐
                                       │ S12: final hardening    │
                                       │ (tier pricing ratchet + │
                                       │  Presidio WONT-FIX doc +│
                                       │  typing_cpm wiring +    │
                                       │  voseo scan +           │
                                       │  ZERO debt log)         │
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
| S6 | S0, S1, S2, S4, S5 | Ratchet congela infra estable. Sweeps S4/S5 cierran shims + LLM_ROLE_BY_SITE expansion. |
| **S6.5** | S6 + 4-week dual-write window | Drop legacy `agent_trace_model` + `LLMLogModel` post 2026-05-26. Cutover `sales_audit.py`. Arch test `__future__ annotations` ratchet. |
| S7 | S3, S6.5 | Lighthouse cae slot cacheable. Sin tablas legacy bloqueando. |
| S8 | S7 | Scheduler tools deben hablar voz de marca. |
| S9 | S7, S8 | Payment hereda voz; flows mezclan booking + payment. |
| S10 | S7, S8, S9 | Goldens cubren features completas. **Incluye DeepSeek alias retire validator + Kimi temp 0.6 conversion monitor** (cierran 2 watchpoints S4). |
| **S11** | S10 | Shared `BaseAgentCallbackHandler` lift coordinado con copilot retrofit (cierra deuda S1). Stranger Fig refactor `chat.py` (1082 LOC) + `closer_studio_service.py` (623 LOC) + `semantic_router.py` (328 LOC). NO toca §3. |
| **S12** | S11 | Final hardening: tier pricing >200k arch ratchet + Presidio WONT-FIX classification + `typing_simulation_cpm` wiring (libera §3 fragment validado por eval loop) + scan voseo final + cierre `05-tech-debt-log.md` con cero DEFERRED. |

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
| **S6.5** | **1-2 días** | 6 (gated por reloj 2026-05-26) |
| S7 | 5-7 días | 6 |
| S8 | 7-10 días | 7 |
| S9 | 7-10 días | 8 |
| S10 | 5-7 días | 9 |
| **S11** | **8-12 días** (refactor riesgoso, 5 days callback handler lift + 7 days orchestrator decomp con tests) | 10 |
| **S12** | **2-3 días** (final hardening + audit cero deuda) | 11 |

**Total ~62-82 días desarrollador** (paralelizable S2/S3/S4/S5).

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

## Definition of Done — del PLAN COMPLETO (cierre S12)

S12 cierra cuando se cumplen TODAS estas condiciones:

1. ✅ S0..S11 todas en estado DONE.
2. ✅ `05-tech-debt-log.md` con **cero entries DEFERRED-* flotantes**. Cada entrada está FIXED (con commit hash) o WONT-FIX (con razón documentada).
3. ✅ Arch tests del producto cubren cada invariante introducido por el plan (ratchet imports, anchors, callback handler, PII, tenant isolation, subagent isolation, channel registry, model tier, system prompt order, tier pricing, `__future__ annotations`).
4. ✅ Reconciliation worker dual-write parado (post-cutover legacy en S6.5).
5. ✅ Quality eval loop S10 corriendo semanal con DeepSeek alias validator + Kimi 0.6 conversion monitor activos.
6. ✅ `chat.py` < 400 LOC (post-Stranger Fig S11). `closer_studio_service.py` split. `semantic_router.py` registry-based.
7. ✅ Backlog general producto recibe items operacionales que NO eran del plan (tier resolution >200k, Presidio enterprise, alias retires futuros) con WONT-FIX o reabrir-condicional documentado.
8. ✅ §3 protected surfaces intactos (closer_studio + buffer + output_manager.process_response + enrollment + agent_state_checkpoint + webhooks + follow_up_engine cadence) — verificado smoke al cierre.

Si **uno** falla → S12 NO cerrada. **El plan NO declara success hasta los 8.**

---

## Cuándo NO seguir el plan al pie de la letra

Si durante research fresco descubres:
- Librería pivot tuvo breaking change
- Stack añadió capa nativa que reemplaza decisión del plan
- Análisis revela sub-decisión subóptima
- **Realidad post-abril 2026 ya implementó** parte del plan (caso S4)

**ENTONCES:** Pausa, documenta en `phases/S{N}-*.md` sección "Ajustes vs plan original", pregunta al usuario si confirma antes de codear.

NO seguir ciego. NO desviar sin documentar.
