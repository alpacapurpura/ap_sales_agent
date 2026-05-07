# T-1 Result — Schema + Loader + Dialect Catalog + Tests baseline

> Story: eval-foundation-tenant-seed-data
> Ticket: T-1 (1 of 4)
> State: pushed
> Date: 2026-05-06

## Summary

T-1 delivered the test infrastructure foundation for the eval tenant seed data story:
- `loader.py`: `load_eval_tenant(archetype_slug: str) → TenantContext` with stable public API
- `TenantContext` `@dataclass(frozen=True)` with `has_lead_magnet` computed property on `offer_ladder`
- `dialect_catalog.yaml`: 15 BCP-47 entries covering all 5 archetype dialect codes
- 4 test files (baseline RED until T-3 creates the 30 seed YAMLs)

## Diff summary

8 new files created under `backend/tests/fixtures/eval/tenants/`:
- `__init__.py` (package marker)
- `conftest.py` (shared fixtures + parametrize hook)
- `loader.py` (load_eval_tenant + TenantContext + OfferLadderContext)
- `dialect_catalog.yaml` (15 BCP-47 entries)
- `test_loader.py` (6 test functions — 1 GREEN, 21 RED baseline)
- `test_realism_smoke.py` (30 parametrized combos, RED baseline)
- `test_schema_alignment.py` (4 test functions — 1 GREEN, 15 SKIPPED)
- `test_dialect_catalog.py` (4 functions — 4 GREEN)

## Validator gates output

| Gate | Result | Notes |
|------|--------|-------|
| A1: Loader function defined + dataclass + has_lead_magnet | PASS | grep confirms all 3 |
| A2: Dialect catalog 15 entries + required fields | PASS | test_dialect_catalog.py 4/4 GREEN |
| A3: Tests baseline running (FAILED or PASSED) | PASS | 22 tests running (21F+1P) |
| A4: Ruff lint + format | PASS | 0 errors, 0 diff |
| A5: Zero src/ changes | PASS | git diff = 0 |
| Architecture fitness | PASS | 827/827 |

## Decisions honored

- AD1: Multi-folder layout per archetype (folder ready for T-3)
- AD2: Reuse Pydantic models — `test_schema_alignment.py` imports brand models read-only
- AD3: TenantContext is `@dataclass(frozen=True)` test infrastructure
- AD4: `dialect_code` in YAML, validated against `dialect_catalog.yaml`, NOT added to runtime model
- AD7: `dialect_catalog.yaml` 15 BCP-47 entries as SSoT
- AD9: Zero src/ changes confirmed
- Q1+Q2: 5 archetype slugs ratified
- Q3: currency=PEN test enforced in test_loader.py
- Q4: In-memory loader (no migrations)
- Q7: Dialect codes per archetype hardcoded in ARCHETYPE_DIALECT_MAP
- Q8: buyer_personas count=3 enforced in test_loader.py

## Commit SHA

(populated post-push — see checkpoint.md)

## Next action

T-2 can now start: PII scanner + pre-commit hook Section 7 + .eval-whitelist
