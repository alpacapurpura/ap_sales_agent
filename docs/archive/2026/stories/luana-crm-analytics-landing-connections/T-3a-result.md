---
ticket_id: T-3a
story_id: luana-crm-analytics-landing-connections
state: pushed
phase: BUILD
last_modified: 2026-05-11
owner: builder-backend (Opus 4.7 rescue)
artifact_kind: result
spec_ref: 06-tickets.yaml § T-3a
---

# T-3a — Result

## Verdict

**done (with planned aggregate-test deferral to T-3c per spec line 159)**

Lifted `backend/src/modules/analytics/{api,application,domain}/` + `__init__.py`
to `~/luana-platform/core/luana-core-analytics-engine/`. Brand-agnostic engine
verified. Workspace registered. Pure-domain tests GREEN. Infrastructure-coupled
tests fail-on-collect AS DESIGNED — they wait for T-3b (`infrastructure/`) and
T-3c (`workers/` + aggregate GREEN).

## Commit + push

- **Commit SHA**: `44e04fbc4252742e6660a2a74a31f4480571c649` (short: `44e04fb`)
- **Branch**: `main`
- **Files**: 171 new + 2 modified (`luana-core-platform/pyproject.toml` passlib + `uv.lock`)
- **AISALESHT base**: `ca1ab02f` UNTOUCHED (verified via `git diff ca1ab02f HEAD --name-only` empty)

## Scope delivered (T-3a per 06-tickets.yaml lines 112-161)

Package `core/luana-core-analytics-engine/` populated with:

```
README.md
pyproject.toml                                          # name=luana-core-analytics-engine, v=0.0.1-alpha
docs/                                                   # lifted docs
scripts/                                                # dev utilities (seed_metrics, regen later in T-3b/c)
src/luana_core_analytics_engine/
  __init__.py
  api/                       5 modules                  # campaigns, email_metrics, etl_admin, metrics
  application/
    __init__.py, config, cost_type_mapping
    dto/                     15 DTOs
    services/                28 services + stage_services/ subpkg
  domain/                    13 modules                 # catalog, resolver, ports, enums, models, etc
tests/
  conftest.py                                           # JSONB+UUID patch at module-load (mirror AISALESHT)
  test_*.py                  ~75 files / 920 tests collected
```

Workspace root membership confirmed in `~/luana-platform/pyproject.toml [tool.uv.workspace] members`
(was committed in `2cac18d`). `uv sync` resolves clean.

## Tests outcome

| Scope | Result | Notes |
|---|---|---|
| Collection (920 tests) | 18 file-level ERROR | All ERROR files reference `luana_core_analytics_engine.infrastructure.*` — UNAVAILABLE until T-3b. Per spec line 159 this is acceptable. |
| Pure domain smoke (`test_metric_resolver_supplemental.py + test_metric_catalog.py`) | **31 passed** | Domain layer functional. |
| Mixed smoke (5 files, domain + period_pipeline) | **43 passed / 18 failed** | Failures isolated to `test_period_pipeline.py` (infrastructure-dependent — T-3b territory). |
| Aggregate GREEN (`pytest core/luana-core-analytics-engine/tests/ -x -q`) | DEFERRED to T-3c | Per spec line 159: "Tests may NOT all be GREEN yet (infrastructure missing). DOCUMENT count + which tests fail. Defer GREEN check to T-3c." |
| Aggregate cross-package (`pytest core/`) | DEFERRED to T-3c | Will use Makefile-driven per-package strategy per 05-guidelines.md §1.5 + 03-arch.md §10.2. |

## Brand-agnostic verification (per 05-guidelines.md §1.7)

```bash
cd ~/luana-platform/core/luana-core-analytics-engine/src
grep -rEn 'if\s+brand\s*==|if\s+tenant\.brand\s*==|brand\s*==\s*"(nicolify|vitalia|comunify|lupulo)"' luana_core_analytics_engine/
# → 0 hits (OK)

grep -rEn '(API_KEY|SECRET|TOKEN)\s*=\s*"...{8,}"' luana_core_analytics_engine/
# → 0 hits (OK)
```

## Cross-scope leak audit

```bash
grep -rn "from src\.\|import src\." src/                        # 0 hits
grep -rn "src\.modules\.copilot\|src\.modules\.sales_agent\|copilot_provider" src/ tests/  # 0 hits
```

Per 05-guidelines.md §3.3, `copilot_provider/` DEFERRED to Story 6 — confirmed not present.

## Validators addressed

- **V-NF-2 (lift fidelity)**: scope correct = api + application + domain only, verbatim names preserved, no logic refactors.
- **V-F-py-2 (analytics tests GREEN)**: DEFERRED to T-3c per spec.

## What unblocks next

- T-3b can proceed (`blocked_by: [T-3a]` ✓)
- T-3b lifts `infrastructure/` → unblocks 18 currently-erroring test files
- T-3c lifts `workers/` + finalizes aggregate GREEN check

## Rescue notes for /pm

Three prior Sonnet attempts cap_reached chasing a phantom "aggregate test isolation" issue that was actually a symptom of over-lifting `infrastructure/` and `workers/` into T-3a (out-of-scope per spec). Removing those directories resolves the apparent isolation issue — those tests need infrastructure (T-3b), not conftest fiddling. Per spec line 159, deferring GREEN to T-3c is explicit and correct.

The pyproject.toml change to `luana-core-platform` (+passlib) is legitimate: `security.py` imports `passlib.context.CryptContext` and was missing from declared deps (Story 2 latent bug, now corrected). Kept in T-3a commit since uv.lock regen is tied to it.

## Last line

t3a-done -> docs/product/stories/luana-crm-analytics-landing-connections/T-3a-result.md
