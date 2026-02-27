# Tasks

- [x] Task 1: Create New Backend Structure
  - [x] SubTask 1.1: Create directory `backend/src/modules/content/brand`.
  - [x] SubTask 1.2: Create subdirectories `domain`, `api`, `application`, `infrastructure`.

- [x] Task 2: Move Brand Logic
  - [x] SubTask 2.1: Move `backend/src/modules/marketing/domain/brand_models.py` to `backend/src/modules/content/brand/domain/models.py`. Update imports.
  - [x] SubTask 2.2: Extract `get_brand_settings` and `update_brand_settings` from `backend/src/modules/iam/api/settings.py` to `backend/src/modules/content/brand/api/router.py`.
  - [x] SubTask 2.3: Move `brand_extraction_service.py` and `tools.py` (extraction endpoints) to `backend/src/modules/content/brand/application/` and `api/`.

- [ ] Task 3: Update System Configuration
  - [ ] SubTask 3.1: Update `backend/src/main.py` to mount the new Brand router.
  - [ ] SubTask 3.2: Update all import references in the codebase (grep `src.modules.marketing.domain.brand_models`).

- [ ] Task 4: Organize Content/Offer (Light Refactor)
  - [ ] SubTask 4.1: Create `backend/src/modules/content/offer` and move `products.py` (API) and `offer_schemas.py` (Domain) there if possible without breaking everything. *Prioritize safety: Alias imports if needed.*

- [ ] Task 5: Verify & Fix Visibility
  - [ ] SubTask 5.1: Create a test script `backend/tests/integration/test_brand_refactor.py` to verify the new endpoints work.
  - [ ] SubTask 5.2: Verify the frontend `features/brand/api/index.ts` points to the correct URLs.
  - [ ] SubTask 5.3: Debug the "empty" issue by ensuring the test script returns valid JSON data that the frontend expects.
