# Tasks

- [x] Task 1: Structural Reorganization
  - [x] SubTask 1.1: Create `backend/src/api/dto` directory.
  - [x] SubTask 1.2: Move existing Pydantic request/response models from `api/routers` or `core/domain` (if they are purely DTOs) to `api/dto`.
  - [x] SubTask 1.3: Update imports in routers and services to reflect DTO moves.

- [x] Task 2: Purify Domain Layer
  - [x] SubTask 2.1: Audit `core/domain` for SQLAlchemy (`Base`, `Column`, etc.) imports.
  - [x] SubTask 2.2: Move ORM models to `services/db/models` if they are misplaced.
  - [x] SubTask 2.3: Ensure Domain models are pure Pydantic schemas.

- [x] Task 3: Refactor Routers (Logic Extraction)
  - [x] SubTask 3.1: Refactor `api/routers/users.py`: Move `db.query` logic to `UserService` or `UserRepository`.
  - [x] SubTask 3.2: Refactor `api/routers/telegram.py`: Move `httpx` calls and DB logic to `TelegramService`.
  - [x] SubTask 3.3: Refactor `api/routers/offer_gallery.py`: Extract logic to `OfferService`.

- [x] Task 4: Consolidate WhatsApp Providers
  - [x] SubTask 4.1: Create `BaseEvolutionApi` class with common methods (JID normalization, typing status, send message).
  - [x] SubTask 4.2: Refactor `v1.py` and `v2.py` to inherit from `BaseEvolutionApi`.

- [x] Task 5: Fix Error Handling & Logging
  - [x] SubTask 5.1: Locate `except: pass` blocks in `api/routers/offer_gallery.py` and `telegram.py`.
  - [x] SubTask 5.2: Implement proper error logging using `structlog` and specific exception handling.
  - [x] SubTask 5.3: Fix swallowed exceptions in `core/services/chat_orchestrator.py`.

- [x] Task 6: Security & Tenant Isolation
  - [x] SubTask 6.1: Audit `api/routers/users.py` for `get_my_tenants`. Ensure it doesn't leak data and explicitly documents why it bypasses standard tenant filters (if valid).
  - [x] SubTask 6.2: Verify `_apply_tenant_filter` usage in all Repositories.

- [x] Task 7: Typing & Cleanup
  - [x] SubTask 7.1: Add return type hints to `api/routers/offer_gallery.py` and `users.py`.
  - [x] SubTask 7.2: Remove unused code and commented-out blocks in `ChatOrchestrator`.
  - [x] SubTask 7.3: Resolve TODOs in `chat_orchestrator.py` and `identity.py` (either implement or convert to GitHub Issues if out of scope).

# Task Dependencies
- Task 3 depends on Task 1 and Task 2.
- Task 7 can be done in parallel with others.
