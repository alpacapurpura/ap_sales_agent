# PR-1-foundation-event-driven-core

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-1-foundation-event-driven-core |
| Sprint padre | S0-foundation |
| PI padre | PI-1-campaigns-module |
| Estado | ready |
| Tipo | infra |
| Esfuerzo | L |
| Owner PM | /pm |
| Claimed by session | — |

## Problema (user-facing)

Campañas, sales_agent y copilot pierden eventos de dominio cuando el proceso muere entre el commit DB y el dispatch in-memory. Webhooks externos (Telegram/ManyChat/Meta) procesan duplicados ante reintentos. Sin una primitiva común reutilizable, cada feature reinventa idempotencia ad-hoc → drift, bugs invisibles, observabilidad inconsistente.

JTBD interno: "Como builder de Nicolify, cuando emito un evento de dominio o consumo un webhook externo, quiero garantía exactly-once + traza unificada, para no debuggear pérdidas silenciosas en producción."

## Outcome esperado

Tres primitivas en `backend/src/shared/` listas para que TODO sprint posterior (S1-S4 + sales_agent outbound + voice_agent futuro) las consuma sin refactor:

1. **Outbox pattern global** transaccional → cero pérdidas eventos entre DB write y handlers async
2. **IdempotencyStore Redis-backed** con decorator → webhooks deduplicados con TTL configurable
3. **`agent_kind="campaign"`** registrado en `shared/agent_observability/` → trazas/costos campaigns visible en dashboards desde día 1

Migración no-disruptiva de 3 emisores existentes (sales_agent + copilot + brand) a outbox.

**Métrica:**
- 0 eventos perdidos en test simulado (kill worker post-commit, restart → outbox dispatcher recupera)
- 0 mensajes Telegram duplicados en test webhook con payload repetido
- 41 call sites `EventBus.publish()` migrados (o adapter backwards-compat aplicado) sin romper tests existentes

## Walking skeleton (mínimo viable cohesivo)

PR amplio cohesivo (Opus 4.7[1M]). 3 sub-deliverables que comparten dominio "event-driven infra":

```
shared/
├── domain_events/
│   ├── outbox/
│   │   ├── domain/event.py              ← DomainEvent (existente, mover desde shared/domain/events.py)
│   │   ├── infrastructure/
│   │   │   ├── models.py                ← DomainEventOutboxModel (tabla domain_event_outbox)
│   │   │   ├── repository.py            ← OutboxRepository
│   │   │   └── dispatcher.py            ← OutboxDispatcher (worker ARQ-friendly)
│   │   ├── application/
│   │   │   ├── outbox_service.py        ← enqueue() en transacción + after_commit fallback
│   │   │   └── event_bus_adapter.py     ← EventBusAdapter compat (redirige a outbox detrás flag)
│   │   └── api/                         ← (vacío esta fase, no expone endpoints)
│   └── (legacy events.py) → deprecation shim que re-exporta desde nuevo path
├── idempotency/
│   ├── domain/key.py                    ← IdempotencyKey VO
│   ├── infrastructure/redis_store.py    ← IdempotencyStore (Redis backend)
│   ├── application/
│   │   ├── decorator.py                 ← @idempotent(key_fn, ttl)
│   │   └── service.py                   ← IdempotencyService (lock-and-execute)
└── agent_observability/                 ← (existente)
    └── registry.py                      ← register_agent_observability(AgentObservabilitySpec(agent_kind="campaign", ...))

backend/migrations/versions/
└── 109_add_domain_event_outbox_and_campaign_observability.py
    ├── CREATE TABLE domain_event_outbox (idempotente)
    ├── CREATE INDEX idx_outbox_pending_at ON domain_event_outbox (status, created_at)
    ├── CREATE TABLE campaign_llm_call (mirrors copilot_llm_call schema)
    └── CREATE TABLE campaign_trace_event (mirrors copilot_trace_event schema)
```

Migración 3 emisores: sales_agent (9 sites) + copilot (8 sites) + brand (4 sites) → 21 call sites prioritarios. Resto (20 sites en connections/scheduling/social_proof/crm) consumen via `EventBusAdapter` shim sin cambios → migración incremental siguiente sprint.

