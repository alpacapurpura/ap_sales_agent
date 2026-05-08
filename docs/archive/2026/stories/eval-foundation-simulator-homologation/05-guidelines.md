# 05-guidelines.md — Story eval-foundation-simulator-homologation

> /architect orchestrator delivered (2026-05-07). Patterns required + forbidden + files in/out scope. Cero ambigüedad. Builders consultan ESTO antes de cada Edit.

## Patterns required (cero deuda — escala 1000+ tenants × N updates)

### Backend (Python 3.12 + FastAPI + SQLA 2.0 + Alembic + Pydantic v2)

- **SQLAlchemy 2.0** — `select(Model).where(...)`, NUNCA `session.query()`
- **Tenant isolation** — cada query DB filtra `tenant_id` (incluye `get_by_id`). Fixture `eval_tenant_seeded` hereda invariante.
- **Soft deletes** — `deleted_at` field, NUNCA hard `DELETE FROM`. Teardown fixture sets `deleted_at = utc_now()`.
- **`utc_now()` from `shared/domain/datetime_utils.py`** — NUNCA `datetime.utcnow()` (deprecated + naive).
- **`DateTime(timezone=True)` Mapped** — siempre con timezone awareness.
- **Pydantic v2 ConfigDict** — `model_config = ConfigDict(extra="forbid", frozen=True)` para Pydantic models inmutables. NUNCA inner `class Config`.
- **`structlog`** logging — NUNCA `print` / `logging.{info,warn,error}`. Structured fields obligatorios (`simulation_id`, `tenant_archetype_slug`, etc.).
- **Idempotent migrations raw SQL** — `ALTER TABLE ... IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`. NUNCA `op.create_table()` / `op.add_column()` (no idempotente). NUNCA `sa.Enum()` en `op.create_table()` (broken SA 2.0.27).
- **Schema-mirror exception R5** — `builder-backend` MAY touch `modules/sales_agent/persistence/models/` SOLO para schema mirror desde shared/migration. NO `domain/`, `application/`, `api/`, `observability/`.
- **Anti-duplication §0** — antes Write nuevo file: grep cross-codebase + `cat .claude/rules/anti-duplication.md` inventario shared. Match → STOP escalate. Subclase desde shared, NO mirror.

### LangGraph + agentic test-infra

- **Pydantic state, NO TypedDict** — D4 ratificado. `SimulationState(BaseModel)` con `schema_version: int = 1` field.
- **Reducers correctos** — `Annotated[list[ConversationTurn], operator.add]` para append-only transcript. Nunca mutate in-place.
- **`from __future__ import annotations` PROHIBIDO** en `simulator/_internal/graph.py` (rompe LangGraph runtime introspection — cement same que `*/orchestrator/graph.py` runtime).
- **`agent_app.ainvoke` in-process** — D1 ratificado. Reusa `ConversationPipeline.{build_identity, build_brand_voice, create_initial_state}` verbatim. NUNCA HTTP webhook.
- **`MultiRoleLLMRouter` + LLMFactory** — customer LLM via `LLMFactory.get_service(model_type=ModelRole.NANO, ...)` con eval-only registry `simulator/_internal/llm_roles.py::EVAL_LLM_ROLES`. NO pollute `LLM_ROLE_BY_SITE` SSoT.
- **`BaseObservabilityContext` subclass** — `EvalSimulatorObservabilityContext(BaseObservabilityContext)`. NUNCA mirror `turn_envelope.py`.
- **`BaseAgentCallbackHandler` subclass** — `EvalSimulatorCallbackHandler(BaseAgentCallbackHandler)`. Override solo `_persist_llm_call_row` + `_persist_trace_event_row` (Template Method).
- **`sanitize_payload(...)` pre-write** — heredado del shared base, NO re-implementar local. Aplicado a TODO `data` + `eval_metadata` jsonb fields.
- **UUID5 deterministic** — `simulation_id = uuid5(NAMESPACE_DNS, f"{run_id}_{slug}_{actor.id}_{trial_n}")`, `tenant_id = uuid5(NAMESPACE_DNS, f"eval-{archetype_slug}")`. H2 idempotency.
- **Async-first** — `run_simulation` `async def`, cero global state mutate. `asyncio.Semaphore(EVAL_SIMULATOR_MAX_CONCURRENCY=10)` global per worker.
- **Observability tags MANDATORY** — TODA row escrita lleva `metadata.eval_run_kind="simulator"` + `archetype_slug` + `actor_profile_id` + `trial_n` + `simulation_id` + `run_id` (H5).
- **Best-effort writes** — try/except + structlog warning. NO rompe simulation por error en observability.
- **Schema versioning forward-compat** — cada Pydantic class `schema_version: int = 1`. Bumps registered en `SCHEMA_MIGRATIONS` registry mismo commit. Frozen golden v1 fixture NUNCA editar.
- **Termination policy registry (Strategy)** — `TERMINATION_POLICIES: dict[str, TerminationPredicate]` + `register_termination_policy(name, predicate)`. Default 4 policies. Story I/H append sin tocar core.
- **Public API minimal** — `simulator/__init__.py::__all__` = exactamente 7 nombres (`run_simulation`, `SimulationResult`, `SimulationState`, `ActorProfile`, `TerminationReason`, `AgentErrorSubtype`, `register_termination_policy`). Resto bajo `_internal/`.

