# 05 · Tech Debt Log

Registro vivo de deuda técnica detectada durante el redesign. Fases agregan; nadie borra (solo marca FIXED con commit hash).

Formato:
```
## [SEVERITY] Título corto — YYYY-MM-DD — fase detectora — STATUS
- Path: `archivo:linea`
- Descripción: ...
- Impacto: ...
- Acción: FIXED en {commit} / DEFERRED a S{N} / FLAGGED
- Razón: ...
```

Severities: `CRITICAL` (security/data loss) · `HIGH` (functional bug visible) · `MEDIUM` (frágil, falla rara) · `LOW` (style, cosmético).

Statuses: `FIXED` · `DEFERRED-S{N}` · `FLAGGED` · `WONT-FIX`.

---

## Sembrado inicial (detectados en diagnóstico previo + revisión 2026-04-28)

### Resumen deprecated cleanup

#### [HIGH] Frontend `/sales/resumen` deprecated activa — 2026-04-28 — diagnóstico — DEFERRED-S00
- Path: `frontend/src/app/(main)/[tenantId]/(dashboard)/sales/resumen/page.tsx`
- Descripción: feature `resumen` deprecated, reemplazado por `closer-studio` (`/sales/studio/{inbox,pipeline,frozen}`). Ruta sigue activa, sidebar la apunta.
- Impacto: doble navegación confusa; usuarios bookmarkean URL muerta; SEO interno duplicado.
- Acción: DEFERRED-S00 — borrar carpeta + page.
- Razón: parte del scope de S00 (codebase audit + cleanup).

#### [HIGH] `sales/page.tsx` redirige a deprecated `/sales/resumen` — 2026-04-28 — diagnóstico — DEFERRED-S00
- Path: `frontend/src/app/(main)/[tenantId]/(dashboard)/sales/page.tsx:12`
- Descripción: `redirect(/${tenantId}/sales/resumen)` debería apuntar a `/sales/studio/inbox`.
- Impacto: cualquier link a `/sales` lleva a página deprecated.
- Acción: DEFERRED-S00.

#### [HIGH] Sidebar entry "Resumen" duplica navegación — 2026-04-28 — diagnóstico — DEFERRED-S00
- Path: `frontend/src/components/shared/layout/AppSidebar.tsx:118`
- Descripción: entry `{ title: "Resumen", href: "/${tenantId}/sales/resumen", ... }` apunta a deprecated.
- Impacto: sidebar muestra 2 entries para mismo feature ("Resumen" + "Studio").
- Acción: DEFERRED-S00 — borrar entry "Resumen", consolidar en "Studio".

### Sales agent observability

#### [HIGH] Sales_agent sin PII sanitization en trace recorder — 2026-04-27 — diagnóstico — DEFERRED-S1
- Path: `backend/src/modules/sales_agent/infrastructure/monitoring/tracing.py`
- Descripción: `@trace_node` persiste `input_state` y `output_state` JSONB sin sanitizar. Mensajes de leads contienen emails, teléfonos, links de pago, posibles DNI/CURP/CUIT/RFC.
- Impacto: compliance LATAM (PDPA, LGPD, LFPDPPP). Riesgo legal + breach.
- Acción: DEFERRED-S1 — bloqueante de S1, debe activarse día 1.
- Razón: requiere callback handler shared para sustituir `@trace_node`.

#### [HIGH] Sales_agent sin retention policy — 2026-04-27 — diagnóstico — DEFERRED-S1
- Path: `backend/src/modules/sales_agent/infrastructure/models/agent_trace_model.py` y `agent_log_model.py`
- Descripción: tablas legacy crecen indefinido. No hay worker de purge.
- Impacto: storage cost + GDPR violation.
- Acción: DEFERRED-S1 (90d trace) y DEFERRED-S2 (365d llm_call).

#### [HIGH] Streamlit `sales_audit.py` lee tabla legacy — 2026-04-28 — diagnóstico — DEFERRED-S1
- Path: `backend/src/admin/modules/sales_audit.py`
- Descripción: page lee `agent_trace_model` (legacy decorator-based). Post S1 cutover debe migrar a `sales_agent_trace_event`.
- Impacto: dashboard miente si dual-write incompleto; tras drop legacy table page rompe.
- Acción: DEFERRED-S1 — agregar dual-read durante ventana 4 semanas, drop legacy en S6.
- Razón: depende de tabla event-sourced de S1.

### LLM cost / cache

#### [MEDIUM] Sales_agent prompt sin cache_boundary — 2026-04-27 — diagnóstico — FIXED en S3
- Path: `backend/src/modules/sales_agent/application/agents/sales/nodes.py` + `backend/src/modules/sales_agent/application/prompts/compose.py` (nuevo).
- Descripción: Jinja render fresh per turn. Cache hit rate ~0%. Sales_agent es módulo más caro en LLM, sobre todo con Kimi/DeepSeek que ya soportan cache.
- Impacto: LLM cost. Estimado 25-30% reducción con hit rate 60%.
- Acción: FIXED — `compose_system_prompt(fragments)` mirror F8 copilot pattern. Single string + `CACHE_BOUNDARY_MARKER` (HTML comment). Slot order: static_identity → tools_hint → playbook → agent_identity → offer (S7 placeholder) → channel (S5 placeholder) → [BOUNDARY] → stage → signals → session_continuity → tool_format. Prefix realista ≥2700 tokens (>2× threshold). Specialists qualifier/product_expert/closer migrados; supervisor fuera de scope (max_output_tokens=10).

