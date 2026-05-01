# PR-4-campaigns-application-and-api

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-4-campaigns-application-and-api |
| Sprint padre | S1-domain-campaigns |
| PI padre | PI-1-campaigns-module |
| Estado | ready |
| Tipo | infra + feature |
| Esfuerzo | L |
| Owner PM | /pm |
| Claimed by session | — (cuando in-progress, anotar fecha + módulo trabajo paralelo si aplica) |

## Problema (user-facing)

PR-3 entregó el data plane completo (`Campaign`, `CampaignStep`, `CampaignTask`, `Segment`, `SegmentSnapshot`, `CampaignTemplate` + repos async tenant-scoped + migration 111). **Falta toda la capa CRUD + lifecycle FSM + exposure HTTP**:

- Sin services: ningún caller (interno o externo) puede crear, programar, pausar o cancelar una campaña.
- Sin endpoints REST: copilot subagent (PI-2 commercial_director) y CRM Hub (S4) no tienen API para invocar.
- Sin templates seed: arrancar de cero un agente outbound es fricción alta — Chris quiere "5 plantillas listas el día 1".
- Sin paginación / filtros / cache: mañana 1000 clientes con 50+ campañas activas cada uno = O(N) latency colapsa.

JTBD interno: "Como builder de Nicolify, cuando S2 implemente `CampaignOrchestrator.launch()` y PI-2 conecte al copilot subagent, quiero servicios + API REST + 5 templates ya listos para que esas piezas consuman contratos estables — sin tener que diseñar sobre la marcha — y que escalen a 1000 tenants sin refactor."

## Outcome esperado

Application + API layer shipped, scoped a:

1. **`CampaignService`** (CRUD + lifecycle FSM transitions: `schedule`, `launch` STUB, `pause`, `resume`, `complete`, `cancel`) con event emission via `OutboxService.enqueue_async_from_sync_caller` + cache TTL 30s in-memory + Redis pub/sub invalidation cross-instance.
2. **`SegmentService`** (CRUD + `resolve(at_time)` SQL-side filtering escalable + `estimate_size` cache 5min + `snapshot` opt-in materialization).
3. **`CampaignTemplateService`** (CRUD + global vs tenant + `clone_to_campaign` transaccional).
4. **API REST `/api/v1/campaigns/*`, `/api/v1/segments/*`, `/api/v1/templates/*`** con DTOs Pydantic v2 + `response_model=` mandatory en TODA ruta + paginación obligatoria con `limit ≤ 100`.
5. **5 templates globales seed** (`welcome`, `launch-4day`, `webinar`, `cold-reactivation`, `post-purchase`) en migration 112 idempotente.
6. **4 arch fitness gates nuevos** + ratchet allowlists shrink-only.
7. **Sin orchestrator real** — `launch()` es STUB (marca `launched_at` + emite `CampaignLaunched` event); ChannelRouter + workers viven en S2.
8. **Sin sales_agent wiring** — diferido S3.
9. **Sin FE** — diferido post PI-1.

**Métricas:**
- 5 templates globales visibles via `GET /api/v1/templates/` (read-only, lite check).
- `/test-backend` 13 gates verde (incluyendo 4 arch tests nuevos).
- `CampaignService.list()` con 50+ campañas + filtros: p95 latency < 50ms (cache hit) / < 200ms (cache miss).
- `SegmentService.resolve()` con segment de 10K leads: p95 < 500ms (SQL-side filtering).
- Cobertura tests application + api ≥ 80% del nuevo código.
- Cero código en `campaigns/orchestrator/` ni `campaigns/workers/` (verificado en REVIEW).

## Walking skeleton (mínimo viable cohesivo)

PR amplio cohesivo (Opus 4.7[1M]). Layout:

