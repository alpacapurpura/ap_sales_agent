# PR-3-campaigns-domain-and-repos

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-3-campaigns-domain-and-repos |
| Sprint padre | S1-domain-campaigns |
| PI padre | PI-1-campaigns-module |
| Estado | ready |
| Tipo | infra |
| Esfuerzo | L |
| Owner PM | /pm |
| Claimed by session | — (cuando in-progress, anotar fecha + módulo trabajo paralelo si aplica) |

## Problema (user-facing)

El módulo `campaigns/` no existe todavía como bounded context con dominio propio. Hoy hay piezas dispersas (sales_agent inbound, MailerLite ETL read-only, assets sin orquestación) y primitivas S0 listas (outbox, idempotency, BudgetGuard, OutboundRateLimiter, ComplianceService, observability `agent_kind="campaign"`). Para que S2 (orchestrator + workers) y S3 (MVP 1 Telegram outbound) puedan construirse sin refactor, se necesita primero el **data plane** (entities + storage + repositories) que persiste campañas, segmentos y unidades de ejecución.

JTBD interno: "Como builder de Nicolify, cuando S2 implemente `CampaignOrchestrator.launch()`, quiero que el dominio (Campaign, CampaignStep, CampaignTask, Segment, SegmentFilter, ChannelRouter port) y los repos async tenant-scoped ya existan y estén verdes, para enfocar S2 en orquestación pura sin diseñar storage al mismo tiempo."

## Outcome esperado

Data plane `campaigns/` shipped, scoped a:

1. **Domain entities** (Pydantic v2 puras, sin framework): Campaign, CampaignStep, CampaignTask, Segment, SegmentSnapshot, SegmentFilter, ChannelRouter port (Protocol), ChannelSendResult, enums (CampaignType, CampaignStatus, StepType, TaskStatus, SegmentType, SegmentFilterCombinator), 11 domain events.
2. **SQLAlchemy 2.0 async models** + repositories tenant-scoped (`tenant_id` mandatory en TODA query, incluido `get_by_id`).
3. **Alembic migration 111** idempotente raw SQL `IF NOT EXISTS` con 6 tablas (`campaign`, `campaign_step`, `campaign_task`, `segment`, `segment_snapshot`, `campaign_template`) + indexes críticos para worker queue performance + un seed mínimo opcional `segment "all_active_leads"`.
4. **TDD por capa** (RED→GREEN domain → infrastructure) + 4 nuevos arch fitness tests + ratchet allowlists shrink-only.
5. **Cero servicios + cero endpoints + cero templates seed** — todo eso es PR-4. Cero ChannelRouter impl, cero workers, cero FE — eso es S2/S3.

**Métricas:**
- 6 tablas en migration 111 idempotente verificada con clone DB.
- `/test-backend` 13 gates verde.
- 4 arch tests nuevos verde + 0 regresión en 89 existentes.
- Cero código en `application/` ni `api/` (verificado con `find` en REVIEW).
- Cobertura tests dominio + repositories ≥80% del nuevo código.

## Walking skeleton (mínimo viable cohesivo)

PR amplio cohesivo (Opus 4.7[1M]). Un sub-deliverable: data plane completo `campaigns/`. Layout:

