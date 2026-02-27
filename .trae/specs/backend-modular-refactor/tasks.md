# Tasks

El proceso de refactorización se realizará módulo por módulo.
**IMPORTANTE**: Antes de iniciar la tarea de código de cada módulo, se debe generar un `/spec` específico para ese módulo para planificar los detalles de migración.

- [x] Task 1: Refactor Shared Kernel
    - [x] SubTask 1.1: Create `src/shared` structure (domain, application, infrastructure, utils).
    - [x] SubTask 1.2: Move/Refactor Base Entities and Exceptions to `shared/domain`.
    - [x] SubTask 1.3: Setup Event Bus in `shared/application`.
    - [x] SubTask 1.4: Setup Database Config and Base Model in `shared/infrastructure`.
    - [x] SubTask 1.5: Move Logging and Crypto utils to `shared/utils`.
    - [x] SubTask 1.6: Implement infrastructure models (AgentTrace, LLMLog, PromptVersion, SensitiveData).

- [x] Task 2: Refactor IAM Module
    - [x] SubTask 2.1: **CREATE SPEC** for IAM Module Refactor (`/spec` -> `backend-refactor-iam`).
    - [x] SubTask 2.2: Implement IAM Domain (User, Tenant Pydantic models).
    - [x] SubTask 2.3: Implement IAM Infrastructure (SQLAlchemy models, Repositories).
    - [x] SubTask 2.4: Implement IAM Application Services (Auth, Tenant).
    - [x] SubTask 2.5: Implement IAM API Routers.

- [x] Task 3: Refactor Brand Module
    - [x] SubTask 3.1: **CREATE SPEC** for Brand Module Refactor (`/spec` -> `backend-refactor-brand`).
    - [x] SubTask 3.2: Implement Brand Domain & Infrastructure.
    - [x] SubTask 3.3: Implement Brand Application (Intelligence Agent) & API.

- [x] Task 4: Refactor Offer Module
    - [x] SubTask 4.1: **CREATE SPEC** for Offer Module Refactor.
    - [x] SubTask 4.2: Implement Offer Domain & Infrastructure.
    - [x] SubTask 4.3: Implement Offer Application & API.

- [x] Task 5: Refactor Sales Module
    - [x] SubTask 5.1: **CREATE SPEC** for Sales Module Refactor.
    - [x] SubTask 5.2: Implement Sales Domain & Infrastructure.
    - [x] SubTask 5.3: Implement Sales Application & API.

- [x] Task 6: Refactor Communication Module
    - [x] SubTask 6.1: **CREATE SPEC** for Communication Module Refactor.
    - [x] SubTask 6.2: Implement Communication Domain & Infrastructure.
    - [x] SubTask 6.3: Implement Communication Application & API.

- [x] Task 7: Refactor Marketing Module
    - [x] SubTask 7.1: **CREATE SPEC** for Marketing Module Refactor.
    - [x] SubTask 7.2: Implement Marketing Domain & Infrastructure.
    - [x] SubTask 7.3: Implement Marketing Application & API.

- [x] Task 8: Refactor Gallery Module
    - [x] SubTask 8.1: **CREATE SPEC** for Gallery Module Refactor.
    - [x] SubTask 8.2: Implement Gallery Domain & Infrastructure.
    - [x] SubTask 8.3: Implement Gallery Application & API.

- [x] Task 9: Refactor Landing Module
    - [x] SubTask 9.1: **CREATE SPEC** for Landing Module Refactor.
    - [x] SubTask 9.2: Implement Landing Domain & Infrastructure.
    - [x] SubTask 9.3: Implement Landing Application & API.

- [ ] Task 10: Final Integration & Verification
    - [ ] SubTask 10.1: Verify all cross-module dependencies.
    - [ ] SubTask 10.2: Run full test suite.
