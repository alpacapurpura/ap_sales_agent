# Strict Senior-Level Audit & Refactor: Offer Module

## Why
The `offer` module currently exhibits technical debt including dead code, potential data loss (unmapped fields), architectural violations (logic in API layer), and loose typing. To achieve a "Senior Level" standard, we must enforce strict Domain-Driven Design (DDD) principles, ensure complete data integrity, and optimize maintainability.

## What Changes

### 1. Cleanup & Hygiene
- **DELETE** `backend/src/modules/offer/infrastructure/repository.py`: This file is unused and references non-existent models. It creates confusion.

### 2. Domain Integrity (`domain/offer.py`)
- **ADD** `marketing_pain_points: List[str] = []`
- **ADD** `marketing_desires: List[str] = []`
- **ADD** `metadata_info: Dict[str, Any] = {}`
- **REASON**: These fields exist in the Database Model (`ProductModel`) and DTOs but are missing from the Domain Entity, causing data loss during `Repo -> Domain` conversion.

### 3. Application Layer Logic (`application/offer_service.py`)
- **ADD** `patch_offer(offer_id: UUID, update_data: Dict[str, Any]) -> Offer` method.
- **LOGIC**: This method will:
  1. Fetch the offer.
  2. Verify Tenant ownership.
  3. Perform a deep merge of `update_data` into the Offer entity.
  4. Call repository to save.
- **REASON**: Encapsulates business logic. The API layer currently handles "atomic updates" by manually manipulating dictionaries and calling `update`, which is an anti-pattern (Anemic Domain).

### 4. Infrastructure Optimization (`infrastructure/repositories/offer_repository.py`)
- **REFACTOR** `_to_domain`: Map the new fields (`marketing_pain_points`, etc.) from Model to Entity.
- **REFACTOR** `_to_model`: Map the new fields from Entity to Model.
- **REFACTOR** `update`: Replace the 40+ lines of manual attribute assignment with a robust, dynamic approach (iterating over the `_to_model` result). This reduces code lines and prevents future bugs where a developer adds a field but forgets to update this method.

### 5. API Layer Refactoring (`api/products.py`)
- **REMOVE** `_atomic_update` helper function.
- **UPDATE** All `PATCH` endpoints (`update_identity`, `update_strategy`, etc.) to call `service.patch_offer`.
- **REASON**: Controllers should be thin. Logic belongs in the Service.

### 6. DTO Synchronization (`api/dto/products.py`)
- **VERIFY**: Ensure `ProductResponse` and `ProductUpdate` include `marketing_pain_points`, `marketing_desires`, and `metadata_info`. (Audit confirms they are present/optional, but need to ensure `ProductResponse` correctly maps them from the Domain Entity).

## Impact
- **Risk**: Low. Mostly internal refactoring.
- **Benefit**: 
  - Prevents silent data loss.
  - Reduces boilerplate code by ~50 lines.
  - Centralizes update logic for better testing and security.

## MODIFIED Requirements
### Requirement: Persistence
The system MUST persist `marketing_pain_points` and `metadata_info` correctly through the `OfferRepository`.

### Requirement: Update Logic
Partial updates MUST be handled by the `OfferService`, ensuring all business rules apply before persistence.
