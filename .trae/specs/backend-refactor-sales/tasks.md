# Tasks

- [ ] Task 5.1: Implement Sales Domain
    - [ ] Create `src/modules/sales/domain/lead.py` with `Lead` entity and `UserProfile`.
    - [ ] Move Enums to `src/modules/sales/domain/enums.py`.

- [ ] Task 5.2: Implement Sales Infrastructure
    - [ ] Update `LeadModel` in `src/modules/sales/infrastructure/models/lead_model.py`.
    - [ ] Create `LeadRepository` in `src/modules/sales/infrastructure/repositories/lead_repository.py`.

- [ ] Task 5.3: Refactor Sales Application
    - [ ] Create `LeadService` for CRUD and channel resolution.
    - [ ] Create `PipelineService` (placeholder or basic logic).

- [ ] Task 5.4: Update Sales API Routers
    - [ ] Update `leads.py` router to use `LeadService`.
