# 05 · Tech Debt Log

Registro vivo de deuda técnica detectada durante el redesign. Fases agregan; nadie borra (solo marca FIXED con commit hash).

> **Decisión CTO 2026-04-28**: el plan es **autocontenido**. Al cerrar
> S12, este log debe tener **cero entries `DEFERRED-*` flotantes**. Cada
> entry termina FIXED (con commit hash) o WONT-FIX (con razón explícita
> + condición de reapertura). Toda DEFERRED apunta a fase concreta del
> plan (S6.5/S7..S12) — nunca a "post-redesign" abierto. La auditoría
> final está en `phases/S12-final-hardening-zero-debt.md` Definition of
> Done.

Formato:
```
## [SEVERITY] Título corto — YYYY-MM-DD — fase detectora — STATUS
- Path: `archivo:linea`
- Descripción: ...
- Impacto: ...
- Acción: FIXED en {commit} / DEFERRED a S{N} / FLAGGED / WONT-FIX
- Razón: ...
```

Severities: `CRITICAL` (security/data loss) · `HIGH` (functional bug visible) · `MEDIUM` (frágil, falla rara) · `LOW` (style, cosmético).

Statuses: `FIXED` · `DEFERRED-S{N}` (target phase concreta) · `FLAGGED` (watchpoint con phase target para resolver) · `WONT-FIX` (con razón + condición reapertura).

---

## Reclasificación CTO 2026-04-28 (post-S6, pre-S6.5/S11/S12)

Cada entrada `DEFERRED-post-S6` o `DEFERRED-pre-Jul-2026` o `FLAGGED` sin
target concreto fue re-clasificada a fase específica:

| Entry original | Re-clasificación | Cierra en |
|---|---|---|
| `DEFERRED-post-S6` callback handler lift (S1) | `DEFERRED-S11A` | S11A (lift + copilot retrofit, mismo sprint) |
| `DEFERRED-post-S6` chat.py overgrown (S00) | `DEFERRED-S11B` | S11B Strangler Fig orchestrator |
| `DEFERRED-post-S6` closer_studio_service split (S00) | `DEFERRED-S11B` | S11B split Query/Command/Kpi |
| `DEFERRED-post-S6` semantic_router registry (S00) | `DEFERRED-S11B` | S11B registry-based + tenant overrides |
| `DEFERRED-post-S6` lazy imports brand+offer (S00) | `DEFERRED-S11B` | S11B (formaliza ports si decomposition los requiere) |
| `DEFERRED-post-S6` Subscribers SessionLocal per-event (S1) | `DEFERRED-S11B` | S11B (event_bus reshape post-decomposition) |
| `DEFERRED-post-S6` _tool_dedup_tracker magic string (S1) | `DEFERRED-S11B` | S11B (TypedDict update post-decomposition) |
| `FLAGGED-S11` Goldens en `tests/` consumidas por cron prod (S10) | `DEFERRED-S11A` | S11A (snapshot framework agnóstico path) — re-evalua si cron rompe |
| `FLAGGED-S11` Drift threshold 5% global, no per-bucket (S10) | `DEFERRED-S+1` | post-redesign cuando emerja volumen real |
| `FLAGGED-S11` Judge LLM sin `prompt_cache_key` (S10) | `DEFERRED-S+1` | post-redesign cuando RUN_LLM_JUDGE=1 esté activo en prod |
| `DEFERRED-post-S6` LiteLLM tier pricing >200k (S2) | `DEFERRED-S12` | S12 arch ratchet |
| `DEFERRED-post-S6` PII async Presidio (S2) | `WONT-FIX` (S12 documenta) | S12 |
| `DEFERRED-pre-Jul-2026` DeepSeek alias retire (S4) | `DEFERRED-S10` | S10 judge validator + S12 cierre |
| `DEFERRED-post-cutover-window` Drop legacy tables (S6) | `DEFERRED-S6.5` | S6.5 trigger 2026-05-26 |
| `FLAGGED-S7` test fixtures duplicados SessionLocal (S1) | `DEFERRED-S11` | S11 (post event_bus reshape) |
| `FLAGGED` __future__ annotations (S1) | `DEFERRED-S6.5` | S6.5 arch test |
| `FLAGGED` agent_log_model name typo (S1) | `DEFERRED-S6.5` | S6.5 cleanup docs |
| `FLAGGED` typing_simulation_cpm (S5) | `DEFERRED-S12` | S12 wiring post-§3 validation |
| `FLAGGED` Closer temp 0.4/Kimi 0.6 (S4) | `DEFERRED-S10` | S10 conversion monitor + S12 cierre |
| `FLAGGED-S7` voseo en templates Jinja sales_agent (S00) | `DEFERRED-S7` | S7 brand voice integration |
| `DEFERRED-S0` orphan FE components ActivityFeedWidget/CalendarWidget/AppointmentSheet/AvailabilityModal (S00) | `DEFERRED-S6.5` | S6.5 cleanup pass (FE orphans no críticos, sólo touch al hacer cleanup admin migration) |
| `DEFERRED-S0` knowledge_builder.py factory amplio (S00) | `DEFERRED-S11` | S11 (simplifica naturalmente con ports brand/offer) |

