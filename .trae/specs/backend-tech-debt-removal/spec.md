# Backend Technical Debt Removal Spec

## Why
The backend codebase has accumulated significant technical debt, including architecture violations (logic in routers, ORM in domain), missing type safety, potential security risks (tenant isolation gaps), and code duplication. This debt hinders maintainability, testability, and scalability. This spec aims to reduce technical debt to zero by enforcing Clean Architecture principles and strict coding standards.

## What Changes
- **Refactor Routers**: Move business logic and direct database access from API routers (`users.py`, `telegram.py`, `offer_gallery.py`) to the Service Layer (`core/services` or `services/`).
- **Purify Domain Layer**: Remove all ORM (SQLAlchemy) dependencies from `core/domain`. Domain models must be pure Pydantic models.
- **Create DTO Layer**: Establish `api/dto` directory and move Request/Response models there to decouple API contract from internal domain models.
- **Consolidate WhatsApp Providers**: Merge duplicated logic in `services/channels/whatsapp/v1.py` and `v2.py` into a base class.
- **Enhance Error Handling**: Replace silent failures (`except: pass`) with proper logging and exception handling.
- **Enforce Strict Typing**: Add missing return type hints and replace `Any` with specific types where possible.
- **Strengthen Security**: Audit and enforce tenant isolation in `api/routers/users.py`.

## Impact
- **Affected Specs**: None directly, but improves stability of all features.
- **Affected Code**: 
  - `backend/src/api/routers/`
  - `backend/src/core/domain/`
  - `backend/src/core/services/`
  - `backend/src/services/channels/`

## ADDED Requirements
### Requirement: API DTO Layer
The system SHALL organize Data Transfer Objects in `src/api/dto/` to separate API contracts from domain entities.

#### Scenario: Request Validation
- **WHEN** an API endpoint receives data
- **THEN** it must be validated against a Pydantic model in `api/dto/` before reaching the service layer.

### Requirement: Unified WhatsApp Service
The system SHALL provide a base `WhatsAppService` class that encapsulates common logic for different API versions.

## MODIFIED Requirements
### Requirement: Router Responsibility
**Modified**: API Routers SHALL ONLY handle request parsing, service invocation, and response formatting. They MUST NOT contain business logic or direct database queries.

### Requirement: Domain Purity
**Modified**: Domain models in `core/domain` MUST NOT import `sqlalchemy` or other infrastructure libraries. They must remain pure Python/Pydantic objects.