```
backend/src/modules/campaigns/
├── application/
│   ├── __init__.py                                   (NEW — exports públicos)
│   ├── dtos/
│   │   ├── __init__.py                               (NEW)
│   │   ├── campaign_dtos.py                          (NEW)
│   │   ├── campaign_step_dtos.py                     (NEW)
│   │   ├── segment_dtos.py                           (NEW)
│   │   ├── campaign_template_dtos.py                 (NEW)
│   │   └── pagination.py                             (NEW — PaginatedResponse[T] generic)
│   ├── services/
│   │   ├── __init__.py                               (NEW)
│   │   ├── campaign_service.py                       (NEW)
│   │   ├── segment_service.py                        (NEW)
│   │   ├── segment_filter_evaluator.py               (NEW — pure SQL predicate compiler)
│   │   ├── campaign_template_service.py              (NEW)
│   │   └── cache.py                                  (NEW — TTLCache wrapper + Redis pub/sub invalidation)
│   └── ports/
│       ├── __init__.py                               (NEW)
│       └── lead_query_port.py                        (NEW — Protocol consumed by SegmentService)
├── api/
│   ├── __init__.py                                   (NEW)
│   ├── router.py                                     (NEW — composite mount)
│   ├── campaigns.py                                  (NEW — campaign CRUD + FSM endpoints)
│   ├── segments.py                                   (NEW)
│   ├── templates.py                                  (NEW)
│   └── deps.py                                       (NEW — service factory deps + tenant context shim)

backend/alembic/versions/
└── 112_campaigns_templates_seed.py                   (NEW — idempotente; INSERT 5 templates ON CONFLICT DO NOTHING)

backend/src/main.py                                   (MOD — include_router /api/v1/campaigns + /segments + /templates)
backend/src/shared/links/ports/campaigns.py           (NEW — public surface for cross-module callers, e.g. copilot subagent PI-2)

backend/tests/modules/campaigns/                      (extend)
└── application/
    ├── test_campaign_service.py
    ├── test_campaign_service_fsm.py
    ├── test_segment_service.py
    ├── test_segment_filter_evaluator.py
    ├── test_campaign_template_service.py
    ├── test_cache.py
    └── test_pagination.py
└── api/
    ├── test_campaigns_api.py
    ├── test_segments_api.py
    ├── test_templates_api.py
    └── test_api_response_model_coverage.py

backend/tests/architecture/                           (extend)
├── test_campaigns_api_response_model.py              (NEW — gate)
├── test_campaigns_pagination_default.py              (NEW — gate)
├── test_campaigns_fsm_service_layer.py               (NEW — gate)
└── test_segment_resolve_sql_filtering.py             (NEW — gate)
```

## Soluciones consideradas

### Decisión D6 — Lifecycle FSM ownership (service vs domain)

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| **A — Domain `Campaign.transition_allowed()` SSoT, service delegates** | FSM matrix vive en domain (PR-3 cementado). Service NO duplica lógica → consistencia | Service hace 2 lookups (read entity → check transition → persist) | **ELEGIDA** (cero deuda técnica) |
| B — Service propio FSM dict | Velocidad lookup | Drift garantizado vs domain matrix | descartada |
| C — Trigger Postgres CHECK constraint | DB-level safety | No emite events. No retorna entidad enriquecida | descartada (insuficiente) |

### Decisión D7 — `launch()` stub vs real orchestration

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| **A — STUB: marca `launched_at` + emite `CampaignLaunched` + transición FSM `scheduled→running`** | S2 wirea ChannelRouter/workers consumiendo el event. PR-4 testeable end-to-end SIN bloquearse en S2 | Subscriber S2 todavía no existe → event en outbox queda hasta S2 | **ELEGIDA** (clean cut, scope-respecting) |
| B — Inline real launch (resolve segment + insert tasks) | E2E real desde día 1 | Sale de scope S1 hacia S2. Wire prematuro. | descartada |
| C — Skip `launch()` route entirely | Más simple | FE/copilot PI-2 no puede testear flow | descartada |

### Decisión D8 — `SegmentService.resolve()` strategy

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| **A — SQL-side filtering: compilar `filter_dsl` → `WHERE` clauses + paginated batches** | Production-grade 1000 clientes (10K+ leads/tenant). p95 < 500ms | Compiler complejo (PredefinedSegmentFilter → SQL) | **ELEGIDA** (Chris framing) |
| B — Cargar leads tenant en Python + filtrar en memoria | Simple | O(N) memory + latency. Colapsa con 10K leads. Anti-pattern. | descartada (deuda técnica) |
| C — Postgres function side | Performance superior | Mantenimiento DB-side. Test gap | descartada |

