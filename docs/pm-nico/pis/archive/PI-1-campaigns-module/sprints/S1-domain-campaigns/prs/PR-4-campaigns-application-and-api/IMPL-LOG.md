# IMPL-LOG — PR-4-campaigns-application-and-api

> Owner: `nicolify-backend`. Append-only durante implementación. Diario de decisiones.

## Sesion 2026-04-29 — nicolify-backend

### Contexto cargado
- `PR.md` + `CONTRACT.md` + `UI-SPEC.md` PR-4
- Skills: `backend-expert`, `tessl__fastapi`, `tessl__pytest-api-testing`, `tessl__graceful-degradation`
- Base: PR-3 domain layer (commit `f951c282` + migration `7b39b66b`)

---

### Sub-deliverables completados

- [x] Sub-A `85e3ca66` — SegmentFilterEvaluator: evaluador SQL-side (LeadQueryPort, filter criteria → SQLA BinaryExpression), 20+ unit tests filter_evaluator (lifecycle, temperatura, canal, tags, fechas, combinaciones AND/OR)
- [x] Sub-B `5802b82c` — Application services: CampaignService (FSM lifecycle, launch/pause/complete/fail/cancel), SegmentService (resolve+snapshot), CampaignTemplateService (catalog+clone). 60+ tests services incluyendo FSM transitions, idempotency, plan enforcement 402, AsyncSession.
- [x] Sub-C `a0a0bfc7` — API endpoints: 23 rutas REST registradas (`/api/v1/{campaigns,segments,campaign-templates}/`), response_model= en todos los endpoints, X-Tenant-ID header, PaginatedResponse canonical, AsyncSession via Depends.
- [x] Sub-D `04a695f1` — 5 templates globales seed: welcome_new_lead, product_launch_4day, webinar_registration, cold_reactivation, post_purchase_followup. Migration 094 idempotente (`INSERT ... ON CONFLICT DO NOTHING`). UUIDs v5 reproducibles para idempotencia.
- [x] Sub-E `531ed287` — 20 arch tests: test_campaigns_api_response_model + test_campaigns_fsm_service_layer + test_campaigns_pagination_default + test_segment_resolve_sql_filtering. AST-based, zero runtime deps, ruff-clean.

---

### Decisiones implementacion

**FSM SSoT en domain layer (no service).**
CampaignStatus enum + transiciones válidas viven en `campaign.py` domain. El service solo orquesta (valida transición → llama repo → emite evento). Nunca lógica de estado en API.

**SQL-side filtering via JOIN customer_profiles.**
SegmentFilterEvaluator construye SQLA BinaryExpression por criterio. Delega ejecución a LeadQueryPort (DDD boundary: campaigns no importa crm directo). Para `lifecycle` + `temperature` hace JOIN con `customer_profiles` SQLA model vía alias. Sin carga Python de leads completos.

**AsyncSession obligatorio en todo código nuevo.**
Política establecida en PR-3. Repos y services usan `AsyncSession` (sqlalchemy.ext.asyncio). Legacy Session migrado incrementalmente donde aplica. Los tests mockearon session via `AsyncMock` + `_patch_session` pattern (resolvió bloqueador de fixtures).

**Cache TTL 30s + Redis pub/sub invalidation para PlanConfig.**
`PlanService.get_effective(tenant_id)` devuelve config con `lru_cache` + Redis pub/sub para invalidar cross-instance cuando tenant cambia de plan. Soft-cap 105% si MV stale > 1h (documentado en PR-2).

**Plan enforcement via 402 HTTP en services, no en API.**
`CampaignService.launch()` llama `BudgetGuard.check()` antes de cada transición que genera LLM cost. 402 se mapea a HTTPException en router. Copilot/sales_agent no afectados (buckets separados por `agent_kind`).

**Idempotency-key opt-in en endpoints POST.**
Headers `Idempotency-Key: <uuid>` opcionales en `POST /campaigns/` y `POST /campaigns/{id}/tasks/`. Cuando presente, `@idempotent(key_fn=...)` decorator en service devuelve resultado cacheado. Sin key = fire-and-forget normal.

**Templates UUID5 reproducibles (namespace + slug).**
Los 5 templates seed usan `uuid.uuid5(NAMESPACE_DNS, slug)` para UUIDs predecibles. Permite re-run migration idempotente sin duplicados. `ON CONFLICT (id) DO NOTHING` garantiza idempotencia.

**Ruff errors en arch tests resueltos antes del commit.**
Pre-commit hook detectó 6 errores (SIM102, F841, B007, TRY003, EM102, RUF005) en los 4 arch test files. Corregidos en-sesión + ruff format aplicado. Tests GREEN 304/304 post-fix.

---

### Tests escritos

- `tests/modules/campaigns/test_segment_filter_evaluator.py` — 20+ tests: lifecycle/temperature/channel/tags/date range, combinaciones AND/OR, evaluador SQL no carga leads en Python
- `tests/modules/campaigns/test_campaign_service.py` — 30+ tests: FSM transitions válidas/inválidas, launch enforcement 402, idempotency, soft-delete, tenant isolation
- `tests/modules/campaigns/test_segment_service.py` + `test_template_service.py` — 30+ tests: resolve+snapshot, clone template, catalog list, plan gates
- `tests/modules/campaigns/test_campaigns_api.py` — 30+ tests: todos los endpoints 201/200/204/422/404, response_model shape, X-Tenant-ID required, pagination defaults
- `tests/architecture/test_campaigns_api_response_model.py` — AST scan: todos los routers campaigns/segments/templates tienen response_model= (no-DELETE)
- `tests/architecture/test_campaigns_fsm_service_layer.py` — AST scan: FSM transitions no hardcodeadas en API layer, domain-only transitions dict
- `tests/architecture/test_campaigns_pagination_default.py` — import + AST scan: PaginatedResponse shape + list endpoints usan limit=20, offset=0
- `tests/architecture/test_segment_resolve_sql_filtering.py` — AST scan: SegmentFilterEvaluator usa SQLAlchemy constructs, SegmentService usa LeadQueryPort, no cross-module crm imports

