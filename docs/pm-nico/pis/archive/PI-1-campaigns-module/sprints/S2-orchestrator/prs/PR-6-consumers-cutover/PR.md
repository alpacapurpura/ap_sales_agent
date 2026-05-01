# PR-6-consumers-cutover

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-6-consumers-cutover |
| Sprint padre | S2-orchestrator |
| PI padre | PI-1-campaigns-module |
| Estado | ready |
| Tipo | infra cutover (no nueva feature user-facing) |
| Esfuerzo | M |
| Owner PM | /pm |
| Claimed by session | 2026-04-30 — paths `modules/{sales_agent,copilot,brand}/` LLM call sites + `core/config.py` flags + `shared/domain_events/outbox/` consumer wiring |

## Problema (user-facing)

S0 entregó primitivas robustas (outbox + idempotency + BudgetGuard + ComplianceService + OutboundRateLimiter) **pero nadie las consume real**:

- `USE_OUTBOX_PATTERN_{SALES_AGENT,COPILOT,BRAND}` = `False` default. Eventos van por path legacy in-memory dispatch (sin durabilidad cross-instance, sin retry, sin rastreo). Si pod crashea durante un evento → evento perdido.
- `BudgetGuard.check(tenant_id, agent_kind, est_cost)` NO wired en LLM call sites copilot + sales_agent. Tenant excede plan sin freno → cost runaway 1000 clientes.
- 20 emisores legacy in-memory dispatch path coexisten con outbox path → dual-write riesgoso (regresión silenciosa si alguien usa path viejo en feature nuevo).
- `ComplianceService` + `OutboundRateLimiter` ya wired PR-5 en `TelegramChannelRouter.send` — OK.

PR-5 entregó pipeline outbound real con primitives wired solo en TelegramChannelRouter. PR-6 = cutover real consumers LLM (copilot + sales_agent + brand) a S0 primitives.

JTBD interno: "Como builder Nicolify post PR-6, cuando un tenant excede su plan en copilot LLM call → BudgetGuard.check raises → respuesta 402 Payment Required en lugar de cost runaway. Cuando emiter sales_agent crashea pod → evento sobrevive en outbox + dispatcher worker lo retransmite. Cero pérdida + cero overage 1000 clientes."

## Outcome esperado

Cutover atómico secuencial (un módulo por commit) scoped a:

1. **Flip 3 flags ENV `USE_OUTBOX_PATTERN_{SALES_AGENT,COPILOT,BRAND}` → `True`** (default OFF → ON dev/staging post smoke).
   - Cada flag flip = 1 commit + 1 smoke test.
   - Decisión D21 (CONTRACT PR-5): SECUENCIAL no paralelo. Blast radius bajo. Si sales_agent rompe → revertir flag = 1 line change. Paralelo = 3 cosas rotas.
2. **Wire `BudgetGuard.check(tenant_id, agent_kind, est_cost)` ANTES cada LLM call site copilot + sales_agent**:
   - Detecta callsites via grep `LiteLLM.acompletion|provider.invoke|client.chat.completions`.
   - Estimate cost via existing pricing snapshot table (`model_pricing_snapshot`).
   - Si check fail → raises `BudgetExceeded` → endpoint retorna 402 + audit row.
3. **Retire 20 emisores legacy in-memory dispatch path** (architect identifica list final en CONTRACT.md):
   - Reemplazar `event_bus.publish_in_memory(event)` por `OutboxService.enqueue(event, session=...)`.
   - Mantener subscribers handlers cross-instance (consumen via dispatcher worker S0).
   - Verificar tests verde post-retire.
4. **Tests integration sin mocks (política F-7 PR-4)**: smoke flag flip per módulo verifica:
   - Evento emitido → row en `domain_event_outbox` table → dispatcher worker pickup → handler invocado.
   - LLM call con BudgetGuard exhausted → 402 + audit row + cost no excede plan.
5. **Cero regresión**:
   - Tests existentes verde con flags ON (currently they pass with flags OFF).
   - 13 gates `/test-backend` verde.

**Métricas:**
- 3 commits flag flip + 1 commit BudgetGuard wiring + 1 commit retire legacy + 1 commit IMPL-LOG.
- 0 callsites LLM sin BudgetGuard.check (verified arch test new).
- 0 emisores legacy `event_bus.publish_in_memory` activos en módulos cutover (verified arch test extends ratchet).

## Walking skeleton

PR cohesivo medio. Layout:

