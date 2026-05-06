# PR-2-shared-agent-observability

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-2-shared-agent-observability |
| Sprint padre | S2-shared-observability |
| PI padre | PI-1.1-pi1-post-mortem |
| Estado | discovery (architect mandatory ANTES builder) |
| Tipo | refactor (lift to shared + dual consumer) |
| Esfuerzo | L |
| Owner PM | /pm |
| Claimed by session | 2026-05-01 |

## Origen

PR-1 PI-1.1 hotfix descubrió:
- Bug #2 sales_agent_trace_event = 0 rows globalmente (real DB query confirmed)
- Bug #8 `FXResolver()` sin `http_client_factory` arg en `factory.py:116, 168` (runtime error context_factory_failed → traces silently dropped)
- Builder agentic creó turn_envelope MIRROR de copilot existente (anti-pattern Chris flagged) → REVERT

Anti-duplication rule (`rules/anti-duplication.md`) cementada cross-layer enforcement post-PR-1. Este PR es el primer test del nuevo proceso.

## Problema (user-facing)

Sales agent observability NO graba traces a `sales_agent_trace_event` / `sales_agent_llm_call` / `sales_agent_routing_log` desde commit `3f7d28bf` (S1-redesign 2026-04). Operaciones ciegas:
- Voice fidelity grader no puede correr (no traces)
- Costos por agente no auditables
- Tool execution flow no rastreable
- Routing decisions perdidas
- PI-3 sales-agent-improvement está construyendo sobre observability que no existe

## Outcome esperado

| Métrica | Target |
|---|---|
| `sales_agent_trace_event` rows post-Telegram message | ≥3 (turn_start + ≥1 llm_call + turn_end) |
| `sales_agent_llm_call` rows post-Telegram message | ≥1 |
| FXResolver instantiation correcta cross-codebase | 0 instances `FXResolver()` sin args |
| Mirror duplication eliminada | 0 `turn_envelope.py` per-module (solo en shared) |
| Copilot observability sigue funcionando | `copilot_trace_event` count crece normal post-refactor |
| Cross-agent extension trivial (futuro commercial_director) | <50 LOC subclass new agent context |

## Walking skeleton

Mínimo cohesivo entrega:
1. `shared/agent_observability/recording/turn_envelope.py::BaseObservabilityContext` — abstract base con `observe_turn` async ctx mgr + commit lifecycle
2. `shared/agent_observability/cost/fx_resolver.py::FXResolver.default()` — classmethod factory que encapsula `lambda: httpx.Client(timeout=10)` boilerplate
3. `modules/copilot/observability/recording/context.py::CopilotObservabilityContext(BaseObservabilityContext)` — concrete, hereda lifecycle, override fields/repos copilot-specific
4. `modules/sales_agent/observability/recording/context.py::SalesAgentObservabilityContext(BaseObservabilityContext)` — idem para sales_agent
5. Migración chat orchestrator copilot (chat.py:647 + 1110 + 1230) usar `FXResolver.default()` + concrete context
6. Migración chat/outbound orchestrator sales_agent usar concrete context (factory.py:116, 168 fix Bug #8 incluido)
7. Real persistence test sales_agent (no mocks DB) → asserts INSERT > 0 rows
8. Smoke real Telegram → trace count growth verified (chris-mediated)

## Soluciones consideradas

### Lift pattern

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| A) Shared base abstract + 2 concrete subclasses | Single source of truth · futuro agent N+1 trivial · drift impossible | Refactor copilot (other session activa) requiere coordinación | **ELEGIDA** — patrón que Chris ratificó growth-aware |
| B) Mirror per-module (current state pre-revert) | Zero coordination | Drift garantizado · cada bug fix N veces · futuro agent = N+1 mirror | descartada (revert tomado) |
| C) Composition (delegate al shared) | Más flexible que herencia | Más boilerplate por agent | descartada — herencia simple basta |

### FX resolver factory

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| A) `FXResolver.default()` classmethod | Single source · 1 línea per call site · test override fácil | — | **ELEGIDA** |
| B) Module-level helper `build_fx_resolver()` | Funcional similar | Duplicar helper per consumer module | descartada |
| C) Factory function en shared/factories.py | Patron DI puro | Over-engineering para 1 obj | descartada |

## Validación técnica preliminar

