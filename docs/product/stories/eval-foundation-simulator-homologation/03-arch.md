---
story_id: eval-foundation-simulator-homologation
arch_role: orchestrator-consolidated
sub_architects:
  - 03-arch-be.md       # BE surface — migration + persistence + fixture + arch gates
  - 03-arch-agentic.md  # AGENTIC surface — LangGraph state machine + dual-LLM dispatch + termination registry
arch_version: 1
last_modified: 2026-05-07T22:00:00Z
links:
  spec: 01-spec.md
  story_yaml: 00-story.md
  outcome: ../../outcomes/pi-12-sales-agent-eval-foundation.md
  pre_requisite: ../../../archive/2026/stories/eval-foundation-tenant-seed-data/
  legacy_simulator: ../../../../client_simulator/
  consumers:
    - ../sales-agent-personas-instrumented-runtime/   # C
    - ../sales-agent-goldens-3-tenants-dataset/        # D
    - ../sales-agent-voice-fidelity-grader-runtime/    # E
    - ../sales-agent-eval-pass-k-tracking/             # F
    - ../sales-agent-voice-fidelity-ci-gate/           # G
    - ../sales-agent-eval-cost-budget-cap/             # H
    - ../sales-agent-adversarial-jailbreak-suite/      # I
---

## Resumen

Story B (`eval-foundation-simulator-homologation`) homologa el legacy
`client_simulator/` raíz a `backend/tests/agentic_evals/sales_agent/simulator/`
con cero deuda técnica para escalar a 1000+ tenants × 1000+ leads × N
actualizaciones futuras. Spec ratificada Chris 2026-05-07 con D1-D11
cardinales + H1-H10 hardening extras.

Tres surfaces:

1. **BE production-code surface** (1 migration Alembic + 4 SQLAlchemy models + 1 spec registration + 1 bootstrap line) — bucket separation cost tracking via tablas nuevas `eval_simulator_{trace_event,llm_call}` + `eval_synthetic_tenants` lookup. Patrón cementado paridad `campaigns/observability/` (PI-1 S0 PR-1 / Alembic 083). Schema-mirror exception R5 aplica.
2. **BE test-infrastructure surface** (DB-seed fixture + arch fitness gates + downstream regression SSoT update) — materializa `TenantContext` Story A en filas DB con `tenant_id = uuid5(NS_DNS, f"eval-{slug}")` deterministic + soft-delete teardown idempotente.
3. **AGENTIC test-infrastructure surface** (~17 archivos Python bajo `simulator/` + 4 fixtures) — LangGraph dual-LLM dispatch in-process via `agent_app.ainvoke`, customer LLM via `LLMFactory.get_service()` con role nuevo `EVAL_USER_SIMULATOR` en eval-only registry, termination policy registry (Strategy pattern H8), schema versioning forward-compat (H1), public API minimal de 7 nombres (H9).

## Surfaces involved

| Surface | Production code? | Builder | Auditor | Skills consultados |
|---|---|---|---|---|
| BE schema mirror + migration + spec registration | YES (R5 schema-mirror exception) | `builder-backend` (Sonnet OK per R5) | `auditor-backend` (Opus C1-C3 + Sonnet tests) | backend-expert, sales-agent-expert, tessl__fastapi |
| BE test-infrastructure (fixture, arch gates) | NO | `builder-backend` (Sonnet) | `auditor-backend` | backend-expert |
| AGENTIC test-infrastructure (state, customer_node, agent_bridge, graph, termination, schemas) | NO (production_code=false per R23) | `builder-agentic` (Opus 4.7 mandatory por agentic complexity, aunque R23 permite Sonnet) | `auditor-agentic` (Opus C1-C3 + Sonnet tests) | sales-agent-expert, copilot-expert, tessl__langgraph, tessl__graceful-degradation |
| FE | N/A | — | — | — |

> **Owner choice rationale**: AGENTIC surface es test-infrastructure (no
> runtime production agentic) → R23 permite Sonnet builder. Sin embargo,
> dado mandato Chris "1000+ tenants cero deuda" + complejidad cross-cutting
> (schema versioning, dual-LLM dispatch, termination registry, voice fidelity
> defense, anti-prompt-injection), recomendamos **Opus 4.7** para ALL
> agentic tickets. PM confirma final routing.

## Resúmenes BE + AGENTIC

### BE arch (cita 03-arch-be.md)