#### [MEDIUM] Sales_agent no usa multi-provider per-role — 2026-04-28 — diagnóstico — FIXED en S4
- Path: `backend/src/modules/sales_agent/application/agents/sales/nodes.py` + `backend/src/modules/sales_agent/domain/model_tier.py` (nuevo SSoT).
- Acción: FIXED — `MultiRoleLLMRouter` ya enrutaba per-role transparente; el missing piece era el mapping `SPECIALIST_TO_ROLE` semántico (SSoT). Closer pasa de `REASONING` → `AGENT` (Kimi K2.6, cache 75-83%); supervisor `FAST` → `NANO` (paridad copilot F8). Qualifier/product_expert mantienen `REASONING` (DeepSeek V4 auto-cache disk-based via `AI_PROVIDER_REASONING=deepseek`). Arch test `tests/architecture/test_no_hardcoded_models_sales_agent.py` bloquea regresiones de hardcoded model strings en `application/agents/sales/`.

#### [LOW] Cost_usd inline sin pricing snapshot — 2026-04-27 — diagnóstico — FIXED en S2
- Path: `backend/src/modules/sales_agent/infrastructure/models/llm_log_model.py` (legacy table, S6 drop) + `sales_agent_llm_call.cost_usd` (event-sourced, S1 callback).
- Acción: el callback handler S1 ya graba `cost_usd` via `shared/agent_observability/cost/calculator.py` + `pricing_snapshot`. S2 lo expone vía `CostAggregator(SalesAgentLlmCallModel)` y suma cross-agent vía MV `mv_daily_llm_cost_per_tenant_v2`. Billing audit reproducible point-in-time. Legacy `LLMLogModel` se drop en S6 cuando dual-write window cierre.

### Channels / OutputManager

#### [MEDIUM] OutputManager hardcodeado por canal — 2026-04-27 — diagnóstico — DEFERRED-S5
- Path: `backend/src/modules/sales_agent/infrastructure/external/output_manager.py`
- Descripción: chunk size, CPM, emoji policy hardcodeados en if-else por canal. Imposible agregar canal sin tocar archivo.
- Impacto: extensibilidad.
- Acción: DEFERRED-S5.

### Brand voice

#### [MEDIUM] Sales_agent identity sin lighthouse — 2026-04-27 — diagnóstico — DEFERRED-S7
- Path: `backend/src/modules/sales_agent/infrastructure/prompts/base.py` (PromptLoader)
- Descripción: `agent_identity` se compone fresh per turn desde `tenant_config` sin caching cross-turn. Brand voice cambia raro pero re-renderiza siempre. Tampoco consume Brand Studio "Estilo Comunicacional" (campo dependiente de verificación en research).
- Impacto: cache hit + costo + voz genérica.
- Acción: DEFERRED-S7.

#### [LOW] Posible voseo en templates Jinja sales_agent — 2026-04-28 — diagnóstico — DEFERRED-S00 (scan) / DEFERRED-S7 (fix)
- Path: `backend/src/modules/sales_agent/infrastructure/prompts/templates/*.j2`
- Descripción: scan voseo pendiente (S00 paso 7).
- Impacto: comunicación de marca inconsistente en mercados no-AR.
- Acción: DEFERRED-S00 scan + DEFERRED-S7 fix masivo (lighthouse decide override per tenant).

### Cohesión / acoplamiento

#### [MEDIUM] Posible duplicación KPIs FE↔BE closer-studio — 2026-04-28 — diagnóstico — DEFERRED-S00 (audit)
- Path: `backend/src/modules/sales_agent/application/services/closer_studio_service.py` + `frontend/src/features/closer-studio/hooks/use-kpis.ts`
- Descripción: posible cálculo duplicado KPIs en BE y derivación FE.
- Impacto: drift métricas.
- Acción: DEFERRED-S00 audit map (sección §1 cross-module callers).

---

## Detectados durante S00 (codebase audit + cleanup deprecated) — 2026-04-28

### Cleanup deprecated `/sales/resumen` — FIXED

#### [HIGH] Frontend `/sales/resumen` deprecated activa — 2026-04-28 — S00 — FIXED en S00
- Path: `frontend/src/app/(main)/[tenantId]/(dashboard)/sales/resumen/page.tsx`
- Acción: directorio borrado.

#### [HIGH] `sales/page.tsx` redirige a deprecated — 2026-04-28 — S00 — FIXED en S00
- Path: `frontend/src/app/(main)/[tenantId]/(dashboard)/sales/page.tsx:12`
- Acción: redirect actualizado a `/${tenantId}/sales/studio/inbox`.

#### [HIGH] Sidebar entry "Resumen" duplica navegación — 2026-04-28 — S00 — FIXED en S00
- Path: `frontend/src/components/shared/layout/AppSidebar.tsx:118`
- Acción: entry borrado. `LayoutDashboard` icon import removido (era único consumer de ese icono en el archivo).