**Las entradas FIXED previas (S00/S0/S1/S2/S3/S4/S5/S6) quedan intactas
con su commit hash original — son log auditable, append-only.**

**Cualquier nueva entrada DEFERRED detectada en S7..S12 debe:**
1. Apuntar a fase específica del plan (S{N}).
2. NO usar "post-S{N}" o "post-redesign".
3. Si no hay fase target apropiada → reabrir discusión CTO antes de aceptar la deuda.

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

## Detectados durante S8 (tools: scheduler integration) — 2026-04-28

### FIXED

#### [HIGH] Sales_agent sin booking-link tool nativo — 2026-04-28 — S8 — FIXED en S8
- Path: `src/modules/sales_agent/application/tools/scheduling/`.
- Descripción: previo a S8 sólo existía `tool_check_schedule` (verifica conexión Google Calendar). Lead con intención de agendar requería intervención humana o flujo enrollment manual.
- Acción: FIXED — 3 tools (`create_booking_link`, `verify_booking_status`, `get_available_slots`) + `SchedulerProvider` Strategy + `InternalSchedulerProvider` impl + `MeetingStateService` JSONB owner + `scheduled_meetings` JSONB en checkpoint + 2 ARQ crons (verify_pending_bookings + appointment_reminder_engine T-24h/T-1h/T+1h) + 5 tests RED→GREEN + 5 arch tests Strategy/anchors. 30/30 S8 tests + 1121 sales_agent + arch verde.

#### [HIGH] Sales_agent sin webhook IN para scheduler externos — 2026-04-28 — S8 — FIXED en S8
- Path: `src/modules/sales_agent/api/scheduler_webhooks.py` + `src/modules/sales_agent/application/tools/scheduling/webhook_providers.py`.
- Descripción: tenants con Cal.com / Calendly / GCal push notifications no tenían entry-point para emitir AppointmentEvent automáticos. Internal scheduler usa book endpoint propio, externo no.
- Acción: FIXED — endpoint genérico registry-driven `POST /api/v1/sales-agent/webhooks/scheduler/{provider}` + `WebhookProvider` Protocol + `SCHEDULER_WEBHOOK_PROVIDERS` registry + dedup table `scheduler_webhook_event` con UNIQUE natural key (provider, tracking_id, event_type, occurred_at) + signature verification per-provider via Strategy + arch test `test_scheduler_provider_strategy.py` bloquea hardcoded provider branches. Concrete impls deferred (no Cal.com/Calendly tenant hoy) — entry-point listo cuando llegue.

#### [HIGH] `scheduling_event_handlers` faltante en sales_agent — 2026-04-28 — S8 — FIXED en S8
- Path: `src/modules/sales_agent/application/scheduling_event_handlers.py`.
- Descripción: AppointmentEvent (admin agenda + futuros webhooks) no se reflejaba en scheduled_meetings JSONB. Closer Studio + reminder engine quedaban ciegos a transiciones manuales.
- Acción: FIXED — 5 subscribers (appointment_booked/completed/no_show/cancelled + booking_missed) registrados en main.py startup + worker startup. Best-effort: short-lived sessions + try/except + logger.warning. `_pick_entry_to_update` heuristic (most recent non-terminal) hasta que el AppointmentModel grow tracking_id FK.

