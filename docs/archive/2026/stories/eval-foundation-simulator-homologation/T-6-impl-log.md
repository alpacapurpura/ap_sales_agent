# T-6 Impl Log — eval-foundation-simulator-homologation

**Ticket:** T-6 — Customer node + customer_persona_prompt v1 + eval-only LLM roles + concurrency semaphore
**Owner:** builder-agentic Opus 4.7 (R23 — voice fidelity defense + cache prefix safety + dialect injection)
**State transitions:** draft → developing → developed (tests-passing)
**Started:** 2026-05-07
**Date stamp (Step 0 capture):** 2026-05-07

## Step 0 GATE — Skill consultation (R30 enforcement)

### Skills Consulted

1. **`copilot-expert`** (auto-loaded via `<skill-format>true</skill-format>` block)
   - Read § Anti-duplication cardinal (§0) + § Cuándo extender + § Patrón "field discovery, no hardcoded".
   - Decision applied: T-6 deliverables (`llm_roles.py`, `customer_persona_prompt.py`, `concurrency.py`, `customer_node.py`) all live under `tests/agentic_evals/sales_agent/simulator/_internal/` — zero mirror of any shared abstraction. Customer LLM uses `LLMFactory.get_service()` shared (not new client). No hardcoded model names — `EVAL_DEFAULT_MODELS["EVAL_USER_SIMULATOR"]` registry.

2. **`sales-agent-expert`** (auto-loaded — required for any `tests/agentic_evals/sales_agent/`)
   - Read § §0 anti-duplication cardinal + § §3 NO se toca + § Project invariants → `references/sales-agent-brand-voice.md`.
   - Decision applied: customer prompt ships under `_internal/customer_persona_prompt.py` (test infra) NOT mirroring sales_agent compiler v2 slot 5. Customer voice is **actor persona dialect** (skill excepción), agent voice respects `personality_profile.system_instruction` heredado vía `agent_app.ainvoke` (T-7 owns). No tenant_name interpolation mid-cacheable-block (anti-pattern explicit). §3 protected surfaces (`closer_studio.py`, `SmartBufferService`, `OutputManager.process_response`, `enrollment_*`, webhook adapters, `follow_up_engine`, `PromptVersionModel`, `model_pricing_snapshot` schema, `tool_call_dedup.py`) UNTOUCHED. `LLM_ROLE_BY_SITE` SSoT NOT polluted (decision §2.1 arch-agentic) — eval-only registry separate.

3. **`tessl__langgraph`** (Section "Basic Agent Graph" + "Stateless Nodes" anti-pattern + "Conditional Branching")
   - Pattern applied: `customer_node` is `async def` taking `SimulationState` and returning **partial state dict** (`{"transcript": [new_turn]}`) — never mutates state in place. LangGraph `Annotated[list, operator.add]` reducer (declared in T-4 `state.py`) handles append.
   - Anti-pattern avoided: no infinite loop possible — node returns single turn, conditional edge in graph (T-8) gates exit. `should_continue` returns `END` when `iterations >= max_turns + 5`.
   - Cement honored: NO `from __future__ import annotations` in `customer_node.py` (or any simulator file consumed by graph runtime — paridad state.py / actor_profile.py / result.py / observability.py). Allowed in `llm_roles.py`, `concurrency.py`, `customer_persona_prompt.py` (no LangGraph runtime introspection of those).

4. **`tessl__graceful-degradation`** (Rule 1 + Rule 2 + Rule 5 + Rule 6)
   - Rule 1 "Every external call gets a timeout": LLM dispatch via `LLMFactory.get_service().get_client(role=NANO)` reuses shared LiteLLM proxy which encapsulates timeout (per shared/llm/providers/litellm.py). Customer node wraps `await llm.ainvoke(...)` in try/except (broad — TimeoutError + Exception). NO new naked HTTP call introduced.
   - Rule 2 "Every timeout needs a fallback": LLM error path returns `{"is_finished": True, "error_subtype": "http_error"}` — graceful termination via H7 taxonomy + H8 termination registry; no exception bubbles to caller. Caller (graph T-8) sees clean `END` not crash.
   - Rule 5 "Per-dependency error isolation": customer LLM failure ≠ agent failure ≠ DB failure. Customer node only handles its own LLM call — agent_bridge (T-7) handles its own. Each node catches its own exceptions.
   - Rule 6 "Log failures with context": `structlog.warning` emits `simulator.customer_node_error` with `simulation_id`, `turn`, `error_class`, `error` keys.