## Soluciones consideradas

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| **A — Outbox new + adapter compat** | Backwards-compat 41 call sites con feature flag por emisor. Migración progresiva. Tests existentes no rompen | Adapter agrega capa indirección temporal | **ELEGIDA** |
| B — Big-bang refactor 41 call sites | Simple, sin compat layer | Blast radius enorme. Bug en outbox afecta sales_agent + copilot + brand simultáneo en prod | descartada por riesgo |
| C — Outbox solo para campaigns, dejar `event_bus` legacy | Sin migración existentes | Duplicación. Sales_agent outbound (S3) sigue con bug exactly-once | descartada — viola "cero refactor entre MVPs" |
| D — Solo idempotency (sin outbox) | Más chico | No resuelve pérdida eventos post-commit. R5 PI-1 sin mitigar | descartada |

**IdempotencyStore:**

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| **A — Redis SETNX + TTL** | Simple, atómico, reusa Redis ya en stack | Single-region (Nicolify hoy single region) | **ELEGIDA** |
| B — Postgres `idempotency_keys` table | Persiste reboot, audit-friendly | Más latencia, contención DB | descartada (Redis suficiente) |
| C — Per-feature ad-hoc (estado actual) | Cero refactor | Drift garantizado. Webhook ManyChat HOY sin idempotencia | descartada — bug latente |

## Validación técnica preliminar (Technical Sanity Check)

> PM ejecutó `Explore` agent (read-only) durante discovery. Brief sintetizado abajo. CONTRACT formal lo escribe `nicolify-architect` en su fase.

**Estado actual `event_bus` (Explore audit 2026-04-29):**

- Path: `backend/src/shared/domain/events.py`
- API: `EventBus.publish(event: DomainEvent, session: Session | None = None)` + `EventBus.subscribe(name, handler)`
- Backend: 100% in-memory singleton. Dispatch inmediato si `session=None`, after-commit hook si session provided. Excepciones loguean y NO propagan
- Persistencia: ninguna. Cero tabla relacionada
- 41 call sites totales. Subscribers registrados en `register_subscribers()` por módulo (copilot/sales_agent/shared/crm) wired al startup app

**Emisores prioritarios (21 sites a migrar PR-1):**

| Módulo | Sites | Paths principales |
|---|---|---|
| sales_agent | 9 | `application/tools/payment/tools.py:165,369`, `application/tools/scheduling/tools.py:136`, `application/orchestrator/audit_emitter.py:97`, `workers/verify_pending_payments.py:99`, `workers/verify_pending_bookings.py:151`, `api/scheduler_webhooks.py:170`, `api/payment_webhooks.py:215` |
| copilot | 8 | `application/extraction_card_flow.py:121,235`, `application/tools/extract_from_doc.py:443,456`, `application/orchestrator/chat.py:830,909,1438,1544` |
| brand | 4 | `infrastructure/repositories/brand_repository.py:85`, `application/services/personality_service.py:119`, `workers/tasks.py:343,416` |

**Resto (20 sites diferidos a S2 vía adapter):** `connections/api/marketing_webhooks.py`, `scheduling/api/agenda.py`, `social_proof/*`, `crm/*`.

**IdempotencyStore actual:**
- Existe parcial: `copilot/application/extraction_card_flow.py:68-77` usa `redis_client.setex(idempotency_key, 86400, "1")` para nav cards
- Webhooks externos (ManyChat/Meta/Telegram/MailerLite): SIN idempotencia hoy → bug latente
- No existe abstracción global. Cada feature ad-hoc

**`shared/agent_observability/` (existente):**
- Path: `backend/src/shared/agent_observability/`
- API: `register_agent_observability(AgentObservabilitySpec(agent_kind=..., llm_call_model=..., trace_event_table=..., llm_call_table=..., trace_retention_env_var=..., llm_call_retention_env_var=..., has_lead_id=...))`
- Registrados hoy: `copilot`, `sales_agent`. Falta: `brand`, `campaign`. **PR-1 agrega `campaign`**, brand queda fuera scope (S2)
- Cada módulo registra en su `observability/__init__.py` durante import

**Migrations:** última head ~`078_sales_agent_observability_tables`. Total 108 migrations. Cero `domain_event_outbox` previo.

**Tests críticos no romper:**
- `backend/tests/shared/test_event_bus.py` (TestDomainEvent + TestEventBusImmediate + TestEventBusAfterCommit + TestEventBusException)
- `tests/{brand,sales_agent,copilot,crm}/test_*_event_handlers.py`
- Webhook integration tests (`payment_webhooks`, `scheduler_webhooks`)
- Brand summary regen debounce (depends on after-commit dispatch)

**Riesgo principal:** 41 call sites = blast radius alto. Mitigación: feature flag `USE_OUTBOX_PATTERN` por emisor + adapter pattern. Rollout: PR-1 ship sin flip flag → siguiente PR flip por módulo en orden sales_agent → copilot → brand → resto.