#### [HIGH] Reminder cadence T-24h / T-1h / T+1h ausente — 2026-04-28 — S8 — FIXED en S8
- Path: `src/modules/sales_agent/workers/appointment_reminder_engine.py` + 3 templates Jinja `appointment_reminder_{t24h,t1h,postcheck}.j2`.
- Descripción: leads con booking confirmado no recibían recordatorio pre-meeting ni postcheck. Voz de marca no se reusaba.
- Acción: FIXED — cron 15min con ventanas ±15min sobre scheduled_at - 24h / -1h / +30min..+3h. Stamps idempotency (reminder_24h_sent_at, reminder_1h_sent_at, postcheck_sent_at). LLM call con `prompt_cache_key=tenant_id` (S7 rule) + `LLM_ROLE_BY_SITE['appointment_reminder_*']=NANO` (cheap, ~50 tokens output). System prompt slot 5 SSoT brand voice se hereda gratis sin per-tenant template forks.

#### [MEDIUM] TOOL_REGISTRY sin stage scoping — 2026-04-28 — S8 — FIXED en S8
- Path: `src/modules/sales_agent/application/tools/registry.py`.
- Descripción: 14 tools visibles en cualquier stage incluyendo `rapport`. LLM podía generar booking link a leads no calificados.
- Acción: FIXED — `STAGE_TOOL_SCOPE` + `ALWAYS_AVAILABLE` + `get_tools_for_stage(stage, registry) -> dict`. Rapport: solo safety net (escalate, recommend, verify). Discovery+Presentation: agregan `get_available_slots`, `create_booking_link`, `list_public_editions`. Closing: full toolkit. Arch test parity contra TOOL_REGISTRY existente.

### Nuevos detectados durante S8

#### [MEDIUM] `BookingLink` model sin tenant_id column — 2026-04-28 — S8 — FLAGGED-S11
- Path: `src/modules/scheduling/infrastructure/models/booking_link.py` + `src/shared/links/ports/scheduling.py::create_personalized_booking_link`.
- Descripción: prod tiene índice `ix_booking_links_tenant_id` (migration `8bd6b013a46e`) pero el modelo SA no declara la columna. Helper `create_personalized_booking_link` aceptaba `tenant_id` kwarg y se lo pasaba a `BookingLink(...)` → `TypeError` en runtime contra schema actual del modelo. Pre-S8 nunca surfaceó porque el helper se llama solo desde `connections/api/calendar.py:168` con DB Postgres tolerante (silentemente desconoce el kwarg cuando la columna existe en la tabla pero no en el ORM).
- Acción: FIXED-PARCIAL — el helper ahora descarta el `tenant_id` kwarg (`_ = tenant_id  # reserved for parity`) y NO lo pasa a `BookingLink(...)`. El BookingLink se persiste sin tenant_id en el ORM aunque la columna prod exista. **Falta DDD fix**: añadir `tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)` al modelo + migration que normalice. Re-clasificada DEFERRED-S11 (acoplamiento orchestrator decomposition incluye scheduling refactor).
- Razón: S8 scope es nuevo flujo end-to-end de scheduling tools — no DDD-cleanup del modelo `BookingLink` pre-existente.

#### [LOW] AppointmentModel.summary como FK suave a event_slug — 2026-04-28 — S8 — FLAGGED-S11
- Path: `src/modules/scheduling/infrastructure/models/appointment_model.py`.
- Descripción: el modelo no tiene FK explícita a `event_types.slug`; `summary` carga el título legible. `InternalSchedulerProvider._lookup_appointment` acepta `event_slug` como hint pero no filtra por él — usa most-recent-by-lead. Si un lead tiene múltiples appointments con event_slugs distintos, la heurística puede mismatch.
- Impacto: bajo hoy (la mayoría de leads tienen 1 appointment activo). Si crece el use case multi-event (discovery + closing call), surfaceá.
- Acción: FLAGGED-S11 — agregar `event_slug` o FK a EventType al AppointmentModel + actualizar `_lookup_appointment` para filter exacto.

#### [LOW] Webhook signing secret stub via env var — 2026-04-28 — S8 — DEFERRED-S9
- Path: `src/modules/sales_agent/api/scheduler_webhooks.py::_resolve_signing_secret`.
- Descripción: `os.environ.get("SCHEDULER_WEBHOOK_SECRET_<PROVIDER>", "")` — global cross-tenant. Cuando llegue Cal.com / Calendly real, cada tenant configura su propio signing secret en `connections.ChannelConnectionModel.config`. Lookup debe ser por tenant.
- Impacto: nulo hoy (no hay webhook provider concreto wireado). Cuando S+1 aterrice tenant real, surfaceá inmediato.
- Acción: DEFERRED-S9 — reuse pattern `get_channel_credentials` cuando se agregue primer external provider concreto. S9 (payment lifecycle) toca el mismo patrón con MercadoPago/Stripe — coordinar.

