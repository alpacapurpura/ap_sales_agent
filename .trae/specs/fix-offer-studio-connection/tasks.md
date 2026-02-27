# Tasks
- [x] Task 1: Fix Frontend Adapter: Update `frontendToBackend` in `adapter.ts` to map `pricing_options` to `pricing`.
- [x] Task 2: Implement Landing Page Endpoints: Add `GET`, `POST (generate)`, `PUT`, and `POST (regenerate-block)` endpoints to `backend/src/modules/landing/api/landing.py` specifically for `offer_id`.
  - [x] SubTask 2.1: Add `get_landing_by_offer` to `LandingService`.
  - [x] SubTask 2.2: Add `generate_landing_for_offer` to `LandingService`.
  - [x] SubTask 2.3: Add `update_landing_for_offer` to `LandingService`.
  - [x] SubTask 2.4: Implement API endpoints in `landing.py`.
- [x] Task 3: Verify and Fix Backend DTOs: Ensure `ProductUpdate` in `backend/src/modules/offer/api/dto/products.py` accepts `pricing` list.
