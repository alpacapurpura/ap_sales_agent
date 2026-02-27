# Tasks

- [ ] Task 4.1: Implement Offer Domain
    - [ ] Create `src/modules/offer/domain/offer.py` with `Offer` entity and value objects.
    - [ ] Create `src/modules/offer/domain/details.py` with polymorphic detail classes.
    - [ ] Move/Refactor Enums to `src/modules/offer/domain/enums.py`.

- [ ] Task 4.2: Implement Offer Infrastructure
    - [ ] Update `ProductModel` in `src/modules/offer/infrastructure/models/product_model.py`.
    - [ ] Create `OfferRepository` in `src/modules/offer/infrastructure/repositories/offer_repository.py`.

- [ ] Task 4.3: Refactor Offer Application
    - [ ] Create `OfferService` for CRUD operations.
    - [ ] Update `OfferGenerator` to use domain entities.

- [ ] Task 4.4: Update Offer API Routers
    - [ ] Update `products.py` router to use `OfferService`.
    - [ ] Ensure `offer_ai.py` works with new entities.
