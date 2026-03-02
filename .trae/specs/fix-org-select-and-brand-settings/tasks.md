# Tasks

- [ ] Task 1: Fix Backend Brand Settings Router
  - [ ] SubTask 1.1: Edit `backend/src/modules/brand/api/router.py` to change `@router.get("/brand")` to `@router.get("")`.
  - [ ] SubTask 1.2: Edit `backend/src/modules/brand/api/router.py` to change `@router.patch("/brand")` to `@router.patch("")`.

- [ ] Task 2: Update Frontend Brand API Client
  - [ ] SubTask 2.1: Edit `frontend/src/features/brand/api/index.ts` to use `${API_URL}/api/v1/brand/settings` for both `getBrandSettings` and `updateBrandSettings`.

- [ ] Task 3: Verification
  - [ ] SubTask 3.1: Verify `GET /api/v1/brand/settings` returns 200 (or 401 if unauth, but not 404).
  - [ ] SubTask 3.2: Verify `GET /api/v1/iam/users/me/tenants` returns 200.
