# T-2 Implementation Log — Migration test + arch fitness gate

**Story:** eval-foundation-simulator-homologation
**Ticket:** T-2
**Owner:** claude-sonnet (builder-backend)
**Started:** 2026-05-07

## Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `backend-expert` | Mandatory: runtime-quality-checklist, migration test patterns, arch fitness gate patterns | Pattern from `test_119_llm_eval_gate.py` for migration tests (importlib.util loading + op.execute patch). Architecture test pattern from `test_sales_agent_observability_invariants.py`. Confirmed tests/ exempt from mypy strict. |
| `tessl__pytest-api-testing` | Mandatory: fixture patterns, conftest scope, no-import-fixtures | Pure file-reading tests (no DB fixtures needed). Used class-based test organization. |
| `brand-expert`, `offer-expert`, `metrics-expert` | Invoked per step_0 skill list | Not relevant to this test-infrastructure ticket. No domain changes. |

## Step 0 Anti-duplication grep (mandatory)

```bash
grep -rn "test_eval_simulator\|test_extend_eval_simulator" backend/tests/ 2>/dev/null
# → cero resultados. No duplicate test files found.
```

## Step 0.5 Default-flip detection

No `core/config.py` touched. Not applicable.

## T-1 Pre-requisite verification

```bash
find backend/alembic/versions -name "125_*"
# → 125_add_eval_simulator_observability_tables.py ✓

grep "eval_simulator" backend/src/shared/infrastructure/agent_observability_bootstrap.py
# → import present ✓

python -c "from src.shared.infrastructure import agent_observability_bootstrap; from src.shared.agent_observability.registry import get_spec; assert get_spec('eval_simulator') is not None"
# → PASS ✓
```

## Implementation

### test_extend_eval_simulator_observability.py

Pattern: `test_119_llm_eval_gate.py` (importlib.util + patch(module.op, "execute")).

Test classes implemented:
- `TestRevisionMetadata` — revision + down_revision chain
- `TestUpgradeCreatesTables` — 3 tables created with IF NOT EXISTS
- `TestUpgradeCreatesIndexes` — 7 indexes created with IF NOT EXISTS
- `TestUpgradeSchemaShape` — key DDL invariants (tenant_id NOT NULL, eval_metadata JSONB NOT NULL, nullable lead_id, TIMESTAMPTZ)
- `TestUpgradeIdempotency` — double upgrade does not raise, IF NOT EXISTS confirmed
- `TestDowngrade` — 3 DROP TABLE IF EXISTS CASCADE
- `TestSpecRegistration` — bootstrap import registers spec (in-memory, no DB)

**Correction during iteration:** Initial count was 6 indexes, actual migration has 7 (missed `ix_eval_synthetic_tenants_slug` on the lookup table). Fixed in test.

### test_eval_simulator_observability_invariants.py

Architecture fitness gate with 7 test classes (ratchet pattern — no allowlists):

- `TestSpecRegistration` — 5 tests: spec.py exists, bootstrap imports eval_simulator, spec calls register_agent_observability, get_spec returns spec at runtime, table names match migration
- `TestOrmModelsExist` — 6 tests: all 3 model files exist, __tablename__ values match migration
- `TestEvalMetadataJsonbColumn` — 4 tests: both tables have eval_metadata JSONB NOT NULL in ORM + migration DDL
- `TestTenantIsolation` — 5 tests: tenant_id present in all 3 models + migration DDL NOT NULL
- `TestTimestampColumnsTimezoneAware` — 5 tests: DateTime(timezone=True) in all ORM models + TIMESTAMPTZ in migration
- `TestCampaignParityFields` — 14 tests: parametrize over 10 required fields + litellm_call_id/span_id, reasoning_tokens, error_type
- `TestR5SchemaMirrorException` — 4 tests: models don't import from domain/application, import Base from shared.domain.base_entity, spec imports LlmCallModel

## Iteration log

| Iter | Action | Result |
|---|---|---|
| 1 | Write both test files | ruff: 9 noqa F401 warnings |
| 2 | ruff --fix (auto-remove unused noqa) | lint clean |
| 3 | ruff format | format clean |
| 4 | pytest both files combined (random ordering) | 79/80 pass, 1 ERROR (Redis timeout — pre-existing conftest session issue, not test-specific), 1 FAIL (index count 6→7) |
| 5 | Fix index count 6→7, add test for synthetic_tenants_slug index | — |
| 6 | pytest arch test in isolation | 43/43 PASS ✓ |
| 7 | pytest migration test in isolation | 38/38 PASS ✓ |
| 8 | pytest both files together (no random) | 81/81 PASS ✓ |
| 9 | Full architecture suite | 880/881 (1 pre-existing flaky performance budget, not caused by T-2) |

## Pre-existing issue documented

`test_arch_fitness_performance_budget` in `test_no_legacy_eventbus_mock_when_outbox_on.py`:
- AST walk 2.108s vs 2.0s budget (832 files)
- This is a timing-sensitive test; 2 new test files add ~2ms (negligible)
- Failed pre-T-2 as well (system load dependent)
- NOT a regression from T-2

`TestEvalMetadataJsonbColumn::test_llm_call_model_has_eval_metadata_column ERROR` (random ordering run):
- Redis connection timeout in background thread `run_server` started by another test
- Pre-existing infrastructure issue in test suite
- Test itself PASSES in isolation (43/43 PASS)
- This is a session-level ordering artifact from pytest-randomly