- **Migration 124** (`backend/alembic/versions/124_add_eval_simulator_observability_tables.py`) — idempotente raw SQL: 3 tablas nuevas (`eval_simulator_llm_call`, `eval_simulator_trace_event`, `eval_synthetic_tenants`) + 6 índices. Cero `agent_kind` enum DB (no existe — discriminador de registry, no DDL). Mirror exact schema `campaigns_llm_call` con caveat `lead_id NULL` + retention 30 días default + `eval_metadata` jsonb column nuevo.
- **SQLAlchemy mirror** (`backend/src/modules/sales_agent/observability/eval_simulator/`) — bajo R5 schema-mirror exception, builder-backend MAY tocar persistence/models. Spec registration via `register_agent_observability(agent_kind="eval_simulator", ...)` siguiendo precedente exacto campaigns.
- **Bootstrap** (`backend/src/shared/infrastructure/agent_observability_bootstrap.py`) — append 1 línea: `from src.modules.sales_agent.observability.eval_simulator import ... # noqa: F401`. Triggers spec registration.
- **DB-seed fixture** (`backend/tests/agentic_evals/sales_agent/simulator/fixtures/tenant_seeded.py`) — story-local (NO cross-eval), idempotent upsert + soft-delete teardown, 5-archetype parametrize-ready.
- **5 arch fitness gates nuevos** — `test_simulator_no_mirrors_shared.py`, `test_simulator_writes_eval_kind_tag.py`, `test_simulator_public_api_surface.py`, `test_schema_migrations_registry_complete.py`, `test_termination_policy_registry_contract.py` (allowlists vacías inicial — shrink-only).
- **Auditor downstream regression** — UPDATE `.claude/rules/auditor-downstream-regression.md` § tabla SSoT con entry `backend/src/modules/sales_agent/observability/eval_simulator/**` → downstream tests.

Detalle completo: `03-arch-be.md`.

### AGENTIC arch (cita 03-arch-agentic.md)

- **`SimulationState` LangGraph state** Pydantic v2 (NO TypedDict — D4) bajo `simulator/state.py`. Reducers: `Annotated[list[ConversationTurn], operator.add]` para transcript append-only. `tenant_id: UUID` MANDATORY tenant isolation. `iterations: int` H3 max-iter guard. **NO `from __future__ import annotations`** en `graph.py` (cement same reason que copilot/sales-agent runtime).
- **Topology**: `customer_node → agent_bridge → increment_turn → [conditional → END | loop]`. LangGraph StateGraph compiled.
- **Dual-LLM dispatch**:
  - Customer LLM via `LLMFactory.get_service()` con `model_type=ModelRole.NANO` + override metadata `model_override="gpt-5-nano"`. Role `EVAL_USER_SIMULATOR` declarado en **eval-only registry** `simulator/_internal/llm_roles.py` (NO en `LLM_ROLE_BY_SITE` SSoT — decisión §2.1 spec).
  - Agent_bridge invoca `agent_app.ainvoke` in-process (D1) reusing `ConversationPipeline.{build_identity, build_brand_voice, create_initial_state}` heredando observability completa.
  - Cost-bucket separation: customer LLM → `eval_simulator_llm_call`; agent runtime → `sales_agent_llm_call`.
- **Customer prompt versioned** `CUSTOMER_PERSONA_PROMPT_V1` con voseo permitido si dialect_code=es-AR (magic comment escape). Cache-prefix safe: NO `{tenant_name}` interpolation, NO timestamps.
- **Observability** — `EvalSimulatorObservabilityContext` + `EvalSimulatorCallbackHandler` SUBCLASSES de `BaseObservabilityContext` + `BaseAgentCallbackHandler` shared (ZERO mirror). Mandatory `eval_metadata` jsonb fields (H5): `eval_run_kind="simulator"`, `archetype_slug`, `actor_profile_id`, `trial_n`, `simulation_id`, `run_id`. `sanitize_payload(...)` aplicado pre-write (heredado).
- **Termination policy registry** (H8 Strategy pattern) — `TERMINATION_POLICIES: dict[str, TerminationPredicate]` + `register_termination_policy(name, predicate)`. Default 4: goal_completion, max_turns, customer_exit, agent_error. Story I appends adversarial_detected; story H appends budget_exceeded.
- **Schema migrations registry** (H1) — `SCHEMA_MIGRATIONS: dict[(model, prev, curr), Callable]`. Story B ships v1 only (registry empty). Frozen golden v1 fixture + regression test.
- **Public API surface minimal** (H9) — `simulator/__init__.py::__all__` = 7 names exact. Resto bajo `_internal/`.
- **Concurrency** (H3 + H4) — `run_simulation` async, cero global state. `asyncio.Semaphore(EVAL_SIMULATOR_MAX_CONCURRENCY=10)` global per worker, env override.