```
backend/src/
├── core/config.py                                         (MOD: cambiar defaults flags 3 USE_OUTBOX_PATTERN_*)
├── modules/sales_agent/
│   ├── application/orchestrator/                          (MOD: wire BudgetGuard.check pre-LLM call)
│   └── (varios callsites legacy event_bus.publish → OutboxService.enqueue)
├── modules/copilot/
│   ├── application/                                       (MOD: wire BudgetGuard.check + retire legacy emit)
│   └── observability/recording/domain_subscribers.py      (MOD si emisor)
├── modules/brand/
│   └── application/                                       (MOD: retire legacy emit si aplica)
└── shared/domain_events/outbox/
    └── (verify consumer/dispatcher invariants si afecta)

backend/tests/
├── modules/sales_agent/integration/test_outbox_cutover.py (NEW política F-7)
├── modules/copilot/integration/test_outbox_cutover.py     (NEW política F-7)
├── modules/copilot/integration/test_budget_guard_wiring.py (NEW)
├── modules/sales_agent/integration/test_budget_guard_wiring.py (NEW)
├── modules/brand/integration/test_outbox_cutover.py       (NEW política F-7)
└── architecture/
    ├── test_budget_guard_pre_llm_call.py                  (NEW gate: cada LLM callsite tiene BudgetGuard.check antes)
    └── test_no_legacy_event_bus_publish.py                (NEW gate: cero `event_bus.publish_in_memory` en módulos cutover; ratchet allowlist)
```

## Soluciones consideradas

### Decisión D26 — Cutover order (paralelo vs secuencial)

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| **A — Secuencial: sales_agent → copilot → brand. Un flag por commit + smoke entre cada flip** | Blast radius bajo. Rollback simple = 1 line change. Cada flag flip aislado. | 3 commits separados (más overhead). | **ELEGIDA** (D21 CONTRACT PR-5) |
| B — Paralelo: 1 commit con 3 flags ON | 1 commit | Si rompe → 3 cosas rotas + diagnostic difícil. | descartada |
| C — Feature flag toggle dinámico runtime | Sin redeploy | Out of scope (no LaunchDarkly setup) | descartada |

Cutover order rationale:
1. **sales_agent primero**: módulo más crítico (outbound revenue). Smoke maduro. Si rompe → más feedback rápido.
2. **copilot segundo**: alta superficie LLM. Tras sales_agent estable.
3. **brand último**: módulo menor blast radius (extraction async, no user-facing real-time).

### Decisión D27 — BudgetGuard estimation strategy

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| **A — Estimate via `model_pricing_snapshot` table + tokens estimated input (max output)** | Production-grade reservación 50% sales_agent invariant respected. | Estimate puede underestimate si modelo cambia mid-call (improbable). | **ELEGIDA** |
| B — No estimate, post-call deduction | Más simple | Cost runaway possible mid-call (descartada anti-1000-clientes) | descartada |
| C — Hard cap fixed por agent_kind | Simple | Insensible a modelo/contexto (anti-elasticity) | descartada |

`BudgetGuard.check` signature: `check(tenant_id, agent_kind, est_cost_usd) -> Reservation`. Pre-LLM: estimate `cost = pricing_snapshot[model] * (input_tokens + max_output_tokens)`. Si `check` fails → raise `BudgetExceeded` → endpoint 402.

### Decisión D28 — Legacy emisores retire policy

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| **A — Replace inline call `event_bus.publish_in_memory(event)` con `await outbox_service.enqueue(event, session=...)` + verificar tests verde** | Cutover atómico per emiter. Cero dual-write. | Requiere AsyncSession en callsite (algunos legacy son sync — refactor needed). | **ELEGIDA** |
| B — Wrapper backwards-compat (publish_in_memory → outbox enqueue) | Minimal change | Mantiene API legacy → arch test no enforce | descartada (deuda) |
| C — Deprecate gradual con warning | Convencional | Lento — preserva path legacy meses | descartada |

Si callsite es sync → architect indica refactor strategy en CONTRACT (probably pass session via DI o use sync-async bridge `OutboxService.enqueue_async_from_sync_caller`).

## Validación técnica preliminar

**Estado actual:**
- `core/config.py:209-212` — flags `USE_OUTBOX_PATTERN_*` defaults `False`.
- `shared/domain_events/outbox/application/event_bus_adapter.py:230-236` — adapter consulta flag por módulo.
- Cero callsites BudgetGuard en sales_agent + copilot (verified `grep -rln BudgetGuard backend/src/modules/{sales_agent,copilot}/` returns nothing).
- ~15 callsites EventBus identificados en sales_agent + copilot + brand (architect filtra subscribers vs emisores en CONTRACT).