Spawn `nicolify-architect` (Opus) Phase 0 → produce CONTRACT.md con:
- Schema interface BaseObservabilityContext
- Migration order (copilot first or sales_agent first or parallel)
- Coordination plan vs PI-5 PR-2 active session (copilot WIP)
- Tests strategy (real DB vs mocks)
- Rollout sequence (lift → migrate copilot → migrate sales_agent → fix Bug #8 → smoke)

## Existing systems audit (MANDATORY — bloque grep evidence)

Architect ejecuta sección 1-5 del template antes de escribir CONTRACT.md. PR.md propaga grep output. Builder Step 0 GATE re-verifica.

Inventario consultar `.claude/rules/anti-duplication.md`:
- Pattern "Observability turn envelope" — STATUS: parcialmente shared. `shared/agent_observability/persistence/` SÍ existe. `shared/agent_observability/recording/` solo tiene `base_callback_handler.py` + `sanitization.py`. Falta `turn_envelope.py` shared. Copilot tiene module-local concrete.
- Pattern "FX resolver factory" — STATUS: shared `FXResolver(http_client_factory=...)` existe. Falta `.default()` classmethod helper. 1 caller correcto (copilot/chat.py:647), 2 callers rotos (sales_agent factory.py:116, 168).

## Decisiones diferidas

- Bug #7 `PersonalityProfileModel.model_dump` type mismatch en `brand/application/services/brand_data_adapter.py:46` → out-of-scope este PR. Abrir PR dedicado backend negocio
- Bug #9 LiteLLM container exited config.yaml mount conflict → out-of-scope (infra). Abrir PR dedicado infra
- Bug #6 tenant switch non-persist Clerk publicMetadata → out-of-scope (FE Clerk session). Abrir PR dedicado FE
- Bug #5 max update depth FE → out-of-scope hasta reproducir
- Backfill traces históricos sales_agent (pre-PR-2) → defer post-PR-2 ship + Chris discussion

## Out of scope

- Cambios a otros agentes shared abstractions (cost calculator, pricing aliases, channel registry) — solo turn_envelope + FX resolver factory
- Cambios a redirect_slashes infra (rule inviolable)
- Refactor brand_data_adapter (Bug #7 separate PR)

## Copilot-first checklist

- [x] ¿Operable conversacional desde copilot? **NO** — refactor invisible al user. Copilot observability sigue funcionando igual (4260 rows existentes, growth normal post-refactor)
- [x] Tools nuevos: ninguno
- [x] Cards/UI nueva: ninguna
- [x] Razón NO copilot: refactor backend transparent. Sales agent observability emerges post-PR2 (capability nueva, no operable conversacional desde copilot — son traces de SU propio agente)

## Agentes / skills recomendados

| Fase | Agente/skill | Prompt | Entregable |
|---|---|---|---|
| Pre-design | `nicolify-architect` (Opus) | `prompts/01-architect-start.md` | `CONTRACT.md` con schema base + migration order + coordination plan |
| Pre-flight context | `nicolify-context-builder` (Haiku) | architect spawn auto | `CONTEXT-BRIEF.md` |
| Implementation | `nicolify-agentic` (Opus) | `prompts/02-builder-agentic.md` (template + Step 0 grep gate) | code + tests + IMPL-LOG-agentic.md |
| Audit | `nicolify-agentic-auditor` (Opus, auto-spawn) | builder dispara | REVIEW-agentic.md (Cat 13 mirror detection MUST PASS) |
| Cierre | `/pm` | `prompts/04-pm-close.md` | `RESULT.md` + `current-state/sales_agent.md` + `current-state/copilot.md` lineage |

**Skills mandatory cargar (anti-skill-routing-violation):**
- Architect: `copilot-expert`, `sales-agent-expert`, `tessl__langgraph` (state hygiene), `tessl__graceful-degradation` (best-effort writes)
- Builder agentic: `copilot-expert` + `sales-agent-expert` + `tessl__langgraph` + `tessl__graceful-degradation` + `tessl__pytest-api-testing`
- Auditor: `copilot-expert` + `sales-agent-expert` + `tessl__langgraph`

## Surface impactada (preliminary — architect refines)

| Tipo | Path | Cambio |
|---|---|---|
| BE shared NEW | `backend/src/shared/agent_observability/recording/turn_envelope.py` | NEW — BaseObservabilityContext abstract |
| BE shared MOD | `backend/src/shared/agent_observability/cost/fx_resolver.py` | add `default()` classmethod |
| BE module copilot | `backend/src/modules/copilot/observability/recording/turn_envelope.py` | RENAME or DELETE → reemplaza por `context.py` que hereda shared base |
| BE module sales_agent NEW | `backend/src/modules/sales_agent/observability/recording/context.py` | NEW concrete subclass (NO mirror file naming) |
| BE module sales_agent MOD | `backend/src/modules/sales_agent/observability/recording/factory.py` | line 116, 168 fix `FXResolver()` → `FXResolver.default()`. Refactor para usar new context |
| BE orchestrator copilot | `backend/src/modules/copilot/application/orchestrator/chat.py` | line 647, 1110, 1230 use new context + `FXResolver.default()` |
| BE orchestrator sales_agent | `backend/src/modules/sales_agent/application/orchestrator/{chat,outbound_orchestrator}.py` | use new context (replaces inexistent envelope) |
| Tests | `backend/tests/modules/sales_agent/observability/test_real_trace_persistence.py` | NEW — real DB persistence assert |
| Tests | `backend/tests/modules/copilot/observability/test_envelope_inheritance.py` | NEW — copilot regression test post-refactor |
| Tests | `backend/tests/shared/agent_observability/test_turn_envelope_base.py` | NEW — base contract tests |
| current-state | `docs/pm-nico/current-state/sales_agent.md` | append capability "Observability traces persistence (live)" with lineage |
| current-state | `docs/pm-nico/current-state/copilot.md` | append note "Observability refactored to shared base — capability unchanged user-facing" |

## Tests requeridos (TDD)

- **Real DB persistence sales_agent** — `tests/modules/sales_agent/observability/test_real_trace_persistence.py` — setup real AsyncSession + lead + tenant → simulate turn lifecycle → assert ≥1 row in `sales_agent_trace_event`. NO mocks DB session.
- **Copilot regression** — `tests/modules/copilot/observability/test_envelope_inheritance.py` — assert `CopilotObservabilityContext(BaseObservabilityContext)` + lifecycle parity con pre-refactor behavior.
- **Base contract** — `tests/shared/agent_observability/test_turn_envelope_base.py` — abstract methods enforced + commit lifecycle correctness.
- **FX factory regression** — `tests/shared/agent_observability/cost/test_fx_resolver_default.py` — `.default()` retorna FXResolver con httpx client functional.
- **Cross-module integration** — ensure no `FXResolver()` (no-arg) calls remain in codebase via grep test.

## Aceptación

- [ ] CONTRACT.md producido por architect Opus con grep evidence completa
- [ ] CONTRACT.md "Existing systems audit" sección con paths + line numbers reales (no claims)
- [ ] Tests verdes incluyendo real DB persistence sales_agent
- [ ] Lint/type/arch fitness verdes (BE)
- [ ] IMPL-LOG-agentic.md con Step 0 grep findings sección obligatoria
- [ ] REVIEW-agentic.md verdict PASS (Cat 13 mirror detection PASS)
- [ ] Smoke real Telegram message → DB trace count growth verified
- [ ] RESULT.md escrito por PM con lineage update
- [ ] `current-state/sales_agent.md` + `current-state/copilot.md` updated
- [ ] Decisiones registradas en `decisions.md` PI-1.1
- [ ] `process-learnings.md` append "Anti-duplication rule first test passed"

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Cross-session collision PI-5 PR-2 (copilot WIP) | PI-5 PR-2 mergea primero. PR-2 architect coordinates lock-step. PM monitorea git status pre-builder spawn |
| Real DB persistence test rompe CI por flakiness | Use `pytest -m verify` marker. Skip en gates default si no DB. Forzar en /test-all |
| Refactor copilot envelope rompe 4260 traces existing functionality | Regression test `test_envelope_inheritance.py` antes de merge. Architect plan migration order copilot first o sales_agent first |
| Architect Opus paused mid-CONTRACT (cap caché) | Re-spawn fresh con avance en disco. Rule "Opus paused → resume Opus" |
| Builder Step 0 grep gate falla detectar duplication | Auditor Cat 13 redundancy + PR.md mandatory grep block triple-layer check |

## Estado lifecycle

`discovery` → architect ejecuta CONTRACT.md → estado `ready` → builder spawn → estado `in-progress` → PASS audit → estado `review` → PM cierra → estado `shipped`
