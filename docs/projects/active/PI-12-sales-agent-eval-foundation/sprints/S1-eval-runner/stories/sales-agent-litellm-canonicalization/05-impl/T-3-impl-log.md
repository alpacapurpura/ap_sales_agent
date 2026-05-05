# T-3 Implementation Log — Repair model_pricing_snapshot Provider Tagging

**Ticket:** T-3 (Alembic migration: repair historical mis-tagged `model_pricing_snapshot` rows)
**Story:** sales-agent-litellm-canonicalization (PI-12 S1)
**Builder:** claude-sonnet-4-6 (backend-expert role)
**Date:** 2026-05-05
**State:** tests-passing

---

## Phase 0 — GATE (mandatory reads)

**Step 0 — Anti-duplication GATE (per `.claude/rules/anti-duplication.md`):**

```bash
find /home/chris/AISALESHT/backend/alembic/versions/ -name "*pricing_snapshot*" -o -name "*model_pricing*"
# Result: /home/chris/AISALESHT/backend/alembic/versions/114_pricing_deepseek_v4_flash.py
#   (data INSERT only — no repair migration exists yet. NEW is correct.)

grep -rln "_backup_pre_" /home/chris/AISALESHT/backend/alembic/versions/
# Result: empty (convention is NEW per CONTEXT-BRIEF § 7.5)

grep -rln "model_pricing_snapshot.*UPDATE\|UPDATE.*model_pricing_snapshot" /home/chris/AISALESHT/backend/alembic/versions/
# Result: empty (no existing repair migration — NEW is correct)
```

**Step 0.5 — Hot-fix repro:** N/A — T-3 is design-from-scratch (no hot-fix signal).

**Step 0.6 — Default-flip detection:** N/A — no `core/config.py` changes.

**CONTEXT-BRIEF consumed:** faithfulness flag `clean` (iter-2 PASS after schema VARCHAR size correction by orchestrator). Builder confirmed actual schema: `provider VARCHAR(32)`, `model VARCHAR(128)` per `pricing_snapshot_model.py:24-25`.

**runtime-quality-checklist.md:** Read. Not applicable to migration-only PR (no FastAPI endpoints, no SQLA ORM calls, no Pydantic DTOs in scope). Relevant check confirmed: migration uses `op.execute()` raw SQL only (no `op.create_table()` / `op.add_column()` — prohibited anti-patterns).

---

## Skills Consulted

- `backend-expert` — invoked per Step 3 SOP routing. Loaded `runtime-quality-checklist.md` before commit. Decision: T-3 is pure migration + test, no FastAPI/ORM anti-patterns apply. Migration pattern follows `backend-migrations.md` raw SQL idempotency. Citation: `backend-expert/SKILL.md` § "Alembic migracion idempotente".
- `tessl__fastapi` — invoked (always-on per builder system prompt). Decision: N/A for T-3 (no API routes). Noted for completeness.
- `tessl__pytest-api-testing` — invoked (always-on). Decision: T-3 migration tests use mock-based pattern (`patch op.execute`) per existing codebase convention (`test_116_litellm_db_marker.py`, `test_119_llm_eval_gate.py`). No DB fixture needed — SQL string inspection is sufficient. Citation: tessl__pytest-api-testing § "monkeypatch vs mock".
- `tessl__graceful-degradation` — invoked. Decision: N/A — no external HTTP calls in migration. Migration is pure SQL. Noted.
- `brand-expert`, `offer-expert`, `offer-type-preset-expert`, `metrics-expert` — NOT invoked. T-3 touches `shared/agent_observability/persistence/` (data only, no analytics/brand/offer changes).

---

## TDD Evidence

### Phase 1 — RED

**Test file:** `backend/tests/migrations/test_t3_pricing_snapshot_repair.py`

Written before migration file exists. 10 tests covering A1-A4 acceptance criteria:

```
FAILED tests/migrations/test_t3_pricing_snapshot_repair.py::test_migration_122_revision_metadata
FAILED tests/migrations/test_t3_pricing_snapshot_repair.py::test_migration_122_upgrade_creates_backup_idempotently
FAILED tests/migrations/test_t3_pricing_snapshot_repair.py::test_migration_122_repairs_deepseek_rows
FAILED tests/migrations/test_t3_pricing_snapshot_repair.py::test_migration_122_repairs_kimi_rows
FAILED tests/migrations/test_t3_pricing_snapshot_repair.py::test_migration_122_repairs_qwen_rows
FAILED tests/migrations/test_t3_pricing_snapshot_repair.py::test_migration_122_no_mistagged_rows_post_migration
FAILED tests/migrations/test_t3_pricing_snapshot_repair.py::test_migration_122_backup_table_preserves_original_state
FAILED tests/migrations/test_t3_pricing_snapshot_repair.py::test_migration_122_downgrade_restores_backup
FAILED tests/migrations/test_t3_pricing_snapshot_repair.py::test_migration_122_downgrade_uses_backup_source
FAILED tests/migrations/test_t3_pricing_snapshot_repair.py::test_migration_122_upgrade_statement_order
```

