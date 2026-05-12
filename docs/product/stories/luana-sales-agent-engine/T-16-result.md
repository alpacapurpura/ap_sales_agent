# T-16 result

**Status:** GREEN
**Commit:** `6625646` (luana-platform main)
**Validator:** V-F-py-3
**Date:** 2026-05-12

## Summary

Replaced `NotImplementedError` stub in `luana-core-connections/api/
dependencies/__init__.py` with real `ChatOrchestrator` wiring. Stories
4+6 deferral resolved.

## Files Modified

| File | Change |
|---|---|
| `core/luana-core-connections/src/luana_core_connections/api/dependencies/__init__.py` | Stub → real wiring (singleton ChatOrchestrator → MessageHandlerPort) |
| `core/luana-core-connections/tests/conftest.py` | Stub MessageModel removed; real MessageModel imported first |
| `core/luana-core-platform/src/luana_core_platform/infrastructure/models/crm.py` | LeadModel.messages: `foreign_keys` → `back_populates="lead"` matching AISALESHT SSoT |

## Verification

- `core/luana-core-connections/tests/` 218/218 PASS
- Smoke `get_message_handler()` returns `ChatOrchestrator` instance
- AISALESHT untouched (V-NF-4)