Detalle completo: `03-arch-agentic.md`.

## Cross-cutting decisions consolidadas

### Tenant isolation strategy

- `tenant_id = uuid5(NAMESPACE_DNS, f"eval-{archetype_slug}")` deterministic UUID5 (D2 + H2)
- Lookup table `eval_synthetic_tenants` (decision D-BE-4 03-arch-be) marca tenant_id como synthetic — Streamlit prod queries pueden filtrar `WHERE tenant_id NOT IN (SELECT tenant_id FROM eval_synthetic_tenants WHERE deleted_at IS NULL)` para vista de producción real.
- NO column `is_eval_synthetic` agregada a tablas business (>5 tablas tocadas — costo migration sin ROI; lookup table escala mejor)
- Cada query DB filtra `tenant_id` explícito en fixture seed + repos (cement `.claude/rules/tenant-isolation.md`)
- Scenario 4 sub-case B grader assertions verifican `SELECT DISTINCT tenant_id FROM ...trace_event WHERE eval_metadata->>'simulation_id' = ?` retorna 1 row (no leak)

### PII handling

- `sanitize_payload(...)` aplicado pre-write a `eval_metadata` + `data` jsonb fields (heredado del shared base, NO re-implementado)
- Transcripts artifacts JSON sanitizados via `write_run_artifacts` patrón existente runner
- Defense in depth H10: `FORBIDDEN_LEAK_STRINGS` frozen list en `_internal/leak_assertions.py` para post-run verify negation

### Currency + master data

- `started_at TIMESTAMPTZ NOT NULL` UTC store en migration
- `tenant_currency CHAR(3)` desde `TenantContext.pricing.currency` (NO hardcoded `'USD'` — heredado de `master-data.md`)
- FX via `FXResolver.default()` shared abstraction

### Schema versioning forward-compat (H1)

- Cada Pydantic class `schema_version: int = 1`
- `SCHEMA_MIGRATIONS` registry chain
- Frozen golden v1 + arch test regression
- Future bumps: append migration entry, golden v1 NUNCA editado (regression integrity)

### Observability tags (H5)

- `eval_metadata.eval_run_kind = "simulator"` MANDATORY en cada row
- Streamlit `/sales-agent-quality` + `/sales-routing` queries de prod NO ven traffic synthetic (separación física por tabla — tabla aparte)

### Cost buckets (H6)

- `agent_kind="eval_simulator"` registrado via `register_agent_observability(...)` paridad campaigns precedent
- Tabla aparte `eval_simulator_llm_call` — cross-agent MV split por `agent_kind` discriminator
- Streamlit `/costo-agentes` muestra "eval CI cost / month" separate de "production cost"

### Determinism + idempotency (H2)

- `simulation_id = uuid5(NAMESPACE_DNS, f"{run_id}_{slug}_{actor.id}_{trial_n}")` — re-run con mismos inputs → mismo UUID → artifact path estable
- Story F (pass^k trials) consumes `trial_n` from day 1

### Spanish neutro

- BE error messages + structlog en español neutro (`.claude/rules/spanish-text.md`)
- Customer prompt voseo permitido si dialect=es-AR (magic comment `# voseo-allowed: actor persona dialect injection`)
- Agent output voice = compiled per `tenant.personality_profile.system_instruction` (heredado, NO override)

### Native-first dev

- Lint/tests run native WSL (`backend/.venv/bin/{ruff,pytest}` + `cd frontend && npx ...`)
- NUNCA `docker exec ruff/pytest/tsc/vitest`

### Anti-duplication §0

- Cero mirror. Cada shared abstraction reused via subclass o direct import:
  - `BaseObservabilityContext` → subclass `EvalSimulatorObservabilityContext`
  - `BaseAgentCallbackHandler` → subclass `EvalSimulatorCallbackHandler`
  - `FXResolver.default()` reused
  - `PricingResolver` reused
  - `sanitize_payload` reused
  - `BaseTraceEventRepoProtocol` + `BaseLLMCallRepoProtocol` impl

## Output contract para consumers (estable forward — schema versioned per H1)

```python
# backend/tests/agentic_evals/sales_agent/simulator/__init__.py
__all__ = [
    "run_simulation",                # async (tenant_archetype_slug, actor_profile, max_turns=10, trial_n=0) → SimulationResult
    "SimulationResult",              # Pydantic v1, frozen
    "SimulationState",               # Pydantic v1 (LangGraph state)
    "ActorProfile",                  # Pydantic v1, frozen
    "TerminationReason",             # StrEnum 6 values
    "AgentErrorSubtype",             # StrEnum 4 values
    "register_termination_policy",   # (name: str, predicate: TerminationPredicate) → None
]
```

