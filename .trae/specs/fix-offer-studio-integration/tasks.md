# Tasks

- [x] Task 1: Create Mock Data & Verify Frontend
  - [x] SubTask 1.1: Create `frontend/src/features/offer-studio/data/mock-offer.json` with comprehensive data covering all sections.
  - [x] SubTask 1.2: Temporarily modify `useOffer` hook to load data from this JSON to verify UI components (excluding Editor).
  - [x] SubTask 1.3: Verify "Offer Studio" dashboard/list view renders correctly.

- [x] Task 2: Fix Frontend API Client & Adapter
  - [x] SubTask 2.1: Update `frontend/src/features/offer-studio/api/adapter.ts` to map `pricing` <-> `pricing_options` and `name` <-> `public_name` correctly.
  - [x] SubTask 2.2: Update `frontend/src/features/offer-studio/api/index.ts` to use `PATCH` for `saveSection` and correct endpoint paths.
  - [x] SubTask 2.3: Ensure `saveSection` payloads match Backend Pydantic models (e.g., nesting `pricing_options` inside object).

- [x] Task 3: Backend Verification & Integration
  - [x] SubTask 3.1: Revert `useOffer` to use real API.
  - [x] SubTask 3.2: Create a test script (or use `curl`) to verify Backend `PATCH` endpoints accept the corrected payloads.
  - [x] SubTask 3.3: Manually test the full flow: Create Offer -> Update Sections -> Verify Persistence in DB.