---

### Quality gates

- [x] Ruff verde (corregido 6 errores pre-commit en arch tests)
- [x] Ruff format verde (3 files reformatted)
- [x] 304 tests PASS (campaigns module + 4 arch tests nuevos)
- [x] Arch fitness tests verde
- [x] Migration 094 idempotente (`INSERT ... ON CONFLICT DO NOTHING`)

---

### Bloqueadores encontrados y resueltos

**LeadModel.country mapped incorrectamente.**
`customer_profiles.country` no estaba en el SQLA model de CRM. Resuelto en commit `ddb6a220` (PR-3 scope): `mapped_column(String, nullable=True)` agregado. SegmentFilterEvaluator pudo hacer JOIN.

**Fixture dependency_override con AsyncMock.**
Tests de API fallaban porque `override_get_db` inyectaba `Session` síncrono. Resuelto: `_patch_session` helper en conftest reemplaza `get_async_session` dependency con `AsyncMock` que yield session real en-memoria. Pattern documentado en `tests/modules/campaigns/conftest.py`.

**Session → AsyncSession en nuevo código.**
Repos legacy de otros módulos usaban `Session` (sync). Política: todo código nuevo campaigns usa `AsyncSession` exclusivamente. Tests usan `pytest-asyncio` con `asyncio_mode=auto`.

---

### Decisiones diferidas durante implementacion

- **ChannelRouter implementations (Telegram/WhatsApp/Email):** solo el port/interfaz existe. Implementaciones reales en S2 con ARQ workers.
- **CampaignExecutionWorker ARQ:** scheduling + retry logic diferido a S2. Tablas `campaigns_tasks` listas pero sin worker ejecutando.
- **Copilot tools `campaign_get_status` / `campaign_pause`:** diferidos a S3. Domain + API listos; wiring copilot provider en S3.
- **sales_agent OutboundOrchestrator wiring:** S3. CampaignService.launch() listo pero sin consumidor agentico aun.

---

### Surface real entregada

| Tipo | Path | Estado |
|---|---|---|
| SegmentFilterEvaluator | `src/modules/campaigns/application/segment_filter_evaluator.py` | SHIPPED |
| CampaignService | `src/modules/campaigns/application/services/campaign_service.py` | SHIPPED |
| SegmentService | `src/modules/campaigns/application/services/segment_service.py` | SHIPPED |
| CampaignTemplateService | `src/modules/campaigns/application/services/campaign_template_service.py` | SHIPPED |
| DTOs (request/response + pagination) | `src/modules/campaigns/application/dtos/` | SHIPPED |
| campaigns_router (9 endpoints) | `src/modules/campaigns/api/routers/campaigns_router.py` | SHIPPED |
| segments_router (7 endpoints) | `src/modules/campaigns/api/routers/segments_router.py` | SHIPPED |
| templates_router (7 endpoints) | `src/modules/campaigns/api/routers/templates_router.py` | SHIPPED |
| Migration 094 seed templates | `src/modules/campaigns/infrastructure/migrations/094_seed_campaign_templates.py` | SHIPPED |
| 4 arch fitness tests | `tests/architecture/test_campaigns_*.py` | SHIPPED |

---

### Commits

- `85e3ca66` — `feat(campaigns): SegmentFilterEvaluator SQL-side filtering + 20+ unit tests (PR-4 Sub-A)`
- `5802b82c` — `feat(campaigns): CampaignService FSM + SegmentService resolve + TemplateService catalog (PR-4 Sub-B)`
- `a0a0bfc7` — `feat(campaigns): API endpoints registered (campaigns + segments + templates routers, response_model + AsyncSession + pagination) (PR-4 Sub-C)`
- `04a695f1` — `feat(db): seed 5 global campaign templates (PR-4 Sub-D)`
- `531ed287` — `test(architecture): campaigns response_model + pagination + FSM service + SQL filtering (PR-4 Sub-E)`

---

### Rollout S2 plan

1. **CampaignExecutionWorker ARQ** — consume `campaigns_tasks` outbox, retry con exponential backoff, circuit breaker por canal
2. **ChannelRouter implementations** — Telegram (via ManyChat bridge), WhatsApp (via ManyChat), Email (via MailerLite). Cada impl subclase `ChannelRouterPort`.
3. **ComplianceService wiring** — `OutboundRateLimiter.check()` antes de cada send en ChannelRouter
4. **Observability emisión** — CampaignExecutionWorker emite a `campaign_llm_call` + `campaign_trace_event` (tablas ya creadas en migration 083)

### Rollout S3 plan (wiring sales_agent)

1. **copilot provider campaigns** — `src/modules/campaigns/copilot_provider/__init__.py` con `campaign_get_status`, `campaign_pause`, `campaign_launch` tools
2. **sales_agent OutboundOrchestrator** — usa `CampaignService.launch()` para mensajes outbound segmentados
3. **Copilot Marketing Campaign Subagent** — deepagents subagent que orquesta campana completa desde lenguaje natural (PI-2)

---

<!-- @pm: implementación done. Próximo paso: ejecutar prompts/03-auditor-start.md o ejecutar /pm "PR-4 builder done". -->
