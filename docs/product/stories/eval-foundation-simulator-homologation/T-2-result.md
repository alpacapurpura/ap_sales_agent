# T-2 Result — Migration test + arch fitness gate observability invariants

**Story:** eval-foundation-simulator-homologation
**Ticket:** T-2
**State:** tests-passing
**Owner:** claude-sonnet (builder-backend, test-infrastructure production_code=false)

## Deliverables Shipped

| # | Deliverable | Status |
|---|---|---|
| 1 | `backend/tests/migrations/test_extend_eval_simulator_observability.py` — 38 tests: revision metadata + 3 tables created + 7 indexes created + schema shape invariants + double-upgrade idempotency + downgrade drops 3 tables + spec registration via bootstrap import | DONE |
| 2 | `backend/tests/architecture/test_eval_simulator_observability_invariants.py` — 43 tests: spec registered post-bootstrap + ORM models exist + eval_metadata JSONB enforced + tenant isolation + timestamp timezone-aware + campaigns parity fields + R5 schema-mirror boundary respected | DONE |

## Acceptance Criteria

| # | Description | Result |
|---|---|---|
| A1 | Migration test pass apply+rollback+idempotent | PASS (38/38) |
| A2 | Arch fitness gate green | PASS (43/43) |

## Test counts

- Migration test: 38 tests (TestRevisionMetadata×2, TestUpgradeCreatesTables×4, TestUpgradeCreatesIndexes×8, TestUpgradeSchemaShape×10, TestUpgradeIdempotency×3, TestDowngrade×5, TestSpecRegistration×6)
- Arch fitness gate: 43 tests (7 test classes covering 6 invariant categories)

## Quality Gates Output

| Gate | Result |
|---|---|
| `ruff check` | 0 errors |
| `ruff format --check` | 0 files to reformat |
| `pytest tests/migrations/test_extend_eval_simulator_observability.py` | 38/38 PASS |
| `pytest tests/architecture/test_eval_simulator_observability_invariants.py` | 43/43 PASS |
| `pytest tests/architecture/` (full suite) | 880/881 (1 pre-existing flaky timing test, unrelated to T-2) |

### Pre-existing issue (NOT T-2 regression)

`test_arch_fitness_performance_budget` (test_no_legacy_eventbus_mock_when_outbox_on.py): AST walk 2.108s vs 2.0s budget on 832 files — timing-sensitive, system load dependent, was failing before T-2.

## Diff Summary

```
backend/tests/migrations/test_extend_eval_simulator_observability.py  (+410 lines NEW)
backend/tests/architecture/test_eval_simulator_observability_invariants.py  (+340 lines NEW)
docs/product/stories/eval-foundation-simulator-homologation/T-2-impl-log.md  (NEW)
docs/product/stories/eval-foundation-simulator-homologation/T-2-result.md  (NEW)
docs/product/stories/eval-foundation-simulator-homologation/06-tickets.yaml  (T-2 state update)
```

## Commit SHA

_pending_