`SegmentFilterEvaluator` — clase pure-function en `application/services/`:
- `to_sql_predicate(filter_dsl) -> ColumnElement` (SQLA expression para `select(LeadModel).where(...)`).
- `evaluate_one(filter_dsl, lead) -> bool` (in-memory para tests + edge cases).
- Soporta los 10 fields v1 del SegmentFilter (lifecycle_stage, score_range, temperature, source, country, created_at_range, last_interaction_at_range, tags, is_blacklisted, has_channel_id) con combinator `all|any`.

### Decisión D9 — Cache strategy (cero refactor 1000 clientes)

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| **A — In-memory `TTLCache` (`cachetools`) + Redis pub/sub invalidation cross-instance (mirror PlanService PR-2 patrón)** | Cero hop Redis read-path → < 1ms cache hit. Invalidation accurate (pub/sub). Mismo patrón cementado en `shared/billing/` | Memory cost (negligible: 50KB / 1000 tenants × 50 campañas) | **ELEGIDA** |
| B — Redis-only cache | Cross-instance trivial | Hop Redis = +5-10ms p50. Innecesario | descartada |
| C — Sin cache | Más simple | List endpoint p95 colapsa con 1000 clientes | descartada (deuda técnica) |

Cache TTLs:
- `CampaignService.list()`: 30s por `(tenant_id, filters_hash)`. Invalidación on `create/update/delete/<FSM transition>`.
- `SegmentService.estimate_size(segment_id)`: 5min. Invalidación on `update segment`.
- `CampaignTemplateService.list_available(tenant_id)`: 5min. Invalidación on `template create/update/delete`.
- Redis channels: `cache_invalidate:campaigns:{tenant_id}`, `cache_invalidate:segments:{tenant_id}`, `cache_invalidate:templates:global` + `cache_invalidate:templates:{tenant_id}`.

### Decisión D10 — Templates persistence (rows vs JSON files)

Confirmar PR-3 D5: tabla `campaign_template` editable + `template_body JSONB`. PR-4 seedea 5 globals via migration 112 idempotente con `INSERT ... ON CONFLICT (slug) WHERE tenant_id IS NULL DO NOTHING`. Editables en runtime; clone a campaign via `CampaignTemplateService.clone_to_campaign`.

### Decisión D11 — `CampaignStep` CRUD ownership

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| **A — `POST /campaigns/{id}/steps`, `PATCH /campaigns/{id}/steps/{step_id}`, `DELETE /campaigns/{id}/steps/{step_id}` (nested)** | Resource hierarchy clara. Tenant + campaign tenant verificado en cada call | Más rutas | **ELEGIDA** |
| B — `PUT /campaigns/{id}` con steps inline | Single roundtrip | Atomicity issues con DAG editing. Optimistic locking complejo | descartada |
| C — Sin endpoints, steps solo via templates | Más simple | Imposible custom campaigns sin templates | descartada |

`CampaignStepService` no es service separado; vive como methods en `CampaignService` (`add_step`, `update_step`, `delete_step`, `list_steps`). Razón: cohesión alta + un solo aggregate root (Campaign).

### Decisión D12 — Segment snapshot creation (lazy vs eager)

PR-3 cementó D3 (lazy default + opt-in snapshot). PR-4 implementa:
- `POST /api/v1/segments/{id}/snapshot` → llama `SegmentService.snapshot(segment_id)` → resolve current → INSERT row → emite `SegmentSnapshotted`. **User-explicit**.
- S2 orchestrator decide cuándo auto-snapshot al `Campaign.status='running'` con `Segment.segment_type=STATIC` — fuera scope PR-4.

### Decisión D13 — Idempotency en POST writes

| Operation | Idempotency strategy |
|---|---|
| `POST /campaigns/` | Header `Idempotency-Key` opt-in via `@idempotent` decorator (`shared/idempotency/`). Sin header → POST normal (allow duplicate) — racing UI no es problema con cache 30s + check name. |
| `POST /campaigns/{id}/{transition}` | Idempotente by domain FSM: re-pause de paused = no-op silent (return current state). Re-launch de running = 409. |
| `POST /segments/` | Natural key `(tenant_id, name)` UNIQUE → DB rejects duplicate, service re-raises 409. |
| `POST /segments/{id}/snapshot` | NO idempotente intencionalmente (cada snapshot es punto en tiempo distinto). |
| `POST /templates/{id}/clone` | Header `Idempotency-Key` opt-in. |