### Voice + Spanish

- **Customer prompt voseo permitido** SI `actor_profile.dialect_code == 'es-AR'`. Magic comment `# voseo-allowed: actor persona dialect injection` en fixtures es-AR.
- **Resto código Spanish neutro** — error messages CLI/structlog/comments/README en español neutro LatAm (no voseo, no léxico regional). Aplica `.claude/rules/spanish-text.md` glosario.
- **Customer prompt NO interpolar `{tenant_name}` mid-block** — anti-pattern cache prefix sales-agent-expert §3.
- **Agent output voice = compiled per `tenant.personality_profile.system_instruction` slot 5** — heredado, NUNCA override. `personality_profile` SSoT respetado.

## Patterns forbidden (cero deuda)

- ❌ `datetime.utcnow()` — use `utc_now()`
- ❌ `DateTime()` sin `timezone=True`
- ❌ Hardcoded `'USD'` — use `tenant_context.pricing.currency`
- ❌ Hardcoded model names en customer_node — use `EVAL_LLM_ROLES` registry
- ❌ Cross-module imports excepto `copilot` (here: simulator imports `shared/agent_observability` + `modules/sales_agent` runtime — both whitelisted)
- ❌ `session.query()` (SA 1.x — broken patterns)
- ❌ `sa.Enum()` en `op.create_table()` (SA 2.0.27 broken)
- ❌ `op.create_table()` / `op.add_column()` / `op.create_index()` no idempotente — RAW SQL `IF NOT EXISTS` only
- ❌ `from __future__ import annotations` en `simulator/_internal/graph.py` (rompe LangGraph)
- ❌ Mirror `turn_envelope.py` / `callback_handler.py` / `cost_calculator.py` / `fx_resolver.py` desde shared — STOP escalate
- ❌ Modify `client_simulator/src/simulator/*.py` legacy (D6 — preservation gate, sha256 unchanged)
- ❌ Pollute `LLM_ROLE_BY_SITE` SSoT con eval-only role (decisión §2.1 03-arch-agentic — eval-only registry separate)
- ❌ Bypass `sanitize_payload` en writes a `eval_simulator_*` tables
- ❌ Skip `tenant_id` filter en query DB (incluye `get_by_id`)
- ❌ TypedDict en LangGraph state (D4 — Pydantic only)
- ❌ HTTP webhook invocation desde agent_bridge (D1 — in-process only)
- ❌ Edit frozen golden v1 fixture `_fixtures/golden_v1_simulation_result.yaml`
- ❌ Hardcoded `tenant_id` en fixture (must `uuid5(NS_DNS, f"eval-{slug}")` deterministic)
- ❌ Edit `.claude/rules/auditor-downstream-regression.md` SSoT table sin freshness gate (R3 enforced)
- ❌ Skip arch fitness gates ratchet — allowlists shrink-only forever
- ❌ Inline `{tenant_name}` interpolation en customer prompt cacheable slots
- ❌ Crear new file en `modules/sales_agent/{domain,application,api,observability}/` desde builder-backend (R5 schema-mirror exception solo aplica a `persistence/models/`)
- ❌ Toca §3 protected surfaces sales-agent (closer_studio, SmartBuffer, OutputManager.process_response, enrollment_*, webhook adapters, follow_up_engine, PromptVersionModel, model_pricing_snapshot schema, tool_call_dedup) — STOP escalate
- ❌ ALTER TYPE ENUM (no existe `agent_kind` enum DB — discriminador registry-level, no DDL — clarification §2.4 BE arch)
- ❌ `// eslint-disable` / `# noqa` sin justification comment
- ❌ `any` TS / loose Python types — strict typing
- ❌ Default exports (excepto Next.js pages — N/A esta story FE no toca)
- ❌ `git add .` / `git add -A` — stage por nombre exacto
- ❌ `git commit --no-verify` — pre-commit hook native enforced
- ❌ `git pull` / `git fetch && merge` — parallel-safety multi-instancia

