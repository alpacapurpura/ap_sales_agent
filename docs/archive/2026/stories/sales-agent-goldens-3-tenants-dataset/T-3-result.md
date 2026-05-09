# T-3 Result — generate_golden_candidates.py + promote_golden.py

Story: sales-agent-goldens-3-tenants-dataset
Ticket: T-3
State: pushed
Commit: pending

## Deliverables

| File | Status |
|---|---|
| `backend/scripts/generate_golden_candidates.py` | NEW — 536 LOC |
| `backend/scripts/promote_golden.py` | NEW — 269 LOC |
| `backend/tests/scripts/test_generate_golden_candidates.py` | NEW — 37 tests |
| `backend/tests/scripts/test_promote_golden.py` | NEW — 31 tests |
| `backend/tests/architecture/test_goldens_cost_bucket_invariant.py` | NEW — env-gated (EVAL_GOLDENS_COST_BUCKET_VERIFY=1) |

## Quality Gates

| Gate | Result |
|---|---|
| ruff check | PASS (0 errors) |
| ruff format --check | PASS (0 files to reformat) |
| pytest T-3 tests | 68 PASS, 3 SKIP (gated) |
| pytest tests/architecture/ | 1015 PASS, 1 SKIP |

## Test Coverage

Tests cover:
- Argparse defaults validation
- Matrix shape: 5x3xN cells, filters by tenant and persona_kind
- Cost budget pre-flight: exit 2 when estimated > budget
- Preview Markdown: deterministic, sorted, pipe-escaped, English headers
- Per-cell isolation: 1 failure continues suite (Rule 5)
- Single cell regen via tenant+persona_kind filter
- Auto-derivation of termination_reason, tools_invoked, forbidden_tools
- voice_attributes extraction from personality_profile.dimensions
- Idempotent YAML overwrite (same args = same content modulo curated_at)
- YAML safe_dump: sort_keys, allow_unicode, parseable back
- Exit code 2 on missing artifact, invalid persona_kind, validation error
- persona_kind out of scope (adversarial/edge/negative) raises ValueError with message matching "not in goldens scope"

## Gated Tests (deferred — require cost authorization from Chris)

| Test | Gate | Estimated cost | Command |
|---|---|---|---|
| TestReproducibilitySmoke | RUN_EVALS=1 | ~$0.15 | `RUN_EVALS=1 pytest tests/scripts/test_generate_golden_candidates.py -k reproducibility` |
| TestE2ESmoke | RUN_EVALS=1 | ~$0.15 | `RUN_EVALS=1 pytest tests/scripts/test_promote_golden.py -k e2e_smoke` |
| TestGoldensCostBucketInvariant | EVAL_GOLDENS_COST_BUCKET_VERIFY=1 | ~$0.22 | `EVAL_GOLDENS_COST_BUCKET_VERIFY=1 pytest tests/architecture/test_goldens_cost_bucket_invariant.py` |

## Usage

```bash
# Generate candidates (75 cells default — ~$5.40)
python backend/scripts/generate_golden_candidates.py \
  --output-dir backend/tests/agentic_evals/sales_agent/_artifacts/goldens_generation/run-001

# Generate for 1 tenant only (3 cells — ~$0.22)
python backend/scripts/generate_golden_candidates.py \
  --tenant tenant_coach_lat --runs-per-cell 1 \
  --output-dir /tmp/goldens-test

# Promote candidate to golden
python backend/scripts/promote_golden.py \
  --simulation-id <uuid> \
  --golden-id coach-lat-happy-001 \
  --artifact-dir /tmp/goldens-test \
  --actor-profile-id lead-frio-impaciente-pe \
  --notes "Selected from run-001, good objection handling"
```
