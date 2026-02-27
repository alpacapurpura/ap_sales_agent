# Tasks
- [ ] Task 1: Recreate `Product` model
  - [ ] Create `backend/src/modules/content/infrastructure/models/product.py` with SQLAlchemy model definition.
- [ ] Task 2: Recreate `PromptVersion` model
  - [ ] Create `backend/src/shared/infrastructure/db/models/prompt.py` with SQLAlchemy model definition.
- [ ] Task 3: Fix Imports in `database.py` and `product.py`
  - [ ] Update `backend/src/shared/infrastructure/db/database.py` imports.
  - [ ] Update `backend/src/modules/content/infrastructure/product.py` imports.
- [ ] Task 4: Verify Fix
  - [ ] Restart backend container.
  - [ ] Check logs for successful startup and seeding.

# Task Dependencies
- Task 3 depends on Task 1 and Task 2.
- Task 4 depends on Task 3.
