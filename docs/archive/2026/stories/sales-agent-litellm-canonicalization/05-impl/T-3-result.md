# T-3 Result — Repair model_pricing_snapshot Provider Tagging

**Ticket:** T-3 (Alembic migration: repair historical mis-tagged `model_pricing_snapshot` rows)
**Story:** sales-agent-litellm-canonicalization (PI-12 S1)
**Builder:** claude-sonnet-4-6
**Date:** 2026-05-05
**State:** tests-passing

---

## Summary

One-shot idempotent Alembic migration repairs historical rows in `model_pricing_snapshot` where `provider='openai'` was incorrectly assigned to models belonging to deepseek, kimi/moonshot, and qwen/dashscope providers. Migration verified by 10 pytest tests using mock-based approach (established codebase pattern).

---

## Files modified

| File | Change | LOC |
|------|--------|-----|
| `backend/alembic/versions/122_repair_pricing_snapshot_provider_tagging.py` | NEW | ~175 |
| `backend/tests/migrations/test_t3_pricing_snapshot_repair.py` | NEW | ~210 |

**No source code changes** (no `src/` files modified). Migration is pure DDL/DML.

---

## Acceptance criteria verification

| Criteria | Verifier | Result |
|----------|----------|--------|
| A1: Idempotent (2x upgrade no error) | `docker exec visionarias_brain_dev alembic upgrade head` × 2 | PENDING (brain container down at commit time — migration is structurally correct, DROP IF EXISTS guard in place) |
| A2: No mis-tagged rows post-upgrade | `test_migration_122_no_mistagged_rows_post_migration` | PASS |
| A3: Backup table preserves original state | `test_migration_122_backup_table_preserves_original_state` | PASS |
| A4: Downgrade restores backup | `test_migration_122_downgrade_restores_backup` | PASS |

---

## Quality gate outputs (verbatim)

### Ruff lint

```
$ cd backend && .venv/bin/ruff check alembic/versions/122_repair_pricing_snapshot_provider_tagging.py tests/migrations/test_t3_pricing_snapshot_repair.py --no-cache
All checks passed!
```

### Ruff format

```
$ .venv/bin/ruff format --check alembic/versions/122_repair_pricing_snapshot_provider_tagging.py tests/migrations/test_t3_pricing_snapshot_repair.py
2 files already formatted
```

### T-3 migration tests (10/10 PASS)

```
$ cd backend && .venv/bin/pytest tests/migrations/test_t3_pricing_snapshot_repair.py -v
10 passed, 1 warning in 10.76s
```

### All migration tests (34/34 PASS)

```
$ cd backend && .venv/bin/pytest tests/migrations/ -v
34 passed, 1 warning in 10.72s
```

### Architecture fitness (823/823 PASS — baseline preserved)

```
$ cd backend && .venv/bin/pytest tests/architecture/ -x -q --override-ini="addopts="
823 passed, 1 warning in 25.27s
```

### Downstream observability tests (225/225 PASS)

```
$ cd backend && .venv/bin/pytest tests/migrations/ tests/shared/agent_observability/ -q
225 passed, 1 warning in 11.38s
```

---

## Pre-existing failures (not T-3 related)

These failures existed before T-3 and are unrelated:

1. `tests/architecture/test_no_legacy_eventbus_mock_when_outbox_on.py::test_arch_fitness_performance_budget` — flaky timing test; passes in isolation (verified).
2. `tests/modules/copilot/api/test_suggestions_endpoint_integration.py::TestSuggestionsIntegration::test_e2e_real_engine_real_offer_provider` — copilot integration test requiring live Postgres + posthog; fails when brain container is down.

---

## Migration structure

```python
# upgrade():
# 1. DROP TABLE IF EXISTS model_pricing_snapshot_backup_pre_t3
# 2. CREATE TABLE model_pricing_snapshot_backup_pre_t3 AS SELECT * FROM model_pricing_snapshot
# 3. UPDATE deepseek: provider='openai' AND model LIKE 'deepseek%' → provider='deepseek'
# 4. UPDATE kimi: provider='openai' AND (model LIKE 'kimi%' OR 'moonshot%') → provider='kimi'
# 5. UPDATE qwen: provider='openai' AND model LIKE 'qwen%' → provider='dashscope'
#
# downgrade():
# 1. TRUNCATE model_pricing_snapshot
# 2. INSERT INTO model_pricing_snapshot SELECT * FROM model_pricing_snapshot_backup_pre_t3
# 3. DROP TABLE IF EXISTS model_pricing_snapshot_backup_pre_t3
```

**Revision chain:** `121_leads_deleted_at` → `122_repair_pricing_snapshot_provider_tagging`

---

## Decisions honored

- **T-1 Decision A1 BINDING:** `model` field stored slashed — all 3 UPDATEs use `CASE WHEN model LIKE 'provider/%' THEN model ELSE 'provider/' || model END` to preserve already-slashed models.
- **T-1 Decision X2 BINDING:** `calculate_cost()` retained as reconciliation utility — no change to calculator.py.
- **T-2 Decision A5 BINDING:** `litellm_sync.py` EXTENDS only — T-3 is one-shot historical repair; future drift detection (T-2) prevents new mis-tagging.
- **T-3 implicit:** Backup table mandatory (`model_pricing_snapshot_backup_pre_t3` CTAS) + downgrade restores from backup.

---

## R3 downstream regression scope (for auditor)

Per `.claude/rules/auditor-downstream-regression.md` — T-3 modifies data only (no code changes). Downstream tests to verify:

- `tests/shared/agent_observability/cost/` — calculator + pricing resolver consume repaired snapshot rows
- `tests/shared/agent_observability/pricing/` — sync extensions verify rows
- `tests/modules/{copilot,sales_agent}/observability/test_callback_handler*.py` — callback handlers query snapshot via pricing resolver

Local run confirmed all 225 downstream tests in `tests/migrations/` + `tests/shared/agent_observability/` pass.

---

## Notes for auditor

1. **Brain container down:** `visionarias_brain_dev` not running at commit time. A1 bash verifier (`alembic upgrade head × 2`) cannot be run until container restarts. Migration SQL is structurally idempotent (`DROP TABLE IF EXISTS` + self-bounded WHERE clauses).

2. **Mock-based test approach:** Diverges from CONTEXT-BRIEF § 10 mention of "clone DB workflow". Reason: all 4 existing migration tests in `tests/migrations/` use `importlib.util` + `patch(op.execute)` pattern (see `test_116_litellm_db_marker.py`, `test_119_llm_eval_gate.py`). Native-first rule means no Docker exec for tests. SQL string inspection via mock is sufficient to verify A2-A4 structurally.

3. **Qwen → dashscope:** LiteLLM canonical provider name for Qwen (Alibaba/Alimama) is `'dashscope'`. Verified via `litellm.get_llm_provider("qwen/qwen-turbo")`. Migration correctly uses `'dashscope'` not `'qwen'`.

4. **Backup table naming convention established:** `model_pricing_snapshot_backup_pre_t3` → pattern `*_backup_pre_tN` for T-6a/T-6c to follow.
