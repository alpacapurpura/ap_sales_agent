# Backend Architecture Refactor Spec

## Why
The current backend structure suffers from "God Object" issues (e.g., `shared/domain/schema.py`) and generic file naming (multiple `schema.py` files), which hinders modularity and maintainability. The Admin module directly accesses the database, bypassing domain logic.

## What Changes
- **Refactor Shared Schema**: Split `backend/src/shared/domain/schema.py` into domain-specific modules within `modules/`.
- **Rename Generic Files**: Rename ambiguous files to descriptive names (e.g., `landing_page/schema.py` -> `landing_page/content_schemas.py`).
- **Centralize Tenant Logic**: Create `TenantService` in `iam` module to be used by both API and Admin.
- **Update Imports**: Update all references to the moved/renamed files.

## Impact
- **Affected Specs**: Backend Architecture, Modular Monolith compliance.
- **Affected Code**: `backend/src/shared/domain/schema.py`, `backend/src/modules/*/domain/*.py`, `backend/src/admin/modules/tenants.py`.

## ADDED Requirements
### Requirement: Domain Isolation
Models and Enums MUST reside within their specific `modules/{module}/domain` directory, not in `shared`.

#### Scenario: Lead Status Enum
- **WHEN** developer imports `LeadStatus`
- **THEN** it should come from `src.modules.sales.domain.lead_enums`, NOT `src.shared.domain.schema`.

### Requirement: Descriptive Naming
Files MUST NOT be named generic names like `schema.py`, `models.py` (unless standard Django/SQLAlchemy pattern, but `domain` models should be specific), or `utils.py` without context.

## MODIFIED Requirements
### Requirement: Admin Module Logic
The Admin dashboard (`src/admin`) SHALL use `TenantService` from `src/modules/iam` instead of direct DB queries for business logic operations (Create/Update Tenant).

## REMOVED Requirements
### Requirement: Shared Schema God Object
**Reason**: `src/shared/domain/schema.py` couples all domains.
**Migration**: Split into `sales/domain/lead_models.py`, `marketing/domain/brand_models.py`, `iam/domain/user_models.py`.
