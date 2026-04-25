# Master Plan — 11 fases

> **Cada fase entrega valor independiente.** Mergeable a `development`. Si rompe, se revierte sin dependencia inversa.

---

## Tabla resumen

| ID | Fase | Sprints (est.) | Pre-req | Valor entregado |
|---|---|---|---|---|
| F0 | Foundation cleanup + baseline tests | 1 | — | dead code fuera, golden snapshots respuestas hoy |
| F1 | Provider pattern + discovery | 2 | F0 | extender copilot sin tocar `copilot/` |
| F2 | Deep Agents harness | 2 | F1 | planning visible, scratchpad, subagentes |
| F3 | Brand summary "lighthouse" | 1 | F1 | marca presente en cada respuesta |
| F4 | URL contextual + scratchpad | 1 | F2, F3 | URLs como inspiración persistente |
| F5 | `ask_tenant_data` subgraph | 2 | F1, F2 | Q&A natural sobre data propia |
| F6 | Workflow unificado | 2 | F1 | un solo concepto multi-step |
| F7 | Channel formatter registry | 1 | F1 | output canal-aware (whatsapp/email/sms) |
| F8 | Routing + cost optimization | 1 | F2-F7 | latencia ↓ cost ↓ |
| F9 | Quality + observability | 1 | F2-F8 | golden tests + LLM-judge dashboard |
| F10 | Marketing KB curado | 1-2 | F9 | RAG técnico con metodología propia |

**Total estimado:** ~14 sprints.

---

## DAG completo

```
                 ┌── F4 (URL ctx)
F0 ──► F1 ──► F2 ┤
       │     │   └── F5 (ask_tenant_data) ──┐
       │     │                              │
       │     └─► F3 (brand summary) ────────┤
       │                                    │
       ├─► F6 (workflow) ───────────────────┤
       │                                    ├──► F8 ──► F9 ──► F10
       └─► F7 (channels) ───────────────────┘
```

**Críticos secuenciales**: F0 → F1.
**Paralelizables tras F1**: F3, F6, F7 (independientes).
**Tras F2**: F4, F5.

---

## Métricas éxito globales (post-F9, pre-F10)

| Métrica | Baseline hoy | Target |
|---|---|---|
| Latencia primer token p50 | ~2s | ≤800ms |
| Latencia primer token p95 | ~5s | ≤2000ms |
| Cost / conversación promedio | ~$0.15 | $0.05 (sin restringir HEAVY) |
| Completion rate workflows guiados | <40% | ≥70% |
| Q&A accuracy (LLM-judge sobre 100 muestras) | n/a | ≥85% |
| Brand coherence score (LLM-judge offer vs brand) | n/a | ≥90% |
| Cache hit rate system prompt | <30% | ≥60% |
| Tools agregados sin tocar `copilot/` | 0 | 100% |
| Arch tests fitness fase específica | varía | 0 violations |

---

## Riesgos cross-fases + mitigaciones

| Riesgo | Mitigación |
|---|---|
| `langchain-deepagents` introduce bug upstream | Lock version exacta. Fork si crítico. Golden tests detectan en F9. |
| Discovery falla en startup → copilot caído | Feature flag `COPILOT_DISCOVERY_V2` + fallback al registry hardcoded existente. |
| Provider rompe módulo pivote (offer F1) | Tests del módulo afectado son obligatorios antes de cerrar fase. |
| Workflow unification rompe onboardings activos | Feature flag `WORKFLOW_V2_ENABLED` por tenant. Backfill validado en clone prod. |
| BrandSummary mal generado degrada respuestas | LLM-judge antes de persistir + manual review primeras 50 + opt-in regen manual user. |
| Marketing KB chunks mal curados | Versioning del corpus, eval-set fijo corre semanal. |
| Drift entre fases (especialmente paralelas) | Cada fase corre golden tests F0 antes de cerrar. Si rompe, no merge. |
| Costo OpenAI explota durante research/eval | Límite mensual por env (`OPENAI_MONTHLY_BUDGET`). Alarma Sentry al 80%. |

---

## Capacidades user-visibles por fase (lo que el usuario nota)

- **F0**: nada (housekeeping).
- **F1**: nada visible. Pero los devs respiran.
- **F2**: ve plan_cards más estructuradas, respuestas con pasos explícitos en tareas complejas.
- **F3**: nota que el copilot "le habla en su voz de marca" siempre, incluso fuera de Brand Studio. Coherencia.
- **F4**: pasa URL → confirma "guardado como inspiración" → puede referenciar en cualquier turn posterior.
- **F5**: **salto cualitativo grande**. Pregunta cosas como Claude Code y obtiene respuesta directa.
- **F6**: experiencia consistente entre setup brand / setup offer / extracción doc.
- **F7**: pide "para WhatsApp" y obtiene texto que copia-pega listo (sin markdown roto).
- **F8**: respuestas más rápidas. Reasoning solo cuando hace falta.
- **F9**: invisible directo. Confianza porque las regresiones se detectan.
- **F10**: respuestas con autoridad, citan método ("aplicando Hormozi value equation:...").

---

## Out of scope explícito (post-F10)

- Multi-modal generative (que el copilot genere imágenes/audios) — se mantiene **solo lookup** vía `search_assets`.
- WhatsApp como canal **inbound** del copilot (hoy es target de output, no source). Cuando llegue, se diseña aparte.
- Fine-tuning modelos propios. Trabajamos con OpenAI catálogo + RAG curado.
- Sales agent — fuera de este plan. Si requiere cambios, plan separado.
- MCP servers públicos. Provider pattern in-process es suficiente. MCP sólo si en futuro abrimos a integraciones externas.