#### [HIGH] Orphan FE components post-resumen-delete — 2026-04-28 — S00 — FIXED en S00
- Paths borrados:
  - `frontend/src/features/sales/components/SalesDashboard.tsx`
  - `frontend/src/features/sales/components/dashboard/ConversionCommandCenter.tsx`
  - `frontend/src/features/sales/components/dashboard/lanes/{SalesLane,AgendaLane,OpportunityLane}.tsx`
  - `frontend/src/features/sales/components/overlay/SalesInboxSheet.tsx`
- Acción: `features/sales/index.ts` barrel actualizado, `features/sales/types/sales-studio.ts` reducido a `PaymentGatewayConfig` (único type con consumer real), `lib/design-system/registry-sales.ts` purgado de las 6 entradas orphan.
- Razón: el deletion del route convirtió toda la cadena en dead code (verificado por grep + AST scan).

### Orphans pre-existentes (no consecuencia del cleanup S00) — DEFERRED

#### [LOW] FE components orphan en `features/sales/components/dashboard/` y `overlay/` — 2026-04-28 — S00 — DEFERRED-S0
- Paths:
  - `frontend/src/features/sales/components/dashboard/ActivityFeedWidget.tsx`
  - `frontend/src/features/sales/components/dashboard/CalendarWidget.tsx`
  - `frontend/src/features/sales/components/overlay/AppointmentSheet.tsx`
  - `frontend/src/features/sales/components/overlay/AvailabilityModal.tsx`
- Descripción: orphans verificables vía grep — sólo `lib/design-system/registry-sales.ts` los menciona (catálogo estático). Sin consumer real en runtime.
- Impacto: dead code, ruido para el AI auto-complete, distorsiona el registry.
- Acción: DEFERRED-S0 — borrarlos en S0 cleanup pass. NO en S00 (scope estricto: sólo cascada de `/sales/resumen`).
- Razón: anti-scope-creep. Cada uno es eliminable en archivo tocado.

### Spanish neutro scan — 0 hits actionables

#### [LOW] Voseo scan sales_agent + closer-studio — 2026-04-28 — S00 — FLAGGED (clean)
- Paths escaneados: `backend/src/modules/sales_agent/`, `frontend/src/features/closer-studio/`.
- Descripción: regex de `.claude/rules/spanish-text.md` (vos|tenés|podés|querés|sabés|hacés|venís|decís|mirá|dejá|poné|configurá|elegí|seleccioná|arrancá|empezá|agregá|escribí|guardá|subí|bajá|abrí|volvé|andá|cambiá|ofrecés|cobrás|integrás|listá|probá|mostrá|compartí|contá|explicá|fijate|acordate|dale) → **0 hits**.
- Impacto: nulo — baseline limpia.
- Acción: FLAGGED — re-correr scan al cierre de S7 (post brand-voice integration) y S10 (post goldens). Cualquier voseo introducido por overrides de tenant en Brand Studio se aplicará vía lighthouse, no inline.
- Razón: scan obligatorio del protocolo S00 documentado para que S7 sepa qué baseline inherita.

#### [LOW] Tilde scan: 1 false-positive en legacy template — 2026-04-28 — S00 — WONT-FIX
- Path: `backend/src/modules/sales_agent/infrastructure/prompts/templates/legacy/state_transition.j2:33`
- Descripción: `"Expansion"` aparece en frase inglesa `"Looking for Order, Expansion, Purpose."` — palabra inglesa, no español sin tilde.
- Impacto: nulo (string interno, no user-facing).
- Acción: WONT-FIX. Archivo `legacy/` candidato a borrar en fase futura junto con migración prompt versioning.

### Cohesión / acoplamiento — DEFERRED

#### [MEDIUM] `chat.py` orchestrator overgrown (1082 LOC) — 2026-04-28 — S00 — DEFERRED-post-S6
- Path: `backend/src/modules/sales_agent/application/orchestrator/chat.py`
- Descripción: orchestrator mezcla parsing + state machine + event publishing + identity resolution + buffer + audit. Candidato Stranger Fig hacia `ConversationPipeline`, `IdentityResolver`, `AuditEmitter`.
- Impacto: cohesión baja, dificulta testing focal.
- Acción: DEFERRED-post-S6 — refactor candidato. Bloqueante de §3: NO tocar `BufferService.smart_debounce` ni `OutputManager.process_response` mientras orchestrator se descompone.
- Razón: scope de redesign infra (S0..S6) NO incluye refactor de domain logic. Post-ratchet S6 abre ventana de cleanup arquitectónico.

#### [MEDIUM] `closer_studio_service.py` 8+ responsabilidades — 2026-04-28 — S00 — DEFERRED-post-S6
- Path: `backend/src/modules/sales_agent/application/services/closer_studio_service.py` (623 LOC)
- Descripción: list/detail/stop/resume/send/nudge/reactivate/diagnose/kpis en una sola clase con SQL inline.
- Impacto: cohesión baja; re-test cada acción al tocar otra.
- Acción: DEFERRED-post-S6 — split en `ConversationQueryService` + `ConversationCommandService` + `KpiService`.
- Razón: idem chat.py — fuera del scope S0..S6.

#### [MEDIUM] `semantic_router.py` routes hardcoded (328 LOC) — 2026-04-28 — S00 — DEFERRED-post-S6
- Path: `backend/src/modules/sales_agent/application/services/semantic_router.py`
- Descripción: routes domain (security/objections/logistics/content) + tenant overrides + embeddings hardcoded en archivo.
- Acción: DEFERRED-post-S6.

