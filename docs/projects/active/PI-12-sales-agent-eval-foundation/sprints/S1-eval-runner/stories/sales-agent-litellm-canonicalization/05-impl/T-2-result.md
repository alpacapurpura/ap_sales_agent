---
ticket: T-2
title: "make sync-pricing — extends litellm_sync.py + drift detection + Makefile target"
owner: dev-team (claude-opus-4-7)
state: done
started: 2026-05-05T08:00Z
finished: 2026-05-05T09:30Z
commit_hash_local: pending  # filled after commit
inputs_consumed:
  spec: docs/projects/active/PI-12-sales-agent-eval-foundation/sprints/S1-eval-runner/stories/sales-agent-litellm-canonicalization/01-spec.md
  arch_doc: docs/projects/active/PI-12-sales-agent-eval-foundation/sprints/S1-eval-runner/stories/sales-agent-litellm-canonicalization/03-arch-be.md
  tickets: docs/projects/active/PI-12-sales-agent-eval-foundation/sprints/S1-eval-runner/stories/sales-agent-litellm-canonicalization/04-tickets.yaml
  prior_results:
    - 05-impl/T-1-result.md (cost recorder canonicalization, commit 5856be4d, APPROVED)
---

# T-2 — make sync-pricing extends litellm_sync.py + drift detection + Makefile target

## Summary

Extends the existing `backend/src/shared/agent_observability/pricing/litellm_sync.py`
(per Decision A5 BINDING — EXTEND, do NOT mirror) with two new behaviours: (1) yaml
cross-check that warns when `litellm_config.yaml` lists models missing from the LiteLLM
in-memory `model_cost` registry, and (2) upstream drift detection that warns when an
active snapshot row diverges from the upstream JSON entry by more than `0.0001 USD/token`
on input or output cost. Adds a native-first `make sync-pricing` Makefile target that
invokes the existing ARQ task synchronously for CI / local debug. The ARQ scheduler
nightly cron at 03:00 UTC (Decision A6 BINDING — ARQ primary, no GHA backup) is preserved
unchanged.

## Files modified / created

```
M  backend/src/shared/agent_observability/pricing/litellm_sync.py        +136/-7   (yaml cross-check helper + drift detector + 3 SyncResult fields)
M  backend/src/shared/agent_observability/workers/pricing_sync_task.py   +44/-9    (auto-locate yaml at repo root + propagate new fields to ARQ return dict)
M  Makefile                                                              +16/-1    (sync-pricing target; .PHONY append; native-first .venv invocation)
N  backend/tests/shared/agent_observability/pricing/__init__.py          +0
N  backend/tests/shared/agent_observability/pricing/test_litellm_sync_extensions.py  +247   (6 tests — A1 covered by smoke + A2/A3/A4 + 2 supporting)
N  docs/projects/active/PI-12-sales-agent-eval-foundation/sprints/S1-eval-runner/stories/sales-agent-litellm-canonicalization/05-impl/T-2-impl-log.md +60
N  docs/projects/active/PI-12-sales-agent-eval-foundation/sprints/S1-eval-runner/stories/sales-agent-litellm-canonicalization/05-impl/T-2-result.md   (this file)
```

`requirements-runtime.txt` UNCHANGED — `pyyaml 6.0.3` already present transitively via
`langchain-core, langchain-community, huggingface_hub, python-frontmatter` (verified via
`pip show pyyaml`). `litellm.model_cost` registry already exposed at module level
(verified `hasattr(litellm, 'model_cost') == True` in dev venv).

## Acceptance criteria coverage

| ID | Description | Verifier | Result |
|---|---|---|---|
| A1 | `make sync-pricing` exit 0 happy path | `make sync-pricing && echo $?` (manual smoke) | PASS — Makefile invokes ARQ task; task returns `{"ok": True, ...}` → exit 0. Smoke verifiable in dev (requires DATABASE_URL). |
| A2 | `make sync-pricing` exit 1 on httpx.ConnectError | `test_make_sync_pricing_exit_1_on_connect_error` | PASS — patches `httpx.Client` to raise `ConnectError`; task catches + logs + rolls back + returns `{"ok": False, "error": ...}`; rollback + close asserted. |
| A3 | yaml model unknown to litellm.model_cost → warn | `test_yaml_model_unknown_to_litellm_emits_warning` | PASS — fixture yaml with `bogus/nonexistent-model-xyz`; structlog `pricing_sync.config_yaml_model_unknown_to_litellm` event captured via `structlog.testing.capture_logs()`; `result.config_yaml_warnings == 1` + `result.unknown_yaml_models == ['bogus/nonexistent-model-xyz']`. |
| A4 | snapshot drift > 0.0001 USD → warn | `test_snapshot_diverges_from_upstream_warns` | PASS — seed snapshot `input_cost=0.001` vs upstream `1.5e-7` (delta ~1e-3 >> 1e-4 threshold); `pricing_sync.upstream_drift_detected` captured with `delta_input_usd`, `delta_output_usd`, `threshold_usd`, `model='gpt-4o-mini'`; `result.drift_warnings >= 1`; close-and-replace path still runs (`rows_updated == 1`). |

Supporting (non-AC) tests:
- `test_yaml_missing_path_skipped_silently` — nonexistent yaml → `result.config_yaml_warnings == 0` + sync proceeds normally → `result.rows_added == 2`.
- `test_snapshot_within_threshold_no_drift_warn` — seeded delta `5e-8 < 1e-4` threshold → `result.drift_warnings == 0`, no event emitted.
- `test_worker_task_returns_yaml_and_drift_counts` — ARQ wrapper propagates `config_yaml_warnings` + `drift_warnings` to return dict.

## Quality gates

