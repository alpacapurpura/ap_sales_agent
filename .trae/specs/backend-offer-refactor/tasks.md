# Tasks

- [x] Task 1: Cleanup
  - [x] Delete `backend/src/modules/offer/infrastructure/repository.py`.

- [x] Task 2: Domain Entity Update
  - [x] Update `backend/src/modules/offer/domain/offer.py`:
    - Add `marketing_pain_points: List[str] = []`.
    - Add `marketing_desires: List[str] = []`.
    - Add `metadata_info: Dict[str, Any] = {}`.

- [x] Task 3: Infrastructure Refactor
  - [x] Update `backend/src/modules/offer/infrastructure/repositories/offer_repository.py`:
    - Update `_to_domain` method to map new fields.
    - Update `_to_model` method to map new fields.
    - Refactor `update` method to use dynamic attribute setting from `_to_model` output.

- [x] Task 4: Service Layer Implementation
  - [x] Update `backend/src/modules/offer/application/offer_service.py`:
    - Implement `patch_offer(self, offer_id: UUID, update_data: Dict[str, Any]) -> Offer`.
    - Ensure it handles tenant verification (if not already handled by repo query).

- [x] Task 5: API Layer Refactor
  - [x] Update `backend/src/modules/offer/api/products.py`:
    - Remove `_atomic_update`.
    - Refactor all `PATCH` endpoints to use `service.patch_offer`.
    - Ensure `ProductUpdate` models are converted to `dict(exclude_unset=True)` before passing to service.

- [x] Task 6: AI API Fixes
  - [x] Update `backend/src/modules/offer/api/offer_ai.py`:
    - Add explicit check: `if not tenant_id: raise HTTPException(401, "Tenant ID required")`.