**Primitivas S0 disponibles (consumidas PR-6):**
- `OutboxService.enqueue(event, session=...)` — replace legacy publish
- `BudgetGuard.check(tenant_id, agent_kind, est_cost) -> Reservation` — wire pre-LLM
- `model_pricing_snapshot` table — estimate cost
- Dispatcher worker S0 — consume outbox events (ya activo)

**Modules afectados:**
- `core/config.py` (3 lines — flag defaults)
- `modules/sales_agent/application/` (LLM callsites + retire legacy emit)
- `modules/copilot/application/` (LLM callsites + retire legacy emit)
- `modules/brand/application/` (retire legacy emit si aplica)
- `tests/modules/{sales_agent,copilot,brand}/integration/` (NEW)
- `tests/architecture/test_{budget_guard_pre_llm_call,no_legacy_event_bus_publish}.py` (NEW)

**Tests críticos no romper:**
- Tests existentes sales_agent + copilot + brand currently green con flags OFF — deben permanecer verde con flags ON.
- 4 arch tests PR-5 + 8 arch tests PR-3/PR-4 frozen.
- `test_ddd_boundaries.py` (cross-module imports allowlist).
- `test_outbox_invariants.py` (events emitted via OutboxService).

**Conflicto sesiones paralelas:** PI-2 paralela cerró S2 (`b813a98a`, `9cac2d21` posts). Builders activos pueden seguir en `copilot/` para nuevas features. PR-6 modifica:
- `core/config.py` — single line per flag (3 lines total). Conflicto improbable.
- LLM callsites copilot — SI hay sesión paralela en mismo callsite, regla M8: extend, no destroy.
- Builder verifica `git status` antes cada commit.

**Tiempo estimado:** M (1 architect + 1 builder + 1 auditor; cutover incremental).

## Decisiones diferidas (explícitas)

| Item | Razón | Cuándo |
|---|---|---|
| `USE_OUTBOX_PATTERN_DEFAULT` flip | scope-cut PR-6 (default OFF mantiene safety net) | post PI-1 |
| BudgetGuard wiring en `campaigns/` LLM call (S3 sales_agent OutboundOrchestrator) | sales_agent OutboundOrchestrator no existe aún | S3 |
| ComplianceService wiring en sales_agent ChatOrchestrator (inbound) | inbound flow es S3 dominio | S3 |
| Retire dispatcher worker legacy si alguno (verify exists) | architect verifica en CONTRACT | PR-6 si existe / PI-2 |

## Out of scope

- Cualquier nueva feature user-facing → PR-6 = cutover infra
- FE → post PI-1
- copilot tools / subagent → PI-2
- ChannelRouter expansion (WhatsApp, Email) → PI-2
- sales_agent OutboundOrchestrator + AgentState campaign_id → S3
- Inbound reply recognition campaigns → S3

## Copilot-first checklist

- [x] **¿Operable conversacional desde copilot?** N/A funcional PR-6 (cutover infra). PI-2 wirea tools campaigns sobre primitives consolidadas.
- [x] **¿Qué tools nuevos requiere?** Ninguno PR-6.
- [x] **¿Cards/UI nueva?** Ninguna PR-6 (sin FE).
- [x] **Si NO copilot → razón documentada:** PR-6 = cutover infra. Beneficio cross-module (sales_agent + copilot + brand). Copilot ya consume primitives via outbox post-cutover automaticamente.

## Agentes / skills recomendados

| Fase | Agente/skill | Prompt pre-coce | Entregable esperado |
|---|---|---|---|
| Pre-design | `nicolify-architect` | `prompts/01-architect-start.md` | `CONTRACT.md` (cutover plan + LLM callsites enumerados + retire list) |
| UX | — | — | N/A |
| Implementation | `nicolify-backend` | `prompts/02-builder-start.md` | code + tests integration (sin mocks) + IMPL-LOG |
| Audit | `nicolify-backend-auditor` | `prompts/03-auditor-start.md` | `REVIEW.md` (13 gates + cutover invariants) |
| Cierre | `/pm` | `prompts/04-pm-close.md` | `RESULT.md` + `current-state` lineage + handoff S3 |