#### [LOW] Closer Studio FE sin meetings tab — 2026-04-28 — S8 — DEFERRED-S+1
- Path: `frontend/src/features/closer-studio/components/conversation-detail/`.
- Descripción: scheduled_meetings JSONB poblado pero la UI Closer Studio no lo expone. Operador humano no ve estado de booking links / appointments del lead inline.
- Impacto: humano debe abrir admin agenda para ver meetings. Tolerable inicial — la voz del agente comunica el booking automático.
- Acción: DEFERRED-S+1 — agregar `MeetingsTab.tsx` que lee scheduled_meetings via API endpoint nuevo `GET /api/v1/closer-studio/conversations/{id}/meetings`. FE work standalone — no acopla con S9/S10.

#### [LOW] LLM call temperatura hardcodeada 0.5 en reminder engine — 2026-04-28 — S8 — FLAGGED
- Path: `src/modules/sales_agent/workers/appointment_reminder_engine.py::_render_reminder` línea 235.
- Descripción: temperatura fija 0.5 + max_output_tokens 160. Si Kimi K2.6 en futuro routes a NANO con temperatura clamp diferente, drift posible.
- Impacto: nulo hoy (NANO defaultea gpt-4o-mini que respeta 0.5).
- Acción: FLAGGED — monitorear post-deploy. Si goldens de reminders muestran drift en tone, considerar ROLE_CONFIG mapping.

---

## Detectados durante S6 (architectural fitness tests ratchet + sweeps) — 2026-04-28

### FIXED (sweeps oportunista)

#### [LOW] Copilot shims `output_channels.py` + `format_for_channel.py` + `channel_intent_detector.py` re-export only — 2026-04-28 — S5 — FIXED en S6
- Paths borrados:
  - `backend/src/modules/copilot/domain/output_channels.py`
  - `backend/src/modules/copilot/application/tools/format_for_channel.py`
  - `backend/src/modules/copilot/application/orchestrator/channel_intent_detector.py`
- Acción: 11 call sites migrados a imports directos del SSoT shared (`src.shared.agent_observability.channels.{format,format_for_channel,intent_detector}`). Shims borrados. 113 tests copilot pasan via los nuevos imports + 3064 tests verde post-sweep.

#### [LOW] Test `test_ddd_boundaries.py:75` allowlist apunta a path obsoleto — 2026-04-28 — S5 — FIXED en S6
- Path: `backend/tests/architecture/test_ddd_boundaries.py:75`.
- Acción: allowlist `_PROVIDER_CONTRACT_IMPORTS` actualizado de `src.modules.copilot.domain.output_channels` → `src.shared.agent_observability.channels.format` (SSoT real post-S5).

#### [LOW] safety_service.py + chat.py:550 + follow_up_engine.py NO consumen SPECIALIST_TO_ROLE — 2026-04-28 — S4 — FIXED en S6
- Paths:
  - `backend/src/modules/sales_agent/infrastructure/external/safety_service.py:120` (FAST)
  - `backend/src/modules/sales_agent/application/orchestrator/chat.py:550` (NANO post-promote, was FAST/summary)
  - `backend/src/modules/sales_agent/workers/follow_up_engine.py:83` (NANO post-promote, was FAST/nudge)
- Acción: extendido `domain/model_tier.py` con `LLM_ROLE_BY_SITE` SSoT cubriendo specialists + summary (NANO) + follow_up_nudge (NANO) + safety (FAST). `SPECIALIST_TO_ROLE` queda como sub-view back-compat consumida por `nodes.py` y los tests S4. Los 3 sites consumen `LLM_ROLE_BY_SITE["site"]`. Cost expected: drop ~10-20% en summary/nudge calls (NANO < FAST en provider gpt-4o-mini estable, pero NANO targets baratos cuando AI_PROVIDER_NANO mapea a tier inferior).

### Nuevos arch tests S6 (ratchet — sin allowlist o frozen baseline)

#### `test_no_new_sales_agent_module_imports.py`
- KNOWN_SALES_AGENT_TO_MODULE_IMPORTS frozen con 4 entradas TYPE_CHECKING / lazy.
- Shrinks-only.

#### `test_sales_agent_anchors.py`
- ANCHOR_REGISTRY con 5 entradas hoy (S1/S3/S4/S5).
- Cap 25.

#### `test_sales_agent_callback_handler_invariants.py`
- 8 on_* methods cubiertos (try/except + logger.warning + safe_rollback).
- 0 allowlist.

