# Tasks

- [ ] Task 1: Refactor `src/shared` Kernel
  - [ ] SubTask 1.1: Flatten `src/shared/utils/utils/utils` to `src/shared/utils`.
  - [ ] SubTask 1.2: Move `src/shared/core/agents/onboarding` to `src/modules/onboarding/application/agents`.
  - [ ] SubTask 1.3: Move `src/shared/core/agents/sales` to `src/modules/sales/application/agents`.
  - [ ] SubTask 1.4: Move `src/shared/core/agents/web_extractor` to `src/modules/sales/application/agents` (if appropriate, or keep as shared tool if generic).
  - [ ] SubTask 1.5: Move `src/shared/core/agents/orchestrator` to `src/modules/iam/application/agents` (if user-centric) or create `src/modules/orchestrator` if generic. (Decision: Move to `src/modules/onboarding` if it's the main entry or keep in shared if truly global. Given it's "Orchestrator", let's keep it in `shared/application/orchestrator` for now if it's generic, but the goal is to empty `core/agents`).

- [ ] Task 2: Refactor `src/domain` Root Directory
  - [ ] SubTask 2.1: Move `src/domain/brand_schema.py` to `src/modules/marketing/domain/brand_schema.py` (or `src/modules/iam/domain` if strictly tenant config).
  - [ ] SubTask 2.2: Move `src/domain/lead_enums.py` to `src/modules/sales/domain/lead_enums.py`.
  - [ ] SubTask 2.3: Move `src/domain/offer_enums.py` to `src/modules/content/domain/offer_enums.py` (verify if duplicate exists).
  - [ ] SubTask 2.4: Move `src/domain/schema.py` to `src/shared/domain/schema.py`.
  - [ ] SubTask 2.5: Delete `src/domain` directory.

- [ ] Task 3: Refactor `src/application` Root Directory
  - [ ] SubTask 3.1: Move `src/application/tools/research.py` to `src/modules/onboarding/application/tools/research.py` (or where it's used).
  - [ ] SubTask 3.2: Delete `src/application` directory.

- [ ] Task 4: Refactor `src/api` Root Directory (Part 1: Communication Module)
  - [ ] SubTask 4.1: Move `src/api/routers/calendar.py` and `src/api/dto/calendar.py` to `src/modules/communication/api/`.
  - [ ] SubTask 4.2: Move `src/api/routers/gmail.py` and `src/api/dto/gmail.py` to `src/modules/communication/api/`.
  - [ ] SubTask 4.3: Move `src/api/routers/event_types.py` (if related to calendar) to `src/modules/communication/api/`.

- [ ] Task 5: Refactor `src/api` Root Directory (Part 2: Content Module)
  - [ ] SubTask 5.1: Move `src/api/routers/avatars.py` and `src/api/dto/avatars.py` to `src/modules/content/api/`.
  - [ ] SubTask 5.2: Move `src/api/routers/definitions.py` to `src/modules/content/api/` (Offer Studio definitions).
  - [ ] SubTask 5.3: Move `src/api/dto/offer_gallery.py`, `src/api/dto/landing.py`, `src/api/dto/products.py`, `src/api/dto/public_links.py` to `src/modules/content/api/dto/` (if not already there).

- [ ] Task 6: Refactor `src/api` Root Directory (Part 3: IAM/Marketing/Tools)
  - [ ] SubTask 6.1: Move `src/api/routers/users.py` and `src/api/dto/users.py` to `src/modules/iam/api/`.
  - [ ] SubTask 6.2: Move `src/api/routers/tools.py` and `src/api/dto/tools.py` to `src/modules/marketing/api/brand_extraction.py` (or split based on function).
  - [ ] SubTask 6.3: Move `src/api/dto/cdp.py` to `src/modules/marketing/api/dto/` (if not already there).

- [ ] Task 7: Update Entry Point and Final Cleanup
  - [ ] SubTask 7.1: Update `src/main.py` imports to reflect all moved files.
  - [ ] SubTask 7.2: Delete `src/api` directory.
  - [ ] SubTask 7.3: Verify no other files remain in root `src` (except `main.py`, `config.py`).
  - [ ] SubTask 7.4: Run linting (`ruff check backend/src --fix`) to resolve import errors.

# Task Dependencies
- [Task 7] depends on [Task 1], [Task 2], [Task 3], [Task 4], [Task 5], [Task 6].