#### [MEDIUM] `knowledge_builder.py` factory amplio (217 LOC) — 2026-04-28 — S00 — DEFERRED-S0
- Path: `backend/src/modules/sales_agent/application/services/knowledge_builder.py`
- Descripción: tenant context + offer + brand + style anchors en una factory con lazy imports cross-module.
- Impacto: si S0 formaliza ports brand/offer, este archivo se simplifica naturalmente.
- Acción: DEFERRED-S0 — re-evaluar al cierre de S0 si los lazy imports siguen necesarios.

### Admin migration

#### [HIGH] `sales_audit.py` lee `agent_trace_model` legacy + `LLMLogModel` — 2026-04-28 — S00 — DEFERRED-S1
- Path: `backend/src/admin/modules/sales_audit.py`
- Descripción: import directo de `AgentTrace` para sidebar "Ver Último Estado" + queries vía `AuditRepository` a tablas legacy.
- Impacto: cutover de tablas legacy en S6 rompe el admin si dual-read no se implementa antes en S1.
- Acción: DEFERRED-S1 — implementar dual-read en S1 (ver `audit/admin-migration-plan.md §2`). Cutover S6.

### Cross-module

#### [LOW] Lazy imports brand + offer en sales_agent services — 2026-04-28 — S00 — DEFERRED-post-S6
- Paths:
  - `backend/src/modules/sales_agent/application/services/style_anchor_retriever.py` — lazy `brand.infrastructure.qdrant.StyleAnchorStore`
  - `backend/src/modules/sales_agent/application/services/business_repository.py` — lazy `offer.infrastructure.models.ProductModel`
- Descripción: cross-module imports vía lazy/TYPE_CHECKING — pasan los arch tests pero al borde.
- Impacto: si S7 (brand voice) o S8 (scheduler) necesitan más datos brand/offer, multiplican lazy imports.
- Acción: re-evaluado cierre S0 — los lazy imports siguen siendo locales a sales_agent, no afectan extract observability. **Re-clasificado DEFERRED-post-S6** porque port formal no entra en redesign infra (S0..S6).
- Razón: scope S0 fue 100% backend cross-cutting, no tocó sales_agent services. Refactor a ports brand/offer es candidato post-redesign.

---

## Detectados durante S0 (shared agent_observability extract) — 2026-04-28

### Shared module extract — FIXED

#### [HIGH] copilot/observability/ contiene primitives reusables hardcoded en BC — 2026-04-28 — S0 — FIXED en S0
- Paths movidos a `src/shared/agent_observability/`:
  - `recording/sanitization.py`
  - `cost/calculator.py`, `cost/fx_resolver.py`
  - `pricing/aliases.py`, `pricing/resolver.py`, `pricing/litellm_sync.py`
  - `persistence/pricing_snapshot_repository.py`, `persistence/tenant_billing_config_repository.py`
  - `persistence/models/pricing_snapshot_model.py`, `persistence/models/tenant_billing_config_model.py`
  - `reporting/cycle_window.py`, `reporting/billing_cycle_service.py`
  - `workers/pricing_sync_task.py`
- Descripción: 13 archivos puros / cross-tenant reference data movidos sin re-exports transitorios. Imports actualizados en consumers (BE + tests).
- Acción: extract completo. 2522 tests passing.

#### [LOW] tests/architecture/test_master_data.py allowlist post-move — 2026-04-28 — S0 — FIXED en S0
- Path: `tests/architecture/test_master_data.py:24,32`
- Descripción: `ALLOWED_USD_DEFAULT_FILES` apuntaba a paths viejos `src/modules/copilot/observability/{cost,persistence/models}`.
- Acción: actualizado a `src/shared/agent_observability/{cost/fx_resolver.py, persistence/models/tenant_billing_config_model.py}`.

### Sales agent observability — refinado scope

#### [HIGH] Sales_agent sin PII sanitization — 2026-04-27 — diagnóstico — DEFERRED-S1 (re-confirmado post-S0)
- Path: `backend/src/modules/sales_agent/infrastructure/monitoring/tracing.py`
- Descripción: ya estaba en log. **Re-confirmado post-S0**: la base shared `sanitize_payload` está lista; S1 extiende con DNI/CURP/CUIT/RFC LATAM y declara `SalesAgentCallbackHandler` heredando `BaseAgentCallbackHandler`.
- Acción: DEFERRED-S1 día 1.

#### [LOW] copilot/observability/__init__.py docstring lista subpaquetes que ya no existen físicamente (cost, pricing) — 2026-04-28 — S0 — FLAGGED
- Path: `backend/src/modules/copilot/observability/__init__.py:8-24`
- Descripción: docstring sigue mencionando `pricing` y `cost` como subpaquetes copilot. Post-S0 viven en shared/.
- Impacto: nulo (docstring solo).
- Acción: FLAGGED — S1 limpia cuando retrofitee `ObservabilityCallbackHandler` para heredar `BaseAgentCallbackHandler`.

---

## Detectados durante S2 (cost guardrails cross-agent + costo-agentes admin) — 2026-04-28

### Cross-agent cost cleanup — FIXED