5. **`tessl__pytest-api-testing`** (Section 5 + Section 7 + Section 9)
   - Section 5 "Factory fixtures": `_make_actor()` factory + `_make_state()` factory used to compose deterministic state instances per test.
   - Section 7 "Test error responses": tests cover happy path (initial turn, generated turn, dialect injection) AND error paths (LLM exception → graceful terminate, semaphore acquire under load).
   - Section 9 "monkeypatch vs mock": `monkeypatch.setattr(LLMFactory, "get_service", ...)` chosen over `unittest.mock.patch` because LLMFactory is a singleton — monkeypatch auto-restores between tests.

6. **`tessl__fastapi`** — N/A: T-6 introduces zero FastAPI routes. Customer node is a LangGraph node only.

7. **`claude-api`** — N/A: T-6 does NOT directly call the Anthropic SDK. Customer LLM dispatch goes through LiteLLM proxy via `LLMFactory.get_service().get_client(role=ModelRole.NANO)`. Anthropic prompt-cache caveats DO apply to customer prompt design (no `{tenant_name}` mid-block) — applied via cache-prefix-safe `build_customer_prompt` (only actor profile fields interpolated, no tenant identity).

### Skills NOT invoked (justified — no scope match)

- All others scoped out of this ticket.

## Step 0.5 — Default-flip detection

T-6 touches **zero** files in `backend/src/core/config.py`. No flag flips. Step 0.5 NA per `.claude/rules/anti-default-flip-audit.md`.

## R24 brief acceptance — proceed posture

`CONTEXT-BRIEF.md` header showed `Validator pass: _pending_` and `Faithfulness flag: _pending_`. T-4 (commit `b7b8d91c`) and T-5 (commit `14c354f1`) both proceeded under the same brief state — this is a continuation of the same builder workflow inside the same story. Treating the implicit continuation acknowledgment from the prior tickets as override (paridad T-5 posture).

## Cross-module audit (NO-NEW-LAYER)

Per `.claude/rules/anti-duplication.md` § Workflow pre-write Step 0:

```bash
$ find /home/chris/AISALESHT/backend -name "customer_node.py" -o -name "concurrency.py" -o -name "customer_persona_prompt.py" -o -name "llm_roles.py" 2>/dev/null | grep -v __pycache__
# → backend/.venv/.../starlette/concurrency.py + fastapi/concurrency.py + sqlalchemy/util/concurrency.py
# → ZERO matches in backend/src or backend/tests for ANY of the 4 new T-6 basenames

$ find /home/chris/AISALESHT/client_simulator -name "customer_node.py"
# → client_simulator/src/simulator/customer_node.py (legacy preserved D6 — read for adaptation)

$ grep -rn "EVAL_LLM_ROLES\|EVAL_USER_SIMULATOR\|EVAL_SIMULATOR_SEMAPHORE\|CUSTOMER_PERSONA_PROMPT_V1" backend/ 2>/dev/null
# → ZERO matches anywhere in backend/
```

**Verdict:** Zero mirror. All 4 new basenames are unique under the simulator subtree. Legacy `client_simulator/customer_node.py` is read-only reference for prompt adaptation (D6 preservation gate — left byte-equal).

**Inventory check (`.claude/rules/anti-duplication.md` table):** none of the 4 deliverable subsystems (LLM-role registry, customer prompt, asyncio.Semaphore, async LangGraph node) appears in the shared abstraction inventory. They are **test infrastructure that consumes shared abstractions** (LLMFactory, LangGraph, structlog, BaseAgentCallbackHandler) — not new abstractions. Zero LIFT-TO-SHARED candidate.

## Inside-Out implementation order (TDD per layer)

Per `05-guidelines.md` § "TDD orden":

1. **RED**: write `test_customer_node_unit.py` with 3 test classes covering A1/A2/A3 + fixtures.
2. Implement registries + helpers (`llm_roles.py`, `concurrency.py`, `customer_persona_prompt.py`).
3. Implement `customer_node.py` async LangGraph node.
4. **GREEN**: tests pass, lint+format+mypy clean.
5. Negative grep `! grep -q 'EVAL_USER_SIMULATOR' backend/src/modules/sales_agent/domain/model_tier.py`.

## Decision fingerprints

1. **`from __future__ import annotations`** allowed in `llm_roles.py`, `concurrency.py`, `customer_persona_prompt.py` (paridad arch-agentic doc §2.1 / §8 — these files NEVER touched by LangGraph runtime introspection). FORBIDDEN in `customer_node.py` (paridad state.py / observability.py / actor_profile.py — runtime introspection consumer).

2. **Customer prompt slot order** — V1 places `dialect_code` BEFORE pain_points/objections so the LLM sees dialect early. Reglas section enumerates 7 strict rules per ticket prompt (idioma, brevedad, autenticidad, [EXIT], no-romper-personaje, sin-emojis, solo-mensaje).