```
backend/src/modules/campaigns/
├── __init__.py                                        (existente)
├── observability/                                     (existente, PR-1)
├── domain/
│   ├── __init__.py                                    (NEW — exports públicos)
│   ├── enums.py                                       (NEW — 6 StrEnum)
│   ├── campaign.py                                    (NEW — Campaign aggregate root)
│   ├── campaign_step.py                               (NEW — CampaignStep + StepType + step_config schemas)
│   ├── campaign_task.py                               (NEW — CampaignTask)
│   ├── segment.py                                     (NEW — Segment + SegmentSnapshot)
│   ├── segment_filter.py                              (NEW — SegmentFilter DSL Pydantic strict)
│   ├── channel_router.py                              (NEW — Protocol + SendResult)
│   ├── campaign_template.py                           (NEW — CampaignTemplate placeholder schema, populated PR-4)
│   ├── events.py                                      (NEW — 11 domain events heredan DomainEvent)
│   └── repositories.py                                (NEW — 6 ABC interfaces async tenant-scoped)
├── infrastructure/
│   ├── __init__.py                                    (NEW)
│   ├── models/
│   │   ├── __init__.py                                (NEW — registra modelos en Base)
│   │   ├── campaign_model.py                          (NEW)
│   │   ├── campaign_step_model.py                     (NEW)
│   │   ├── campaign_task_model.py                     (NEW)
│   │   ├── segment_model.py                           (NEW)
│   │   ├── segment_snapshot_model.py                  (NEW)
│   │   └── campaign_template_model.py                 (NEW)
│   └── repositories/
│       ├── __init__.py                                (NEW)
│       ├── campaign_repository_impl.py                (NEW)
│       ├── campaign_step_repository_impl.py           (NEW)
│       ├── campaign_task_repository_impl.py           (NEW)
│       ├── segment_repository_impl.py                 (NEW)
│       ├── segment_snapshot_repository_impl.py        (NEW)
│       └── campaign_template_repository_impl.py       (NEW)
└── application/                                       (NO crear — PR-4)
└── api/                                               (NO crear — PR-4)

backend/alembic/versions/
└── 111_campaigns_domain.py                            (NEW — idempotente, down_revision=110)

backend/tests/modules/campaigns/                       (NEW)
└── domain/
    ├── test_campaign_entity.py
    ├── test_campaign_fsm.py
    ├── test_campaign_step_dag.py
    ├── test_campaign_task.py
    ├── test_segment.py
    ├── test_segment_filter_dsl.py
    └── test_events.py
└── infrastructure/
    ├── test_campaign_repository.py
    ├── test_campaign_step_repository.py
    ├── test_campaign_task_repository.py
    ├── test_segment_repository.py
    ├── test_segment_snapshot_repository.py
    └── test_campaign_template_repository.py

backend/tests/architecture/                            (extend)
├── test_campaigns_tenant_isolation.py                 (NEW — gate)
├── test_campaign_fsm_invariants.py                    (NEW — gate)
├── test_segment_filter_pydantic_validated.py          (NEW — gate)
└── test_campaign_task_idx_workers.py                  (NEW — gate, performance crítico 1000 clientes)
```

## Soluciones consideradas

### Decisión D1 — Campaign FSM

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| **A — 6 estados (`draft`/`scheduled`/`running`/`paused`/`completed`/`canceled`)** con FSM matrix explícita | Cubre happy path + pause/resume + cancel terminal. Compatible con FOUNDATION (renombre `active`→`running` clarifica semántica). Test arch enforce transitions | Renombrar `active` (legacy doc) → `running` requiere doc-update | **ELEGIDA** (production-grade) |
| B — 7 estados incluyendo `failed` (legacy FOUNDATION) | Compat 1:1 con doc | `failed` no aporta vs `canceled + last_error`. Confusión user. Worker propio se trackea en `CampaignTask.status` | descartada (drift signal) |
| C — 4 estados (`draft`/`active`/`paused`/`done`) | Más simple | Sin `scheduled` rompe la separación crear-vs-activar (S2 scheduler depende). Sin `canceled` borra historial intencional | descartada |

### Decisión D2 — CampaignStep linked-list vs DAG

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| **A — DAG con `next_step_ids: list[UUID]`** (branching nativo) | Soporta multi-step + branching condicional desde día 1 (welcome 4-step lineal + launch 4-day + branch on score/lifecycle). Production-grade 1000 clientes | Walker más complejo en S2 | **ELEGIDA** (Chris framing 1000 clientes) |
| B — Linked-list `next_step_id: UUID \| None` | Más simple S2 | Limita branching real. Branching emulado con N steps duplicados → footgun | descartada (cuesta más mañana) |
| C — Tree con padre `parent_step_id` | Mejora DAG limitado | DAG ya cubre tree; tree no cubre DAG | descartada |

### Decisión D3 — Segment materialización

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| **A — Filter LAZY default + opcional `SegmentSnapshot` separado** (audience locked en `running`) | Resolve runtime = always fresh. Snapshot opt-in protege audiencia locked en campañas inmutables. Production-grade | Dos modelos coexistiendo (acepted) | **ELEGIDA** |
| B — Materialización siempre (snapshot ALL segments) | Reads más rápidos | Stale cuando lifecycle cambia. Storage explosivo 1000 clientes × 10K leads | descartada |
| C — Solo lazy (sin snapshot) | Más simple | Audiencia "se mueve" durante una campaña en `running` = bug user | descartada |