#### `test_pii_sanitization_coverage_sales_agent.py`
- AST scan: cada `data=<expr>` en repos observability sales pasa por sanitize_payload o es empty dict / passthrough.
- 0 allowlist.

#### `test_sales_agent_tenant_isolation.py`
- AST scan: cada `select(SalesAgentXModel)` filtra `tenant_id`.
- 1 allowlist (reconciliation worker cross-tenant aggregate, lineno specific).

#### `test_subagent_isolation_invariants_sales_agent.py`
- Preventive: REGISTERED_SUBAGENTS_RATCHET = (). Bloquea `astream_events` sin `policy_for`.

### Sweeps NO ejecutados en S6 + razón

#### [LOW] Test fixtures de subscribers + node_tool_executor mockean SessionLocal + AuditRepository per-test — 2026-04-28 — S1 — FLAGGED-S7
- Paths: `tests/modules/sales_agent/orchestrator/test_node_tool_executor_dedup.py:_mute_trace_node_writes` + `tests/modules/sales_agent/observability/test_domain_event_subscribers.py:_stub_session_local`.
- Re-evaluación S6: las 2 fixtures patchean rutas distintas (`tracing.SessionLocal` vs `subscribers.SessionLocal`) — no son literal-duplicate. Promoverlas a conftest requiere parametrización (helper `mute_session_local_at(module_path)`); ratio savings/complexity bajo (2 fixtures × ~10 LOC). Los 6 arch tests nuevos S6 son AST-only y NO suman demanda de SessionLocal mock.
- Acción: FLAGGED-S7 — re-evaluar cuando 3+ tests requieran el mismo mock. Hoy el threshold no se alcanza.

### Deferred posteriores S6

#### [HIGH] Drop tablas legacy `agent_trace_model` + `LLMLogModel` — 2026-04-28 — S6 — DEFERRED-post-cutover-window
- Path: `backend/src/modules/sales_agent/infrastructure/models/agent_trace_model.py` + `llm_log_model.py`.
- Descripción: el plan S6 original incluía drop legacy + cutover `sales_audit.py`. La ventana dual-write son 4 semanas desde S1 close (2026-04-28). Hoy día 0 — la ventana NO cumplió.
- Acción: DEFERRED-post-cutover-window — drop tablas + cutover admin admin se ejecutan post 2026-05-26 (4 semanas dual-write completed). `tests/architecture/test_no_legacy_agent_trace_reads.py` + `test_admin_no_legacy_table_reads.py` se crean ahí.
- Razón: cutover prematuro rompe `sales_audit.py` dual-read; reconciliation worker aún midiendo diff entre tablas.

#### [LOW] `agent_log_model` mencionado en docs no existe — 2026-04-28 — S1 — FLAGGED-cutover-window
- Path: docs `02-architecture-target.md §2.Legacy` + `audit/sales-agent-current-state.md §2.B inbound + §3.b legacy`.
- Descripción: ya FLAGGED en S1 — la tabla legacy real es `llm_logs` con clase `LLMLog`. Cleanup pendiente al ejecutar el drop legacy.
- Acción: FLAGGED-cutover-window — corregir nombre cuando se haga el drop S6.5 (ventana cumplida).

#### [LOW] `from __future__ import annotations` en archivos que LangGraph introspecta — 2026-04-28 — S1 — FLAGGED
- Path: ratchet preventivo NO agregado en S6.
- Razón: el watchpoint S1 quedó documentado. Agregar arch test que bloquee `__future__ annotations` en `*/orchestrator/graph.py` files es scope creep. El runtime warning de LangGraph hoy es ruidoso pero no breaking. Si futuro nodo lo agrega, el warning aparece en logs y lo cazamos antes de prod.
- Acción: FLAGGED — sigue como watchpoint manual.

#### [LOW] `typing_simulation_cpm` declarado pero no consumido (S5 carry-over) — 2026-04-28 — S5 — FLAGGED
- Sin cambio en S6. §3 protección de CPM_SPEED bloquea el wiring.
- Acción: FLAGGED — esperar a fase post-redesign infra que abra ventana §3.

---

## Detectados durante S5 (channel format registry shared) — 2026-04-28

### FIXED