#### [HIGH] cost_aggregator copilot-only SQL hardcoded — 2026-04-28 — S2 — FIXED en S2
- Path antes: `src/modules/copilot/observability/reporting/cost_aggregator.py` (acoplado a `CopilotLlmCallModel`).
- Path post: `src/shared/agent_observability/reporting/cost_aggregator.py` parametrizado por `(db, llm_call_model)` + `CrossAgentCostAggregator` que itera registry.
- Acción: refactor a model-class injection. `top_conversations_by_cost` ahora es opt-in via `_has_conversation_id`; nuevo `top_leads_by_cost` para sales_agent. 10 tests cross-agent verdes.

#### [HIGH] cost_alert_service copilot-only — 2026-04-28 — S2 — FIXED en S2
- Path antes: `src/modules/copilot/observability/application/cost_alert_service.py`.
- Path post: `src/shared/agent_observability/application/cost_alert_service.py`.
- Acción: usa `CrossAgentCostAggregator`. Threshold cross-agent. Alert structlog `cost_alert_threshold_exceeded` con `breakdown_usd_by_agent={copilot, sales_agent}`. 3 RED tests breakdown verdes.

#### [HIGH] aggregate_refresh_task copilot-only — 2026-04-28 — S2 — FIXED en S2
- Path antes: `src/modules/copilot/observability/workers/aggregate_refresh_task.py` (refresh único MV).
- Path post: `src/shared/agent_observability/workers/aggregate_refresh_task.py` refresca **ambos** MVs (`mv_daily_llm_cost_per_tenant` legacy + `mv_daily_llm_cost_per_tenant_v2` cross-agent). Best-effort por MV (failure de uno no aborta el otro).
- Acción: 5 tests verdes — concurrent refresh + partial failure + rollback per-MV.

#### [HIGH] retention_task copilot-only — 2026-04-28 — S2 — FIXED en S2
- Path post: `src/shared/agent_observability/workers/retention_task.py`. Itera `agent_observability_registry()` con SQL parametrizado por `spec.trace_event_table`/`spec.llm_call_table`. Env vars per-agent (`COPILOT_*` y `SALES_AGENT_*`). Best-effort per-table.
- Acción: 6 tests verdes — incluye env-var override per-agent + per-table failure isolation.

### Migration

#### [HIGH] No MV cross-agent — 2026-04-28 — S2 — FIXED en S2
- Path: `backend/alembic/versions/079_cross_agent_daily_cost_mv.py`.
- Descripción: nueva MV `mv_daily_llm_cost_per_tenant_v2` UNION ALL de `copilot_llm_call` + `sales_agent_llm_call` con discriminator `agent_kind`. Unique index `(agent_kind, tenant_id, occurred_on)` — todos NOT NULL para que CONCURRENT refresh no rompa por NULL=NULL.
- Acción: idempotente (`CREATE MATERIALIZED VIEW IF NOT EXISTS` + `CREATE UNIQUE INDEX IF NOT EXISTS`). Verificada en clone DB + concurrent refresh manual.

### Admin

#### [HIGH] Streamlit `costo-agentes` faltante — 2026-04-28 — S2 — FIXED en S2
- Paths: `src/admin/modules/costo_agentes.py` + `src/admin/pages/costo-agentes.py` + `PageSpec` en `app.py`.
- Acción: tabs **Total** (cross-agent KPIs + stacked bar tenant×agente) y **Por agente** (selector via `_shared.render_agent_kind_selector`, drill-down por modelo + serie 60d + top leads cuando `spec.has_lead_id`). Smoke test admin verde + 10 tests page-specific.

### Architecture / cohesión

#### [HIGH] registry shared no podía importar agent models — 2026-04-28 — S2 — FIXED en S2
- Path: `src/shared/agent_observability/registry.py` + `src/shared/infrastructure/agent_observability_bootstrap.py`.
- Descripción: `test_shared_agent_observability_purity` bloquea cualquier import `src.modules.*` desde shared/agent_observability/. La primera versión de registry hardcodeaba ambos imports → arch test rojo.
- Acción: registry pasivo con `register_agent_observability(spec)`. Cada agente registra su spec desde su propio `observability/__init__.py`. Bootstrap module `shared/infrastructure/agent_observability_bootstrap.py` (donde sí se permite importar modules) es importado por main.py / admin/app.py / workers/settings.py / tests/conftest.py. Dependencia invertida cleanly.

### Watchpoints (DEFERRED)

#### [MEDIUM] LiteLLM tier pricing > 200k tokens — 2026-04-28 — S2 — DEFERRED-post-S6
- Path: `src/shared/agent_observability/cost/calculator.py`.
- Descripción: research S2 confirmó que LiteLLM JSON tiene `input_cost_per_token_above_200k_tokens` + variants para output/cache. Sales_agent puede entrar en tier alto con Kimi K2.6 / DeepSeek-V4 + long conversations. Calculator actual ignora tiers.
- Impacto: drift entre `cost_usd` grabado y reconciliation real con LiteLLM si emergen tier hits. Estimado <5% de calls del tenant promedio hoy (LATAM con conversaciones <50 turnos).
- Acción: DEFERRED-post-S6 — agregar tier resolution al calculator + nuevo column opcional `tier_applied` en `*_llm_call` cuando se detecte. Flag para escalar si reconciliation muestra >5% drift.

