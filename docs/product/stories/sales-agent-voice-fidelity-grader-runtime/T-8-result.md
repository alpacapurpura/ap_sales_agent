# T-8 — Result

**Ticket**: T-8 — `simulator/__init__.py` H9 expand 7→8 (`grade_transcript_maj_eval`) + arch fitness re-freeze + 4 NEW grader gates (effective: 2 NEW + 1 EDIT — 4 grader arch gates ALREADY shipped via T-5/T-7)
**Owner**: builder-agentic-opus-4.7
**State**: tests-passing
**Date**: 2026-05-09

## Summary

Cemented H9 public API surface expansion 7→8 names (single addition `grade_transcript_maj_eval`) and added 2 NEW grader-specific architecture fitness gates (D-AG-16 cement + H7 cost-bucket invariant). Re-frozen the simulator package allowlist at 8 names; downstream Stories F/G/H/I now consume an authoritative, ratchet-protected surface.

The other 4 "NEW" arch fitness gates referenced in `06-tickets.yaml` T-7 deliverables (`test_grader_no_mirrors_shared`, `test_grader_pii_sanitize_pre_judge`, `test_grader_round_2_no_self_reasoning`, `test_grader_sandbox_markers_enforced`) were ALREADY shipped via T-5 / T-7. T-8 verified them GREEN post-expand without modification.

## Deliverables vs T-8 acceptance

| AcceptanceID | Description | Verifier path | Result |
|---|---|---|---|
| A1 | H9 expand 7→8 — `__all__` exact 8 names alphabetical | `tests/architecture/test_simulator_public_api_surface.py` | ✅ 22/22 PASS (incl. parametrized + new `test_grade_transcript_maj_eval_is_callable`) |
| A2 | grader/__init__.py cero re-exports (D-AG-16) | `tests/architecture/test_grader_public_api_surface.py` | ✅ 8/8 PASS |
| A3 | Cost-bucket invariant H7 — grader writes eval_simulator_llm_call ONLY | `tests/architecture/test_grader_writes_eval_only_bucket.py` | ✅ 9/9 PASS (parametrized 3 forbidden classes + 3 forbidden table literals + 3 sanity) |
| A4 | Story B 5 + Story C 1 arch fitness gates STILL GREEN (no regression) | `tests/architecture/` (`-k 'simulator or schema_migrations or termination_policy or eval_simulator'`) | ✅ 144/144 PASS |

## Quality gates (T-8 `quality_gates.validator_ids`)

| Validator ID | Status |
|---|---|
| `be_lint` (`ruff check`) | ✅ PASS — All checks passed (T-8 files + simulator/__init__.py) |
| `be_format` (`ruff format --check`) | ✅ PASS — 4 files already formatted post auto-format |
| `be_arch_fitness_full` | ✅ PASS — 1063/1063 architecture fitness gates GREEN, 1 skipped (env-gated `EVAL_GOLDENS_COST_BUCKET_VERIFY` cost-control opt-in) |
| `public_api_surface_h9_expand_8` | ✅ PASS — `test_simulator_public_api_surface.py` 22/22 |
| `grader_public_api_surface_zero_exports` | ✅ PASS — `test_grader_public_api_surface.py` 8/8 |
| `agentic_cost_bucket_zero_contamination_grader` | ✅ PASS — `test_grader_writes_eval_only_bucket.py` 9/9 |
| `legacy_simulator_invariants_intact` | ✅ PASS — Story B 5 gates + Story C 1 gate + Story E pre-T-8 4 gates = 144/144 PASS |

## Validator logs (executable evidence)