### Decisión D14 — Bucket `agent_kind="campaign"` en BudgetGuard (PR-2 wiring deferred S2)

PR-4 NO wirea `BudgetGuard.check` en `launch()` stub (S2 wirea cuando workers reales hagan LLM calls). Confirmado scope-cut explícito.

## Validación técnica preliminar (Technical Sanity Check)

**Estado actual `campaigns/`:**
- `domain/` + `infrastructure/{models,repositories}/` shipped (PR-3, PASS).
- `observability/` shipped (PR-1).
- `application/` + `api/` NO existen → PR-4 los crea.

**Primitivas S0 disponibles (consumidas PR-4):**
- `OutboxService.enqueue_async_from_sync_caller(event, *, session=...)` desde `shared/domain_events/outbox/` — usado en cada FSM transition.
- `@idempotent(key_fn=lambda req: f"campaign-create:{req.headers['Idempotency-Key']}", ttl_seconds=86400)` opt-in por endpoint.
- `PlanService.get_effective(tenant_id)` — usado para validar `max_campaigns_active` cap pre-create.
- `BudgetGuard` / `OutboundRateLimiter` / `ComplianceService` — primitivas expuestas, NO consumidas en PR-4 (consumers reales = S2 worker / S3 sales_agent).

**Primitivas codebase reusables:**
- `cachetools.TTLCache` + Redis pub/sub pattern → mirror `PlanService.subscribe_cache_invalidations()` (PR-2).
- `get_tenant_context` / `get_current_user` deps en `iam/api/dependencies.py` (X-Tenant-ID header resolver).
- `get_db` (sync Session) y patrón AsyncSession factory en `shared/billing/infrastructure/` (PR-2 cementado).

**Modules afectados:** SOLO `modules/campaigns/{application,api}/` + `alembic/versions/112_*.py` + `shared/links/ports/campaigns.py` + `main.py` (router register) + `tests/modules/campaigns/{application,api}/` + `tests/architecture/test_campaigns_*.py`. Cero touch en otros modules de negocio (lectura ports `crm/offer/brand/tenant_profile`).

**Tests críticos no romper:**
- 4 arch tests PR-3 (`test_campaigns_tenant_isolation.py`, `test_campaign_fsm_invariants.py`, `test_segment_filter_pydantic_validated.py`, `test_campaign_task_idx_workers.py`).
- `test_ddd_boundaries.py`, `test_outbox_invariants.py`, `test_no_new_copilot_module_imports.py` (ratchet 22 frozen).
- `test_master_data_compliance.py` (DateTime timezone=True), `test_currency_consistency.py` (N/A), `test_domain_purity.py`.

**Conflicto sesiones paralelas:** PI-2 PR-2 suggestions-engine activa en `copilot/application/{services/offer_suggestion_reader,suggestions/}`, `sales_agent/output_manager/*`, copilot observability. PR-4 NO toca esos paths. Cero conflicto.

**Tiempo estimado:** L (1 architect + 1 builder denso TDD por capa + 1 auditor).

## Decisiones diferidas (explícitas)

| Item | Razón | Cuándo |
|---|---|---|
| `CampaignOrchestrator.launch()` real (resolve segment → idempotent task creation → outbox enqueue → ARQ enqueue) | Out of scope S1 | S2 |
| `CampaignExecutionWorker` / `CampaignSchedulerWorker` / `SegmentRefreshWorker` ARQ | S2 |
| ChannelRouter impl (Telegram/WhatsApp/Email) | S2 |
| Auto-snapshot on `Campaign.status='running'` cuando `segment_type=STATIC` | S2 orchestrator decide | S2 |
| sales_agent `OutboundOrchestrator` + `campaign_id` AgentState slot | S3 |
| Wire `BudgetGuard.check` / `OutboundRateLimiter.check` / `ComplianceService.check` en launch path | Wire vive en worker S2 |
| Inbound reply recognition → tag conversación con `campaign_id` | S3 |
| Marketing campaign subagent copilot (`commercial_director`) tools (`campaign_create`, `segment_create`, `campaign_get_status`, `campaign_pause`, `campaign_launch`) | PI-2 |
| FE `/campañas/*` UI | post PI-1 |
| Mini CRM Hub `/sales/contactos` | S4 paralelo |
| `ExpressiveSegmentFilter` (full DSL) + group nesting (mixed AND/OR) | PR-3 cementó abstract base extensible-ready | post PI-1 |
| `CampaignTemplate` versionado (`parent_template_id`) | aditivo migration | post PI-1 |
| Endpoint `GET /campaigns/{id}/stats` (SENT/RESPONDED/CONVERTED) | requiere CampaignTask data real (S2/S3) | S3 |

