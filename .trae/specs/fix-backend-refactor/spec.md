# Fix Backend Refactor Regression Spec

## Why
The backend is failing to start due to `ModuleNotFoundError: No module named 'src.infrastructure'`. This is a regression from a recent refactor where `Product` and `PromptVersion` models were either deleted or moved without updating imports. The system cannot initialize the database or API.

## What Changes
- **Recreate Missing Models**:
  - `Product` model in `src/modules/content/infrastructure/models/product.py`.
  - `PromptVersion` model in `src/shared/infrastructure/db/models/prompt.py`.
- **Fix Imports**:
  - Update `src/shared/infrastructure/db/database.py` to import models from their new locations.
  - Update `src/modules/content/infrastructure/product.py` to import `Product` correctly.
- **Ensure Schema Compliance**:
  - Match the schema expected by `database.py` (seeding) and `product.py` (repository).

## Impact
- **Affected Specs**: Backend Initialization, Content Module, Prompt Management.
- **Affected Code**: 
  - `backend/src/shared/infrastructure/db/database.py`
  - `backend/src/modules/content/infrastructure/product.py`
  - New files: `backend/src/modules/content/infrastructure/models/product.py`, `backend/src/shared/infrastructure/db/models/prompt.py`

## ADDED Requirements
### Requirement: Product Model
The system SHALL define a SQLAlchemy model for `Product` in the `content` module.
- Fields: `id`, `name`, `type`, `status`, `pricing`, `dates`, `metadata_info`, `requires_application`, `specific_details`, `tenant_id`.

### Requirement: PromptVersion Model
The system SHALL define a SQLAlchemy model for `PromptVersion` in the `shared` module.
- Fields: `key`, `version`, `content`, `is_active`, `change_reason`, `author_id`, `metadata_info`.

## MODIFIED Requirements
### Requirement: Database Initialization
The `init_db` function SHALL import models from their correct modular locations to ensure tables are created and seeded correctly.
