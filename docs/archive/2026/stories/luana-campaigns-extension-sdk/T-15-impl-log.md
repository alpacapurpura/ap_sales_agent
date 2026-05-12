# T-15 Implementation Log — apps/test-brand smoke tests (10 scenarios)

**Story:** luana-campaigns-extension-sdk
**Batch:** E
**Date:** 2026-05-12
**Builder:** builder-backend Sonnet

## Summary

Wrote `apps/test-brand/tests/test_sdk_smoke.py` with 10 smoke scenarios covering
D1-D3 (dispatch dispatch graceful) + C1-C5 (cross-cutting policies) + E1 (BrandContext
frozen + no PII). All 10 GREEN.

## File created

- `apps/test-brand/tests/test_sdk_smoke.py` — 10 scenarios

## Scenarios implemented

| Test | Validator | Result |
|---|---|---|
| D1 `test_lifespan_registers_all_18_eps` | V-F-test-brand-1 | GREEN |
| D2 `test_ep1_to_ep5_executable` | V-F-sdk-2 | GREEN |
| D3 `test_ep6_to_ep18_not_implemented_graceful` | V-F-sdk-3 | GREEN |
| C1 `test_duplicate_registration_raises` | V-F-sdk-4 CC-4 | GREEN |
| C2 `test_namespace_violation_raises` | V-AG-namespace-allowlist | GREEN |
| C3 `test_post_startup_registration_raises` | CC-3 | GREEN |
| C4 `test_no_unregister_method_exists` | V-AG-cc5-no-unregister | GREEN |
| C5a `test_override_mode_restricted_to_ep17_ep18` | CC-2 | GREEN |
| C5b `test_override_mode_permitted_on_ep17_ep18` | CC-2 | GREEN |
| E1 `test_brand_context_frozen_no_pii` | V-F-sdk-5 | GREEN |

## Test results

```
10 passed, 0 failed
```

## Invariants confirmed

- **V-NF-1:** zero AISALESHT touch
- **V-F-sdk-2:** EP-1..EP-5 return typed results
- **V-F-sdk-3:** EP-6..EP-18 dispatch raises NotImplementedError with descriptive message
- **V-AG-namespace-allowlist:** bare names rejected, unknown brand prefix rejected
- **CC-5:** no `unregister_*` method found via `getattr(registry, 'unregister_field_override')`

## luana-platform commit

`3df55df` — `test(apps/test-brand): smoke pack 10 scenarios D1-D3 + C1-C5 + frozen ctx GREEN`

## Skills Consulted

- `backend-expert`: TDD RED first per layer rule
- `tessl__pytest-api-testing`: parametrize edge cases, error flow tests
