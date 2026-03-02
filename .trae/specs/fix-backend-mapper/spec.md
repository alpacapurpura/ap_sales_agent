# Backend Mapper Fix Spec

## Why
The backend is throwing a `sqlalchemy.exc.InvalidRequestError` during startup because it cannot resolve the relationship `TenantModel.connections` which points to `src.modules.sales_agent.infrastructure.models.channel_model.ChannelConnectionModel`.
This is caused by the missing `__init__.py` file in `backend/src/modules/sales_agent/infrastructure/models`, preventing it from being treated as a proper Python package for string-based resolution.

## What Changes
- **`backend/src/modules/sales_agent/infrastructure/models/__init__.py`**: Create this empty file.
- **`backend/src/modules/sales_agent/infrastructure/__init__.py`**: Create this empty file (good practice).

## Impact
- **Affected Specs**: None.
- **Affected Code**: Python package structure.
- **Breaking Changes**: None.

## ADDED Requirements
### Requirement: Package Structure
All infrastructure directories SHALL contain `__init__.py` to ensure proper module resolution.

## MODIFIED Requirements
None.
