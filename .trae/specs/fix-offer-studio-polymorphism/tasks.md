# Tasks

- [x] Task 1: Create Mock Data Infrastructure
  - [x] SubTask 1.1: Create `frontend/src/features/offer-studio/api/mock-data.ts` with realistic JSON data for different offer types (Program, Service, Product).
  - [x] SubTask 1.2: Add a toggle (env var or config) in `frontend/src/features/offer-studio/api/index.ts` to switch between Real API and Mock Data.
  - [x] SubTask 1.3: Implement `getOffer` and `saveSection` in the mock adapter to simulate persistence in memory (or just success response).

- [x] Task 2: Fix Frontend Section Saving Logic
  - [x] SubTask 2.1: Refactor `getSectionData` in `utils/section-helpers.ts` to clearly separate `specific_details` from top-level fields.
  - [x] SubTask 2.2: Fix `offerApi.saveSection` in `api/index.ts` to prevent double nesting of `specific_details`.
  - [x] SubTask 2.3: Ensure `saveSection` handles mixed updates (top-level fields + specific details) by either calling multiple endpoints or using the generic `saveOffer` fallback if complex.

- [x] Task 3: Backend Schema Alignment (If required)
  - [x] SubTask 3.1: Check if `access_duration` and `requires_application` need to be saved via `PATCH /details`. If so, add them to `OfferDetailsUpdate` in backend `schemas.py` and update `products.py`.
  - [x] SubTask 3.2: Verify `OfferDetailsUpdate` correctly handles the polymorphic union.

- [x] Task 4: Verification
  - [x] SubTask 4.1: Verify "Identity" section saving.
  - [x] SubTask 4.2: Verify "Program Details" section saving (including nested curriculum/schedule if applicable).
  - [x] SubTask 4.3: Verify "Strategy" section saving.
  - [x] SubTask 4.4: Verify "Visuals" section saving.
