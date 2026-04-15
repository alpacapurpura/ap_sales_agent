---
globs: "{backend/src/modules/analytics/**/*.py,frontend/src/features/growth-studio/**/*.{ts,tsx}}"
description: 4-layer data verification protocol for Growth Studio pipeline
---

# Data Reliability Verification — Always Verify, Never Guess

Non-negotiable workflow rule for any task touching Growth Studio data pipeline.
4-Layer Verification Protocol = only way to confirm displayed values correct.

## The 4 Layers

| Layer | What it verifies | Command | When to run |
|-------|-----------------|---------|-------------|
| 0: ETL Execution | Fresh data in DB | `make verify-etl provider={name}` | Before Layers 1-3 when data stale |
| 1: Source Probe | External API values == official_metrics | `make verify-probe-{provider}` | After touching providers or ETL pipeline |
| 2: Pipeline Integrity | official_metrics values == stage service DTOs | `make verify-pipeline` | After touching stage services, DTOs, or API routes |
| 3: UI Fidelity | Backend API response == UI display | `make verify-ui` | After touching frontend components, hooks, or formatters |

## Trigger Matrix

| You modified... | Run these layers |
|----------------|-----------------|
| `backend/src/modules/analytics/infrastructure/providers/*.py` | 0 + 1 + 2 |
| `backend/src/modules/analytics/infrastructure/etl/*.py` | 0 + 1 + 2 |
| `backend/src/modules/analytics/application/services/stage_services/*.py` | 2 |
| `backend/src/modules/analytics/application/dto/*.py` | 2 + 3 |
| `backend/src/modules/analytics/api/metrics.py` | 2 + 3 |
| `backend/src/modules/analytics/api/campaigns.py` | 2 + 3 |
| `backend/src/modules/analytics/api/email_metrics.py` | 2 + 3 |
| `backend/src/modules/analytics/application/services/channel_registry.py` | 2 |
| `frontend/src/features/growth-studio/components/**` | 3 |
| `frontend/src/features/growth-studio/api/*.ts` | 3 |
| `frontend/src/features/growth-studio/hooks/*.ts` | 3 |
| `frontend/src/lib/format-money.ts` | 3 |
| `frontend/src/lib/format-date.ts` | 3 |

## The 5-step verification workflow

1. **Before modifying:** Run relevant layers, capture baseline
2. **Make the change**
3. **After modifying:** Run same layers, verify no regression
4. **If any layer fails:** Investigate and fix — no skip, no suppress
5. **Commit:** Note which verification layers passed

## Quick commands

```bash
make verify-meta              # Full 4-layer chain, local
make verify-meta env=prod     # Full 4-layer chain, production
make verify-pipeline          # Layer 2 only (pytest -m verify)
make verify-ui                # Layer 3 only (Playwright --project=verify)
make verify-probe-meta days=7 # Layer 1 only (Meta API vs DB)
make verify-etl provider=meta # Layer 0 only (trigger extraction)
```

## Adding a new provider

Follow Meta pilot:

1. Create `backend/scripts/verify/probes/{provider}_probe.py` (copy meta_probe.py as template)
2. Define `EXPECTED_MAPPINGS` for all API fields provider extracts — independent of ETL provider code
3. Create `backend/tests/verification/test_pipeline_{provider}.py` with `@pytest.mark.verify`
4. Create `frontend/e2e/specs/verify/{provider}-fidelity.verify.spec.ts`
5. Add `verify-probe-{provider}` and `verify-{provider}` targets to Makefile
6. Update `verify-all` to include new provider

## Anti-patterns to refuse

- Modify provider without running Layer 1 (`make verify-probe-{provider}`)
- Modify stage service or DTO without running Layer 2 (`make verify-pipeline`)
- Modify dashboard component without running Layer 3 (`make verify-ui`)
- Skip verification because "small change" — no small changes to data pipeline
- Use mocked data in verify tests — exist for real data verification only
- Commit Growth Studio changes without noting which verification layers passed
- Add `@pytest.mark.skip` or `test.skip()` to verification tests to make CI pass

## Relationship to other rules

- **ETL Extraction Contract** (`.claude/rules/etl-extraction-contract.md`): Governs what ETL extracts. This rule governs verifying extraction correct.
- **Analytics Metrics** (`.claude/rules/analytics-metrics.md`): Governs runtime pipeline architecture. This rule governs verifying pipeline produces correct output.
- **Currency Handling** (`.claude/rules/currency-handling.md`): Governs currency handling. Layers 2 and 3 verify currency flows correctly.