## Out of scope

- Cualquier worker / orchestrator / scheduler → S2
- Cualquier ChannelRouter sender (Telegram/WhatsApp/Email/IG DM) → S2
- Cualquier sales_agent wiring → S3
- Cualquier FE → post PI-1
- Cualquier copilot subagent / tools → PI-2
- Real `launch()` end-to-end (segment resolve → task insert → ARQ enqueue) → S2
- Auto-snapshot al transitionar a running → S2
- `CampaignTask` mutation routes (mark_dispatched/sent/failed/skipped) — solo via worker S2, NO API HTTP
- Bulk operations (`POST /campaigns/bulk-cancel`, etc.) — out of scope

## Copilot-first checklist

- [x] **¿Operable conversacional desde copilot?** Default Sí, **N/A funcional PR-4**: PR-4 expone API REST consumible. PI-2 commercial_director subagent wirea las tools.
- [x] **¿Qué tools nuevos requiere?** Ninguno PR-4. PI-2: `campaign_create`, `campaign_launch`, `campaign_pause`, `campaign_resume`, `campaign_cancel`, `campaign_get_status`, `segment_create`, `segment_resolve`, `template_clone`.
- [x] **¿Cards/UI nueva?** Ninguna PR-4 (sin FE). PI-2 introduce `CampaignProposalCard`, `SegmentPreviewCard`, `TemplateBrowserCard`.
- [x] **Si NO copilot → razón documentada:** PR-4 = exposure layer. Copilot consume PI-2 vía tools que invocan estos endpoints.

## Agentes / skills recomendados

(Ref: `process/agent-routing-matrix.md` — fila "Backend feature: services + endpoints + migration seed")

| Fase | Agente/skill | Prompt pre-coce | Entregable esperado |
|---|---|---|---|
| Pre-design | `nicolify-architect` | `prompts/01-architect-start.md` | `CONTRACT.md` (este doc) |
| UX | — | — | N/A (no UI) |
| Implementation | `nicolify-backend` | `prompts/02-builder-start.md` | code + tests + migration 112 + IMPL-LOG |
| Audit | `nicolify-backend-auditor` | `prompts/03-auditor-start.md` | `REVIEW.md` (13 gates `/test-backend`) |
| Cierre | `/pm` | `prompts/04-pm-close.md` | `RESULT.md` + `current-state/campaigns.md` update |

**Skills módulo a invocar durante audit:** `backend-expert` (DDD inside-out, Pydantic v2 + response_model, Ruff, arch-fitness), `copilot-expert` (anchor budget gating refleja API surface — ver §11), `sales-agent-expert` (anchor outbound gating sin regression), `metrics-expert` (port `mv_daily_llm_cost_per_tenant_v2` ref no roto).

## Surface impactada

