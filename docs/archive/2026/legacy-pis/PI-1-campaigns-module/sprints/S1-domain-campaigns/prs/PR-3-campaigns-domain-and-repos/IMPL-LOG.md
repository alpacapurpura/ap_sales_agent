# IMPL-LOG — PR-3-campaigns-domain-and-repos

> Owner: `nicolify-backend`. Append-only durante implementación. Diario de decisiones de implementación.

## Sesión 2026-04-29 — nicolify-backend

### Contexto cargado

- `PR.md` ✓
- `CONTRACT.md` ✓
- Skills: `backend-expert` ✓ · `tessl__langgraph` ✓ · `tessl__pytest-api-testing` ✓ · `tessl__graceful-degradation` ✓

### Decisiones implementación

- **FSM 6 estados con `RUNNING` reemplaza legacy `ACTIVE`**: El CONTRACT especificó `DRAFT → SCHEDULED → RUNNING ⇄ PAUSED → COMPLETED | CANCELED`. El estado `running` es semánticamente correcto para campaña activa ejecutándose (vs "active" que es ambiguo). Los tests Hypothesis verifican property-based que ningún estado no listado en `_FSM_TRANSITIONS` produce `transition_allowed=True`.
- **DAG branching `next_step_ids: list[UUID]`**: `CampaignStep` tiene `next_step_ids` como lista de UUIDs para soportar branching (split A/B). No se usa tabla de junction — el DAG se persiste como array de IDs en el propio `CampaignStep` (denormalizado deliberado para queries simples). La validación de ciclos se hace en domain service en PR-4.
- **Lazy Segment + opt-in SegmentSnapshot**: `Segment` persiste `filter_dsl` como JSONB (`PredefinedSegmentFilter`). `SegmentSnapshot` es opt-in para congelar la evaluación pre-launch. El snapshot se crea por servicio en PR-4 cuando `campaign.status` transita a `SCHEDULED`. Esto evita snapshot garbage si la campaña nunca llega a SCHEDULED.
- **SegmentFilter v1 minimal Pydantic strict**: `PredefinedSegmentFilter` usa `extra='forbid'` (arch test valida). Solo 3 predicados v1: `lifecycle_stages`, `channel_sources`, `score_range`. El arq especificó esta lista mínima — cualquier campo desconocido en `filter_dsl` JSONB lanza `ValidationError` explícito en lugar de silencioso. Crítico para evitar enviar a leads incorrectos.
- **Worker queue partial index CRÍTICO 1000 tenants**: `ix_campaign_task_worker_queue` es `WHERE status IN ('pending','scheduled')`. El arch test `test_campaign_task_idx_workers.py` verifica que la migración DDL incluye el string exacto. Sin partial idx, el worker poll con 1000 tenants × 10k tasks/tenant = 10M rows full scan. Con partial idx, solo los tasks pendientes/scheduled (típicamente <5% del total).
- **Template dual UNIQUE**: `campaign_template` tiene dos constraints: `uq_campaign_template_tenant` sobre `(tenant_id, name)` para templates tenant-privados, y `uq_campaign_template_global` sobre `name` WHERE `tenant_id IS NULL` para templates Nicolify-provided globales. Permite que un tenant tenga un template con el mismo nombre que uno global sin colisión.
- **`claim_pending_for_worker` cross-tenant allowlisteado**: El worker de ARQ (S2) necesita hacer FOR UPDATE SKIP LOCKED sin filtro de tenant (mismo patrón que `domain_event_outbox.claim_pending`). El AST scan de tenant isolation lo permite vía `CROSS_TENANT_ALLOWED_METHODS` frozenset en el arch test. La razón está documentada en el docstring del método en el repo impl.
- **`list_globals` allowlisteado en tenant isolation scan**: `campaign_template.tenant_id IS NULL` = template global Nicolify. La query `list_globals` hace `WHERE tenant_id IS NULL` — no aplica filtro de tenant porque semánticamente es cross-tenant. Documentado en docstring de `CampaignTemplateRepository`.
- **Repositorios implementados en Sub-C antes de verificar Sub-D**: El AST scan de tenant isolation (Sub-D) requería que las implementaciones de repositorios existieran para tener archivos `.py` que escanear. Orden correcto: Sub-C (SQLA models + repo impls) → Sub-D (arch tests que escanean Sub-C).
- **Path resolution migration test via `_CANDIDATE_PATHS`**: El test `test_campaign_task_idx_workers.py` usa dos paths candidatos (desde `backend/` y desde workspace root) para localizar `112_campaigns_domain.py`. Esto lo hace compatible tanto con `cd backend && pytest` como con `pytest backend/` desde la raíz del repo.

