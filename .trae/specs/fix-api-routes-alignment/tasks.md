# Tasks

- [x] Task 1: Fix Backend Brand Router
  - [x] SubTask 1.1: Edit `backend/src/modules/brand/api/router.py` to change `@router.get("/brand")` to `@router.get("")`.
  - [x] SubTask 1.2: Edit `backend/src/modules/brand/api/router.py` to change `@router.patch("/brand")` to `@router.patch("")`.

- [x] Task 2: Fix Frontend Brand API
  - [x] SubTask 2.1: Edit `frontend/src/features/brand/api/index.ts` to use `/api/v1/brand/settings` instead of `/api/v1/settings/brand`.
  - [x] SubTask 2.2: Verify `frontend/src/lib/api/settings.ts` uses `/api/v1/brand/settings`.

- [x] Task 3: Verification
  - [x] SubTask 3.1: Curl `GET /api/v1/brand/settings` (should return 401 or 200, not 404).
