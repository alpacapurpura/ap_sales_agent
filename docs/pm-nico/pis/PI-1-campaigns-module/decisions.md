# PI-1-campaigns-module — Decisiones

> ADR-style. Append-only. Cada decisión = fecha + decisión + razón + alternativas consideradas.

## 2026-04-29 — Crear PI dedicado para campaigns

**Decisión:** Campañas como módulo nuevo, no extensión de `advertising` / `social_media` placeholder.

**Razón:**
- Campaigns = capa de orquestación cross-channel
- Advertising / social_media son data sources (ETL) o placeholders
- Confundirlos = mezcla concerns

**Alternativas consideradas:**
- Extender `sales_agent` con "campaign_mode" → descartado, agente vs orquestador son responsabilidades distintas
- Hub directo en `growth_studio` action triggers → descartado, action triggers son atómicos, campaigns es flujo continuo

## 2026-04-29 — SMS descartado

**Decisión:** SMS NO va en módulo campaigns.

**Razón:** WhatsApp domina LATAM. SMS es duplicación con worse UX y cost. (Confirmación Chris desde legacy `docs/pm/campaigns/`).

## 2026-04-29 — Channels Tier 1

**Decisión:** Priorizar TikTok DM + retargeting ads + webinar orchestration.

**Razón:**
- TikTok DM: Manychat ya conectado, LATAM apertura
- Retargeting: capturar warm audiences que ya interactuaron
- Webinar: alto value para infoproductos

**Pendiente:** orden interno de implementación (cuál PR-1).

## 2026-04-29 — D1-D9 legacy confirmadas (importadas desde MASTER_TODO)