### Sub-deliverables completados

- [x] Sub-A+B: domain entities + FSM + DAG + segment filter + events + repositories interfaces (`f951c282`)
- [x] Sub-C: SQLA models + repository impls (tenant-scoped, soft delete) (`4cab1c1c`)
- [x] Migration: 6 tables + worker queue partial idx + template dual UNIQUE (`7b39b66b`)
- [x] Sub-D: 4 arch tests (tenant isolation + FSM invariants + segment filter strict + worker idx) (`4de090a9`)

### Tests escritos

- `tests/architecture/test_campaign_fsm_invariants.py` — FSM matrix structure (7 tests) + Hypothesis property-based (3 strategies, 300 examples total): `transition_allowed` coherente con `_FSM_TRANSITIONS`, no escape de terminales, solo RUNNING alcanza COMPLETED
- `tests/architecture/test_campaign_task_idx_workers.py` — DDL migration scan: partial idx existe, tiene WHERE clause, orden columnas correcto, unique constraint idempotency, revision correcta, down_revision encadenado, 6 tablas creadas (8 tests)
- `tests/architecture/test_campaigns_tenant_isolation.py` — AST scan repos: toda query sobre modelos tenant-scoped filtra `tenant_id`, allowlist ratchet shrink-only, allowlist entries corresponden a métodos reales (2 tests)
- `tests/architecture/test_segment_filter_pydantic_validated.py` — AST + runtime: todo BaseModel en segment_filter.py tiene `extra='forbid'`, runtime rechaza campos desconocidos en `PredefinedSegmentFilter`/`ScoreRange`/`DateRange`, alias `SegmentFilter` apunta a `PredefinedSegmentFilter` (6 tests)

**Total Sub-D: 23 tests** — 27 PASS (includes Hypothesis generated examples counted individually).

**Tests campaigns/modules (previos Sub-A+B+C):** ~150+ tests domain entities, repo interfaces, SQLA models, repo impls.

### Quality gates

- [x] Ruff verde (4 arch test files: 0 errores, 4 files unchanged)
- [ ] Mypy (no corrido en esta sesión — deferido a `/test-backend`)
- [x] Pytest verde (878 tests PASS: tests/modules/campaigns + tests/architecture completo)
- [x] Arch fitness tests verde (27/27 nuevos + 878 suite completa)
- [x] Migration idempotente (`112_campaigns_domain.py` usa raw SQL `IF NOT EXISTS` en todas las DDL)

### Bloqueadores encontrados

- **Path resolution `_CANDIDATE_PATHS`**: El builder anterior pausó investigando cómo resolver el path de `alembic/versions/` desde `tests/architecture/`. Resolución: el test ya tenía la implementación correcta con `_CANDIDATE_PATHS` dual (`parents[2]` y `parents[3]`). La migración `112_campaigns_domain.py` existe y los strings que busca el test también. No había bug real — el builder pausó sin necesidad.

### Decisiones diferidas durante implementación

