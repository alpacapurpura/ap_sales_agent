# Tasks

- [x] Task 1: Create reproduction script `backend/src/modules/brand/tests/repro_issue.py`
  - [x] SubTask 1.1: Create a script that mocks the DB session and calls `get_brand_settings` logic with `None` data to confirm the crash.
  - [x] SubTask 1.2: Run the script to confirm failure.

- [x] Task 2: Fix Backend `get_brand_settings` in `backend/src/modules/brand/api/router.py`
  - [x] SubTask 2.1: Implement safe retrieval: `brand_data = config.get("brand_settings") or {}`.
  - [x] SubTask 2.2: Add try-except block around `BrandSettings` instantiation to catch validation errors and log them, returning default settings if needed.

- [ ] Task 3: Improve Frontend Error Handling
  - [x] SubTask 3.1: Update `frontend/src/features/brand/hooks/useBrandSettings.ts` to return `error` from `useQuery`.
  - [x] SubTask 3.2: Update `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-settings/page.tsx` to display `error.message` if available.

- [ ] Task 4: Verify Fix
  - [x] SubTask 4.1: Run the reproduction script again to confirm it passes.
  - [x] SubTask 4.2: (Manual) Verify via browser if the page loads.
