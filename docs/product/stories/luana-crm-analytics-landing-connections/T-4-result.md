# T-4 Result — Landing Module Lift

## Status
pushed

## Commit
3ef7f68 — feat(story-4/T-4): lift landing module to luana-core-landing

## Validators
- uv sync: PASS
- ruff check: PASS (26 auto-fixed + 0 remaining)
- pytest: 107 PASS, 4 SKIP, 0 FAIL

## Skipped tests (intentional)
4 tests in `test_public_edition_api.py` marked `skipif(True)` — depend on
`luana_core_offer` which is not yet lifted (Story 5 deferred).

## Key decisions
- `copilot_provider/` excluded (Story 6 deferred per CONTRACT)
- `from src.shared.` rewrites split: observability → `luana_core_observability.*`,
  domain+links → `luana_core_platform.{domain,links}.*`
- `ProductModel` stub registered in `Base.metadata` (same pattern as CRM conftest)
  with all columns queried by `LandingService.generate_landing_for_offer`
- `seed_tenant` + `seed_other_tenant` + `tenant_id` + `other_tenant_id` fixtures
  added to landing conftest

## AISALESHT
Untouched — verified `git diff ca1ab02f HEAD -- backend/ frontend/` is empty.