#### [MEDIUM] OutputManager hardcodeado por canal — 2026-04-27 — diagnóstico — FIXED en S5
- Path: `backend/src/modules/sales_agent/infrastructure/external/output_manager.py`.
- Descripción original: "chunk size, CPM, emoji policy hardcodeados en if-else por canal".
- Realidad post-audit: `_parse_response` recibía `channel_type` con `# noqa: ARG003` y splitting era paragraph-only. NO había if-else activos — era un wiring missing, no anti-pattern.
- Acción: FIXED — `_parse_response` consume `ChannelFormat.chunk_size` via `get_channel_format(channel_type)`. `_enforce_chunk_size` + `_split_by_cap` aplican cap con boundary preference (sentence → whitespace → hard cut). §3 protected `process_response` typing simulation + `CPM_SPEED` global intactos. Arch ratchet `tests/architecture/test_no_hardcoded_channel_in_output_manager.py` bloquea regresiones (sin allowlist).

#### [LOW] `agent_identity.j2` mezcla offer + channel rules — 2026-04-28 — S3 — FIXED-PARTIAL en S5
- Path: `backend/src/modules/sales_agent/application/prompts/compose.py`.
- Descripción: slot 6 `CHANNEL_FORMAT_HINT` quedaba vacío en S3. agent_identity.j2 incluía `## Reglas por Canal` inline.
- Acción: FIXED-PARTIAL — slot 6 ahora se puebla via `_channel_format_hint(state)` que consume `get_channel_format(state.channel_type).structure_hint`. La extracción del bloque inline en `agent_identity.j2` queda DEFERRED-S7 (el render Jinja sigue emitiendo el bloque pero ahora el slot 6 lo respalda canonicalmente — duplicación benigna mientras lighthouse no esté activo).
- Razón split: S5 = registry + slot wiring (infra cross-agent). S7 = brand voice lighthouse retire del bloque inline en agent_identity.j2 (toca templates Jinja del tenant).

### Nuevos detectados en S5

#### [MEDIUM] `agent_identity.j2` duplica `## Reglas por Canal` con slot 6 — 2026-04-28 — S5 — DEFERRED-S7
- Path: `backend/src/modules/sales_agent/infrastructure/prompts/templates/agent_identity.j2`.
- Descripción: slot 4 (AGENT_IDENTITY) renderiza `## Reglas por Canal` con texto generado del tenant config. Slot 6 (CHANNEL_FORMAT_HINT) ahora también emite `# Reglas del canal (Label)\n\n{structure_hint}` desde el registry. El LLM lee ambos — son consistentes pero redundantes.
- Impacto: ~100-200 tokens duplicados por turn (slot 6 < slot 4 inline section). Cache hit no se afecta (ambos slots están en prefix cacheable).
- Acción: DEFERRED-S7 — al integrar lighthouse de brand voice (`brand_voice_summary` mirror copilot F3), retirar `## Reglas por Canal` del template Jinja agent_identity.j2 y dejar solo slot 6 como SSoT del channel hint.
- Razón: scope S5 estricto fue mover registry + wirear slot 6. S7 toca templates Jinja del tenant (brand voice integration) — momento natural para limpiar.

#### [LOW] `format_for_channel` tool no wireado en sales tools registry — 2026-04-28 — S5 — DEFERRED-S8
- Path: `backend/src/modules/sales_agent/application/tools/registry.py` (no toca acá).
- Descripción: `format_for_channel` ahora vive en `shared/agent_observability/channels/format_for_channel.py` y está disponible como `@tool`. Sales no lo agrega al registry de tools en S5 — el wiring activo es OutputManager._parse_response consume chunk_size (suficiente para WhatsApp template-safe). Si en S8/S9 surge necesidad de adaptar texto post-generación a otro canal (lead pide "mándame por WhatsApp" pero `channel_type=telegram`), agregar al registry.
- Impacto: nulo hoy.
- Acción: DEFERRED-S8 — evaluar al agregar scheduler tool si format_for_channel es necesario.

#### [LOW] `channel_intent_detector` no wireado en sales orchestrator — 2026-04-28 — S5 — DEFERRED-post-S6
- Path: `backend/src/modules/sales_agent/application/orchestrator/chat.py` (no toca acá).
- Descripción: el detector está disponible vía shared ahora. Sales no consume. BufferService.smart_debounce agrupa fragmentos antes del LLM call; agregar pre-detection de "mándame por X" requiere tocar el flow del buffer — §3 protected.
- Impacto: nulo hoy. Si lead pide explícito otro canal, el agente lo entiende vía LLM (no determinístico).
- Acción: DEFERRED-post-S6 — re-evaluar cuando `chat.py` Stranger Fig refactor abra ventana (post-ratchet S6).