**Modules afectados:** `shared/domain_events/`, `shared/idempotency/` (nuevos) + migración 3 módulos cliente (sales_agent, copilot, brand) + migration nueva.

**Tiempo estimado:** L (3 ejecuciones agente: architect → builder → auditor; builder denso por TDD multi-capa).

## Decisiones diferidas (explícitas)

| Item | Razón | Cuándo |
|---|---|---|
| Migrar 20 call sites restantes (connections/scheduling/social_proof/crm) | Reduce blast radius PR-1. Adapter cubre transparente | S2 |
| Outbox dispatcher como ARQ worker dedicado vs in-process scheduler | Ambas funcionan. ARQ requiere si scale-out. Decide architect basado en BudgetGuard timing | architect (CONTRACT) |
| Registrar `agent_kind="brand"` en observability | Fuera scope S0 PR-1 | S2 |
| Backfill eventos pre-existentes (in-memory perdidos) a outbox | No aplica: outbox arranca vacía. Eventos hot-path durante deploy se manejan con `EventBusAdapter` legacy hasta cutover | — |
| Multi-region Redis para IdempotencyStore | Nicolify single-region hoy | post PI-1 |
| Audit log dedicado | Movido a S2 ya | S2 |
| Circuit breaker + DLQ | Movido a S2 ya | S2 |

## Out of scope

- Cualquier código de dominio campaigns (S1+)
- Migrar 20 call sites no-prioritarios (S2)
- ARQ worker dedicado fuera dispatcher (S2 `CampaignExecutionWorker`)
- UI/admin Streamlit relacionada con outbox (no necesaria — observabilidad via trace_event)
- ComplianceService + BudgetGuard + RateLimiter (PR-2)

## Copilot-first checklist

- [x] **¿Operable conversacional desde copilot?** Default Sí, pero **N/A funcional**: PR-1 es infra cross-cutting sin user-facing flow. Copilot consume primitivas downstream (S2+).
- [x] **¿Qué tools nuevos requiere?** Ninguno en PR-1. Sí en S2 (`launch_campaign_dry_run`, `inspect_outbox_health`).
- [x] **¿Cards/UI nueva?** Ninguna PR-1.
- [x] **Si NO copilot → razón documentada:** infra layer. Copilot consume vía services downstream (S2 CampaignOrchestrator, S3 OutboundOrchestrator). Trazas observables en dashboard via `agent_kind="campaign"` desde día 1.

## Agentes / skills recomendados

(Ref: `process/agent-routing-matrix.md` — fila "Pure backend infra")

| Fase | Agente/skill | Prompt pre-coce | Entregable esperado |
|---|---|---|---|
| Pre-design | `nicolify-architect` | `prompts/01-architect-start.md` | `CONTRACT.md` con schemas + interfaces + migration plan + adapter pattern |
| UX | — | — | N/A (no UI) |
| Implementation | `nicolify-backend` | `prompts/02-builder-start.md` | code + tests + migration + IMPL-LOG |
| Audit | `nicolify-backend-auditor` | `prompts/03-auditor-start.md` | REVIEW.md (13 gates `/test-backend`) |
| Cierre | `/pm` | `prompts/04-pm-close.md` | `RESULT.md` + `current-state/{campaigns,sales_agent,copilot,brand}.md` updates |

**Skills módulo a invocar durante audit:** `sales-agent-expert` + `copilot-expert` + `brand-expert` (los 3 emisores migrados). `architectural-fitness` regla automática.

## Surface impactada

| Tipo | Path / nombre | Cambio |
|---|---|---|
| Tabla DB | `domain_event_outbox` | nueva |
| Tabla DB | `campaign_llm_call` | nueva (mirror copilot_llm_call) |
| Tabla DB | `campaign_trace_event` | nueva (mirror copilot_trace_event) |
| Module | `backend/src/shared/domain_events/outbox/` | nuevo (domain + infrastructure + application) |
| Module | `backend/src/shared/idempotency/` | nuevo |
| Module | `backend/src/shared/domain/events.py` | deprecation shim (re-export desde `shared/domain_events/outbox/domain/event.py`) |
| Module | `backend/src/modules/campaigns/observability/__init__.py` | nuevo (registra `agent_kind="campaign"`) |
| Migration | `backend/migrations/versions/109_*.py` | idempotente raw SQL |
| Adapter | `shared/domain_events/outbox/application/event_bus_adapter.py` | nuevo (compat 41 call sites) |
| Tests | `backend/tests/shared/domain_events/`, `tests/shared/idempotency/`, `tests/architecture/test_outbox_invariants.py` | nuevos |
| Env var | `USE_OUTBOX_PATTERN_{SALES_AGENT,COPILOT,BRAND}` | nuevos (feature flags rollout) |
| Env var | `IDEMPOTENCY_DEFAULT_TTL_SECONDS` | nuevo (default 86400) |
| current-state/ | `current-state/campaigns.md` | append capability "observability spec registered" |
| current-state/ | `current-state/sales_agent.md` | append "outbox migration ready (flag)" |
| current-state/ | `current-state/copilot.md` | append idem |
| current-state/ | `current-state/brand.md` | append idem |

