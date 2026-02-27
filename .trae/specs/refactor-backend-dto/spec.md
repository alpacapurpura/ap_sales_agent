# Refactor Backend DTO Spec

## Why
Currently, Pydantic models (Schemas) are defined directly within API routers, mixing routing logic with data validation. Additionally, the Domain layer may contain SQLAlchemy models, violating Clean Architecture principles by coupling the core domain to the database technology.

## What Changes
- **Create DTO Layer**: New directory `backend/src/api/dto/`.
- **Extract Schemas**: Move Pydantic models from `backend/src/api/routers/*.py` to `backend/src/api/dto/*.py`.
- **Refactor Routers**: Update routers to import schemas from the new DTO layer.
- **Purify Domain**: Audit `backend/src/core/domain` and move any SQLAlchemy models (using `Base`, `Column`, etc.) to `backend/src/services/db/models`.
- **Linting**: Ensure codebase passes `ruff check backend/src`.

## Impact
- **Affected Specs**: Backend Architecture.
- **Affected Code**: `backend/src/api/routers/`, `backend/src/api/dto/`, `backend/src/core/domain/`.
- **Breaking Changes**: None external (API contract remains the same), but internal imports will change significantly.

## ADDED Requirements
### Requirement: DTO Structure
The system SHALL have a dedicated `backend/src/api/dto` package for all API Request/Response Pydantic models.

### Requirement: Pure Domain
The `backend/src/core/domain` package SHALL NOT contain any SQLAlchemy models or database-specific dependencies.

## MODIFIED Requirements
### Requirement: Router Implementation
Routers SHALL import Pydantic models from `backend/src/api/dto` instead of defining them inline.
