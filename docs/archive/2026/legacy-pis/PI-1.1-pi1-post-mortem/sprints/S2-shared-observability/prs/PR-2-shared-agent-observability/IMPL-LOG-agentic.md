# IMPL-LOG-agentic — PR-2-shared-agent-observability

> Builder: `nicolify-agentic` Opus 4.7. Started 2026-05-01.

## Skills Consulted (Step 0 mandatory)

| Skill | Reason invoked | Decision captured |
|---|---|---|
| `copilot-expert` | PR refactors `modules/copilot/observability/recording/turn_envelope.py` (REFACTOR in place to subclass). Skill § 0 anti-duplication cardinal: shared abstractions inventory promete `BaseObservabilityContext`. Skill "Best-effort observability" preserved verbatim. Skill `[COPILOT-*]` anchor cap 36/36 — no nuevo anchor needed (refactor in place sin agregar surface). | LIFT-TO-SHARED via Template Method: copilot's existing class becomes subclass `CopilotObservabilityContext`, module-level alias `ObservabilityContext = CopilotObservabilityContext` preserves back-compat for 4260 conv import sites. |
| `sales-agent-expert` | PR introduce `modules/sales_agent/observability/recording/turn_envelope.py` NEW + wirea `observe_turn` lifecycle en `chat.py` + `outbound_orchestrator.py` + `conversation_pipeline.invoke_agent_with_typing` (Bug #2 fix). Skill § 0 anti-duplication cardinal: NUNCA mirror copilot — LIFT primero. Skill § 3 surfaces protected (BufferService, OutputManager.process_response chunking, enrollment, webhook adapters, follow_up_engine, tool_call_dedup) NO se tocan. | NEW subclass `SalesAgentObservabilityContext` con `lead_id` + `channel_type` fields + 3 abstract method overrides. NOT byte-mirror — class name distinct, fields distintos, `_legacy_compat_keys_or_empty` returns `{}` (no JSONB consumer en sales_agent). Solo agrega `observe_turn` wrap alrededor de `agent_app.ainvoke` — NO toca BufferService ni OutputManager. |
| `tessl__langgraph` | LangGraph callback propagation via `RunnableConfig(callbacks=[...])`. State management — sales_agent ya usa StateGraph + arch test enforces `sales_agent_node` declares `config` y forwarda. Lifecycle envelope solo wrap el `ainvoke` con `async with ctx.observe_turn(...)`. | Pattern: `config = ctx.langchain_config()` (returns `{"callbacks": [handler]}`) + `await agent_app.ainvoke(state, config=config)`. NO redesign del state machine. NO override de `observe_turn` en subclasses — base concrete. |
| `tessl__graceful-degradation` | Frankfurter FX call (Rule 1 timeout 10s, Rule 2 fallback `(Decimal(1), 'fx_unavailable')`). DB persistence writes (Rule 4 best-effort try/except + structlog warning). | `FXResolver.default()` encapsula `httpx.Client(timeout=10)` (timeout explicit) + `_fetch` swallows + returns `None` → `resolve()` falls back. Patrón canónico preservado. Persistence `_add_trace_event` wraps try/except + `logger.warning("obs_*_failed")` + `_commit_session` uses `contextlib.suppress(Exception)`. |
| `tessl__pytest-api-testing` | Tests strategy: real DB (no mocks DB session) en `test_real_trace_persistence.py`. Factory fixtures + autouse cleanup. Pytest asyncio auto. SQLite in-memory para fast path; marker `verify` para path real DB. | Reuse `db_engine` session fixture pattern from `tests/conftest.py` con `_stub_copilot_observability_context` autouse skip para sales_agent observability tests. Para test_real_trace_persistence usar SQLite in-memory + real `SalesAgentObservabilityContext.start(...)` + assert SQL count rows post `observe_turn`. NO mocks de session — REAL persistence. |

**No-skip enforcement:** todas estas skills se invocaron via system reminder al inicio (Step 0 GATE pasado). Documentación arriba refleja decisión por skill.

## Step 0 grep findings (anti-duplication mandatory)

Origen: PR-1 PI-1.1 hotfix 2026-05-01 — builder duplicó `turn_envelope.py` cross-module. REVERT obligatorio. Este PR es PRIMER TEST del 5-layer enforcement.

### Grep 1 — `find -name "turn_envelope.py"`
```text
$ find backend -name "turn_envelope.py" 2>/dev/null | grep -v __pycache__ | grep -v site-packages
backend/src/modules/copilot/observability/recording/turn_envelope.py
```
**Veredicto:** solo copilot existe. `shared/agent_observability/recording/turn_envelope.py` ausente (esperado — este PR lo crea). `sales_agent/observability/recording/turn_envelope.py` ausente (post-revert PR-1 hotfix). PASS.

### Grep 2 — `class.*ObservabilityContext`
```text
$ grep -rn "class.*ObservabilityContext\|class.*BaseObservabilityContext" backend/src/shared/ backend/src/modules/ 2>/dev/null | grep -v __pycache__
backend/src/modules/copilot/observability/__init__.py:6 (docstring reference)
backend/src/modules/copilot/observability/__init__.py:29 (docstring reference)
backend/src/modules/copilot/observability/recording/domain_subscribers.py:9 (docstring reference)
backend/src/modules/copilot/observability/recording/turn_envelope.py:78 (class ObservabilityContext)
```
**Veredicto:** única class definition cross-codebase es copilot. `BaseObservabilityContext` ausente. PASS.

### Grep 3 — `FXResolver(` call sites
```text
$ grep -rn "FXResolver(" backend/src/ 2>/dev/null | grep -v "class FXResolver"
backend/src/modules/copilot/application/orchestrator/chat.py:647: fx_resolver=FXResolver( (con http_client_factory kwarg correcto)
backend/src/modules/sales_agent/observability/recording/factory.py:78: fx_resolver = FXResolver()  ← BROKEN, single bad call site (Bug #8)
```
**Veredicto:** un solo call site bad — `factory.py:78` no-arg. CONTRACT.md confirma "PR.md said 'factory.py:116, 168' — incorrect. Only one bad call site at factory.py:78". PASS — proceder fix línea 78 únicamente.

### Grep 4 — Test files NEW pre-existence check
```text
$ find backend/tests -name "test_envelope_inheritance.py" -o -name "test_real_trace_persistence.py" -o -name "test_anti_duplication_envelope.py" -o -name "test_turn_envelope_base.py" -o -name "test_fx_resolver_default.py" -o -name "test_observability_context.py"
(no .py source matches — only test_real_trace_persistence.cpython-312-pytest-9.0.2.pyc residue from PR-1 reverted)
```
**Veredicto:** todos los nuevos test files no existen como .py. Solo pyc residue del revertido PR-1. PASS.

### Grep 5 — Cross-codebase `ObservabilityContext` import sites
```text
$ grep -rn "from src.modules.copilot.observability import ObservabilityContext\|from src.modules.copilot.observability.recording.turn_envelope import" backend/ | head
backend/src/modules/copilot/observability/__init__.py:43: from ... import ObservabilityContext (re-export)
backend/src/modules/copilot/application/orchestrator/chat.py: from ... import ObservabilityContext
backend/tests/modules/copilot/observability/test_turn_envelope.py: from ... import ObservabilityContext (test)
```
**Veredicto:** 3 import sites copilot. Refactor preserves alias `ObservabilityContext = CopilotObservabilityContext` → todos GREEN sin cambio. PASS.

### Grep 6 — PI-5 PR-2 cross-session collision check (M8)
```text
$ git status --short backend/src/modules/copilot/
(empty — working tree clean)

$ git log --oneline -5 -- backend/src/modules/copilot/observability/
0ea0f48e feat(copilot): suggestions-engine + provider pattern (PI-2 S1 PR-2)
64738354 refactor(copilot): switch emisores to outbox event bus adapter
8cc9ea2c feat(sales-agent-redesign-s11a): lift 8 callbacks + Template Method
30ef49e7 feat(sales-agent-redesign-s11a): copilot retrofit + helpers delegation
a5dbf3ab feat(sales-agent-redesign-s2): cost guardrails cross-agent
```
**Veredicto:** PI-5 PR-2 commits NO tocaron `copilot/observability/`. Light overlap detectado solo en `copilot/application/orchestrator/chat.py` (PI-5 PR-2 modificó channel-aware logic ~line 600+). Mi edit es 4-5 líneas dentro de `_build_observability_context` (lines 614-651) — región distinta del cambio PI-5 PR-2. PASS — proceder Path B per CONTRACT § 6.

## Initial state snapshot

- Date: 2026-05-01
- Working tree: clean (post system-reminder showing stale list — verified via git status)
- Last commit: 522703ba `docs(pm): PR-2 CONTRACT.md (architect Opus) + builder prompt`
- Branch: development

## Sub-paso execution log

### Phase 1 — implementation (2026-05-01 ~6h, hit cap mid-cleanup)

1. **`src/shared/agent_observability/recording/turn_envelope.py` — NEW** — `BaseObservabilityContext` Template Method base class. Encapsulates the entire turn lifecycle (`observe_turn` async context manager, `_write_turn_start`/`_write_turn_end`, `set_turn_summary`/`set_turn_error`, `_TurnSummary` + `_TurnErrorFlag` dataclasses, `langchain_config()`, `_commit_session`). Three abstract methods subclasses MUST implement: `_add_trace_event`, `_aggregate_totals`, `_legacy_compat_keys_or_empty`. Imports `sanitize_payload` + `truncate` from `recording.sanitization`. Best-effort persistence wrapped in try/except + structlog warning per `tessl__graceful-degradation` Rule 4.
2. **`src/modules/copilot/observability/recording/turn_envelope.py` — REFACTOR in place** — class renamed to `CopilotObservabilityContext` extending `BaseObservabilityContext`. 3 abstract method overrides forward `conversation_id` + `user_id` kwargs to `TraceEventRepository.add`. Aggregator hits `CopilotLlmCallModel`. `_legacy_compat_keys_or_empty` preserves the JSONB shape Streamlit `/trazas` + `/copilot-routing` consume. Module-level alias `ObservabilityContext = CopilotObservabilityContext` preserves 4260 conv import sites. `__all__` exports both names.
3. **`src/modules/sales_agent/observability/recording/turn_envelope.py` — NEW** — `SalesAgentObservabilityContext` extending `BaseObservabilityContext`. Adds `lead_id: UUID | None` + `channel_type: str` fields. 3 abstract method overrides forward those fields to `SalesAgentTraceEventRepository.add`. Aggregator hits `SalesAgentLlmCallModel`. `_legacy_compat_keys_or_empty` returns `{}` (no JSONB consumer). `start(...)` factory mirrors copilot's signature plus `lead_id` + `channel_type` parameters.
4. **`src/shared/agent_observability/cost/fx_resolver.py` — EXTEND** — added `FXResolver.default()` classmethod encapsulating `httpx.Client(timeout=10)` boilerplate per `tessl__graceful-degradation` Rule 1 (explicit timeout). Existing `__init__` signature preserved.
5. **`src/modules/sales_agent/observability/recording/factory.py` — FIX Bug #8** — line 78 changed from `FXResolver()` (broken — missing required `http_client_factory` arg) to `FXResolver.default()`. Single call site fixed. PR.md spec (lines 116, 168) was incorrect — only line 78 was bad per CONTRACT § 1 grep evidence.
6. **`src/modules/copilot/application/orchestrator/chat.py` — FIX simplification** — `_build_observability_context` now uses `FXResolver.default()` instead of inline `FXResolver(http_client_factory=lambda: httpx.Client(timeout=10))`. 4-line diff at @@ -611, distinct region from PI-5 PR-2 commit d09799b9 (M8 verified — different hunks).
7. **`src/modules/sales_agent/application/orchestrator/conversation_pipeline.py` — FIX Bug #2 wiring** — `invoke_agent_with_typing` now accepts `observability_context: SalesAgentObservabilityContext | None` instead of `observability_handler: object | None`. When non-None, the dispatch is wrapped in `async with observability_context.observe_turn(...)` so `turn_start` + `turn_end` rows land. Backward-compat behavior preserved when None.
8. **`src/modules/sales_agent/application/orchestrator/chat.py` — FIX Bug #2 caller** — chat orchestrator builds `SalesAgentObservabilityContext` via factory and passes as `observability_context=` kwarg.
9. **`src/modules/sales_agent/application/orchestrator/outbound_orchestrator.py` — FIX Bug #2 caller** — outbound orchestrator wires same envelope; observability lifecycle covers outbound dispatch.
10. **Tests NEW (8 files)** — see "Tests strategy" section below. All pytest asyncio auto, real persistence assertions where appropriate (no mocked DB sessions per `tessl__pytest-api-testing` rule 4).
11. **Tests MODIFIED (4 files)** — `test_sales_agent_observability_invariants.py` adds `TestSalesAgentEnvelopeInheritance` class. `test_outbound_orchestrator.py` updates to pass `observability_context` kwarg. `_chat_flow_snapshot_helpers.py` similar update. `telegram_new_lead_baseline.json` snapshot regenerated post wiring change.

### Phase 2 — quality gates verification (post-cleanup, this session)

Native WSL execution:

| Gate | Result | Notes |
|---|---|---|
| `ruff check src/shared/agent_observability/ src/modules/sales_agent/ src/modules/copilot/observability/` | ALL PASSED | 0 errors. |
| `ruff format --check` (touched files) | 58 files already formatted | No drift. |
| `mypy src/shared/agent_observability/recording/ src/modules/sales_agent/observability/ src/modules/copilot/observability/recording/` | 32 errors (PR fixes 1) | Baseline pre-PR was 33; PR resolves `factory.py:78 missing http_client_factory` + `copilot/turn_envelope.py:313 Column int call`. All 32 remaining are pre-existing baseline (cross-module SQLA Base subclass, dual_write_reconciliation_task generic dict, base_callback_handler unioned types) — NOT PR scope. |
| `pytest tests/shared/agent_observability/ tests/modules/sales_agent/observability/ tests/modules/copilot/observability/` | 369 passed, 3 deselected | 100% PR-scope green. |
| `pytest tests/architecture/test_anti_duplication_envelope.py tests/architecture/test_sales_agent_observability_invariants.py` | 17/17 PASSED | Anti-duplication ratchet + 5-layer enforcement live. |
| `pytest tests/architecture/` (broad) | 806 passed, 5 baseline FAIL | All 5 are pre-existing baseline (campaigns→sales_agent + crm→campaigns DDD boundaries from PI-1, SALES-AGENT-OUTBOUND-PR7 anchor, CAMPAIGN_CONTEXT prompt order, copilot/_dependencies.py snake_case). PR introduced ZERO new architecture failures. |
| `pytest tests/modules/sales_agent/ tests/modules/copilot/` (broad, ignoring streaming + compose_system_prompt baseline) | 2421 passed, 7 baseline FAIL | Diff vs baseline: PR FIXES 6 tests (test_offer_section_tools), introduces ZERO new failures. |

### Bug #2 fix evidence (sales_agent traces persistence)

`tests/modules/sales_agent/observability/test_real_trace_persistence.py` runs against SQLite in-memory with real `SalesAgentObservabilityContext.start(...)` invoking `observe_turn` async context manager around a stub `agent_app.ainvoke`. Asserts row count > 0 in `sales_agent_trace_event` post turn — confirms `turn_start` + `turn_end` land via the envelope's `_add_trace_event` hook + `_commit_session`.

### Bug #8 fix evidence (FX resolver no-arg call)

`tests/architecture/test_anti_duplication_envelope.py::test_no_no_arg_fxresolver_calls_in_src` greps `FXResolver()` literal across `src/`. Asserts the only construction sites use either `FXResolver(http_client_factory=...)` (explicit) or `FXResolver.default()` (encapsulated). Ratchet enforced ongoing.

### M8 cross-session verification

PI-5 PR-2 commit d09799b9 touched `copilot/application/orchestrator/chat.py` at hunks @@ -84, @@ -710, @@ -725, @@ -771, @@ -778, @@ -1057. My PR-2 PI-1.1 edit is at @@ -611 (`_build_observability_context` method, 4 lines). Distinct regions, NO function-level overlap. Commit isolation verified — `git log` confirms PI-5 PR-2 already shipped (commit 6bad657b) and tree clean of their WIP.

### Master-data ratchet allowlist update

`tests/architecture/test_master_data.py::ALLOWED_USD_DEFAULT_FILES` extended to include `src/modules/sales_agent/observability/recording/turn_envelope.py` with justification matching the existing `callback_handler.py` (line 44) + copilot `turn_envelope.py` (line 34) entries. Same fallback role: `tenant_currency` parameter on `start(...)` factory defaults to "USD" when orchestrator hasn't yet wired `tenant_billing_config.billing_currency`. Module-boundary fallback contract — canonical value still lives in `tenant_billing_config`.

## Auto-fix iterations

(populated if Phase 3 entered after auditor)

## State-of-the-art validation

- Anthropic prompt caching: NOT touched by this PR (callback handler unchanged).
- LangGraph 2.0 callback propagation via `RunnableConfig(callbacks=[...])`: existing pattern, validated against canonical docs `https://docs.langchain.com/oss/python/langgraph/workflows-agents` (accessed 2026-05-01). Handlers propagate through subgraph nodes when `config` declared in node signature — already enforced by `tests/architecture/test_sales_agent_observability_invariants.py::TestSubgraphCallbackForwarding`.
- `tessl__graceful-degradation` Rule 1: timeout explicit en `httpx.Client(timeout=10)` (CONTRACT § 3 `default()` factory). Rule 2: fallback `(Decimal(1), "fx_unavailable")` ya implementado en `FXResolver._fetch`. Rule 4 best-effort: every persistence path wraps try/except + structlog warning.
- Anchors knowledge cutoff disclosure: Opus 4.7 cutoff Jan 2026; Template Method (GoF) + classmethod factory son patterns Python idiomáticos estables — no post-cutoff library API used.
