---
ticket: T-3
title: "Implement BrandContext frozen dataclass — 9 fields per §7.5.2 D3 (TDD)"
story_id: luana-campaigns-extension-sdk
completed_at: 2026-05-12
iteration: 1
commit: 6e01a7b
---

## Files Created

- `core/luana-core-extension-sdk/tests/unit/test_brand_context.py` — 4 RED tests (TDD phase)
- `core/luana-core-extension-sdk/src/luana_core_extension_sdk/brand_context.py` — GREEN implementation

## Implementation

Per 06-tickets.yaml T-3 TDD workflow:

### RED Phase

Wrote 4 failing tests in `tests/unit/test_brand_context.py`:
1. `test_brand_context_frozen` — asserts `__dataclass_params__.frozen is True`
2. `test_brand_context_9_fields` — asserts exactly 9 field names matching §7.5.2 D3
3. `test_brand_context_mutation_raises` — asserts `FrozenInstanceError` on assignment attempt
4. `test_brand_context_no_pii_safe_to_log` — asserts no PII patterns in field names

All 4 failed with `ImportError: cannot import name 'BrandContext'` (brand_context.py did not exist).

### GREEN Phase

Created `src/luana_core_extension_sdk/brand_context.py`:
- `@dataclass(frozen=True, slots=True, kw_only=True)` per §1.4 canonical pattern
- 9 fields verbatim per §7.5.2 D3:
  - `tenant_id: UUID`
  - `brand_slug: Literal["nicolify", "vitalia", "comunify", "lupulo", "test-brand"]`
  - `plan_tier: str`
  - `locale: str`
  - `feature_flags: dict[str, bool]`
  - `tenant_profile_id: UUID`
  - `vertical_kind: Literal["marketing", "medical", "creator-economy", "gastronomy"]`
  - `compliance_flags: dict[str, bool]`
  - `pii_policy: Literal["standard", "medical", "creator", "gastronomy"]`

## Validators Run

- V-F-sdk-5: 4 tests PASS (frozen + 9 fields + mutation raises + no PII)
- `uv run --package luana-core-extension-sdk ruff check src/` → 0 errors

## Deviations

None. BrandContext 9 fields exactly match §7.5.2 D3. dict fields use `dict[str, bool]` (mutable type annotation is fine — frozen prevents field reassignment, dict contents are caller-controlled per spec).