## Files in scope (builders edit ONLY these)

### Migration (BE prod-code R5)
- `backend/alembic/versions/124_add_eval_simulator_observability_tables.py` (NEW)
- `backend/src/modules/sales_agent/observability/eval_simulator/__init__.py` (NEW)
- `backend/src/modules/sales_agent/observability/eval_simulator/persistence/__init__.py` (NEW)
- `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/__init__.py` (NEW)
- `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_llm_call.py` (NEW — schema mirror)
- `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_simulator_trace_event.py` (NEW — schema mirror)
- `backend/src/modules/sales_agent/observability/eval_simulator/persistence/models/eval_synthetic_tenants.py` (NEW — schema mirror lookup)
- `backend/src/modules/sales_agent/observability/eval_simulator/spec.py` (NEW — `register_agent_observability(agent_kind="eval_simulator", ...)`)
- `backend/src/shared/infrastructure/agent_observability_bootstrap.py` (1-LINE EDIT — append `from src.modules.sales_agent.observability.eval_simulator import spec  # noqa: F401`)

### Test infrastructure (BE non-prod-code)
- `backend/tests/migrations/test_extend_eval_simulator_observability.py` (NEW)
- `backend/tests/agentic_evals/sales_agent/simulator/__init__.py` (NEW — public API surface H9)
- `backend/tests/agentic_evals/sales_agent/simulator/state.py` (NEW)
- `backend/tests/agentic_evals/sales_agent/simulator/actor_profile.py` (NEW)
- `backend/tests/agentic_evals/sales_agent/simulator/result.py` (NEW — SimulationResult + ConversationTurn + CostSummary)
- `backend/tests/agentic_evals/sales_agent/simulator/termination.py` (NEW)
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/__init__.py` (NEW)
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/runner.py` (NEW — `run_simulation` orchestrator)
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/graph.py` (NEW — LangGraph compose)
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/customer_node.py` (NEW)
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/agent_bridge.py` (NEW)
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/observability.py` (NEW — EvalSimulatorObservabilityContext + EvalSimulatorCallbackHandler subclasses)
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/llm_roles.py` (NEW — `EVAL_LLM_ROLES = {"EVAL_USER_SIMULATOR": "gpt-5-nano"}`)
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/leak_assertions.py` (NEW — `FORBIDDEN_LEAK_STRINGS` frozen list)
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/concurrency.py` (NEW — global semaphore)
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/schema_migrations.py` (NEW — `SCHEMA_MIGRATIONS` registry)
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/customer_persona_prompt.py` (NEW — `CUSTOMER_PERSONA_PROMPT_V1` constant)
- `backend/tests/agentic_evals/sales_agent/simulator/fixtures/__init__.py` (NEW)
- `backend/tests/agentic_evals/sales_agent/simulator/fixtures/tenant_seeded.py` (NEW — `eval_tenant_seeded` fixture)
- `backend/tests/agentic_evals/sales_agent/simulator/fixtures/actor_profiles.py` (NEW — 3 hardcoded ActorProfile fixtures Pydantic)
- `backend/tests/agentic_evals/sales_agent/simulator/fixtures/test_tenant_seeded.py` (NEW — fixture test)
- `backend/tests/agentic_evals/sales_agent/simulator/test_simulator_smoke.py` (NEW — 9 test cases: 5-archetype parametrize + 4 single-tenant)
- `backend/tests/agentic_evals/sales_agent/simulator/test_schema_migration_regression.py` (NEW — H10 frozen golden)
- `backend/tests/agentic_evals/sales_agent/simulator/test_concurrency_property.py` (NEW — H3 property test)
- `backend/tests/agentic_evals/sales_agent/simulator/test_termination_registry.py` (NEW — H8 registry contract)
- `backend/tests/agentic_evals/sales_agent/simulator/_fixtures/__init__.py` (NEW)
- `backend/tests/agentic_evals/sales_agent/simulator/_fixtures/golden_v1_simulation_result.yaml` (NEW — frozen H10)
- `backend/tests/agentic_evals/sales_agent/simulator/conftest.py` (NEW — pytest fixtures wiring + `--run-evals` flag honor)

### Architecture fitness gates (BE non-prod-code)
- `backend/tests/architecture/test_eval_simulator_observability_invariants.py` (NEW)
- `backend/tests/architecture/test_simulator_no_mirrors_shared.py` (NEW)
- `backend/tests/architecture/test_simulator_writes_eval_kind_tag.py` (NEW)
- `backend/tests/architecture/test_simulator_public_api_surface.py` (NEW)
- `backend/tests/architecture/test_schema_migrations_registry_complete.py` (NEW)
- `backend/tests/architecture/test_termination_policy_registry_contract.py` (NEW)

### SSoT updates (rules + capability + module narrative — post-merge by /pm)
- `.claude/rules/auditor-downstream-regression.md` (1-line update — add entry `backend/src/modules/sales_agent/observability/eval_simulator/**` → downstream tests when consumers C/D/E/F/G/H/I arrive)
- `docs/product/capabilities/sales_agent/sales-conversational-engine.yaml` (4 new fields appended)
- `docs/product/modules/sales_agent.md` (1-2 sentence narrative update — bucket separation eval_simulator)

## Files NEVER touched (escalate to Chris if needed)

- `backend/src/modules/sales_agent/{domain,application,api,observability}/` ← R5 schema-mirror exception SOLO permite `persistence/models/` — el resto agentic territory builder-agentic NO builder-backend
- `backend/src/modules/sales_agent/observability/recording/` ← runtime sales_agent owns this. eval_simulator/ es OTRA cosa adyacente.
- `backend/src/modules/copilot/**` ← agentic builder territory only
- `backend/src/shared/agent_observability/{recording,cost,channels}/` ← solo lectura. Cualquier cambio requiere LIFT-TO-SHARED process via /pm
- `backend/src/core/config.py` ← R31 anti-default-flip-audit aplica
- `backend/alembic/versions/[!1][!2][!4]*.py` ← migraciones existentes — solo migration 124 nueva
- `frontend/**` ← N/A esta story FE no toca
- `client_simulator/src/simulator/*.py` ← D6 preservation gate (sha256 unchanged byte-equal)
- `.claude/skills/`, `.claude/agents/`, `.claude/rules/` (excepto auditor-downstream-regression entry add) ← skill/rule edits manual via /pm
- §3 sales-agent protected surfaces — `closer_studio.py`, `SmartBufferService`, `OutputManager.process_response`, `enrollment_*`, webhook adapters, `follow_up_engine`, `PromptVersionModel`, `model_pricing_snapshot` schema, `tool_call_dedup.py` ← STOP, ASK CHRIS

## Reference docs (load before coding — orden estricto)

### Universal (load primero, todos tickets)
1. `01-spec.md` (re-read scenarios + decisions D1-D11 + hardening H1-H10 mid-build)
2. `03-arch.md` (consolidated cross-cutting decisions)
3. `03-arch-be.md` (BE-specific tickets T-1..T-3)
4. `03-arch-agentic.md` (AGENTIC-specific tickets T-4..T-10)
5. `04-validators.yaml` (test commands ejecutables)

### Skills (per surface)
- `sales-agent-expert` — §3 protected surfaces, anti-patterns, decisiones cross-fase, brand voice cement
- `tessl__langgraph` — LangGraph patterns (Pydantic state, reducers, conditional edges, runtime introspection)
- `claude-api` — Anthropic SDK patterns + prompt caching slot architecture
- `tessl__pytest-api-testing` — pytest-asyncio patterns, fixtures, parametrize
- `tessl__graceful-degradation` — timeouts, fallbacks, circuit breakers, structured logs
- `backend-expert` — DDD patterns, arch fitness, currency, master-data, schema-mirror exception R5
- `copilot-expert` — observability writes best-effort patterns

### Rules (cement before each Edit)
- `.claude/rules/anti-duplication.md` — inventario shared SSoT (CONSULTAR antes Write nuevo file)
- `.claude/rules/anti-default-flip-audit.md` — no flag flip aquí (rule reference informational)
- `.claude/rules/auditor-downstream-regression.md` — UPDATE entry post-merge
- `.claude/rules/architectural-fitness.md` — 5 NEW gates con allowlists vacías shrink-only
- `.claude/rules/backend-ddd.md` — schema-mirror exception R5 alcance estricto
- `.claude/rules/backend-migrations.md` — idempotent raw SQL `IF NOT EXISTS`
- `.claude/rules/copilot-observability.md` — best-effort writes try/except + structlog warning
- `.claude/rules/copilot-resilience.md` — observability invariants
- `.claude/rules/parallel-safety.md` — `git add` por nombre, no force push, no pull
- `.claude/rules/sales-agent-brand-voice.md` — excepción simulator: voz tenant respetada agent-side; voseo permitido en customer prompts es-AR
- `.claude/rules/spanish-text.md` — voseo glosario + magic comment escape `<!-- voseo-allowed -->`
- `.claude/rules/tdd-mandatory.md` — RED → GREEN → REFACTOR per layer
- `.claude/rules/tenant-isolation.md` — every query filter `tenant_id`
- `.claude/rules/git-safety.md` — Conventional Commits, branch=development, no feature branches

### Templates (consult during ticket execution)
- `docs/specs/templates/T-handoff-template.md`
- `docs/specs/templates/T-impl-log-template.md`
- `docs/specs/templates/T-result-template.md`
- `docs/specs/templates/T-review-template.md`

## Native-first execution (mandatory)

Toda lint/test/type-check NATIVE WSL — NUNCA Docker:
- BE: `cd backend && .venv/bin/{ruff,pytest,mypy,jscpd}` (venv 3.12)
- Migration: `docker exec visionarias_brain_dev alembic upgrade head` (Docker SOLO para alembic + runtime)

Pre-commit hook native enforced — `--no-verify` PROHIBIDO.

## TDD obligatorio (RED → GREEN → REFACTOR per layer)

Orden estricto:
1. **Domain Pydantic models** RED → GREEN → REFACTOR (state.py, actor_profile.py, result.py, termination.py)
2. **Infrastructure** (observability subclasses, persistence models) RED → GREEN
3. **Application** (customer_node, agent_bridge, runner) RED → GREEN
4. **Integration** (graph compose + run_simulation) RED → GREEN
5. **API surface** (`__init__.py` + arch fitness gates) RED → GREEN

Cada layer: tests primero (failing) → implementación mínima (passing) → refactor.

Default flag flips: N/A esta story (no flag en `core/config.py`).

## Anti-telephone-game (subagent return contract)

Cada builder/auditor MUST devolver UNA línea final:
```
<verdict> -> <path-to-artifact>
```

Examples:
- `done -> docs/product/stories/eval-foundation-simulator-homologation/T-1-result.md`
- `blocked -> docs/product/stories/eval-foundation-simulator-homologation/checkpoint.md`
- `failed -> backend/tests/agentic_evals/sales_agent/simulator/test_simulator_smoke.py:42 [empty_response not raised]`

NUNCA inline >500 tokens de artifact body. Caller lee file on demand.

## Process metrics (R12 Layer 1 — emit on each ticket close)

Builder Step 5.5 + Auditor Step 4.5 emit metrics via `scripts/emit_process_metric.py`. Default fields: ticket_id, story_id, phase, duration_minutes, tokens_consumed, model_used, validators_pass_count, validators_fail_count.

## Decisiones de owner routing (per /architect)

| Ticket | Surface | production_code | Owner recomendado | Justificación |
|---|---|---|---|---|
| T-1 | BE prod-code R5 | true | builder-backend Sonnet | Schema mirror + migration — R5 exception aplica |
| T-2 | BE test-infra | false | builder-backend Sonnet | Migration test + arch gate — test infra |
| T-3 | BE test-infra | false | builder-backend Sonnet | Fixture seed — test infra |
| T-4 | AGENTIC test-infra | false | builder-agentic Opus 4.7 | Pydantic state machines + schema versioning — agentic complexity (R23 permite Sonnet pero recomendamos Opus) |
| T-5 | AGENTIC test-infra | false | builder-agentic Opus 4.7 | Observability subclasses — anti-mirror discipline crítica |
| T-6 | AGENTIC test-infra | false | builder-agentic Opus 4.7 | Customer LLM dispatch + prompt v1 — voice fidelity defense |
| T-7 | AGENTIC test-infra | false | builder-agentic Opus 4.7 | Agent_bridge in-process + leak assertions — anti-prompt-injection |
| T-8 | AGENTIC test-infra | false | builder-agentic Opus 4.7 | LangGraph graph compose + runner orchestration |
| T-9 | AGENTIC test-infra | false | builder-agentic Opus 4.7 | Public API + frozen golden + arch gates — H9/H10 invariants |
| T-10 | AGENTIC test-infra | false | builder-agentic Opus 4.7 | Smoke + regression + downstream rule update |

> **Decisión final routing**: Per `CLAUDE.md` cost-routing matrix + R23 + Chris mandato cero deuda 1000+ tenants. Aunque R23 permite Sonnet en agentic test-infra, complejidad cross-cutting (schema versioning, dual-LLM dispatch, termination registry, voice fidelity defense, anti-prompt-injection) justifica Opus 4.7. PM confirma final routing antes Conv 2 arranca.
