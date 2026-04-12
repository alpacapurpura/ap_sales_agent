# Data Reliability Verification — Always Verify, Never Guess

Non-negotiable workflow rule for any task that touches the Growth Studio data pipeline.
The 4-Layer Verification Protocol is the only way to confirm that displayed values are correct.

## The 4 Layers

| Layer | What it verifies | Command | When to run |
|-------|-----------------|---------|-------------|
| 0: ETL Execution | Fresh data in DB | `make verify-etl provider={name}` | Before Layers 1-3 when data may be stale |
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

1. **Before modifying:** Run the relevant layers to capture baseline state
2. **Make the change**
3. **After modifying:** Run the same layers to verify no regression
4. **If any layer fails:** Investigate and fix — do not skip or suppress
5. **Commit:** Note in the commit message which verification layers passed

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

When creating a probe for a new provider, follow the Meta pilot:

1. Create `backend/scripts/verify/probes/{provider}_probe.py` (copy meta_probe.py as template)
2. Define `EXPECTED_MAPPINGS` for all API fields the provider extracts — independent of the ETL provider code
3. Create `backend/tests/verification/test_pipeline_{provider}.py` with `@pytest.mark.verify`
4. Create `frontend/e2e/specs/verify/{provider}-fidelity.verify.spec.ts`
5. Add `verify-probe-{provider}` and `verify-{provider}` targets to Makefile
6. Update `verify-all` to include the new provider

## Anti-patterns to refuse

- Modifying a provider without running Layer 1 (`make verify-probe-{provider}`)
- Modifying a stage service or DTO without running Layer 2 (`make verify-pipeline`)
- Modifying a dashboard component without running Layer 3 (`make verify-ui`)
- Skipping verification because "it is just a small change" — there are no small changes to the data pipeline
- Using mocked data in verify tests — they exist specifically for real data verification
- Committing Growth Studio changes without noting which verification layers passed
- Adding `@pytest.mark.skip` or `test.skip()` to verification tests to make CI pass

## Relationship to other rules

- **ETL Extraction Contract** (`.claude/rules/etl-extraction-contract.md`): Governs what the ETL extracts. This rule governs verifying that the extraction is correct.
- **Analytics Metrics** (`.claude/rules/analytics-metrics.md`): Governs the runtime pipeline architecture. This rule governs verifying that the pipeline produces correct output.
- **Currency Handling** (`.claude/rules/currency-handling.md`): Governs how currency is handled. Layer 2 and 3 verify that currency flows correctly.
