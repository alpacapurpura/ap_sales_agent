---
globs: "{backend/src/modules/analytics/**/*.py,frontend/src/features/growth-studio/**/*.{ts,tsx}}"
description: 4-layer data verification protocol for Growth Studio pipeline
---

# Data Reliability Verification

Non-negotiable para Growth Studio pipeline changes. 4-Layer Protocol = only way to confirm displayed values correct.

## 4 Layers

| Layer | Verifies | Command | When |
|---|---|---|---|
| 0: ETL Execution | Fresh data en DB | `make verify-etl provider={name}` | Before 1-3 si stale |
| 1: Source Probe | External API == official_metrics | `make verify-probe-{provider}` | After providers/ETL pipeline |
| 2: Pipeline Integrity | official_metrics == stage service DTOs | `make verify-pipeline` | After stage services/DTOs/API routes |
| 3: UI Fidelity | Backend API == UI display | `make verify-ui` | After FE components/hooks/formatters |

## Trigger Matrix

| Modified | Layers |
|---|---|
| `analytics/infrastructure/providers/*.py` | 0 + 1 + 2 |
| `analytics/infrastructure/etl/*.py` | 0 + 1 + 2 |
| `analytics/application/services/stage_services/*.py` | 2 |
| `analytics/application/dto/*.py` | 2 + 3 |
| `analytics/api/metrics.py` | 2 + 3 |
| `analytics/api/campaigns.py` | 2 + 3 |
| `analytics/api/email_metrics.py` | 2 + 3 |
| `analytics/application/services/channel_registry.py` | 2 |
| `frontend/src/features/growth-studio/components/**` | 3 |
| `frontend/src/features/growth-studio/api/*.ts` | 3 |
| `frontend/src/features/growth-studio/hooks/*.ts` | 3 |
| `frontend/src/lib/format-money.ts` | 3 |
| `frontend/src/lib/format-date.ts` | 3 |

## Workflow

1. Before modifying: run layers, capture baseline
2. Make change
3. After: run same layers, verify no regression
4. Fail → investigate+fix. No skip, no suppress.
5. Commit: note layers passed

## Quick commands

```bash
make verify-meta              # Full 4-layer local
make verify-meta env=prod     # Full 4-layer prod
make verify-pipeline          # Layer 2 (pytest -m verify)
make verify-ui                # Layer 3 (Playwright --project=verify)
make verify-probe-meta days=7 # Layer 1 (Meta API vs DB)
make verify-etl provider=meta # Layer 0 (trigger extraction)
```

## Nuevo provider

Follow Meta pilot:
1. `backend/scripts/verify/probes/{provider}_probe.py` (copy meta_probe.py)
2. Define `EXPECTED_MAPPINGS` for every API field — independent of provider code
3. `backend/tests/verification/test_pipeline_{provider}.py` con `@pytest.mark.verify`
4. `frontend/e2e/specs/verify/{provider}-fidelity.verify.spec.ts`
5. Makefile: `verify-probe-{provider}` + `verify-{provider}` targets
6. Update `verify-all`

## Anti-patterns

- Modify provider sin Layer 1
- Modify stage service/DTO sin Layer 2
- Modify dashboard component sin Layer 3
- Skip "small change" — no small data pipeline changes
- Mocked data en verify tests — exist for real data only
- Commit Growth Studio sin noting layers passed
- `@pytest.mark.skip`/`test.skip()` en verify tests para pass CI

## Relación otras rules

- **ETL Contract** (`etl-extraction-contract.md`): gobierna qué extrae. Este = verificar correcto.
- **Analytics Metrics** (`analytics-metrics.md`): gobierna runtime arch. Este = verificar output correcto.
- **Currency** (`currency-handling.md`): gobierna currency. Layers 2+3 verifican currency flow.