### Decisión D4 — SegmentFilter DSL minimal vs expressive

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| **A — Predefined fields v1 + abstract base** (`SegmentFilterBase` con `to_sql_predicate()`, subclass `PredefinedSegmentFilter` v1) | Pydantic strict valida shape. Extensible a `ExpressiveSegmentFilter` vNext sin migration breaking | v1 no expone full SQL/MongoDB DSL | **ELEGIDA** (minimal v1 + extensible-ready) |
| B — Full JSON-logic DSL (mongo-style) | Power user | Pesadilla validar / autorizar (SQL injection si mal mapeado). Sobre-ingeniería v1 | descartada |
| C — Hardcoded strings | Más simple | Sin extensibilidad. Imposible Segment Builder Visual PI-3 | descartada |

**Predefined v1 fields (cubre 100% segmentos catálogo FOUNDATION):**
- `lifecycle_stage` (in [...])
- `score_range` (`fit_score_min`/`fit_score_max` + `intent_score_min`/`intent_score_max`)
- `temperature` (in [`COLD`/`WARM`/`HOT`])
- `source` (in [...])
- `country` (in [...]) — alimentado por columna `leads.country` (PR-2)
- `created_at_range` (gte/lte)
- `last_interaction_at_range` (gte/lte)
- `tags` (any/all)
- `is_blacklisted` (bool)
- `has_channel_id` (in [`telegram_id`/`whatsapp_id`/`instagram_id`/`tiktok_id`/`email`])

Combinator: `combinator: "all" | "any"` (AND / OR top-level). Anidamiento NO en v1 (out-of-scope, tracked).

### Decisión D5 — Persistencia Templates

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| **A — Tabla `campaign_template` editable + `template_body JSONB` en PR-4** (PR-3 schema only, vacío) | Templates editables sin migration. Rows globales (`tenant_id` NULL) + per-tenant (futuro). Versionable | UI extra (PR-4 / S4) | **ELEGIDA** |
| B — JSON files en código | Simple deploy | Editar = code change + deploy | descartada |
| C — Combo (rows + files) | Flexible | Drift garantizado | descartada |

PR-3 crea schema y deja tabla vacía. PR-4 seedea 5 templates globales + service.

## Validación técnica preliminar (Technical Sanity Check)

> PM ya ejecutó `Explore` agent durante S1 bootstrap. Architect re-validó código vivo S0 + dependencies brand/offer/crm.

**Estado actual `campaigns/`:**
- `backend/src/modules/campaigns/observability/` ya existe (PR-1) — `agent_kind="campaign"` registrado, `CampaignLlmCallModel` placeholder.
- `domain/`, `infrastructure/`, `application/`, `api/` NO existen — PR-3 los crea (sin `application/` ni `api/`).

**Primitivas S0 disponibles + relación PR-3:**
- `shared/domain_events/outbox/` (PR-1) — los 11 domain events de PR-3 heredan `DomainEvent` base. PR-3 NO emite via outbox (eso es PR-4 service layer); solo declara los eventos para consumo PR-4+.
- `shared/idempotency/` (PR-1) — irrelevante PR-3 (sin webhooks ni decorators acá).
- `shared/billing/` (PR-2) — irrelevante PR-3 (sin LLM call ni outbound aún).
- `shared/compliance/` (PR-2) — irrelevante PR-3 (gate vive en S2 worker).
- `shared/agent_observability/` registrado `agent_kind="campaign"` (PR-1) — irrelevante PR-3 (CampaignCallbackHandler vive en S2).

**Dependencies cross-module (read-only via ports — sin imports directos):**
- `shared/links/ports/crm.py` — Segment.resolve() en S2 leerá leads vía port. PR-3 declara la dependency en domain (`SegmentResolverPort` Protocol) sin implementar.
- `shared/links/ports/offer.py` — Campaign.offer_id FK string referenciada en service layer (PR-4) vía `get_offer(...)`. PR-3 solo persiste UUID string.
- `shared/links/ports/brand.py` — Sin uso PR-3 (BrandSummary lo lee S2/S3 desde sales_agent).

**`leads.country` columna:** PR-2 ya hizo `ALTER TABLE leads ADD COLUMN country` (verificado via migration 110). SegmentFilter v1 puede filtrar por `country` desde día 1.

**Migration head:** `110_billing_compliance_tables`. PR-3 crea `111_campaigns_domain` con `down_revision="110_billing_compliance_tables"`.

**Tests críticos no romper:**
- `tests/architecture/test_outbox_invariants.py` (no toca outbox)
- `tests/architecture/test_ddd_boundaries.py` — PR-3 no importa otros módulos directamente
- `tests/architecture/test_no_new_copilot_module_imports.py` (ratchet 22 frozen)
- `tests/architecture/test_sales_agent_tenant_isolation.py` (no toca sales_agent)