#### [MEDIUM] PII async post-write worker (Presidio + spaCy NER) — 2026-04-28 — S2 — DEFERRED-post-S6
- Descripción: research S2 confirmó que regex sync (lo que hace `sanitization.py` hoy) cubre 80% del PII pero pierde nombres/organizaciones/locations sin keyword. Presidio + spaCy NER agrega 50-200ms; demasiado para hot path (<10ms p99 target).
- Acción: DEFERRED-post-S6 — `pii_async_audit_task.py` que lee batches de `*_trace_event`/`*_llm_call`, corre Presidio offline, UPDATE row si encuentra PII no enmascarada. Compliance opcional para tenants enterprise; compliance LATAM (LGPD/LFPDPPP/PDPA) ya cubierto por keyword anchoring S1.

---

## Detectados durante S1 (sales-agent observability parity) — 2026-04-28

### Fixes ejecutados

#### [HIGH] Sales_agent sin PII sanitization en trace recorder — 2026-04-27 — diagnóstico — FIXED en S1
- Path: `src/shared/agent_observability/recording/sanitization.py` (extensión LATAM) + `src/modules/sales_agent/observability/recording/callback_handler.py` (uso).
- Acción: PII regex LATAM (DNI / CURP / CUIT / RFC / CC / RUC / CPF / CVV / tarjeta) con keyword guards añadidos. Callback handler enruta toda payload a `sanitize_payload` antes de persistir. 9 tests RED→GREEN cubriendo redacción + false-positives.

#### [HIGH] `sales_audit.py` lee tabla legacy — 2026-04-28 — diagnóstico — FIXED-DUAL en S1
- Path: `src/admin/modules/sales_audit.py` + `src/modules/sales_agent/infrastructure/memory/audit_repository.py`.
- Acción: dual-read pattern activo. AuditRepository.get_event_sourced_rows() + get_last_event_sourced_state(). Banner UI explicita la fuente. clear_user_history extendido a `sales_agent_trace_event` + `sales_agent_llm_call`. Cutover full a S6 — la entrada se cierra entonces.

#### [HIGH] Sales_agent sin retention 90d trace — 2026-04-27 — diagnóstico — FIXED en S2
- Path: `src/shared/agent_observability/workers/retention_task.py` (movido de copilot/ a shared/, parametrizado por registry).
- Acción: worker itera `agent_observability_registry()` y purga ambas tablas (`{agent}_trace_event` 90d default, `{agent}_llm_call` 365d default). Env vars per-agent: `COPILOT_*_RETENTION_DAYS` + `SALES_AGENT_*_RETENTION_DAYS`. Best-effort por tabla (fallo en una no aborta el resto).

### Nuevos detectados en S1

#### [MEDIUM] `SalesAgentCallbackHandler` duplica 6 LangChain callbacks de copilot — 2026-04-28 — S1 — DEFERRED-post-S6
- Path: `src/modules/sales_agent/observability/recording/callback_handler.py` (575 LOC).
- Descripción: copia literal del plumbing copilot (`on_chat_model_start/end/error`, `on_tool_start/end/error`, `on_chain_start/end` + helpers `_extract_usage`, `_from_openai_token_usage`, `_extract_provider_and_model`, etc). ~250 LOC.
- Impacto: drift potencial si copilot evoluciona el callback. Mantenibilidad doble.
- Acción: DEFERRED-post-S6 — lift al `BaseAgentCallbackHandler` (Template Method). Pattern: `on_*` callbacks concretos en abstract base + `_persist_llm_call_row` / `_persist_trace_event_row` overrides per-agent. Trade-off: requiere retrofit copilot al mismo tiempo (scope creep en S1).

#### [LOW] `agent_log_model.py` mencionado en docs no existe — 2026-04-28 — S1 — FLAGGED-S6
- Paths afectados: `02-architecture-target.md §2 (línea Legacy)` + `audit/sales-agent-current-state.md §2.B inbound + §3.b legacy` + entrada `[HIGH] Sales_agent sin retention policy` en este doc.
- Descripción: la tabla legacy real es `llm_logs` con clase `LLMLog` en `src/modules/sales_agent/infrastructure/models/llm_log_model.py`. Las docs mencionan `agent_log_model` que nunca existió.
- Impacto: nulo (cosmético — confunde a future reader, no afecta runtime).
- Acción: FLAGGED-S6 — corregir nombres durante cleanup S6 cuando dropeo de legacy se haga.

#### [LOW] Subscribers crean `SessionLocal()` per-event — 2026-04-28 — S1 — DEFERRED-post-S6 (re-clasificada en S2)
- Path: `src/modules/sales_agent/observability/domain_events/subscribers.py`.
- Descripción: 4 handlers, cada uno abre y cierra una nueva session por event. Best-effort y rápido (single insert + commit), pero contention en pool en alta carga.
- Impacto: si turn rate > 10/s/tenant pool puede saturar.
- Acción: DEFERRED-post-S6 — re-evaluación durante S2 mostró que el costo en producción (sin tráfico real >2/s) no justifica el contextvar refactor todavía. Si reconciliation worker dispara latency spike → priorizar.
- Razón: scope S2 fue cost guardrails cross-agent, no event_bus reshape.

