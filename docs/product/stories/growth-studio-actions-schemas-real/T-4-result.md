# T-4 Result — growth-studio-actions-schemas-real

**Ticket:** T-4 — AGENTIC: 3 voice fidelity eval goldens (Spanish neutro + tool dispatch correctness + no retry loop)
**Owner:** claude-opus (builder-agentic) — R23 Opus required (production_code: true)
**State:** tests-passing (per R30 builder verdict; awaiting auditor-agentic independent contract)
**Depends on:** T-3 (DONE — commit 12962e0d)
**Closed at:** 2026-05-09T07:30:00Z

## Outcome

**3 voice fidelity eval goldens shipped + 1 deterministic test runner with 29 tests covering 6 invariants.**

The goldens lock in the post-T-3 contract for the new analytics tools registered in `ANALYTICS_TOOLS`:

| Golden | Category | Locked invariant |
|---|---|---|
| `stage-query-happy.json` | `tool_dispatch_correctness` | Spanish neutro tuteo + correct dispatch of `get_stage_metrics(stage='adopcion', period='30d')` + `growth.stage-metrics` block kind |
| `etl-refresh-confirm.json` | `tool_dispatch_polite_confirm` | Polite confirm copy (interrogative + confirmation verb) + dispatch of `trigger_etl_refresh(channel='meta-ads', confirmed=False)` returning `requires_confirmation=true` |
| `etl-refresh-rate-limited.json` | `no_retry_loop` | Single-shot dispatch (`max_tool_invocations_per_turn=1`) + retry-time copy required + action-retry phrases forbidden |

## Files delivered

### NEW (5)

```
backend/tests/quality/golden/growth_studio_actions/__init__.py
backend/tests/quality/golden/growth_studio_actions/stage-query-happy.json
backend/tests/quality/golden/growth_studio_actions/etl-refresh-confirm.json
backend/tests/quality/golden/growth_studio_actions/etl-refresh-rate-limited.json
backend/tests/quality/golden/test_growth_studio_voice.py
```

### MODIFIED (0)

No existing files modified — pure ADD per the T-4 ticket spec. Reuses `CopilotJudge` + `judge_llm` fixture + `DEFAULT_THRESHOLD` from existing infrastructure.

## Validators GREEN

| Validator | Status | Evidence |
|---|---|---|
| `agentic_voice_fidelity_goldens` | ✓ | `pytest tests/quality/golden/test_growth_studio_voice.py -v` → 29/29 PASSED |
| `be_lint` | ✓ | `ruff check` → All checks passed |
| `be_format` | ✓ | `ruff format --check` → 0 changes |
| `be_typecheck` (mypy) | ✓ | `mypy tests/quality/golden/test_growth_studio_voice.py` → Success |
| `be_arch_fitness_full` | ✓ | `pytest tests/architecture/` → 939/939 PASSED (no regression) |
| Quality golden suite (no regression) | ✓ | `pytest tests/quality/golden/` → 70/70 PASSED + 2 skipped (existing RUN_LLM_JUDGE=1 opt-in unchanged) |
| Copilot golden + tool suite (T-3 contract preserved) | ✓ | `pytest tests/modules/copilot/golden/ tests/modules/copilot/application/tools/` → 73/73 PASSED |
| `agentic_eval_real_llm_optin` | (advisory) | RUN_LLM_JUDGE=1 path wired; weekly cron + ad-hoc inspection eligible. Cost target ≤$0.05/run. |

## Architecture invariants honored

- **Reuses CopilotJudge (F9)** — no new judge class, no new rubric, no fork. Single LLM call per evaluation, NANO model, fail-soft.
- **Reuses `judge_llm` fixture** (`tests/quality/conftest.py`) — stub default returns 4.0/dim, opt-in real NANO via `RUN_LLM_JUDGE=1` (matches F9 + S10 cost guard pattern cementado).
- **Reuses `ANALYTICS_TOOLS` registry** — golden tool names cross-checked against the registry; regression-detector for any future T-3 follow-up that drops a tool.
- **Anti-duplication** — extended `tests/quality/golden/` with sub-directory + test runner; no parallel layer, no mirror of existing infrastructure.
- **Spanish neutro tuteo** — voseo glossary regex covers 50+ verbs (matches `.claude/rules/spanish-text.md` R2). Pre-commit hook covers files at commit time; this regex covers golden expected_output regression at test time.
- **No retry loop** — `max_tool_invocations_per_turn: 1` enforced; forbidden action-retry phrases regex (`intento de nuevo`, `vuelvo a intentar`, `reintento`, `lo intento otra vez`, `reintentar ahora`); informational retry copy (`Próximo intento en 31 minutos`) explicitly allowed.

## Determinism profile

- **24 deterministic invariants** run on every CI without LLM (dataset shape, tool registration check, voice constraints, polite confirm, no retry loop, block kind namespacing).
- **3 LLM-dependent assertions** gated by `RUN_LLM_JUDGE=1` env flag — stub mode (default) returns canned 4.0/dim across rubric so the pipeline plumbs correctly without burning OpenAI/Anthropic budget on every CI run.
- **Cost guard:** stub mode = $0 (free); opt-in real LLM single eval pass ≈$0.01-0.05 (NANO model, single call per golden, temperature=0 + seed=42 for determinism).

## Anti-telephone-game footer

```
done -> docs/product/stories/growth-studio-actions-schemas-real/T-4-result.md
```

## Notes for auditor-agentic

- Test file imports: `CopilotJudge`, `DEFAULT_THRESHOLD`, `ANALYTICS_TOOLS` — all live, all in scope.
- Voseo regex is **defensive subset** (not exhaustive) covering the verbs most likely to appear in copilot UI strings. Pre-commit hook covers cross-codebase voseo at commit time; this regex is the test-time backup for golden expected_output drift.
- `polite_confirm_required` and `no_retry_loop` are **per-golden flags** in `voice_constraints` — only goldens that opt in are subject to their respective assertions (parametrize-filter idiom).
- Real-LLM weekly cron (RUN_LLM_JUDGE=1) is **out of T-4 scope** — wiring into the existing `weekly_copilot_quality_eval` cron is a future follow-up if/when product wants growth-studio voice tracked alongside the canonical 20 goldens.
- No changes to runtime code — pure test artefacts. ANALYTICS_TOOLS registry preserved exactly as T-3 left it (commit 12962e0d).

## Commit

```
test(copilot): 3 voice fidelity eval goldens (Spanish neutro + dispatch + no-retry) (T-4 Story 2B)
```

Push commit SHA: TBD (post-build hook).