**Conflicto sesiones paralelas:** PI-2 PR-2 suggestions-engine activa en `copilot/application/{services/offer_suggestion_reader,suggestions/}`, `sales_agent/output_manager/*`, copilot observability. PR-3 NO toca esos paths. Cero conflicto.

**Modules afectados:** SOLO `modules/campaigns/{domain,infrastructure}/` + `alembic/versions/111_*.py` + `tests/modules/campaigns/` + `tests/architecture/test_campaigns_*.py`. Cero touch en otros módulos.

**Tiempo estimado:** L (1 architect + 1 builder denso TDD por capa + 1 auditor).

## Decisiones diferidas (explícitas)

| Item | Razón | Cuándo |
|---|---|---|
| `CampaignService` (CRUD + lifecycle FSM) | Service layer = PR-4 | PR-4 |
| `SegmentService.resolve()` + `estimate_size()` | Service layer = PR-4 | PR-4 |
| API endpoints `/campaigns`, `/segments`, `/templates` | API layer = PR-4 | PR-4 |
| 5 templates globales seed (welcome, launch-4day, webinar, cold-reactivation, post-purchase) | PR-4 seedea via INSERT en seed migration o service init | PR-4 |
| `ChannelRouter` impl Telegram/WhatsApp/Email | S2 | S2 |
| `CampaignOrchestrator.launch()` | S2 | S2 |
| `CampaignExecutionWorker` / `CampaignSchedulerWorker` / `SegmentRefreshWorker` ARQ | S2 | S2 |
| `OutboundOrchestrator` sales_agent + `campaign_id` AgentState slot | S3 | S3 |
| FE `/campañas/*` UI | post PI-1 | post PI-1 |
| Anidamiento de `SegmentFilter` (groups con AND/OR mixed) | v1 minimal cubre 100% catálogo FOUNDATION | post PI-1 |
| `ExpressiveSegmentFilter` (full JSON DSL) | Extensible-ready desde día 1 vía abstract base | post PI-1 si user lo pide |
| Materialización de `SegmentSnapshot` automática al `Campaign.status='running'` | Snapshot escritura es service decision (PR-4 service o S2 orchestrator) | PR-4 / S2 |
| Versionado `CampaignTemplate` (column `version` + `parent_template_id`) | Templates v1 sin versioning. Migration aditiva si user pide | post PI-1 |

## Out of scope

- Cualquier service / API endpoint / DTO Pydantic request-response → PR-4
- Cualquier template seed → PR-4
- Cualquier worker ARQ / orchestrator / scheduler → S2
- Cualquier channel sender (Telegram/WhatsApp/Email) → S2
- Cualquier sales_agent OutboundOrchestrator → S3
- Cualquier FE component / hook / route → post PI-1
- Cualquier CRM Hub UI → S4
- Wiring BudgetGuard / ComplianceService / OutboundRateLimiter en domain — gate vive en S2 service/worker
- Cross-module SQL JOIN (storage refs UUID string only; resolución en service PR-4 via port)

## Copilot-first checklist

- [x] **¿Operable conversacional desde copilot?** Default Sí, pero **N/A funcional**: PR-3 es data plane sin user-facing flow. Copilot consume PR-4 endpoints (segment_create, campaign_create) en PI-2 vía `MARKETING_CAMPAIGN_SUBAGENT`.
- [x] **¿Qué tools nuevos requiere?** Ninguno PR-3. PI-2: `campaign_create` / `segment_create` / `campaign_get_status` / `campaign_pause` / `campaign_launch`.
- [x] **¿Cards/UI nueva?** Ninguna PR-3.
- [x] **Si NO copilot → razón documentada:** infra layer (data plane). Copilot consume vía services downstream PR-4 + subagent PI-2.

## Agentes / skills recomendados

(Ref: `process/agent-routing-matrix.md` — fila "Pure backend infra")

| Fase | Agente/skill | Prompt pre-coce | Entregable esperado |
|---|---|---|---|
| Pre-design | `nicolify-architect` | `prompts/01-architect-start.md` | `CONTRACT.md` (este doc) |
| UX | — | — | N/A (no UI) |
| Implementation | `nicolify-backend` | `prompts/02-builder-start.md` | code + tests + migration + IMPL-LOG |
| Audit | `nicolify-backend-auditor` | `prompts/03-auditor-start.md` | `REVIEW.md` (13 gates `/test-backend`) |
| Cierre | `/pm` | `prompts/04-pm-close.md` | `RESULT.md` + `current-state/campaigns.md` update |

