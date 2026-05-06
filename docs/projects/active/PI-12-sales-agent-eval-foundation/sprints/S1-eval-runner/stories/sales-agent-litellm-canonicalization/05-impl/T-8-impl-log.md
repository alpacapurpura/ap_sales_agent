# T-8 Implementation Log

**Ticket:** T-8 — Arch fitness shrink + 3 ratchet enforcement assertions + 1 meta-test
**Story:** sales-agent-litellm-canonicalization
**Sprint:** S1-eval-runner / PI-12
**Builder:** `builder-backend` (Claude Opus 4.7 — HARD MANDATE per architect verified pre-spawn)
**Commit:** `253e6024`
**Date:** 2026-05-06

## Summary

Codify post-Wave-3 ratchet enforcement: 3 architectural assertions guard against regression of T-4 (legacy adapter deletion) + T-5 (LITELLM_PROXY_ENABLED flag deletion). Meta-test `test_violation_detection_works` evergreen-validates the 3 ratchet tests correctly raise on injected violations.

## Skills Consulted

- `backend-expert` — references/architectural-fitness.md ratchet shrink-only pattern + violation detection convention
- `tessl__pytest-api-testing` — factory/fixture pattern for tmp_path-based meta-test
- `tessl__fastapi` — N/A (no API surface change)
- `tessl__graceful-degradation` — N/A (no external HTTP)

## Decisions Honored

T-8 ticket spec lacks `decisions_applicable` field. Builder honored implicit architecture invariants:
- Ratchet allowlists shrink-only (architectural-fitness.md SSoT)
- Self-exclusion via `__file__` resolution to prevent meta-test scanning itself
- TDD: write failing test injection scenarios first, then assert canonical state

## Files Changed (1)

### Modified
- `backend/tests/architecture/test_llm_routing_ssot.py` (+216 / -15)

### Functions Added
- `_scan_for_legacy_adapter_imports(roots: list[Path]) -> list[tuple[Path, int, str]]` — scanner helper, excludes `__file__` self
- `test_no_legacy_adapter_imports()` — A1 ratchet enforcement
- `test_known_legacy_files_set_is_empty()` — A2 ratchet shrink-only enforcement
- `test_settings_has_no_litellm_proxy_enabled_attr()` — A3 post-T-5 flag deletion enforcement
- `test_violation_detection_works()` — A4 meta-test validating 3 ratchet assertions detect injection

### Stripped
- Stale `LITELLM_PROXY_ENABLED` + `build_provider_service` references in `test_router_dispatches_via_litellm_only` docstring + assertion text

## TDD Trace

1. **RED**: write A1 test against current state — PASS immediately (T-4 already deleted adapters)
2. **RED**: write A2 test against current state — PASS immediately (T-4 audit confirmed empty allowlist)
3. **RED**: write A3 test against current state — PASS immediately (T-5 deleted flag)
4. **VIOLATION INJECTION**: write A4 meta-test that monkeypatches:
   - `KNOWN_LEGACY_LLM_FILES.add('x')` → A2 raises AssertionError ✓
   - `Settings.model_fields['LITELLM_PROXY_ENABLED']` → A3 raises ✓
   - synthetic file with forbidden import → `_scan_for_legacy_adapter_imports()` returns 1 violation ✓
5. **GREEN**: A4 PASSES — ratchet enforcement validates correctly

## Quality Gates Run

| Gate | Result | Detail |
|---|---|---|
| ruff check | PASS | clean (1 pre-existing unrelated warning) |
| ruff format | PASS | 2328 files already formatted |
| pytest test_llm_routing_ssot | PASS | 8/8 (4 pre-existing + 3 ratchet + 1 meta) |
| pytest tests/architecture/ full | PASS | 827/827 (delta 823 → 827) |
| pytest -m "not integration" --cov | PASS_KNOWN_FLAKE | 9063 PASS / 38 SKIP / 1 unrelated flake (test_arch_fitness_performance_budget under coverage.py overhead — passes isolated; auditor re-verified) |
| Coverage threshold 43% | PASS | satisfied per exit pattern |

## Native-First Compliance

- All tests via `cd /home/chris/AISALESHT/backend && .venv/bin/pytest ...`
- Lint via `.venv/bin/ruff` — NEVER docker exec

## Anti-Duplication §0

T-8 is pure addition to existing test file. Zero new utility mirrors. Self-exclusion logic in `_scan_for_legacy_adapter_imports` correctly implemented via `__file__` resolution to prevent meta-test scanning itself.

## Acceptance

| ID | Verifier | Status |
|---|---|---|
| A1 | pytest test_no_legacy_adapter_imports | PASS |
| A2 | pytest test_known_legacy_files_set_is_empty | PASS |
| A3 | pytest test_settings_has_no_litellm_proxy_enabled_attr | PASS |
| A4 | pytest test_violation_detection_works | PASS (4 sub-checks via meta-test) |

## Outcome

- **State:** `audit-passed`
- **Verdict:** APPROVED per `06-audit/T-8-review.md` (1 non-blocking WARN: this impl-log was missing — created retroactively by /pm orchestrator)
- **Commit:** `253e6024` on `development`
- **Blocks unblocked:** T-9 (docs purge — depends on T-8)
- **Process metric (R12):** emitted via orchestrator