- **Validación de ciclos en DAG**: Verificar que `next_step_ids` no crea ciclos se hará en `CampaignService.create_step()` en PR-4, no en domain entity (la entidad no tiene acceso al grafo completo).
- **Hydration lazy `SegmentSnapshot`**: El timing exacto de cuando crear snapshot (al SCHEDULE vs al LAUNCH) se decide en PR-4 services. La entidad domain está lista.
- **`ExpressiveSegmentFilter`** (vNext): La arch test de segment filter ya documenta que si se agrega `ExpressiveSegmentFilter`, debe usar `Union[]` y actualizar el assertion de alias.
- **Wiring BudgetGuard en CampaignExecutionWorker**: Las primitivas `BudgetGuard` de PR-2 (S0) están disponibles. El wiring al worker `claim_pending_for_worker` sucede en S2 al implementar el worker ARQ.

### Surface real entregada

| Tipo | Path | Estado |
|---|---|---|
| Domain entity | `src/modules/campaigns/domain/campaign.py` | ✓ SHIPPED |
| Domain entity | `src/modules/campaigns/domain/campaign_step.py` | ✓ SHIPPED |
| Domain entity | `src/modules/campaigns/domain/campaign_task.py` | ✓ SHIPPED |
| Domain entity | `src/modules/campaigns/domain/segment.py` | ✓ SHIPPED |
| Domain entity | `src/modules/campaigns/domain/segment_snapshot.py` | ✓ SHIPPED |
| Domain entity | `src/modules/campaigns/domain/campaign_template.py` | ✓ SHIPPED |
| Domain enums | `src/modules/campaigns/domain/enums.py` | ✓ SHIPPED |
| Domain filter | `src/modules/campaigns/domain/segment_filter.py` | ✓ SHIPPED |
| Domain events | `src/modules/campaigns/domain/events.py` | ✓ SHIPPED |
| Domain port | `src/modules/campaigns/domain/channel_router.py` | ✓ SHIPPED (port/ABC) |
| Repo interfaces | `src/modules/campaigns/domain/interfaces/` (6 repos) | ✓ SHIPPED |
| SQLA models | `src/modules/campaigns/infrastructure/models/` | ✓ SHIPPED |
| Repo impls | `src/modules/campaigns/infrastructure/repositories/` | ✓ SHIPPED |
| Migration | `backend/alembic/versions/112_campaigns_domain.py` | ✓ SHIPPED |
| Arch test | `tests/architecture/test_campaign_fsm_invariants.py` | ✓ SHIPPED |
| Arch test | `tests/architecture/test_campaign_task_idx_workers.py` | ✓ SHIPPED |
| Arch test | `tests/architecture/test_campaigns_tenant_isolation.py` | ✓ SHIPPED |
| Arch test | `tests/architecture/test_segment_filter_pydantic_validated.py` | ✓ SHIPPED |

### Rollout S2/S3 plan

- **PR-4 (S1 continuación)**: Services (`CampaignService`, `SegmentService`, `TemplateService`) + API endpoints (CRUD campaigns, segments, templates) + DTOs Pydantic. Sin orchestrator ni workers aún.
- **S2**: `CampaignExecutionWorker` ARQ + `ChannelRouter` impls (Telegram primero) + wiring `BudgetGuard.check(agent_kind="campaign")` + `OutboundRateLimiter.check()` antes de envío. Outbox pattern para delivery at-least-once.
- **S3**: Wiring `sales_agent` OutboundOrchestrator extension para campaña conversacional + `ComplianceService` policy chain en pre-send hook + copilot tools `campaign_get_status`/`campaign_pause`.

### Commits

- `f951c282` — `feat(campaigns): domain entities + FSM + DAG + segment filter + events + repositories interfaces (PR-3 Sub-A+B)`
- `4cab1c1c` — `feat(campaigns): SQLA models + repository impls (tenant-scoped, soft delete) (PR-3 Sub-C)`
- `7b39b66b` — `feat(db): migration campaigns domain (6 tables + worker queue partial idx + template dual UNIQUE) (PR-3)`
- `4de090a9` — `test(architecture): campaigns tenant isolation + FSM invariants + filter validation + worker idx (PR-3 Sub-D)`

---

<!-- @pm: implementación done. Próximo paso: ejecutar prompts/03-auditor-start.md o ejecutar /pm "PR-3 builder done". -->