| Tipo | Path / nombre | Cambio |
|---|---|---|
| API endpoint | `POST /api/v1/campaigns/` | nuevo |
| API endpoint | `GET /api/v1/campaigns/` (paginated + filters) | nuevo |
| API endpoint | `GET /api/v1/campaigns/{id}` | nuevo |
| API endpoint | `PATCH /api/v1/campaigns/{id}` | nuevo |
| API endpoint | `DELETE /api/v1/campaigns/{id}` | nuevo |
| API endpoint | `POST /api/v1/campaigns/{id}/{schedule,launch,pause,resume,complete,cancel}` | 6 nuevos (FSM) |
| API endpoint | `POST /api/v1/campaigns/{id}/steps/` | nuevo |
| API endpoint | `PATCH /api/v1/campaigns/{id}/steps/{step_id}` | nuevo |
| API endpoint | `DELETE /api/v1/campaigns/{id}/steps/{step_id}` | nuevo |
| API endpoint | `GET /api/v1/segments/` (paginated) | nuevo |
| API endpoint | `POST /api/v1/segments/` | nuevo |
| API endpoint | `GET /api/v1/segments/{id}` | nuevo |
| API endpoint | `PATCH /api/v1/segments/{id}` | nuevo |
| API endpoint | `DELETE /api/v1/segments/{id}` | nuevo |
| API endpoint | `POST /api/v1/segments/{id}/resolve` | nuevo |
| API endpoint | `POST /api/v1/segments/{id}/snapshot` | nuevo |
| API endpoint | `GET /api/v1/templates/` | nuevo |
| API endpoint | `POST /api/v1/templates/{id}/clone` | nuevo |
| Module | `backend/src/modules/campaigns/application/` | nuevo |
| Module | `backend/src/modules/campaigns/api/` | nuevo |
| Module | `backend/src/shared/links/ports/campaigns.py` | nuevo (cross-module port para PI-2) |
| Migration | `backend/alembic/versions/112_campaigns_templates_seed.py` | idempotente raw SQL INSERT ON CONFLICT |
| Tests | `backend/tests/modules/campaigns/{application,api}/` | nuevos |
| Tests arch | `tests/architecture/test_campaigns_api_response_model.py` | nuevo |
| Tests arch | `tests/architecture/test_campaigns_pagination_default.py` | nuevo |
| Tests arch | `tests/architecture/test_campaigns_fsm_service_layer.py` | nuevo |
| Tests arch | `tests/architecture/test_segment_resolve_sql_filtering.py` | nuevo |
| Env var | `CAMPAIGNS_LIST_CACHE_TTL_SECONDS=30` | nuevo (opcional) |
| Env var | `CAMPAIGNS_LIST_LIMIT_MAX=100` | nuevo (opcional) |
| Env var | `SEGMENT_ESTIMATE_CACHE_TTL_SECONDS=300` | nuevo (opcional) |
| Env var | `TEMPLATES_CACHE_TTL_SECONDS=300` | nuevo (opcional) |
| current-state/ | `current-state/campaigns.md` | append capability "Application services + REST API + 5 templates seed shipped" con lineage PR-4 |

## Tests requeridos (TDD)

### Layer A — Application services (RED por capa antes implementar)

- `test_campaign_service.py` — CRUD async tenant-scoped (create, get, list paginated + filters, update con FSM 409, soft delete con event)
- `test_campaign_service_fsm.py` — todas las transitions válidas + reject inválidas + idempotencia (re-pause de paused = no-op) + 409 transitions inválidas
- `test_segment_service.py` — CRUD + resolve(at_time) SQL-side + estimate_size cache + snapshot con event
- `test_segment_filter_evaluator.py` — `to_sql_predicate(filter_dsl)` produce SQLA expression correcta para cada combinator + cada field (10 fields v1)
- `test_campaign_template_service.py` — CRUD global vs tenant + clone_to_campaign transaccional + cache
- `test_cache.py` — TTLCache hit/miss + Redis pub/sub invalidation cross-instance (mock Redis pubsub)
- `test_pagination.py` — `limit ≤ MAX` enforcement + offset + `total_count`

### Layer B — API endpoints (httpx AsyncClient + pytest-asyncio)

- `test_campaigns_api.py` — happy path + 401/404/409 + paginación + filters + Idempotency-Key
- `test_segments_api.py` — happy path + resolve + snapshot + 409 dup name
- `test_templates_api.py` — list globals + clone (transaction)
- `test_api_response_model_coverage.py` — escanea router → toda ruta declara `response_model=`

### Layer C — Architecture (introspection + AST scan)

- `test_campaigns_api_response_model.py` — toda ruta `/api/v1/{campaigns,segments,templates}/*` declara `response_model=` (regla `pii-sanitisation.md`)
- `test_campaigns_pagination_default.py` — list endpoints requieren `limit` query param con `le=100` constraint
- `test_campaigns_fsm_service_layer.py` — `CampaignService` NO duplica FSM lógica (AST scan: si encuentra `dict` literal con keys que matchean `CampaignStatus` values fuera de `Campaign._FSM_TRANSITIONS` → fail)
- `test_segment_resolve_sql_filtering.py` — `SegmentService.resolve()` AST scan: NO encuentra `for lead in leads:` o similar Python loop sobre leads en filter path (escalabilidad 1000 clientes)