| Story | Consumes |
|---|---|
| C (personas-instrumented-runtime) | `ActorProfile` class + extends YAML loader |
| D (goldens-3-tenants-dataset) | `run_simulation(...)` + reads `_artifacts/{run_id}/simulator/{simulation_id}/transcript.json` |
| E (voice-fidelity-grader-runtime) | `SimulationResult.transcript` for grading |
| F (eval-pass-k-tracking) | `run_simulation(..., trial_n=k)` for pass^k |
| G (voice-fidelity-ci-gate) | `SimulationResult.cost_summary` + `SimulationResult.transcript` for CI threshold check |
| H (eval-cost-budget-cap) | `register_termination_policy("budget_exceeded", budget_predicate)` |
| I (adversarial-jailbreak-suite) | `register_termination_policy("adversarial_detected", adversarial_predicate)` |

## Open architecture risks

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Builder confunde "agent_kind enum extension" del spec H6 con DDL enum (no existe — es registry discriminator) | high | BE arch §2.4 audit cita verbatim; T-1 prompt cita específicamente; arch fitness gate `test_eval_simulator_observability_invariants.py` validates spec registered post-bootstrap import |
| `EVAL_USER_SIMULATOR` añadido a `LLM_ROLE_BY_SITE` SSoT por error (decisión §2.1 ratifica eval-only registry) | medium | Arch fitness gate `test_no_hardcoded_models_sales_agent.py` baseline NOT bumped; OQ-A3 escalada a PM |
| Customer LLM cost > $0.05/run (gpt-5-nano price model post-2026-05) | medium | T-9 contract test verifica suite total `<$0.30`; soft-fail with structlog warning permite story H/G implementar CI gate |
| `ActorProfile` schema cambia entre Story B y C (multi-persona loader) → breaking | medium | H1 schema versioning + frozen golden v1 + regression test enforces forward-compat |
| Concurrency race en `EvalSyntheticTenantModel` upsert si 5 tests parametrize paralelos | low | UUID5 deterministic + upsert idempotent; pytest-asyncio default sequential per file; semaphore cap evita >10 paralelos |
| LangGraph runtime introspection breaks por `from __future__ import annotations` | low | Cement: NO `from __future__ import annotations` en `simulator/_internal/graph.py` (test arch fitness verifica) |
| `client_simulator/` legacy raíz hash drift post-merge | low | D6 preservation gate + arch fitness `find client_simulator/src/simulator/*.py | xargs sha256sum` pre/post commit unchanged |
| Builder skip Step 0 anti-duplication audit | medium | Builder prompt template Step 0 cite verbatim §2.4 audit + escalate match — auditor Cat 12 cement |
| Migration 124 rompe MV `mv_daily_llm_cost_per_tenant_v2` | low | Migration NO toca MV existente — solo agrega tablas. Cross-agent MV extension future migration. Test arch verifica MV unchanged |

## Out of scope (consolidado)

- NO graders/judges (Story E)
- NO multi-persona YAML loader (Story C — Story B Pydantic-only fixtures)
- NO goldens curation (Story D)
- NO CI gate threshold (Story G)
- NO budget cap CI gate enforcement (Story H — interface ready)
- NO adversarial jailbreak suite full (Story I — interface ready)
- NO eliminar `client_simulator/` legacy (D6 preservation)
- NO modificar §3 protected surfaces sales-agent (closer_studio, SmartBuffer, OutputManager.process_response, enrollment_*, webhook adapters, follow_up_engine, PromptVersionModel, model_pricing_snapshot schema, tool_call_dedup)
- NO modificar `LLM_ROLE_BY_SITE` SSoT (decisión §2.1)
- NO FE work
- NO ALTER TYPE ENUM (no existe `agent_kind` enum DB — clarification §2.4 BE arch)

## Tickets preview (orchestrator será 06-tickets.yaml)