| # | Decisión | Razón |
|---|---|---|
| D1 | Multi-canal outbound (Telegram tests, WABA prod, ManyChat bridge transitorio) | Cobertura LATAM + sin bloqueos Meta para tests |
| D2 | Sales Agent personaliza siempre, no templates fijos | `campaign_instructions` = directriz, no guión |
| D3 | Foundation-first, MVPs sin refactor | Reduce ciclo "MVP → feature nueva → refactor" |
| D4 | Commercial Director = Copilot subagent (#4) | Industry standard: planning ≠ execution. Patterns Artisan/11x/Luru |
| D5 | Sales Agent = B2C ONLY | Nunca habla con emprendedor |
| D6 | `campaigns/` módulo independiente | Non-breaking, máxima escalabilidad |
| D7 | Copilot = único punto contacto emprendedor | Toda intención emprendedor pasa por Copilot |
| D8 | ManyChat = bridge WhatsApp transitorio | Hasta WABA directo |
| D9 | Telegram = canal pruebas | Sin aprobación Meta |

## 2026-04-29 — D10: Sprint 0 = Robustez + Escalabilidad cross-cutting

**Decisión:** Antes de escribir dominio campaigns (Sprint 1), construir Sprint 0 con 8 sub-sprints de primitivas reusables (outbox, idempotency, rate limiter, circuit breaker, compliance gate, observability ext, audit, migraciones idempotentes + arch tests).

**Razón:**
- Reframing Chris: "robustez + escalabilidad como paso 0"
- Patrón histórico Nicolify: implementar MVP → llega feature → refactor. FOUNDATION.md ya identificó esto.
- Primitivas cross-cutting reusables: campaigns es primer consumer, sales_agent outbound + voice_agent + content_agent las heredan.
- Costo: 1.5-2 semanas extra upfront.
- Beneficio: 0 refactor entre MVPs subsecuentes. Validable por arch tests.

**Alternativas consideradas:**
- "Empezar con dominio + agregar robustez progresivo" → descartado, viola D3 (foundation-first).
- "Solo idempotency + rate limiter (mínimo)" → descartado, deja agujeros (compliance, observability gap = bug invisible).

## 2026-04-29 — D11: PI-1 cierra con MVP 1 Telegram. Multi-canal/email/event → PI-2/3

**Decisión:** PI-1 alcance = S0 + S1 + S2 + S3 (Telegram MVP). PI-2 toma multi-canal + Copilot subagent + email. PI-3 toma event campaigns + CRM Hub FE.

**Razón:**
- Reduce scope creep PI-1.
- Retro temprana captura aprendizajes antes de comprometer roadmap completo.
- Permite re-priorización entre PIs según data real (uso S0 primitivas, demanda canales).

**Alternativa considerada:**
- "Un solo PI gigante hasta MVP 5" → descartado, no permite retro intermedia ni re-priorización.

## 2026-04-29 — D12: Primitivas Sprint 0 viven en `shared/`

**Decisión:** Outbox, idempotency store, rate limiter, circuit breaker, compliance gate, observability extension, audit trail = `backend/src/shared/` (subpaquete dedicado). NO en `campaigns/`.

**Razón:**
- Reuso futuro: sales_agent outbound, voice_agent, content_agent las heredan sin acoplamiento a campaigns.
- Test arch enforcement (no cross-module imports) lo permite si vive en shared/.

**Alternativa considerada:**
- "Vivir en `campaigns/`" → descartado, futuros consumers tendrían que importar campaigns/ violando DDD.

## 2026-04-29 — D13: 5 planes tarifarios con tope LLM mensual

**Decisión:** Catálogo de 5 planes con tope mensual de gasto LLM:

| Plan | Tope LLM total |
|---|---|
| Free | $5 |
| Básico | $15 |
| Intermedio | $30 |
| Avanzado | $45 |
| Ultra | $95 |

Tabla `plan_config` editable sin migration (UPDATE row). Streamlit admin permite ajustar cuotas y agregar/desactivar planes.

**Razón:**
- Modelo de monetización claro y escalable.
- Permite ajustes de pricing sin code change (config-driven).
- Variables expuestas: budget_total, sales_agent_reserved_pct, max_outbound_msg_per_day, max_campaigns_active, max_segment_size, max_contacts_total, features JSONB.

**Razonamiento numérico:** `research/2026-04-29-billing-tiers-cost-model.md` (cost model real Nicolify, traducción a quotas, supuestos).

## 2026-04-29 — D14: Reservación 50% sales_agent (invariante)

**Decisión:** 50% del tope LLM mensual (configurable por plan) **reservado exclusivamente para sales_agent**. Copilot, brand_extraction, doc_extraction, futuros agentes consumen del 50% restante. **Copilot exhausto NO consume budget de sales_agent.**

`BudgetGuard.check(tenant_id, agent_kind, est_cost)` enforza. Test arch valida invariante.

**Razón (Chris textual):** "las ventas no deben parar, no vaya a ser que se consuma todo en conversaciones con copilot y no quede dinero para vender."

**Alternativas consideradas:**
- "Pool unificado, primero llegado primero servido" → descartado, copilot intensivo (extraction tools, $0.30/op) puede vaciar budget en horas, dejando ventas sin atender.
- "Reservar 70% sales_agent" → descartado por ahora, 50/50 más balanceado para tenants nuevos. Configurable per-plan si data lo justifica.

## 2026-04-29 — D15: Outbox pattern aplica GLOBALMENTE (no solo campaigns)

**Decisión:** Sprint 0.1 = refactor del `event_bus` actual del proyecto + tabla `domain_event_outbox`. Aplica a TODOS los emisores de domain events: sales_agent, copilot, brand, offer, crm, campaigns. Garantiza exactly-once entre commit DB + dispatch al subscriber.

**Razón (Chris textual):** "Para todo. Debemos dejar las bases bien definidas."

**Alternativa considerada:** outbox solo para campaigns events → descartado, deja agujeros en sales_agent webhooks + copilot turn events que pueden perderse en crash de worker.

**Costo agregado:** ~3-5 días extra vs outbox solo campaigns. Migración suave: emisores existentes siguen funcionando, outbox table se habilita progresivo con feature flag.

## 2026-04-29 — D16: NO crear módulo observability nuevo. Reusa `shared/agent_observability/`

**Decisión:** Campaigns observability = declarar `AgentObservabilitySpec(agent_kind="campaign")` consumiendo `shared/agent_observability/` ya existente. Mismo patrón que sales_agent (que ya migró post audit S0).

**Razón:**
- Audit 2026-04-29 confirma: shared layer ya tiene `BaseAgentCallbackHandler`, `cost calculator`, `PricingResolver`, `BillingCycleService`, `CostAggregator`, MV cross-agent.
- Reuso = 1 callback subclass + 1 model + 1 spec registration. Trivial.
- Single trace surface en Streamlit admin (no fragmentar entre módulos).

**Alternativa considerada:** `campaign_trace_event` paralelo → descartado, fragmenta observabilidad y duplica esfuerzo.

## 2026-04-29 — D17: Sprint 0 cortado a 5 sub-sprints (S0.1, S0.2, S0.3, S0.5, S0.6)

**Decisión:** Sub-sprints originales S0.4 (circuit breaker), S0.7 (audit log), S0.8 (arch tests dedicado) se mueven:
- S0.4 → Sprint 2 (cuando hay external API calls reales que romper)
- S0.7 → Sprint 2 (cuando hay mutaciones a auditar)
- S0.8 → ya cubierto por regla estándar `.claude/rules/architectural-fitness.md` aplicado auto en CI

**Razón (Chris textual):** "Cortemos, prioricemos hacerlo muy bien en vez de aumentar el alcance."

## 2026-04-29 — D18: Sprint 4 = Mini CRM Hub lite con arquitectura forward-compatible

**Decisión:** PI-1 incorpora Sprint 4 (paralelo a Sprint 3): vista lite contactos + segment manual creation. Permite a Chris testear MVP 1 Telegram con UI real, no SQL manual.

Principio arquitectónico: **API contracts FINALES desde día 1. UI compone subset hoy. PI-3 agrega componentes/páginas que CONSUMEN la misma API y mismos primitives FE. Cero refactor.**

**Razón (Chris textual):** "Asegurate de entregarme una versión lite ahora pero que no requiera tooodo un refactoring luego, se inteligente y deja la arquitectura diseñada."

**Forward-compat invariantes:**
1. `FilterParams` Pydantic schema soporta TODOS los filters (incluido `traits.{key}`, `last_activity_at`, ranges) desde S4.1; lite UI expone subset.
2. `ContactDetailContent` component aislado — drawer S4 + página completa PI-3 lo reusan.
3. `Segment` domain soporta STATIC + DYNAMIC desde S1; S4 lite crea STATIC manual, PI-3 builder visual crea DYNAMIC con filters.
4. `DataTable` primitive en `components/shared/data-table/` (NO en `features/crm-hub/`), reusable por campañas + segmentos PI-3.
5. `SelectedContactsBar` con slot pattern: S4 = solo "Crear segmento". PI-3 agrega "Exportar Meta", "Bulk update", "Agregar a campaña".
6. Endpoint stubs documentados en S4.1 con `# deferred PI-3` flag (`/contacts/{id}/journey`, `/contacts/{id}/campaigns`, `POST /audience-exports`).

**Alternativas consideradas:**
- A — CRM Hub completo en PI-3 (status quo) → descartado: Chris no puede testear S3 sin SQL manual.
- B — Mini Hub en PI-2 → descartado: testing S3 sigue bloqueado.
- D-no-forward (lite "rápido y feo") → descartado: requeriría refactor PI-3.

**Costo:** +1 sem FE paralelo a S3. Reusa UX session previa (`docs/ux-sessions/2026-04-29-crm-module-proposal/`).

**Beneficio:** Chris testea S3 con UX real. PI-3 entrega CRM Hub completo agregando archivos, no editando primitives.

## Pendientes registrar

_Decisiones tomadas durante discovery + ejecución se registran aquí._