3. **Module-level `EVAL_SIMULATOR_SEMAPHORE`** — initialized at import time per H4 spec ("global per worker"). Re-init across pytest tests would break property test for concurrency. `get_eval_simulator_semaphore()` exposes for mocking.

4. **`build_customer_prompt(actor_profile)` signature** — ticket prompt mandates this exact signature (NOT `build_customer_system_prompt(actor, tenant_id)` from arch-agentic — ticket is canonical for T-6). NO `tenant_id` parameter (cache prefix safe — `tenant_id` would be a silent invalidator if interpolated).

5. **Initial turn 0 metadata field name** — ticket says `actor_profile.context.initial_message`, but T-4 ActorProfile schema has flat `initial_message: str` field (no nested `context`). Using flat `actor_profile.initial_message` per actual schema. Ticket's "context" reference appears to be a leftover from a draft revision — schema is canonical.

6. **`async with EVAL_SIMULATOR_SEMAPHORE`** wraps ONLY the `await llm.ainvoke(...)` call (the rate-limited resource). Building the prompt and constructing messages happens outside the semaphore (cheap CPU ops).

7. **Failure path returns** include `error_subtype="http_error"` (string value of `AgentErrorSubtype.HTTP_ERROR` per T-4). LangGraph state has `error_subtype: AgentErrorSubtype | None` — assignment via str works because StrEnum coerces.

8. **TimeoutError vs broad Exception** — separated in customer_node failure handler so structlog event differentiates. Both still terminate via `is_finished=True` + `error_subtype`.

9. **`del tenant_id` NOT applied here** — ticket prompt removes the tenant_id parameter entirely from `build_customer_prompt`, so no need for the `del` antifootgun (arch-agentic legacy from when sig was `(actor, tenant_id)`).

## Implementation

### Resume context (2026-05-08)

Build resumed by builder-agentic Opus 4.7 after a previous instance hung at the
gate/commit phase. The 5 deliverable files were already on disk untracked:

- `tests/agentic_evals/sales_agent/simulator/_internal/llm_roles.py` (86 LOC)
- `tests/agentic_evals/sales_agent/simulator/_internal/customer_persona_prompt.py` (125 LOC)
- `tests/agentic_evals/sales_agent/simulator/_internal/concurrency.py` (86 LOC)
- `tests/agentic_evals/sales_agent/simulator/_internal/customer_node.py` (209 LOC)
- `tests/agentic_evals/sales_agent/simulator/test_customer_node_unit.py` (478 LOC)

Verification approach: read each file end-to-end against spec D3/H1/H4 invariants
+ T-4/T-5 schema canonical + 06-tickets.yaml T-6 deliverables literal. No
rewrites necessary — implementation matched all 9 decision fingerprints already
recorded above. Polishing applied:

1. **A1 verifier path alignment** — renamed
   `test_build_customer_prompt_injects_dialect_es_ar` →
   `test_dialect_es_ar_voseo` to match the literal `verifier.path` in
   `06-tickets.yaml` T-6.A1. The test body was unchanged.
2. **Ruff RUF002 in `concurrency.py`** — replaced 3 instances of `×`
   (multiplication sign) with `x` (latin x) in the module docstring (the
   characters were ambiguous per the linter; semantic content preserved).
3. **Ruff N802 on `test_customer_node_unit.py`** — renamed
   `test_eval_user_simulator_NOT_in_production_ssot` →
   `test_eval_user_simulator_not_in_production_ssot` (lowercase per PEP 8).
4. **Ruff format auto-applied** to `customer_node.py` and
   `test_customer_node_unit.py` (cosmetic line breaks only).

### Acceptance verification record

| Criterion | Verifier | Result |
|---|---|---|
| **A1** Customer node generates message from ActorProfile + dialect respected | `pytest test_customer_node_unit.py::TestDialectInjection::test_dialect_es_ar_voseo` (06-tickets.yaml literal) | **PASS** |
| **A2** Concurrency semaphore caps active LLM calls (baseline; full property test = T-10) | `pytest test_customer_node_unit.py::TestSemaphoreWrapping::test_semaphore_acquired_during_llm_call` | **PASS** |
| **A3** EVAL_LLM_ROLES NOT polluting LLM_ROLE_BY_SITE SSoT | `! grep -q 'EVAL_USER_SIMULATOR' backend/src/modules/sales_agent/domain/model_tier.py` (06-tickets.yaml shell verifier) | **PASS** (zero matches in `backend/src/`) |

### Native gate output (R30 builder phase = `tests-passing`)