**Skills módulo a invocar durante audit:** `backend-expert` (DDD inside-out, master-data, currency-handling, arch-fitness), `metrics-expert` (port `mv_daily_llm_cost_per_tenant_v2` ref check no roto), `architectural-fitness` regla automática.

## Surface impactada

| Tipo | Path / nombre | Cambio |
|---|---|---|
| Tabla DB | `campaign` | nueva |
| Tabla DB | `campaign_step` | nueva |
| Tabla DB | `campaign_task` | nueva |
| Tabla DB | `segment` | nueva |
| Tabla DB | `segment_snapshot` | nueva |
| Tabla DB | `campaign_template` | nueva (placeholder schema, populated PR-4) |
| Module | `backend/src/modules/campaigns/domain/` | nuevo |
| Module | `backend/src/modules/campaigns/infrastructure/models/` | nuevo |
| Module | `backend/src/modules/campaigns/infrastructure/repositories/` | nuevo |
| Migration | `backend/alembic/versions/111_campaigns_domain.py` | idempotente raw SQL |
| Tests | `backend/tests/modules/campaigns/{domain,infrastructure}/` | nuevos |
| Tests arch | `tests/architecture/test_campaigns_tenant_isolation.py` | nuevo |
| Tests arch | `tests/architecture/test_campaign_fsm_invariants.py` | nuevo |
| Tests arch | `tests/architecture/test_segment_filter_pydantic_validated.py` | nuevo |
| Tests arch | `tests/architecture/test_campaign_task_idx_workers.py` | nuevo |
| current-state/ | `current-state/campaigns.md` | append capability "Domain entities + repos + tablas DDL" con lineage PR-3 |

## Tests requeridos (TDD)

### Domain (RED por capa antes implementar)

- `tests/modules/campaigns/domain/test_campaign_entity.py` — Campaign aggregate root invariants (tenant_id required, deleted_at None default, status default DRAFT, transitions FSM via FsmGuard)
- `tests/modules/campaigns/domain/test_campaign_fsm.py` — transitions matrix (draft→scheduled, scheduled→running, running⇄paused, *→canceled, *→completed terminal). Reject inválidas (canceled→running, completed→running, draft→running sin scheduled)
- `tests/modules/campaigns/domain/test_campaign_step_dag.py` — CampaignStep DAG: `next_step_ids` puede contener N IDs (branching), validates no self-loop, validates step_config Pydantic per step_type
- `tests/modules/campaigns/domain/test_campaign_task.py` — CampaignTask invariants (scheduled_at required, status default PENDING, attempt_count ≥0, soft delete deleted_at)
- `tests/modules/campaigns/domain/test_segment.py` — Segment + SegmentSnapshot (filter_dsl Pydantic strict, snapshot lead_ids list[UUID] no duplicates)
- `tests/modules/campaigns/domain/test_segment_filter_dsl.py` — SegmentFilter DSL strict: reject unknown fields (`extra="forbid"`), validate combinator `all|any`, validate score_range, country list, etc. Property-based con Hypothesis para fuzz.
- `tests/modules/campaigns/domain/test_events.py` — 11 domain events heredan DomainEvent + serialization roundtrip + tenant_id required

### Infrastructure (RED por capa)

- `tests/modules/campaigns/infrastructure/test_campaign_repository.py` — CRUD async tenant-scoped (incl. `get_by_id` con tenant_id), `list_by_tenant(tenant_id, limit, offset, status_filter)` paginated, soft delete via `deleted_at`
- `tests/modules/campaigns/infrastructure/test_campaign_step_repository.py` — CRUD + `list_by_campaign(campaign_id, tenant_id)`
- `tests/modules/campaigns/infrastructure/test_campaign_task_repository.py` — CRUD + `claim_pending_for_worker(tenant_id, status, scheduled_before, batch_size)` (FOR UPDATE SKIP LOCKED) + `mark_dispatched`/`mark_failed`/`mark_sent` con tenant_id
- `tests/modules/campaigns/infrastructure/test_segment_repository.py` — CRUD + UNIQUE `(tenant_id, name)` partial WHERE deleted_at IS NULL
- `tests/modules/campaigns/infrastructure/test_segment_snapshot_repository.py` — CRUD + retrieval por segment_id + tenant_id scoping
- `tests/modules/campaigns/infrastructure/test_campaign_template_repository.py` — CRUD + UNIQUE `(tenant_id, slug)` partial (NULL tenant_id = global) + `list_globals()` y `list_for_tenant(tenant_id)`