#### [LOW] `_tool_dedup_tracker` en state es magic string — 2026-04-28 — S1 — DEFERRED-post-S6
- Path: `src/modules/sales_agent/application/orchestrator/state.py` + `chat.py` seed + `nodes.py` read.
- Descripción: AgentState es TypedDict pero `_tool_dedup_tracker` es key arbitraria sin tipo. Funciona porque LangGraph propaga dict a todos los nodos.
- Impacto: API no auto-discoverable; renaming silencioso rompe wiring.
- Acción: DEFERRED-post-S6 — tipar AgentState para incluir `_tool_dedup_tracker: ToolCallDedupTracker | None`. Trade-off: AgentState compartido por nodos varios, evitar acoplar al tipo concrete del tracker.

#### [LOW] `from __future__ import annotations` rompe LangGraph runtime introspection — 2026-04-28 — S1 — FLAGGED
- Path: `src/modules/sales_agent/application/orchestrator/graph.py` (workaround aplicado: import directo + sin `__future__`).
- Descripción: con `__future__ annotations`, type hints quedan strings al import time; LangGraph hace `inspect` runtime check del shape (`config: RunnableConfig | None`) y emite UserWarning sobre tipado raro.
- Impacto: warning ruidoso en logs, no breaking.
- Acción: FLAGGED — guardrail preventivo: no usar `from __future__ import annotations` en archivos que LangGraph introspecta. **Watchpoint S6**: agregar arch test que bloquee `__future__ annotations` en `*/orchestrator/graph.py` files si futuro nodo lo agrega.

#### [LOW] Test fixtures de subscribers + node_tool_executor mockean SessionLocal + AuditRepository per-test — 2026-04-28 — S1 — DEFERRED-S6 ratchet pass
- Paths: `tests/modules/sales_agent/orchestrator/test_node_tool_executor_dedup.py:_mute_trace_node_writes` + `tests/modules/sales_agent/observability/test_domain_event_subscribers.py:_stub_session_local`.
- Descripción: 2 tests duplican fixture autouse mockeando `SessionLocal` + repos. Si más tests sales_agent necesitan ese mock se promueve a `tests/modules/sales_agent/conftest.py`.
- Impacto: mínimo — ~20 LOC duplicadas hoy.
- Acción: DEFERRED-S6 ratchet pass — promover a conftest cuando 3+ tests lo requieran.

---

## Detectados durante S4 (ChatModelSpec adopt + per-role multi-provider) — 2026-04-28

### FIXED (entrada arriba ya marcada)

- `[MEDIUM] Sales_agent no usa multi-provider per-role` — FIXED en S4 (ver sección sembrado inicial).

### Nuevos detectados en S4

#### [MEDIUM] DeepSeek alias retire deadline 2026-07-24 — 2026-04-28 — S4 — DEFERRED-pre-Jul-2026
- Path: `backend/src/core/config.py` (env vars `AI_MODEL_REASONING` / `AI_MODEL_AGENT` defaults) + tenant configs en producción.
- Descripción: research S4 confirmó que `deepseek-chat` y `deepseek-reasoner` aliases retiran completamente Jul 24 2026 15:59 UTC. DeepSeek pide migrar explícito a `deepseek-v4-pro` (1.6T params) o `deepseek-v4-flash` (284B).
- Impacto: post-deadline calls a alias rompen con 404. Sales_agent usa env var (`AI_MODEL_REASONING` default `gpt-4o`), pero tenants que sobreescriban a `deepseek-reasoner` rompen.
- Acción: DEFERRED-pre-Jul-2026 — al migrar `AI_PROVIDER_REASONING=deepseek` en producción, default explícito a `deepseek-v4-flash` (más barato, suficiente para qualifier/product_expert) o `deepseek-v4-pro` (cierres complejos si se promueve closer→REASONING en lugar de AGENT). Watchpoint S5/S6.
- Razón: scope S4 fue adopción + mapping; cambio de defaults env-var es deploy concern.

#### [LOW] safety_service.py + chat.py:550 + follow_up_engine.py NO consumen SPECIALIST_TO_ROLE — 2026-04-28 — S4 — DEFERRED-post-S6
- Paths:
  - `backend/src/modules/sales_agent/infrastructure/external/safety_service.py:120` (FAST)
  - `backend/src/modules/sales_agent/application/orchestrator/chat.py:550` (FAST, summary)
  - `backend/src/modules/sales_agent/workers/follow_up_engine.py:83` (FAST, nudge gen)
- Descripción: estas 3 LLM calls también podrían beneficiarse de SSoT (especialmente summary/follow_up: candidatos NANO post-S4). Hoy quedan FAST hardcoded — no son specialists del StateGraph, viven en infra/orchestrator/workers.
- Impacto: cost menor (FAST sigue mappeando a OpenAI gpt-4o-mini típico, ya barato). Drift potencial si se quiere modificar el role centralizado.
- Acción: DEFERRED-post-S6 — extender `SPECIALIST_TO_ROLE` a un mapping más amplio `LLM_ROLE_BY_SITE` cuando S6 ratchet pass formalice los anchors. Promote `summary` + `follow_up_nudge` a NANO.

