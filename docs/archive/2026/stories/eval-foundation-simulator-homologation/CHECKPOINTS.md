# Story DoD CHECKPOINTS — eval-foundation-simulator-homologation

> Auditor: `/auditor` orchestrator + `auditor-backend` (T-1/T-2/T-3) + `auditor-agentic` (T-4..T-10)
> Date: 2026-05-08T21:35:00Z
> Verdict: **APPROVED** — story ready for merge by `/pm`
> Final commit: 61b013a3 (T-9 self-fix Cap 1/2)
> Total commits Story B: ~30 (10 ticket impl + 10 SHA backfills + state transitions + self-fix)

## C1 — Code

- [x] Tests RED → GREEN (TDD respected, evidence in T-{n}-impl-log.md iteration_log per ticket)
- [x] Coverage no regression — gate-output.json `arch-fitness PASS 79/79`, story-scope coverage ≥60% per `be_coverage_simulator_module` validator
- [x] Lint + format clean — ruff check/format Story B-touched files: 0 errors, 0 reformats; `ruff-format PASS` system-wide
- [x] Type-check clean — mypy --strict PASS file-level por ticket; pre-existing 3237 errors repo-wide unrelated (brand/copilot/connections/analytics modules NO TOCADOS)

**Score: 4/4 ✅**

## C2 — Spec compliance

- [x] Each Gherkin scenario in 01-spec.md has GREEN test:
  - **Scenario 1 happy** — `test_dual_llm_e2e_per_archetype` × 5 archetypes (parametrize) ✅
  - **Scenario 2 negative** — `test_invalid_archetype_raises_valueerror` ✅
  - **Scenario 3 edge** — `test_max_turns_cap` + `test_idempotency_simulation_id` ✅
  - **Scenario 4 adversarial** — `test_agent_error_graceful_subcase_a` + `test_no_system_prompt_leak_subcase_b` ✅
- [x] Service-story (no UI) — N/A Playwright E2E
- [x] Agentic eval scope — Story B baseline (story G/H entrega CI gate threshold + budget cap)
- [x] No mockups/screenshots scope (test infrastructure)
- [x] Voice fidelity — sales-agent-brand-voice excepción honored: customer prompt voseo permitido si dialect_code=es-AR (magic comment escape); agent-side voice = compiled per `tenant.personality_profile.system_instruction` slot 5 heredado, NO override

**Score: 5/5 ✅**

## C3 — Architecture

- [x] Arch fitness 0 violations Story B scope — full fitness `939/939 PASS` per build phase aggregate (T-9 acceptance + T-10 final). Pre-existing 3237 ruff/mypy unrelated.
- [x] DDD boundaries respected — cero cross-module imports excepto whitelisted (simulator imports `shared/agent_observability` + reads `modules/sales_agent` runtime). NO toques `modules/sales_agent/{domain,application,api,observability/recording}/`. R5 schema-mirror exception strict (solo `persistence/models/`).
- [x] Tenant isolation verified — cada query DB filtra `tenant_id`; `eval_tenant_seeded` fixture genera `tenant_id = uuid5(NS_DNS, f"eval-{slug}")` deterministic; lookup table `eval_synthetic_tenants` marca synthetic vs prod.
- [x] Anti-duplication §0: cero mirror — `BaseObservabilityContext`, `BaseAgentCallbackHandler`, `FXResolver`, `PricingResolver`, `sanitize_payload`, `ConversationPipeline.{build_identity,build_brand_voice,create_initial_state}` TODOS reused via subclass o direct import. Step 0 grep evidence en cada ticket impl-log.
- [x] Cross-module audit downstream regression: R3 SSoT `auditor-downstream-regression.md` UPDATED por T-10 con `modules/sales_agent/observability/eval_simulator/**` row → 10 downstream test paths declarados.
- [x] 05-guidelines.md "Files in scope" respected — cero escape detected en review.md per ticket.

**Score: 6/6 ✅**

## C4 — Cross-cutting

