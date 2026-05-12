---
ticket: T-7
story_id: luana-campaigns-extension-sdk
title: "ExtensionPointRegistry EP-6..EP-18 backlog signature-only stubs + dispatch raises NotImplementedError + unit tests"
owner: builder-backend (Sonnet)
state: done
completed_at: 2026-05-12
luana_platform_commit: 665331a
---

# T-7 Implementation Log

## Summary

TDD RED→GREEN: wrote 32 unit tests for EP-6..EP-18 backlog signature-only stubs.

**Pre-condition discovery:** The `extension_points.py` already contained all EP-6..EP-18 methods (register + dispatch) from Batch B (T-5 by builder-agentic Opus). T-7 was the test file only — the implementation already existed. Per TDD protocol, wrote tests first, ran them immediately GREEN (implementation was already in place).

## Files created

- `core/luana-core-extension-sdk/tests/unit/test_ep6_through_ep18_signature_only.py` — 32 tests

## Tests written (32 total)

Per scenarios B6-B18 per 06-tickets.yaml:

### Per-EP tests (13 register + 13 dispatch = 26 tests)
- B6: `test_ep6_register_succeeds` + `test_ep6_dispatch_raises_not_implemented`
- B7: `test_ep7_register_succeeds` + `test_ep7_dispatch_raises_not_implemented`
- B8: `test_ep8_register_succeeds` + `test_ep8_dispatch_raises_not_implemented`
- B9: `test_ep9_register_succeeds` + `test_ep9_dispatch_raises_not_implemented`
- B10: `test_ep10_register_succeeds` + `test_ep10_dispatch_raises_not_implemented`
- B11: `test_ep11_register_succeeds` + `test_ep11_dispatch_raises_not_implemented`
- B12: `test_ep12_register_succeeds` + `test_ep12_dispatch_raises_not_implemented`
- B13: `test_ep13_register_succeeds` + `test_ep13_dispatch_raises_not_implemented`
- B14: `test_ep14_register_succeeds` + `test_ep14_dispatch_raises_not_implemented`
- B15: `test_ep15_register_succeeds` + `test_ep15_dispatch_raises_not_implemented`
- B16: `test_ep16_register_succeeds` + `test_ep16_dispatch_raises_not_implemented`
- B17: `test_ep17_register_succeeds` + `test_ep17_dispatch_raises_not_implemented`
- B18: `test_ep18_register_succeeds` + `test_ep18_dispatch_raises_not_implemented`

### Cross-cutting CC tests (6 tests)
- `test_ep17_override_mode_permitted` — EP-17 mode='override' round-trip works
- `test_ep18_override_mode_permitted` — EP-18 mode='override' round-trip works
- `test_all_18_register_methods_exist` — V-F-sdk-1: 18 methods exposed
- `test_namespaced_obligatorio_applies_backlog` — CC-4: bare name raises NamespaceViolationError
- `test_lock_blocks_backlog_register` — CC-3: post-close raises RegistrationClosedError
- `test_mode_override_only_ep17_ep18` — CC-2: EP-6..16 reject override, EP-17+18 accept

## Test results

```
92/92 PASS (was 60 pre-T-7; +32 new tests)
```

## Validators addressed

- V-F-sdk-1: 18 register methods exposed (verified inline + cross-assertion test)
- V-F-sdk-3: EP-6..EP-18 dispatch raises NotImplementedError (26 dispatch tests)
- V-F-sdk-4 (CC-2/CC-3/CC-4): cross-cutting policies verified for backlog EPs

## Implementation note

No `extension_points.py` changes were needed — all EP-6..EP-18 methods were already present from T-5 (builder-agentic Opus Batch B). The `_BACKLOG_EPS` frozenset already covered EP-6..EP-18. The test file was the sole deliverable of T-7.
