# Repair Connections Module Spec

## Why
The `connections` module (formerly `integration`) has been refactored/renamed, but there are leftover references to the old `integration` module name in imports across the codebase. This causes `ImportError` and breaks functionality for WhatsApp, Telegram, Calendar, and other external channels.

## What Changes
- Rename all imports `src.modules.integration` -> `src.modules.connections` in:
    - `backend/src/main.py`
    - `backend/src/modules/connections/api/*.py`
    - `backend/src/modules/scheduling/application/services/availability_service.py`
    - Any other files found via grep.
- Verify that `backend/src/modules/connections` contains all necessary files (confirmed via Glob).

## Impact
- **Affected specs**: None directly, this is a refactor/repair.
- **Affected code**: `main.py`, `connections` module, `scheduling` module.

## ADDED Requirements
None.

## MODIFIED Requirements
### Requirement: Module Import Paths
All references to external channel adapters and services MUST use `src.modules.connections` namespace instead of `src.modules.integration`.

## REMOVED Requirements
None.