### Migration

- Test idempotency clone-DB (regla `backend-migrations.md`) + verificación de los 5 templates seed (count + slugs).

### Integration

- E2E test: crear campaign DRAFT → add 3 steps → schedule → launch (STUB) → verificar event `CampaignLaunched` en `domain_event_outbox` table (sin worker dispatcher activo).

## Aceptación

- [ ] `/test-backend` 13 gates verde (ruff + format + mypy strict 8 domains + arch fitness + coverage 43% + verify + integration + migration idempotency + jscpd 5% + interrogate 85% + pip-audit)
- [ ] 4 arch tests nuevos verde + 0 regresión en existentes
- [ ] Migration 112 idempotente verificada con clone DB; 5 templates seedeados verificable via `SELECT COUNT(*) FROM campaign_template WHERE tenant_id IS NULL` = 5
- [ ] Cobertura tests application + api ≥ 80% del nuevo código
- [ ] Cero código en `campaigns/orchestrator/` o `campaigns/workers/` (REVIEW verifica via `find`)
- [ ] Cero wiring real `BudgetGuard.check` / `OutboundRateLimiter.check` / `ComplianceService.check` en launch path (S2 lo hace)
- [ ] `IMPL-LOG.md` completo (sub-deliverables + decisiones + commits)
- [ ] `REVIEW.md` veredicto PASS
- [ ] `RESULT.md` escrito por `/pm`
- [ ] `current-state/campaigns.md` actualizado con lineage PR-4
- [ ] Decisiones registradas en `decisions.md` PI-1 (D6-D14)
- [ ] Spanish neutro LATAM en docstrings + DTO descriptions + template names/descriptions (sin voseo)
- [ ] Master-data: `DateTime(timezone=True)` mantenido; service usa `utc_now()` siempre
- [ ] Tenant isolation: cada query repo recibe `tenant_id` (heredado PR-3 + tests application verifican via inspect mock)

## Riesgos

| Riesgo | Mitigación | Owner |
|---|---|---|
| Service duplica FSM lógica → drift vs domain | Arch test `test_campaigns_fsm_service_layer.py` enforce delegación a `Campaign.transition_allowed()` | architect |
| `SegmentService.resolve()` carga leads en Python (insostenible 1000 clientes) | Arch test `test_segment_resolve_sql_filtering.py` AST scan + perf benchmark con 10K leads p95 < 500ms | architect |
| Cache stale cross-instance (2 pods, uno cachea outdated) | Mirror PlanService Redis pub/sub patrón cementado PR-2. Test cross-instance simulado | builder |
| `launch()` stub confunde a integradores ("¿esto envía mensajes?") | Docstring + DTO `CampaignLaunchResponse` incluye `notice: str` ("STUB: no real send. S2 wires execution.") + arch test verifica el notice presente | architect |
| Templates seed schema rigid (lock-in si v1 mal) | `template_body JSONB` + `slug` natural key + `version` numeric. Aditivo en migrations futuras. | architect |
| Cross-module import accidental al consumir leads | `SegmentService` consume `LeadQueryPort` Protocol (en `campaigns/application/ports/`) implementado por `crm` adapter via `shared/links/ports/`. Cero import directo. | builder |
| Idempotency-Key opt-in deja ventana race UI | Cache 30s + check name UNIQUE → race produce 409 explícito (no silent dup) | architect |
| `response_model=` PII leak en SegmentResolveResponse `lead_ids` | Solo UUIDs (no PII por sí mismos). Si `evidence` JSONB contiene email/phone → masked via sanitizer service | architect |
| Migration 112 conflicts si templates ya existen post backfill manual | `INSERT ... ON CONFLICT (slug) WHERE tenant_id IS NULL DO NOTHING` idempotente | builder |
| Conflict sesiones paralelas (PI-2 PR-2 suggestions-engine) | PR-4 toca `modules/campaigns/{application,api}/` — paths disjuntos. Pull antes commit (regla M5). | builder |
| `BudgetGuard` cap `max_campaigns_active` no validado pre-create → tenant excede plan | `CampaignService.create` consulta `PlanService.get_effective(tenant_id).max_campaigns_active`; si excede → 402 Payment Required con plan upgrade hint | architect |
