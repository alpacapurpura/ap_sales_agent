# Tasks

- [x] Task 1: Generate Mock Offers
    - [x] Update `frontend/src/features/offer-studio/api/mock-data.ts`.
    - [x] Create helper function or manual list to generate 23+ offers.
    - [x] Ensure each offer has valid `id`, `name`, `type`, `status`, `value_level`, `delivery_model` and `pricing`.
    - [x] Export `MOCK_OFFERS` array.

- [x] Task 2: Enable Mock Mode
    - [x] Modify `frontend/src/features/offer-studio/api/index.ts`.
    - [x] Set `USE_MOCK_DATA = true`.
    - [x] Verify `listOffers` returns `MOCK_OFFERS`.
    - [x] Verify `getOffer` finds the correct offer from `MOCK_OFFERS`.

- [x] Task 3: Verification
    - [x] Open Offer Studio in the browser (User Verification).
    - [x] Check if all offer types are visible in the dashboard.
