# Tasks

- [x] Task 1: Setup DTO Structure
  - [x] Create `backend/src/api/dto` directory and `__init__.py`.
  - [x] Create a virtual environment and install `ruff` for verification.

- [x] Task 2: Extract DTOs from Routers
  - [x] Identify Pydantic models in `api/routers/*.py`.
  - [x] Create corresponding files in `api/dto/` (e.g., `avatars.py`, `calendar.py`).
  - [x] Move models to DTO files.
  - [x] Update Router imports to use new DTO locations.

- [x] Task 3: Audit and Clean Domain Layer
  - [x] Scan `backend/src/core/domain` for SQLAlchemy usage (`Base`, `Column`, `sqlalchemy`).
  - [x] Move identified DB models to `backend/src/services/db/models` (Verified: no direct violations found, domain layer is pure Pydantic).
  - [x] Fix imports in `core/domain` and consumers.

- [x] Task 4: Verification and Linting
  - [x] Run `ruff check backend/src` to identify broken imports and style issues.
  - [x] Fix all reported errors (F401, F821, E712, etc.).
  - [x] Verify application startup (optional but recommended).