| # | Ticket | Owner | Deps | Type |
|---|---|---|---|---|
| T-1 | Migration 124 + 4 SQLAlchemy models + spec registration + bootstrap line | builder-backend (Sonnet OK) | — | BE prod-code R5 |
| T-2 | Migration test (apply/rollback/idempotency) + arch gate `test_eval_simulator_observability_invariants.py` | builder-backend | T-1 | BE test-infra |
| T-3 | Fixture `eval_tenant_seeded` + fixture test | builder-backend | T-1 | BE test-infra |
| T-4 | Pydantic state + actor_profile + result + termination + schema_migrations files | builder-agentic (Opus rec) | — | AGENTIC schemas |
| T-5 | EvalSimulator{ObservabilityContext,CallbackHandler} subclasses + observability.py | builder-agentic | T-1, T-4 | AGENTIC observability |
| T-6 | Customer node + prompt v1 + llm_roles registry + concurrency semaphore | builder-agentic | T-4 | AGENTIC LLM |
| T-7 | Agent_bridge in-process invocation + leak_assertions | builder-agentic | T-4, T-5 | AGENTIC dispatch |
| T-8 | Graph compose + routing fn + run_simulation orchestrator | builder-agentic | T-6, T-7 | AGENTIC graph |
| T-9 | Public API `__init__.py` + 3 hardcoded ActorProfile fixtures + frozen golden v1 + 4 arch gates | builder-agentic | T-4..T-8 | AGENTIC API + arch |
| T-10 | Smoke test parametrized + schema regression test + downstream regression rule update | builder-agentic | T-9 | AGENTIC tests + R3 update |

> Detail in `06-tickets.yaml` (orchestrator will produce). Estimate 2-3d total.

## Architecture fitness impact

- **Allowlists shrink-only**: 5 NEW gates (BE arch §5) start with empty allowlists.
- **Existing gates preserved**:
  - `test_no_new_sales_agent_module_imports.py` — frozen baseline 4 entries; NEW directory `modules/sales_agent/observability/eval_simulator/` is intra-module, NOT cross-module → no ratchet impact.
  - `test_sales_agent_observability_invariants.py` — applies to BOTH `SalesAgentCallbackHandler` AND new `EvalSimulatorCallbackHandler` (subclass shares base contract).
  - `test_no_hardcoded_models_sales_agent.py` — baseline NOT bumped (decisión §2.1 — eval-only registry separate).
- **Capability YAML / modules update post-merge**:
  - `docs/product/capabilities/sales_agent/sales-conversational-engine.yaml` — append `eval.simulator_path: backend/tests/agentic_evals/sales_agent/simulator/`, `eval.dual_llm_pattern: true`, `eval.actor_profile_schema_version: 1`, `eval.simulation_state_schema_version: 1`, `eval.observability_table_eval_simulator_llm_call: true`
  - `docs/product/modules/sales_agent.md` — narrative update mentioning eval_simulator bucket separation (1-2 sentences)

## Test surfaces (TDD-mandatory RED first)

- **BE**: migration test → fixture test → arch fitness gates (RED por capa, see BE arch §4-5)
- **AGENTIC**: smoke test 5-archetype parametrize → negative → edge → adversarial → schema regression → arch fitness gates (RED por scenario, see AGENTIC arch §13)
- **E2E**: N/A (no FE)
- **Coverage**: BE 60%/módulo nuevo + global 43% threshold no bajar; AGENTIC 60% módulo `simulator/`

## Research notes (DATE-AWARE)

> All cited research accessed **2026-05-07** (`date -u +%Y-%m-%d` Step 0 captured).

- LangGraph 0.2+ — `https://docs.langchain.com/oss/python/langgraph/workflows-agents` (canonical, accessed 2026-05-07). Pydantic state OK; runtime introspection breaks with `from __future__ import annotations` cement.
- Anthropic prompt caching — `https://platform.claude.com/docs/en/build-with-claude/prompt-caching` (canonical). Anti-pattern: tenant_name interpolated mid-block in cacheable slots; customer prompt v1 honors.
- AWS Strands Evals — ActorProfile pattern (referenced via spec D7 ratification + Story 00-story.md May 2026 research citation).
- Pydantic v2 — `https://docs.pydantic.dev/latest/` (accessed 2026-05-07). `ConfigDict(extra="forbid")` cement.
- tessl__graceful-degradation — Rule 1 (timeouts), Rule 2 (fallbacks), Rule 5 (per-dependency isolation), Rule 6 (structured context logs) cited.

Knowledge cutoff disclosure: Opus 4.7 cutoff Jan 2026; topic researched live 2026-05-07.

## Próximo paso

`/architect` orchestrator reads this consolidated arch doc + 03-arch-be.md + 03-arch-agentic.md → produces:
- `04-validators.yaml` — ejecutables tests con must_pass:true c/u
- `05-guidelines.md` — patterns required/forbidden + files in scope + skills/rules a cargar
- `06-tickets.yaml` — T-1..T-10 work units atómicos con deps + acceptance + owner_eligibility

State transition: `refined → ready` cuando `04-validators.yaml + 05-guidelines.md + 06-tickets.yaml` cerrados.