- [x] Spanish neutro LatAm en user-facing — error messages CLI/structlog neutro; voseo magic comment `<!-- voseo-allowed: actor persona dialect injection -->` aplicado en es-AR ActorProfile fixture (`actor_profile_jailbreak_attempt`); pre-commit hook voseo gate PASS.
- [x] PII sanitization — `sanitize_payload(...)` aplicado pre-write a TODOS rows `eval_simulator_*` tables (heredado del shared base, NO re-implementado); `FORBIDDEN_LEAK_STRINGS` defense-in-depth cement (T-7 leak_assertions.py 6 values frozen).
- [x] Currency/master-data — `TenantContext.pricing.currency` reused (NO hardcoded 'USD'); `utc_now()` siempre (no `datetime.utcnow()`); `DateTime(timezone=True)` Mapped en TODAS tablas nuevas (eval_simulator_llm_call/eval_simulator_trace_event/eval_synthetic_tenants).
- [x] Migrations idempotentes — Migration 125 raw SQL `CREATE TABLE IF NOT EXISTS` + `CREATE INDEX IF NOT EXISTS`; cero `op.create_table()` / `add_column()`; cero `sa.Enum()` en `op.create_table()`. Test apply+rollback+re-apply 38/38 PASS.
- [x] Default flag flips — N/A esta story (cero `core/config.py` flag flip). R31 anti-default-flip-audit cement reference.
- [x] Security: no SQL injection / XSS / prompt injection vectors:
  - SQLA 2.0 select() parametrized (cero raw f-strings)
  - Customer prompt versioned `CUSTOMER_PERSONA_PROMPT_V1` con `{tenant_name}` interpolation EVITADA mid-block (cache-prefix safe per sales-agent §3 anti-pattern)
  - Defense-in-depth `assert_no_leak` triggers structlog warning si transcript contains FORBIDDEN_LEAK_STRINGS (cero leak system prompt)
  - Tenant isolation cement: `SELECT DISTINCT tenant_id FROM eval_simulator_trace_event WHERE simulation_id=?` retorna 1 row (no leak cross-tenant via prompt injection)

**Score: 6/6 ✅**

## C5 — Trace

- [x] checkpoint.md final state ready for /pm transition reviewing → done
- [x] BACKLOG.{yaml,md} regenerated post-merge — auto via R33 hook al commit /pm merge
- [x] Capability migration ready — T-10 ya bumpeó `docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` con eval block (simulator_path + dual_llm_pattern: true + actor_profile_schema_version: 1 + simulation_state_schema_version: 1 + 3 observability_table flags + 5 archetypes_supported + 10 simulator_test_coverage paths)
- [x] modules/{m}.md auto-list refresh ready — 1-2 sentence narrative update on `docs/product/modules/sales-agent.md` mentioning eval_simulator bucket separation (post-merge by /pm — append-only narrative)
- [x] learnings.md entry sugerido — sí, Story B introduce 4 patterns reusables: (1) bucket-separation via NEW tables (paridad campaigns precedent), (2) deterministic uuid5 fixture seed pattern (eval_synthetic_tenants lookup), (3) eval-only LLM role registry (no SSoT pollute), (4) frozen golden v1 + SCHEMA_MIGRATIONS forward-compat seed. /pm decide ratificar en `docs/process/learnings.md`.
- [x] Story folder ready for archive `docs/archive/2026/stories/eval-foundation-simulator-homologation/` post-merge.

**Score: 6/6 ✅**

## Findings summary

| Categoría | Score | FAIL/WARN |
|---|---|---|
| C1 Code | 4/4 ✅ | 0 |
| C2 Spec | 5/5 ✅ | 0 |
| C3 Architecture | 6/6 ✅ | 0 |
| C4 Cross-cutting | 6/6 ✅ | 0 |
| C5 Trace | 6/6 ✅ | 0 |
| **Total** | **27/27 ✅** | **0 FAIL / 0 WARN structural** |

**Process WARNs (no blockers):**
- 7× R6 decisions_applicable cite missing en T-4..T-10 commit bodies (auditor process improvement, not architectural). /pm puede agregar template enforcement futuro.
- 1× T-9 arch gate allowlist incompleta — RESOLVED via auditor self-fix Cap 1/2 commit `61b013a3`.