```bash
# A1 — H9 expand
$ cd backend && .venv/bin/pytest tests/architecture/test_simulator_public_api_surface.py -v --tb=short --override-ini="addopts="
22 passed in ~3s

# A2 — grader public API surface (D-AG-16)
$ cd backend && .venv/bin/pytest tests/architecture/test_grader_public_api_surface.py -v --tb=short --override-ini="addopts="
8 passed in ~3s

# A3 — cost-bucket invariant H7
$ cd backend && .venv/bin/pytest tests/architecture/test_grader_writes_eval_only_bucket.py -v --tb=short --override-ini="addopts="
9 passed in ~3s

# A4 — legacy_simulator_invariants_intact validator scope
$ cd backend && .venv/bin/pytest \
  tests/architecture/test_simulator_no_mirrors_shared.py \
  tests/architecture/test_simulator_writes_eval_kind_tag.py \
  tests/architecture/test_eval_simulator_observability_invariants.py \
  tests/architecture/test_termination_policy_registry_contract.py \
  tests/architecture/test_schema_migrations_registry_complete.py \
  tests/architecture/test_personas_yaml_completeness.py \
  tests/architecture/test_grader_no_mirrors_shared.py \
  tests/architecture/test_grader_pii_sanitize_pre_judge.py \
  tests/architecture/test_grader_round_2_no_self_reasoning.py \
  tests/architecture/test_grader_sandbox_markers_enforced.py \
  -v --tb=short --override-ini="addopts="
144 passed in ~12s

# Full architecture fitness suite
$ cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short --override-ini="addopts="
1063 passed, 1 skipped in 26.16s

# Native grader + simulator ticket tests
$ cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/grader/ tests/agentic_evals/sales_agent/simulator/ -v --tb=short --override-ini="addopts=" -p no:randomly --timeout=60
315 passed, 36 skipped in 1m53s
```

## Files modified

```
M backend/tests/agentic_evals/sales_agent/simulator/__init__.py     (+29 / -10 — H9 expand 7→8 + docstring cement)
M backend/tests/architecture/test_simulator_public_api_surface.py   (+24 / -10 — allowlist 7→8 + new callable check)
A backend/tests/architecture/test_grader_public_api_surface.py      (+218 — D-AG-16 cement, 8 tests)
A backend/tests/architecture/test_grader_writes_eval_only_bucket.py (+243 — H7 cement, 9 tests parametrized)
```

## Out-of-scope confirmation

- ❌ Other arch fitness gates (sandbox/round2/pii/no_mirrors) — covered by T-7 (already shipped).
- ❌ Integration scenarios — T-9.

T-8 stayed strictly within the public API surface re-freeze + 2 NEW arch fitness gates scope.

## Anti-default-flip audit

N/A — T-8 doesn't touch `core/config.py`. No flag side-effect path changes. No `USE_*_PATTERN_*` / `LITELLM_PROXY_ENABLED` / `USE_DEEPAGENTS_*` modifications.

## Anti-duplication audit (per `.claude/rules/anti-duplication.md`)

✅ Pre-Write Step 0 grep executed — no mirror detected:
- T-8 NEW arch tests live ONLY under `backend/tests/architecture/` (no consumer mirror).
- T-8 NEW arch tests do NOT duplicate basenames with any file under `shared/agent_observability/`.
- Existing `test_grader_no_mirrors_shared.py` (T-7) covers the basename-collision invariant for the grader subtree itself; T-8 adds orthogonal invariants (public API surface + cost-bucket).

## Cross-cutting consistency

- **Tenant isolation** — N/A T-8 (arch fitness gates do not query DB; T-5/T-9 enforce tenant isolation in production grader code).
- **PII sanitization** — N/A T-8 (T-5/T-7 enforce `sanitize_payload` pre-judge call via `test_grader_pii_sanitize_pre_judge.py`).
- **Spanish neutro** — T-8 files English-only with `voseo-allowed` magic comment per Story B/C precedent (cited inline in module docstrings).
- **Native-first** — All commands run via `cd backend && .venv/bin/{ruff,pytest,mypy}`. Zero `docker exec` for lint/tests/type-check.

## Final state

**tests-passing** — All T-8 acceptance criteria verified GREEN. Story E T-8 build phase complete; awaiting orchestrator (`/dev-team`) → gate-runner → auditor-backend / auditor-agentic independent verdict per R30 (2026-05-05 cement: builder phase output is `tests-passing` ONLY).

## Next ticket dependency

T-9 (Integration — `run_simulation` grader_callback hook + 4 scenarios + calibration MD) `depends_on: [T-5, T-6, T-7, T-8]` — all 4 deps now satisfied.
