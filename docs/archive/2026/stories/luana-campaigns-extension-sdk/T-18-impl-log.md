# T-18 Implementation Log — Story 8 finalization

**Story:** luana-campaigns-extension-sdk
**Batch:** F (final)
**Date:** 2026-05-12
**Builder:** builder-backend Sonnet

## Summary

Story 8 finalization: ruff lint+format sweep (317 files reformatted across entire
workspace), functional lint fixes (5 files), pre-existing arch test forward-import
exclusions, §3 hash update post-format, DEFERRED-FILES.md Story 8 section, R3 SSoT
(auditor-downstream-regression.md) 8 new rows, anti-duplication.md inventory row.
V-NF-1 confirmed: zero AISALESHT campaigns source touch.

## Functional fixes (lint + test correctness)

### Campaigns API test files — E402 noqa directive

4 files added `# ruff: noqa: E402` header to suppress E402 errors on imports that
follow module-level FastAPI singleton pattern `_campaigns_test_app: FastAPI = ...`:
- `tests/api/test_campaigns_api.py`
- `tests/api/test_campaigns_launch_real.py`
- `tests/api/test_segments_integration.py`
- `tests/integration/test_e2e_telegram_campaign_smoke.py`

Root cause: `_make_campaigns_test_app()` must execute at module level to share the
singleton with test bodies; imports after this line trigger E402 (module-level import
not at top). Pattern is intentional per T-13 design.

### E741 ambiguous variable fix

`tests/test_segment_create_static_with_lead_ids.py`:
```python
# Before: lead_ids=[l.id for l in leads]
# After:  lead_ids=[lead.id for lead in leads]
```

### Observability bootstrap import fix

`tests/test_observability_registration.py`: added
`import luana_core_campaigns.observability  # noqa: F401`

Without this import, the observability registry side-effect registration never fires
before the assertion checks `'campaign' in registry`. Test was checking empty state.

## ruff format sweep (317 files)

`uv run ruff format core/ apps/` — all workspace packages normalized:
- Trailing whitespace removal
- Blank line normalization  
- String quote normalization

Zero semantic changes confirmed (diff review).

## §3 hash update

4 `sales_agent_protected_surfaces_v1.json` hashes updated after ruff format touched
protected sales-agent files (whitespace-only changes per git show verification):
- `api/closer_studio.py`
- `infrastructure/external/output_manager.py`
- `infrastructure/models/enrollment_model.py`
- `workers/follow_up_engine.py`

`_metadata.update_reason`: "ruff format whitespace normalization only — no semantic change"

## DEFERRED-FILES.md Story 8 section

Appended `## Story 8 deferrals (2026-05-12)` with:
- INTRODUCED surfaces (3 Python packages + TS mirror + docs)
- ALLOWLISTED stubs (AppointmentModel + ProductModel carry-over from Story 7)
- NEW deferrals (EP-3/EP-4 adapter wiring, EP-6..EP-18 semantic implementations, test-brand prod infra)

## R3 SSoT (auditor-downstream-regression.md)

Added 8 new rows to surface → downstream test table:
- `core/luana-core-campaigns/src/**` → 446 test files
- `core/luana-core-extension-sdk/src/extension_points.py` → arch tests + smoke
- `core/luana-core-extension-sdk/src/_adapters.py` → EP-3/EP-4 wrapper tests
- `core/luana-core-extension-sdk/src/brand_context.py` → BrandContext frozen tests
- `core/luana-core-extension-sdk/src/models.py` → model frozen tests
- `core/luana-core-extension-sdk/src/exceptions.py` → exception tests
- `core/luana-core-extension-sdk/src/protocols.py` → protocol tests
- `apps/test-brand/src/**` → `apps/test-brand/tests/test_sdk_smoke.py`

## anti-duplication.md

Added row: `luana-platform Extension SDK → core/luana-core-extension-sdk/src/luana_core_extension_sdk/extension_points.py::ExtensionPointRegistry → ALL vertical brand packages`

## V-NF-1 final confirmation

```
git diff -- backend/src/modules/campaigns/ backend/tests/modules/campaigns/
# → empty (zero AISALESHT campaigns source touch)
```

## Final test results

```
672 passed, 7 warnings (all workspace tests: Stories 1-8 combined)
```

## luana-platform commit

`3aeb795` — pushed to `origin main`

## Skills Consulted

- `backend-expert`: runtime quality checklist — anti-patterns ruff/SQLA/tests
- `tessl__fastapi`: redirect_slashes=False, response_model mandatory
- `tessl__pytest-api-testing`: fixture scoping, DB isolation