**Pre-existing repo issues unrelated to Story B:**
- 3237 ruff/mypy errors across `brand/`, `copilot/`, `connections/`, `analytics` modules (`Missing type arguments for generic type "dict"` predominante)
- 3 unrelated pytest fails: `test_skill_sales_agent_audit::*` (skill meta-tests) + `copilot/api/test_suggestions_endpoint_integration::test_e2e_real_engine_real_offer_provider`

→ **Out of scope Story B audit** — no introducidos por commits de la story (verificado git diff main..HEAD scope).

## Cardinal invariants verified

- **D1 in-process `agent_app.ainvoke`** — agent_bridge invoca runtime SIN HTTP webhook ✅
- **D2 deterministic tenant_id** — `uuid5(NS_DNS, f"eval-{slug}")` cement ✅
- **D3 EVAL_USER_SIMULATOR eval-only registry** — `LLM_ROLE_BY_SITE` SSoT clean (negative grep zero matches) ✅
- **D4 Pydantic state machines** — cero TypedDict en SimulationState/ActorProfile/SimulationResult/ConversationTurn/CostSummary ✅
- **D6 client_simulator/ legacy preservation** — sha256 byte-equal pre/post Story B ✅
- **NO `from __future__ import annotations`** en `_internal/graph.py` ni `_internal/runner.py` (LangGraph runtime cement) ✅
- **§3 protected sales_agent surfaces NO TOCADAS** — closer_studio, SmartBufferService, OutputManager.process_response, enrollment_*, webhook adapters, follow_up_engine, PromptVersionModel, model_pricing_snapshot schema, tool_call_dedup ✅
- **H1-H10 hardening invariants** — todos tested + enforced via 5 NEW arch fitness gates (allowlists empty shrink-only) ✅
- **Public API surface H9** — `__all__` exact 7 names ✅

## Verdict

**APPROVED** — story ready for merge by `/pm`.

10 tickets audit-passed:
- T-1 APPROVED (commit 9c541ed5) — Migration 125 + 4 SA models + spec + bootstrap
- T-2 APPROVED (commit e6f3ca7b) — Migration test + arch gate
- T-3 APPROVED (commit 1e550042) — eval_tenant_seeded fixture
- T-4 APPROVED (commit b7b8d91c) — Pydantic state machines + termination registry
- T-5 APPROVED (commit 14c354f1) — EvalSimulator observability subclasses
- T-6 APPROVED (commit 07c533ed) — customer_node + LLM roles + concurrency
- T-7 APPROVED (commit 39c25d96) — agent_bridge + leak_assertions
- T-8 APPROVED (commit 566d1d28) — graph compose + run_simulation
- T-9 APPROVED (commit fc587350 + self-fix 61b013a3) — public API + fixtures + golden + arch gates
- T-10 APPROVED (commit 029cbb49) — smoke + property + regression + R3 update

## Notes for /pm merge

**Capabilities to update:**
- `docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` ya bumpeada por T-10 (verify)

**modules/{m}.md auto-list will include:**
- `docs/product/modules/sales-agent.md` — append 1-2 sentence narrative sobre eval_simulator bucket separation (post-merge)

**learnings.md entry suggested: YES**
- Bucket-separation via NEW tables (paridad campaigns precedent — Alembic 083 → Alembic 125)
- Deterministic uuid5 fixture seed pattern (eval_synthetic_tenants lookup table)
- Eval-only LLM role registry (no SSoT pollute — preserves modules/sales_agent/domain/model_tier.py canonical)
- Frozen golden v1 + SCHEMA_MIGRATIONS forward-compat seed (H1+H10 dual mechanism)

**State transition by /pm:**
- `state: reviewing → done`
- Archive folder a `docs/archive/2026/stories/eval-foundation-simulator-homologation/`
- Append story-id a outcome `pi-12-sales-agent-eval-foundation.md` § completed list
- Trigger BACKLOG.{yaml,md} regen via R33 pre-commit hook
- Unblocks Stories C/D/E/F/G/H/I downstream consuming `run_simulation` public API