### Architecture fitness (RED por gate)

- `tests/architecture/test_campaigns_tenant_isolation.py` — toda query `campaign_*` / `segment*` SQLA filtra `tenant_id`. AST scan modelo `Campaign{Step,Task,Template}Model`, `Segment{,Snapshot}Model`. Excepción única documentada: `claim_pending_for_worker` (worker-scope, mismo patrón outbox) en `CROSS_TENANT_ALLOWED_METHODS` allowlist (frozenset ratchet shrink-only).
- `tests/architecture/test_campaign_fsm_invariants.py` — verifica `Campaign._FSM_TRANSITIONS` matrix shape (introspect dict literal). Property-based: ningún state alcanzable post-terminal (canceled/completed → cualquier transition rechazada).
- `tests/architecture/test_segment_filter_pydantic_validated.py` — `SegmentFilter` y `PredefinedSegmentFilter` declaran `model_config = ConfigDict(extra="forbid")`. AST scan + introspect.
- `tests/architecture/test_campaign_task_idx_workers.py` — verifica que migration 111 contiene índice partial `WHERE status IN ('pending','scheduled')` sobre `(tenant_id, status, scheduled_at)`. Performance crítico 1000 clientes — el worker S2 hace polling con esta consulta.

### Migration

- Test idempotency vs prod-clone DB (regla `backend-migrations.md` — el builder corre `pg_dump -s` + apply en migration_test DB).

## Aceptación

- [ ] `/test-backend` 13 gates verde (ruff + format + mypy strict 8 domains + arch fitness 89→93 + coverage 43% + verify + integration + migration idempotency + jscpd 5% + interrogate 85% + pip-audit)
- [ ] 4 arch tests nuevos verde
- [ ] Migration 111 idempotente verificada con clone DB
- [ ] Cero código en `application/` ni `api/` (verificado via `find backend/src/modules/campaigns/{application,api}/ -name "*.py"` retorna vacío salvo `__init__.py` placeholder opcional)
- [ ] Cobertura tests dominio + repos ≥80% del nuevo código
- [ ] `IMPL-LOG.md` completo (sub-deliverables + decisiones + commits)
- [ ] `REVIEW.md` veredicto PASS
- [ ] `RESULT.md` escrito por `/pm`
- [ ] `current-state/campaigns.md` actualizado con lineage PR-3
- [ ] Decisiones registradas en `decisions.md` PI-1
- [ ] Spanish neutro LATAM verificado en docstrings/labels (sin voseo)

## Riesgos

| Riesgo | Mitigación | Owner |
|---|---|---|
| Domain over-engineered (entities sin use case S2/S3 real) | Cada entity referenciada en FOUNDATION + casos S2/S3/S4 documentados. SegmentFilter minimal v1 (10 fields) NO full DSL. CampaignStep DAG (branching real para welcome+launch). | architect |
| SegmentFilter DSL escapa scope | Predefined fields v1 + abstract base extensible-ready. NO json-logic vNext (out-of-scope). | architect |
| CampaignTask worker queue performance 1000 clientes | Index partial `WHERE status IN ('pending','scheduled')` sobre `(tenant_id, status, scheduled_at)`. Test arch enforce existencia. | builder |
| Migration 111 rompe entornos prod (heads divergentes) | Builder corre `pg_dump -s` clone DB regla `backend-migrations.md`. CI gate idempotency. | builder |
| Templates schema rigid (lock-in si v1 mal) | `template_body JSONB` + `slug` natural key + `version` numeric column. Aditivo en PR-4. | architect |
| Anidamiento SegmentFilter user-pedido post v1 | Abstract base `SegmentFilterBase` permite vNext sin breaking change. | architect |
| Cross-module import accidental (DDD violation) | `test_ddd_boundaries.py` ya bloquea. PR-3 NO importa otros modules. Repo deps via UUID string solo. | builder |
| FOUNDATION renombre `active`→`running` confunde | Doc-update PR.md + CONTRACT.md + decisions.md PI-1. Sales agent legacy usa `ACTIVE` en otros contextos sin colisión. | architect |
| Conflicto con sesiones paralelas (PI-2 PR-2 suggestions-engine) | PR-3 toca solo `modules/campaigns/{domain,infrastructure}/` — paths disjuntos. Pull antes commit (regla M5). | builder |