#### [LOW] `typing_simulation_cpm` declarado pero no consumido — 2026-04-28 — S5 — FLAGGED
- Path: `backend/src/shared/agent_observability/channels/format.py` campo `typing_simulation_cpm: int | None = None`.
- Descripción: el campo está disponible en el dataclass pero `OutputManager._calculate_typing_time` sigue usando `cls.CPM_SPEED` global hardcoded en `domain/tuning.py`. §3 protección dice "CPM_SPEED + caracter cap calibrados, no tocar".
- Impacto: nulo (CPM_SPEED global trabaja). Pero hay un campo declarativo sin consumer.
- Acción: FLAGGED — si en S6 ratchet pass se decide permitir override per-canal del typing speed (ej. SMS no necesita typing simulation, voice tampoco), wirear `OutputManager._calculate_typing_time` para preferir `fmt.typing_simulation_cpm` cuando declared.
- Razón: §3 protected del CPM_SPEED bloqueó el wiring en S5.

#### [LOW] Copilot shims `output_channels.py` + `format_for_channel.py` + `channel_intent_detector.py` re-export only — 2026-04-28 — S5 — DEFERRED-post-S6
- Paths:
  - `backend/src/modules/copilot/domain/output_channels.py`
  - `backend/src/modules/copilot/application/tools/format_for_channel.py`
  - `backend/src/modules/copilot/application/orchestrator/channel_intent_detector.py`
- Descripción: cada archivo es ~30-50 LOC re-exportando símbolos del shared. Mantienen back-compat para 6+ consumers copilot (synthesizer, output_sanitizer, chat.py, registry, tests).
- Impacto: bajo. Los tests viejos de copilot siguen verdes (113 passed). Los shims no tienen lógica.
- Acción: DEFERRED-post-S6 — sweep de imports copilot directos a shared como cleanup. NO breaking change.
- Razón: scope S5 fue extract + wire sales. Migrar consumers copilot es scope creep.

#### [LOW] Test `tests/architecture/test_ddd_boundaries.py:75` allowlist apunta a path obsoleto — 2026-04-28 — S5 — DEFERRED-post-S6
- Path: `backend/tests/architecture/test_ddd_boundaries.py:75`.
- Descripción: allowlist `_PROVIDER_CONTRACT_IMPORTS` lista `"src.modules.copilot.domain.output_channels"` para futuros providers `copilot_provider/` que registren canales custom. Post-S5 el SSoT real es `src.shared.agent_observability.channels.format`. La allowlist sigue siendo correcta funcionalmente (el shim re-exporta) pero el path forward-looking debería apuntar al SSoT.
- Impacto: nulo. Tests verdes (113 copilot + 3134 total). Forward-looking nada más.
- Acción: DEFERRED-post-S6 — actualizar allowlist a `src.shared.agent_observability.channels.format` cuando se retiren los shims copilot.

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

## Detectados durante S10 (quality eval loop) — 2026-04-28

### FIXED

#### [HIGH] Sales_agent sin LLM-judge eval loop — 2026-04-27 — diagnóstico — FIXED en S10
- Path: `src/modules/sales_agent/application/quality/judge.py` + `tests/quality/sales_agent_goldens/`.
- Descripción: previo a S10 no existía mecanismo automatizado para detectar regresiones de calidad. Voice fidelity grader (S7) era manual / Streamlit-only.
- Acción: FIXED — `SalesAgentJudge` con 5-dim rubric (brand_voice_fidelity / commercial_effectiveness / pii_safety / channel_format_correctness / tone_locale_fitness) + 20 goldens cubriendo 6 categorías + cron weekly + drift detection (>5% week-over-week → structlog warning) + Streamlit `/sales-agent-quality` dashboard. Stub default; opt-in real LLM via `RUN_LLM_JUDGE=1`.

#### [LOW] Voice fidelity grader sin CI gate — 2026-04-28 — S7 — FIXED-PARTIAL en S10
- Path: `backend/src/modules/brand/application/voice_fidelity/grader.py` (S7 grader) + `backend/src/modules/sales_agent/application/quality/judge.py` (S10 judge).
- Descripción: S7 dejó el grader como Streamlit `/voice-fidelity` + script manual; sin wiring a CI.
- Acción: FIXED-PARTIAL — `SalesAgentJudge` cubre el caso de regresión via cron weekly + goldens. El voice fidelity grader S7 (G-Eval per-preset) sigue separado para evaluation cualitativa profunda; los dos coexisten y se invocan en flujos distintos. CI gate completo para grader S7 sigue siendo opcional (no bloquea S10).
- Razón: el judge S10 detecta regresiones agregadas a nivel pipeline; el grader S7 detecta drift fino per-preset. Diferentes herramientas, diferentes momentos.

