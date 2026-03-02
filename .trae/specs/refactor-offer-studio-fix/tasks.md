# Tasks

- [x] Task 1: Clean Up & Preparation
  - [x] SubTask 1.1: Revert the commented-out filter logic in `offer-studio-dashboard.tsx` to its original (but corrected) state.
  - [x] SubTask 1.2: Remove the defensive "Unknown" label hack in `offer-card.tsx` and replace it with proper type handling.

- [x] Task 2: Robust Adapter Implementation
  - [x] SubTask 2.1: Refactor `backendToFrontend` in `adapter.ts` to strictly validate and normalize Enums (`OfferType`, `OfferStatus`) using a helper function. Log warnings for unknown values instead of passing them through.
  - [x] SubTask 2.2: Ensure `name` vs `public_name` logic is clean and documented.

- [x] Task 3: Create UI Tests (The "Real" Proof)
  - [x] SubTask 3.1: Create `frontend/src/features/offer-studio/tests/fixtures.ts` with the REAL JSON data we captured earlier.
  - [x] SubTask 3.2: Create `frontend/src/features/offer-studio/tests/offer-card.test.tsx` to test that a card renders correctly with that data.
  - [x] SubTask 3.3: Create `frontend/src/features/offer-studio/tests/dashboard-logic.test.tsx` to verify the filtering and grouping logic (that was previously commented out).

- [x] Task 4: Execute & Verify
  - [x] SubTask 4.1: Run the tests. If they fail, fix the code until they pass.
  - [x] SubTask 4.2: Once tests pass, confirm the solution is ready for the user.
