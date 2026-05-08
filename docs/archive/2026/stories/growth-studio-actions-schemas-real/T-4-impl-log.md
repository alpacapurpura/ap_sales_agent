<!-- voseo-allowed: this impl-log cites the voseo glossary verbatim to document the test-time blocklist (per .claude/rules/spanish-text.md R25 magic comment escape for technical references). -->
# T-4 Impl Log — growth-studio-actions-schemas-real

**Ticket:** T-4 — AGENTIC: 3 voice fidelity eval goldens (Spanish neutro + tool dispatch correctness + no retry loop)
**Owner:** claude-opus (builder-agentic) — R23 Opus required
**Assigned at:** 2026-05-09T06:00:00Z
**Surface:** AGENTIC eval goldens
**production_code:** true (R23 — AGENTIC eval goldens validate runtime behavior)
**Depends on:** T-3 (DONE — `12962e0d`)

## Plan

3 voice fidelity eval goldens:
- Spanish neutro user-facing output (voseo glossary compliance)
- Tool dispatch correctness (correct tool selected per intent)
- No retry loop (idempotency + bounded attempts)

R23 Opus required: AGENTIC `production_code: true`.

## Skills Consulted

- **copilot-expert** — confirmed CopilotJudge multi-dim rubric pattern (F9), `judge_llm` fixture default stub + RUN_LLM_JUDGE=1 opt-in, no new golden infrastructure needed (extend existing `tests/quality/golden/`)
- **sales-agent-expert** — confirmed voice grader pattern (S10) reusable: stub default 4.0/dim, threshold 3.5, brand_voice_diff differentiation goldens as model. Spanish neutro tuteo applies to copilot UI; sales_agent voseo respect is module-specific exception
- **tessl__langgraph** — N/A this ticket: no new graph nodes / state / edges, goldens consume existing `ANALYTICS_TOOLS` registry
- **tessl__graceful-degradation** — N/A this ticket: deterministic JSON file load + CopilotJudge stub; no external calls in default mode
- **tessl__pytest-api-testing** — confirmed parametrize over loaded goldens, deterministic invariants run on every CI, opt-in real LLM via env flag

## Cross-module audit (NO-NEW-LAYER)

```bash
grep -rn "test_growth_studio_voice\|growth_studio_actions" backend/tests/ 2>/dev/null
# Result: 0 matches before this commit — no duplicate goldens dir

grep -rn "_VOSEO_REGEX\|voseo_forbidden" backend/tests/ 2>/dev/null
# Result: golden runner is novel (regex applied at test time vs pre-commit hook applied at commit time)

ls backend/tests/quality/golden/
# Result: existing __init__.py, conversations.py, test_golden_conversations_semantic.py,
#         test_rag_retrieval.py, test_voice_fidelity_outbound.py
# → New files: growth_studio_actions/{__init__.py, *.json} + test_growth_studio_voice.py
#   coexist with existing — no overlap, no mirror.
```

EXTEND > REPLACE > NEW priority honored: extended existing `tests/quality/golden/` with new
sub-directory + test runner (matches conversations.py pattern). Reuses CopilotJudge + judge_llm
fixture + DEFAULT_THRESHOLD constant. NO new judge class, NO new fixture, NO mirror of existing
infrastructure.

## Iteration log

### Iter 1 (2026-05-09) — full implementation

- **Files created (5):**
  - `backend/tests/quality/golden/growth_studio_actions/__init__.py` (empty package marker)
  - `backend/tests/quality/golden/growth_studio_actions/stage-query-happy.json` (voice fidelity Spanish neutro + tool dispatch correctness)
  - `backend/tests/quality/golden/growth_studio_actions/etl-refresh-confirm.json` (polite confirm copy + tool dispatch correctness)
  - `backend/tests/quality/golden/growth_studio_actions/etl-refresh-rate-limited.json` (no retry loop + retry copy)
  - `backend/tests/quality/golden/test_growth_studio_voice.py` (test runner — 29 test cases via parametrization)
- **Pattern compliance:**
  - Reuses `CopilotJudge` from `src.modules.copilot.application.observability.judge` (F9)
  - Reuses `judge_llm` fixture from `tests/quality/conftest.py` (stub default 4.0/dim, RUN_LLM_JUDGE=1 opt-in)
  - Mirrors `test_golden_conversations_semantic.py` shape (parametrize over goldens + threshold gate)
- **Determinism:**
  - 24 deterministic invariants (run on every CI without LLM):
    - Dataset shape (3 entries, unique ids, 3 distinct categories)
    - Tool registration check against ANALYTICS_TOOLS (regression-detector for T-3 future drift)
    - Voice constraints (voseo regex covering 50+ verbs, max_length, max_lines)
    - Polite confirm copy (interrogative ¿?, confirmation verb regex)
    - No retry loop (forbidden action-retry phrases regex; max_tool_invocations_per_turn=1; retry-time copy required)
    - Block kind namespacing (`growth.*` matches FE GROWTH_STUDIO_ACTION_KEYS from T-2)
  - 3 LLM-dependent invariants (one per golden) gated by RUN_LLM_JUDGE flag
- **Test results:**
  - `pytest tests/quality/golden/test_growth_studio_voice.py -v`: 29/29 PASSED
  - `pytest tests/quality/golden/`: 70/70 PASSED + 2 skipped (existing RUN_LLM_JUDGE=1 opt-in)
  - `pytest tests/architecture/`: 939/939 PASSED
  - `pytest tests/modules/copilot/golden/ tests/modules/copilot/application/tools/`: 73/73 PASSED
  - `ruff check`: All checks passed
  - `ruff format --check`: 0 changes (post-format)
  - `mypy`: Success — no issues
- **Validators per 04-validators.yaml:**
  - `agentic_voice_fidelity_goldens` ✓ (29/29 tests pass — 24 deterministic + 3 stub-judged + 2 sanity dataset shape)
  - `copilot_trace_event_recorded` — N/A this ticket (T-4 is goldens, not trace recording)
  - `cost_budget_per_session` — advisory; stub mode = $0 (free); opt-in real LLM ~$0.01-0.05 (within budget)
- **No retry loop discipline:**
  - `etl-refresh-rate-limited.json` enforces `max_tool_invocations_per_turn: 1` → arch test asserts cap is exactly 1
  - Forbidden phrases regex catches `intento de nuevo`, `vuelvo a intentar`, `reintento`, `lo intento otra vez`, `reintentar ahora` (action retry); allows `Próximo intento en 31 minutos` (informational)
- **Spanish neutro voseo glosario coverage:**
  - 50+ voseo verbs blocklisted (matches `.claude/rules/spanish-text.md` R2)
  - All 3 expected_outputs validated tuteo-only (no `vos/podés/tenés/refrescá/etc.`)
  - Tildes preserved (`¿cómo`, `próximo`, `período`, etc.)

### Quality gates summary

- ✓ Lint clean (ruff check)
- ✓ Format clean (ruff format --check)
- ✓ Type-check clean (mypy)
- ✓ All 29 new tests GREEN
- ✓ All 70 quality golden tests GREEN (no regression)
- ✓ All 939 architecture fitness tests GREEN (allowlists shrink-only respected)
- ✓ All 73 copilot golden + tool tests GREEN (T-3 contract preserved)

### Outcome

State: tests-passing per R30. Awaiting orchestrator → gate-runner → auditor-agentic.