#### [LOW] Closer temperature 0.4 clamped a 0.6 por Kimi K2.6 — 2026-04-28 — S4 — FLAGGED
- Path: `backend/src/modules/sales_agent/application/agents/sales/nodes.py:174` + `backend/src/shared/infrastructure/llm/providers/kimi.py:78-85`.
- Descripción: closer pide `temperature=0.4`, Kimi K2.6 con thinking-disabled requiere temp 0.6 server-side (clamp + structlog warning).
- Impacto: nulo funcional (clamp + log claro). Pero el specialist code dice 0.4 mientras el wire sale 0.6 — posible confusión para futuro reader.
- Acción: FLAGGED — monitorear post-deploy. Si los closes empíricamente suenan menos creativos que pre-S4 con OpenAI temp 0.4, opciones: (a) override por canal (Telegram más creativo, web más conservador), (b) accept Kimi 0.6 como nuevo baseline, (c) routing condicional pre-S6 según tier de oferta.
- Razón: kimi.py ya hace lo correcto; el log warning lo documenta runtime.

#### [LOW] supervisor + summary/follow_up FAST → NANO no migrado — 2026-04-28 — S4 — DEFERRED-post-S6
- Idem [LOW] anterior. Documentado para que S6 ratchet pass los lift al SPECIALIST_TO_ROLE expandido.

---

## Detectados durante S3 (prompt cache_boundary refactor) — 2026-04-28

### FIXED (entrada arriba ya marcada)

- `[MEDIUM] Sales_agent prompt sin cache_boundary` — FIXED en S3 (ver sección sembrado inicial).

### Nuevos detectados en S3

#### [LOW] `agent_identity` slot mezcla offer + channel rules — 2026-04-28 — S3 — DEFERRED-S5/S7
- Path: `backend/src/modules/sales_agent/infrastructure/prompts/templates/agent_identity.j2`.
- Descripción: el render de `agent_identity` (cacheable per-tenant slot 4) ya incluye `## Catálogo de Ofertas` (offer summary) y `## Reglas por Canal` (channel format). Los slots S3 5 (`OFFER_SUMMARY`) y 6 (`CHANNEL_FORMAT_HINT`) quedan vacíos para no duplicar contenido.
- Impacto: si Brand Studio cambia tono pero offers no, el cache invalida (porque agent_identity es un solo blob). Ideal: split por scope (brand voice cambia raro, offers cambian más, channel cambia rarísimo) → cada slot invalida independiente.
- Acción: DEFERRED — S5 extrae channel rules a `CHANNEL_FORMAT_HINT` (registry-based), S7 extrae offer summary a su propia tabla `brand_voice_summary` mirror copilot lighthouse. La estructura S3 (slots 5+6 placeholder) está lista para cuando esas fases lleguen.

#### [LOW] `_realistic_state` test fixture inline ~30 líneas hard-coded — 2026-04-28 — S3 — DEFERRED-S6
- Path: `backend/tests/modules/sales_agent/prompts/test_build_specialist_system_prompt.py`.
- Descripción: el fixture `_realistic_state` inline ~30 líneas de agent_identity. Si más tests de prompt necesitan el mismo tenant base, promover a `tests/modules/sales_agent/conftest.py` o factory en `tests/modules/sales_agent/fixtures/`.
- Impacto: mínimo hoy (1 test file lo usa). Si S7 brand_voice tests duplican el fixture → promover.
- Acción: DEFERRED-S6 ratchet pass.

#### [LOW] PromptVersionModel override + cache scope — 2026-04-28 — S3 — FLAGGED
- Path: `backend/src/modules/sales_agent/application/prompts/compose.py::_render_static_specialist_body`.
- Descripción: cuando un tenant define un override DB-backed para `specialist_qualifier`, el override entra al slot SALES_PLAYBOOK_HINT (cacheable cross-tenant en design intent, ahora cacheable per-tenant porque cada tenant ve su override). Resultado: cache hit cross-tenant pierde el slot 3, pero per-tenant cache sigue válida si el override no cambia turn-a-turn.
- Impacto: ~5-10% pérdida en hit rate global cross-tenant para tenants con overrides activos. Aceptable — la mayoría de tenants no overridean specialists; quienes lo hacen ganan customización a costo marginal.
- Acción: FLAGGED — monitorear post-deploy via `sales_agent_llm_call.cached_read_tokens` segmentado por tenants con/sin override.

#### [LOW] `_BASE_IDENTITY` y `_TOOLS_HINT` constants en código — 2026-04-28 — S3 — FLAGGED
- Path: `backend/src/modules/sales_agent/application/prompts/compose.py`.
- Descripción: dos string constants (~150 + ~250 tokens) viven inline en compose.py. Cualquier edit obliga deploy. Alternativa: tenerlos en `templates/_base_identity.j2` + `templates/_tools_hint.j2` y renderizarlos via prompt_loader (consistencia con specialists + posibilidad de override via PromptVersionModel).
- Impacto: bajo — son strings universales cross-tenant; no requieren tenant-specific override.
- Acción: FLAGGED — promover a Jinja templates en S5 cuando tools registry sea fuente de verdad de la lista de tools (hoy lista hardcoded en `_TOOLS_HINT` puede driftear de TOOL_REGISTRY).

---

## Cómo agregar entrada (durante fase activa)

1. Detectaste algo durante S{N}.
2. Verificá que es real (test reproductor o evidencia clara).
3. Decidí severity + acción según `04-principles.md §2`.
4. Agregá entrada al final de la sección "Detectados durante S{N}" (creala si no existe).
5. Si FIXED: commit hash en la entrada. Si DEFERRED: target phase clara.
6. NO mover entradas FIXED a sección separada — log es append-only auditable.