### Watchpoints — DEFERRED a S11/S12

#### [LOW] Goldens viven en `tests/` pero el cron las consume — 2026-04-28 — S10 — FLAGGED-S11
- Path: `src/shared/workers/sales_agent_quality_eval.py::_load_goldens` (lazy import a `tests.quality.sales_agent_goldens.conversations`).
- Descripción: convención que el cron de prod importe fixtures de tests es atípica. Funciona porque los goldens son fixtures sintéticas inmutables (sin PII, no requiere mocks). Si crece el catálogo, considerar moverlos a `src/modules/sales_agent/application/quality/goldens/` y hacer el cron path-agnostic.
- Impacto: bajo. Hoy 20 goldens, dataclass simple. Si crece a 100+ con metadata adicional → re-evaluar.
- Acción: FLAGGED-S11 — incluir en el sub-sprint de cohesión orchestrator si los goldens crecen.
- Razón: scope S10 fue establecer el plumbing + threshold + drift detection. Re-ubicación del dataset es scope creep.

#### [LOW] Sample real conversations cuando haya volumen multi-tenant — 2026-04-28 — S10 — DEFERRED-S+1
- Path: `src/shared/workers/sales_agent_quality_eval.py::run_weekly_quality_eval`.
- Descripción: hoy el cron sólo evalúa los 20 goldens fijos. Cuando exista volumen real ≥10 tenants × ≥50 conversations completadas/semana, agregar segundo path que samplee conversaciones reales (con anonimización via `sanitize_payload`) y persista bucket discriminator distinto en `extra_metadata` para que el dashboard distinga golden-vs-real.
- Impacto: nulo hoy (no hay volumen). Cuando emerja, reabrir.
- Acción: DEFERRED-S+1 — futuro post-redesign cuando producción tenga datos.

#### [LOW] Drift threshold 5% es global, no per-bucket — 2026-04-28 — S10 — FLAGGED
- Path: `src/shared/workers/sales_agent_quality_eval.py::DRIFT_THRESHOLD = 0.05`.
- Descripción: cada bucket (qualification, objections, etc) usa el mismo umbral. En la práctica, `closing_payment` puede tener noise mayor que `qualification` (samples más variables) → false-positive risk si la variance natural ya está cerca del 5%.
- Impacto: bajo hoy (stub mode emite 4.0 fijo, no varía). Cuando RUN_LLM_JUDGE=1 corra en producción, monitorear ratio de drift_alerts per bucket; si uno dispara false-positives, configurar threshold per-bucket via `extra_metadata`.
- Acción: FLAGGED — esperar 4 corridas reales antes de tunear.

#### [LOW] Judge LLM no setea `prompt_cache_key=tenant_id` — 2026-04-28 — S10 — FLAGGED
- Path: `src/modules/sales_agent/application/quality/judge.py::_resolve_llm`.
- Descripción: el judge se invoca con NANO sin `prompt_cache_key`. Razón: el prompt prefix del judge es **judge-specific** (rúbrica + dims), no per-tenant; no se beneficia de cache routing per-tenant. Pero múltiples corridas weekly idénticas SÍ se beneficiarían de cache hit en el system prompt. Si el cost del judge crece, considerar `prompt_cache_key="sales_agent_judge_v1"` (constante) para forzar prefix cacheable cross-corrida.
- Impacto: nulo hoy (stub mode). Cuando RUN_LLM_JUDGE=1 corra ~52 weeks/año × 20 goldens × 5 dims = 1040 calls/año. Cost negligible (NANO). No bloqueante.
- Acción: FLAGGED — si el cost del judge aparece en `/costo-agentes`, optimizar.

---

## Cómo agregar entrada (durante fase activa)

1. Detectaste algo durante S{N}.
2. Verificá que es real (test reproductor o evidencia clara).
3. Decidí severity + acción según `04-principles.md §2`.
4. Agregá entrada al final de la sección "Detectados durante S{N}" (creala si no existe).
5. Si FIXED: commit hash en la entrada. Si DEFERRED: target phase clara.
6. NO mover entradas FIXED a sección separada — log es append-only auditable.