**Skills módulo a invocar:**
- `sales-agent-expert` (BudgetGuard wiring sales_agent — invariante reservación 50%)
- `copilot-expert` (BudgetGuard wiring copilot LLM call sites)
- `tessl__graceful-degradation` (BudgetGuard fallback strategy si dependency down)

## Surface impactada

| Tipo | Path / nombre | Cambio |
|---|---|---|
| Config | `backend/src/core/config.py` | MOD: flip defaults `USE_OUTBOX_PATTERN_{SALES_AGENT,COPILOT,BRAND}` `False → True` |
| Wiring | `backend/src/modules/sales_agent/application/` callsites | MOD: BudgetGuard.check pre-LLM + retire legacy emit |
| Wiring | `backend/src/modules/copilot/application/` callsites | MOD: BudgetGuard.check pre-LLM + retire legacy emit |
| Wiring | `backend/src/modules/brand/application/` callsites | MOD: retire legacy emit (no LLM cost wiring si brand no LLM directo) |
| Tests | `tests/modules/{sales_agent,copilot,brand}/integration/test_outbox_cutover.py` | NEW política F-7 |
| Tests | `tests/modules/{sales_agent,copilot}/integration/test_budget_guard_wiring.py` | NEW |
| Tests arch | `tests/architecture/test_budget_guard_pre_llm_call.py` | NEW gate |
| Tests arch | `tests/architecture/test_no_legacy_event_bus_publish.py` | NEW gate (ratchet allowlist) |
| current-state | `current-state/{sales_agent,copilot,brand}.md` | append capability "PR-6: outbox cutover ON + BudgetGuard wired" |

## Tests requeridos (TDD)

### Layer A — Per-module integration (política F-7 sin mocks)

- `test_outbox_cutover.py` (×3 módulos): emiter → outbox row → dispatcher pickup → handler invocado. Sin mocks.
- `test_budget_guard_wiring.py` (×2 sales_agent + copilot): LLM call con tenant exhausted plan → 402 + audit row + cost no excede.

### Layer B — Architecture gates

- `test_budget_guard_pre_llm_call.py` — AST scan: cada `LiteLLM.acompletion` / `provider.invoke` / `client.chat.completions` precedido por `BudgetGuard.check`. Ratchet allowlist.
- `test_no_legacy_event_bus_publish.py` — AST scan: cero `event_bus.publish_in_memory` en módulos cutover. Ratchet allowlist (post-cutover).

## Aceptación

- [ ] `/test-backend` 13 gates verde
- [ ] 2 arch tests nuevos verde + 0 regresión existentes
- [ ] Tests integration F-7 verde (cutover smoke per módulo)
- [ ] Cero callsites LLM sin BudgetGuard.check (verified arch test)
- [ ] 3 commits flag flip + 1 BudgetGuard wiring + 1 retire legacy + 1 IMPL-LOG (~6 commits)
- [ ] `IMPL-LOG.md` completo (decisiones D26-D28 + cutover order outcomes + flags before/after)
- [ ] `REVIEW.md` veredicto PASS
- [ ] `RESULT.md` escrito por `/pm`
- [ ] `current-state/{sales_agent,copilot,brand}.md` lineage updated
- [ ] Decisiones D26-D28 registradas en `decisions.md` PI-1
- [ ] handoff.md S3 escrito (siguiente sprint mvp Telegram)

## Riesgos

| Riesgo | Mitigación | Owner |
|---|---|---|
| Flag flip rompe tests sales_agent existentes | Smoke per flip + revert flag = 1 line change | builder |
| BudgetGuard.check estimate mismatch real cost mid-call | Reservation 50% safety margin + post-call reconciliation cron (existente?) | architect |
| Retire legacy callsite sync requiere AsyncSession refactor | Architect indica `enqueue_async_from_sync_caller` bridge en CONTRACT | architect |
| Conflict sesiones paralelas (modify mismo callsite copilot) | Builder verifica `git status` + regla M8 extend, no destroy | builder |
| Smoke test crashea Postgres dev local | Re-run tras docker compose restart | builder |
| Cutover deja dispatcher worker no consumer events | Verify dispatcher worker S0 active + smoke test cubre | architect |
| `model_pricing_snapshot` table empty/stale | Worker `sync_litellm_pricing` ya cron diaria existente — verify | builder |
| Brand cutover sin LLM wiring confunde scope | Brand NO tiene LLM call directo (extraction usa shared LLM service que ya wired post-PR-6 copilot/sales_agent) | architect |