## Tests requeridos (TDD)

Cada sub-deliverable tiene tests RED antes implementación, capa por capa:

**Outbox:**
- `tests/shared/domain_events/test_outbox_domain.py` — DomainEvent invariants
- `tests/shared/domain_events/test_outbox_repository.py` — append + claim_pending + mark_dispatched (tenant scoping)
- `tests/shared/domain_events/test_outbox_service.py` — enqueue dentro transacción + rollback semantics + at-least-once con idempotency key
- `tests/shared/domain_events/test_outbox_dispatcher.py` — pending → dispatched, kill+restart recovery, exactly-once con dedupe key
- `tests/shared/domain_events/test_event_bus_adapter.py` — compat: legacy `EventBus.publish()` redirige a outbox cuando flag ON

**Idempotency:**
- `tests/shared/idempotency/test_idempotency_key.py` — VO equality
- `tests/shared/idempotency/test_redis_store.py` — SETNX + TTL + race condition (concurrent inserts)
- `tests/shared/idempotency/test_decorator.py` — `@idempotent` first call → execute, repeat → cached result

**Observability:**
- `tests/modules/campaigns/test_observability_registration.py` — `agent_kind="campaign"` registrado correcto

**Architecture:**
- `tests/architecture/test_outbox_invariants.py` — toda escritura `domain_event_outbox` filtra `tenant_id`
- `tests/architecture/test_idempotency_used_at_webhooks.py` — todo handler webhook externo (`@router.post("/webhooks/...")`) tiene `@idempotent` decorator (regla shrink-only ratchet con allowlist legacy)

**Migración emisores (regression no-romper):**
- Tests existentes `tests/{brand,sales_agent,copilot,crm}/test_*_event_handlers.py` siguen verdes con flag OFF y con flag ON

## Aceptación

- [ ] `/test-backend` 13 gates verde (ruff + format + mypy strict 8 domains + arch fitness 78 + coverage 43% + verify + integration + migration idempotency + jscpd 5% + interrogate 85% + pip-audit)
- [ ] `IMPL-LOG.md` completo (sub-deliverables + decisiones + commits)
- [ ] `REVIEW.md` veredicto PASS (cero FAIL en cat 1/2/8/9/11)
- [ ] `RESULT.md` escrito por `/pm`
- [ ] 4 `current-state/{m}.md` actualizados con lineage
- [ ] Decisiones registradas en `decisions.md` PI-1
- [ ] Migration 109 idempotente verificada con clone DB (regla `backend-migrations.md`)
- [ ] Feature flag rollout plan documentado en `IMPL-LOG.md` (sales_agent → copilot → brand → resto)

## Riesgos

| Riesgo | Mitigación | Owner |
|---|---|---|
| 41 call sites blast radius | Feature flag por emisor + adapter compat. PR-1 ship con todas flags OFF. Flip incremental siguiente PR | architect |
| In-memory handlers race con outbox dispatcher | Outbox dispatcher solo procesa filas `status='pending'`. Subscribers in-memory siguen funcionando con flag OFF (legacy path) | architect |
| Migration backfill (eventos in-memory ya consumidos) | No aplica: outbox arranca vacía. Cutover post-deploy → eventos nuevos van por outbox via flag ON. Legacy in-memory queda como dead code S2 | builder |
| Tests existentes `test_event_bus.py` rompen | Re-export shim desde `shared/domain/events.py` mantiene API pública. Tests existentes siguen pasando | builder |
| Idempotency Redis cae → webhooks fallan | `IdempotencyService` en modo "soft fail" si Redis unavailable: log warning + permitir ejecución (better double-process que pérdida). Documentar trade-off | architect |
| Observability `campaign_*` tablas crean ruido en dashboards si no hay datos | Aceptado. UNION-ALL view filtra empty. Cuando campaigns ejecuten S2+ se llenan natural | — |
| Webhook handler con `@idempotent` rompe tests integration ManyChat/Meta | Allowlist ratchet inicial poblado con call sites legacy. Solo nuevos webhooks deben tener decorator | auditor |