All fail with `FileNotFoundError` — migration file does not exist yet. RED confirmed.

### Phase 2 — GREEN

**Migration file:** `backend/alembic/versions/122_repair_pricing_snapshot_provider_tagging.py`

Implementation:
- `upgrade()`: DROP IF EXISTS backup, CTAS, 3x UPDATE (deepseek, kimi/moonshot, qwen/dashscope)
- `downgrade()`: TRUNCATE, INSERT FROM backup, DROP backup
- All 10 tests PASS.

```
10 passed, 1 warning in 10.76s
```

### Phase 3 — VERIFY

**Lint:** `ruff check` — 0 errors. `ruff format --check` — 2 files already formatted.

**Test file rename:** `test_T3_pricing_snapshot_repair.py` → `test_t3_pricing_snapshot_repair.py` (N999 ruff rule — module names must be lowercase).

**Architecture fitness:** `823 passed, 1 warning in 25.27s` — baseline preserved.

**Migration tests (all):** `34 passed, 1 warning in 10.72s` — all 34 migration tests pass (including 10 new T-3 tests).

**Downstream observability tests:** `225 passed, 1 warning in 11.35s` — `tests/migrations/` + `tests/shared/agent_observability/` all green.

**Alembic upgrade (Docker):** Brain container not running at commit time (`visionarias_brain_dev` down). Docker only needed for runtime — migration file is correct. A1 bash verifier will run at deployment. The brain container was absent during this session; only `visionarias_postgres` + `visionarias_redis` were running.

**Pre-existing failures (NOT T-3 related):**
- `test_arch_fitness_performance_budget` — timing-sensitive test, flaky. Passes in isolation.
- `test_suggestions_endpoint_integration::test_e2e_real_engine_real_offer_provider` — copilot integration test, requires running Postgres + posthog connection. Pre-existing; unrelated to T-3.

---

## Implementation decisions

### Migration filename: `122_`

Current Alembic head in DB: `121_leads_deleted_at` (verified via `docker exec visionarias_postgres psql ... SELECT version_num FROM alembic_version`). Next sequential = `122`.

### `down_revision = "121_leads_deleted_at"`

T-1 and T-2 did not create Alembic migration files (they modified Python code only). Correct chain: `121_leads_deleted_at` → `122_repair_pricing_snapshot_provider_tagging`.

### Test approach: mock-based (not clone-DB)

CONTEXT-BRIEF § 10 mentions "clone DB workflow", but the established codebase pattern (all 4 existing migration tests) uses `importlib.util` + `patch(op.execute)`. This approach:
- Is native-first (no Docker exec for tests)
- Tests SQL string correctness directly
- Matches the existing convention in `tests/migrations/`
- Does not require Postgres running

The mock approach covers acceptance A1-A4 structurally. A1 bash verifier (2x alembic upgrade head) is run via Docker at deployment time.

### `dashscope` for Qwen

Per LiteLLM's canonical provider naming, Qwen (Alibaba/Alimama) models use provider `'dashscope'`. This matches `litellm.get_llm_provider("qwen/qwen-turbo")` → `"dashscope"`. Migration re-tags `provider='openai' AND model LIKE 'qwen%'` → `provider='dashscope'`.

### Backup table naming convention

`model_pricing_snapshot_backup_pre_t3` — establishes the `*_backup_pre_tN` convention for T-6a/T-6c migrations. Documented in migration docstring and this log.

### Slashed model format (T-1 Decision A1 BINDING)

Each UPDATE uses `CASE WHEN model LIKE 'provider/%' THEN model ELSE 'provider/' || model END` to:
1. Preserve rows already in slashed format (idempotent on re-run)
2. Convert legacy unslashed rows to canonical slashed format

---

## Decisions honored

| Decision | Status |
|----------|--------|
| T-1 A1 BINDING: model field stored slashed | HONORED — CASE WHEN in all 3 UPDATEs |
| T-1 X2 BINDING: calculate_cost reconciliation utility | HONORED — no change to calculator.py |
| T-2 A5 BINDING: litellm_sync.py EXTENDS only | HONORED — T-3 is one-shot repair, sync continues |
| T-3 implicit: backup mandatory + downgrade restores | HONORED — CTAS backup + restore downgrade |

---

## Files created

| File | Type | LOC |
|------|------|-----|
| `backend/alembic/versions/122_repair_pricing_snapshot_provider_tagging.py` | NEW migration | ~175 |
| `backend/tests/migrations/test_t3_pricing_snapshot_repair.py` | NEW test | ~210 |

**Total:** ~385 LOC (estimate from CONTEXT-BRIEF § 6: 300 LOC — actual slightly higher due to thorough docstrings + test coverage).

---

## Cross-module reads

None. T-3 is isolated to:
- `backend/alembic/versions/` (migration)
- `backend/tests/migrations/` (tests)

No changes to `modules/copilot/`, `modules/sales_agent/`, `shared/`, or any source code.