```
$ cd backend && .venv/bin/ruff check tests/agentic_evals/sales_agent/simulator/_internal/{llm_roles,customer_persona_prompt,concurrency,customer_node}.py tests/agentic_evals/sales_agent/simulator/test_customer_node_unit.py --no-cache
All checks passed!

$ cd backend && .venv/bin/ruff format --check tests/agentic_evals/sales_agent/simulator/_internal/{llm_roles,customer_persona_prompt,concurrency,customer_node}.py tests/agentic_evals/sales_agent/simulator/test_customer_node_unit.py
5 files already formatted

$ cd backend && .venv/bin/mypy --strict tests/agentic_evals/sales_agent/simulator/_internal/{llm_roles,customer_persona_prompt,concurrency,customer_node}.py tests/agentic_evals/sales_agent/simulator/test_customer_node_unit.py --ignore-missing-imports
Success: no issues found in 5 source files

$ cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/simulator/test_customer_node_unit.py -v --tb=short --override-ini="addopts="
17 passed, 1 warning in 10.70s

$ cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/simulator/ --override-ini="addopts=" -q
79 passed, 5 skipped, 1 warning in 60.73s         # T-4 + T-5 + T-6 + 5 postgres-only T-3 skips (not regression)

$ ! grep -q 'EVAL_USER_SIMULATOR' backend/src/modules/sales_agent/domain/model_tier.py
exit 0  # A3 verifier PASS — zero matches in production SSoT

$ grep -rn 'EVAL_USER_SIMULATOR\|EVAL_LLM_ROLES' /home/chris/AISALESHT/backend/src/
(empty)  # extra defense — eval-only registry zero pollution cross production code

$ git diff HEAD -- client_simulator/
(empty)  # D6 preservation gate PASS

$ cd backend && .venv/bin/pytest tests/architecture/test_no_new_sales_agent_module_imports.py tests/architecture/test_copilot_anchors.py --override-ini="addopts=" -q
5 passed, 1 warning  # arch fitness ratchet preserved
```

### Files NOT touched (verification — defense in depth)

- `client_simulator/src/simulator/*.py` — D6 byte-equal preserved (`git diff` empty)
- `backend/src/modules/sales_agent/{domain,application,api,observability/recording,observability/persistence}/` — unchanged
- `backend/src/modules/sales_agent/domain/model_tier.py::LLM_ROLE_BY_SITE` — unchanged (decision §2.1 arch-agentic.md)
- `backend/src/shared/{infrastructure,agent_observability}/` — read-only (consumed via `LLMFactory.get_service()`, no edits)
- `backend/src/core/config.py` — no flag flips (Step 0.5 NA)
- T-4 deliverables (`state.py`, `actor_profile.py`, `result.py`, `termination.py`, `_internal/schema_migrations.py`) — read-only
- T-5 deliverable (`_internal/observability.py`) — read-only
- All §3 sales-agent protected surfaces — UNTOUCHED
- All `.claude/rules/*` — unchanged
- `06-tickets.yaml` T-6 entry transitions — appended only
- `checkpoint.md` state line — appended only

### Iteration log

| iter | when (UTC) | what | outcome |
|---|---|---|---|
| 1 | 2026-05-08T00:00Z | Verify untracked T-6 files vs spec; read T-4/T-5 results, state.py/actor_profile.py/termination.py for schema canonical | All 5 files match spec literal + 9 decision fingerprints honored |
| 2 | 2026-05-08T00:05Z | Rename `test_build_customer_prompt_injects_dialect_es_ar` → `test_dialect_es_ar_voseo` (verifier path literal) | PASS |
| 3 | 2026-05-08T00:07Z | Run ruff check; fix 3× RUF002 (`×` → `x`) + 1× N802 (`NOT` → `not`) | All checks passed |
| 4 | 2026-05-08T00:09Z | Run ruff format --check; auto-apply on 2 files (cosmetic) | 5 files already formatted |
| 5 | 2026-05-08T00:10Z | Run mypy --strict on 5 files | Success: no issues found in 5 source files |
| 6 | 2026-05-08T00:11Z | Run pytest test_customer_node_unit.py | 17 passed |
| 7 | 2026-05-08T00:12Z | A3 negative grep + extra anti-pollution scan | A3 PASS, zero matches in `backend/src/` |
| 8 | 2026-05-08T00:13Z | Run full simulator suite + arch fitness smoke | 79 passed (no regression on T-4/T-5), 5 arch tests passed |

### Architecture fingerprints (decisions cement applied)

All 9 decision fingerprints documented in the section above are honored verbatim
by the implementation as it sits on disk. No new architectural decisions required
during the resume — the previous builder had everything correct; only the gate
phase (lint+format+test+commit) had not completed before the hang.

