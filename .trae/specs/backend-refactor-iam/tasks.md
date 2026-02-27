# Tasks

- [ ] Task 2.1: Implement IAM Domain
    - [ ] Define `User` entity in `src/modules/iam/domain/user.py`.
    - [ ] Define `Tenant` entity in `src/modules/iam/domain/tenant.py`.
    - [ ] Define shared Value Objects if necessary.

- [ ] Task 2.2: Implement IAM Infrastructure Models
    - [ ] Create/Update `UserModel` in `src/modules/iam/infrastructure/models/user_model.py`.
    - [ ] Create/Update `TenantModel` in `src/modules/iam/infrastructure/models/tenant_model.py`.
    - [ ] Create/Update `UserTenantModel` in `src/modules/iam/infrastructure/models/user_tenant_model.py`.

- [ ] Task 2.3: Implement IAM Repositories
    - [ ] Implement `SqlAlchemyUserRepository` in `src/modules/iam/infrastructure/repositories/user_repository.py`.
    - [ ] Implement `SqlAlchemyTenantRepository` in `src/modules/iam/infrastructure/repositories/tenant_repository.py`.

- [ ] Task 2.4: Refactor IAM Application Services
    - [ ] Update `UserService` to use repositories.
    - [ ] Update `TenantService` to use repositories.
    - [ ] Update `AuthService` to use repositories and Domain Entities.

- [ ] Task 2.5: Update IAM API Routers
    - [ ] Update `auth_router` (or `admin.py` / `users.py`) to work with new services.
    - [ ] Ensure all DTOs in `api/dto` are correctly mapped.