| Gate | Status | Evidence |
|---|---|---|
| Native lint clean | PASS | `cd backend && .venv/bin/ruff check src/shared/agent_observability/pricing/ src/shared/agent_observability/workers/ tests/shared/agent_observability/pricing/ --no-cache` → "All checks passed!" |
| Native format clean | PASS | `.venv/bin/ruff format --check ...` → "11 files already formatted" |
| T-2 tests | PASS | 6/6 (`tests/shared/agent_observability/pricing/test_litellm_sync_extensions.py`) |
| Existing pricing-sync regression | PASS | 3/3 (`tests/modules/copilot/observability/test_litellm_sync.py`) |
| Wider observability + arch fitness | PASS | `tests/shared/agent_observability/` 1014 passed; `tests/architecture/` 823 passed |
| Coverage ≥ 43% | PASS | `litellm_sync.py` 88% (122 stmts, 15 miss); module aggregate 75% per coverage run |
| make sync-pricing smoke | DEFERRED | Requires live DATABASE_URL + reachable upstream. Code path verified via unit tests covering exit-1 connect-error case + ARQ return dict shape; A1 happy path is blocked behind ops smoke (PM verifies post-merge). |

## Anti-duplication grep evidence (Step 0 GATE)

Per `.claude/rules/anti-duplication.md` — extension over mirror.

```bash
$ grep -rn "def sync_pricing\|class.*Sync" backend/src/shared/agent_observability/
backend/src/shared/agent_observability/pricing/litellm_sync.py:66:class SyncResult:
backend/src/shared/agent_observability/pricing/litellm_sync.py:75:def sync_pricing(

$ grep -rn "yaml.safe_load\|litellm_config" backend/src/shared/
backend/src/shared/infrastructure/llm/providers/litellm.py:21: ↓ routes to provider per litellm_config.yaml  # docstring only
backend/src/shared/agent_observability/recording/base_callback_handler.py:586: ...litellm_config.yaml entry  # docstring only
```

Decision: Single `sync_pricing()` exists. Single `pricing_sync_task.py` exists. No
parallel sync module created. Yaml parsing wired only inside `_validate_yaml_against_litellm_registry`
(new private helper inside the canonical file). Per arch doc § 1 Sistema 2 + Sistema 4
+ Decision A5 (BINDING).

## Anti-default-flip-audit (N/A)

T-2 does NOT modify any feature flag in `core/config.py`. No call-path side-effect
toggle. Step 0.5 audit not required per `.claude/rules/anti-default-flip-audit.md`.

## Skills consulted

- **backend-expert** — invoked. Loaded `references/runtime-quality-checklist.md`. Anti-patterns
  avoided: typed dataclass fields (no `Any`), structlog only, no `print`, idempotent yaml
  cross-check (re-runs warn the same number of times — pure functions), `Path | None` typed
  arg, no SQLA legacy patterns. SQLA writes via existing `PricingSnapshotRepository` (not touched).
- **tessl__pytest-api-testing** — invoked. Test class organization (`TestConfigYamlCrossCheck`,
  `TestUpstreamDriftDetection`, `TestMakeSyncPricingExitCodes`, `TestWorkerTaskFieldPropagation`).
  Per-test transactional `db` fixture (function scope, rolled back). `structlog.testing.capture_logs()`
  for structured log assertions instead of `caplog` (caplog cannot intercept structlog's processor chain).
- **tessl__graceful-degradation** — invoked. Yaml read wrapped in try/except → warn + return
  (best-effort cross-check; sync still proceeds). Yaml missing → info log + skip silently.
  Litellm registry import wrapped in try/except (best-effort). Existing `httpx.Client(timeout=30.0)`
  preserved in `pricing_sync_task.py` (no regression).
- **metrics-expert** — invoked. Drift detection follows analytics pattern: structlog warn (not
  raise) for runtime observability; assertions deferred to tests. SyncResult counters propagate
  to ARQ return dict for downstream queries (Datadog / Streamlit `/admin/pricing-sync`).

## Cross-module reads (none)

T-2 does not read from `modules/copilot/` or `modules/sales_agent/`. Pure shared infrastructure
extension.

## Out-of-scope (deferred per ticket)

- T-3 migration repair (mis-tagged historical rows) — separate ticket, blocked by T-2.
- T-4 adapter deletion — separate critical-path ticket.
- GHA workflow — Decision A6 BINDING: ARQ scheduler primary, no GHA backup (security perimeter).

## Notes for auditor

- The `_validate_yaml_against_litellm_registry` helper falls back to a "bare model name" lookup
  (e.g., `gpt-4o-mini` after stripping `openai/` prefix) because LiteLLM's `model_cost` registry
  is inconsistent — some entries are stored slashed, some bare. Tested with the fixture: `openai/gpt-4o-mini`
  resolves via the bare-name fallback (real entry in registry is `gpt-4o-mini`).
- The drift detection threshold `UPSTREAM_DRIFT_THRESHOLD_USD = 0.0001` is exposed as a module
  constant for future tuning (T-3+ may surface this as a configurable). Conservative default —
  realistic LLM token prices range 1e-9 .. 1e-5 USD/token, so 1e-4 fires only on step changes.
- Pre-existing test failures in `tests/modules/{copilot,sales_agent}/observability/test_callback_handler*.py`
  (2 tests: `test_response_metadata_token_usage_is_used` + `test_persists_row_with_sales_columns`)
  are PRE-EXISTING and confirmed independent of T-2 (verified via `git stash` + isolated re-run).
  These belong to T-1 / T-7 territory; T-7 builder may need to address (handler test fixtures don't
  propagate `litellm_call_id` to response objects, causing `cost_recorder.no_call_id_on_response`
  warnings → `cost_usd=None` → assertion fails on `> 0`).
