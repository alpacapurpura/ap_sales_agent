# Backend Architecture Refactor Spec

## Why
The current backend codebase has accumulated technical debt with files scattered in legacy directories (`src/api`, `src/domain`, `src/application`) and mixed responsibilities. This violates the Modular Monolith architecture standard, making the system harder to maintain, test, and scale. The goal is to enforce a strict module structure where every file belongs to a specific Domain Module or the Shared Kernel.

## What Changes
- **Refactor Root `src/api`**: Eliminate `src/api` by moving all routers and DTOs to their respective modules (`src/modules/{module}/api`).
- **Refactor Root `src/domain`**: Eliminate `src/domain` by moving shared schemas to `src/shared/domain` or specific modules.
- **Refactor Root `src/application`**: Eliminate `src/application` by moving orchestrators and tools to `src/shared/application` or specific modules.
- **Clean Shared Kernel**: Flatten nested utils in `src/shared` and move domain-specific agents from `src/shared/core/agents` to their respective modules.
- **Update Entry Point**: Refactor `src/main.py` to import routers from their new module locations.
- **Breaking Changes**: All import paths for moved files will change.

## Impact
- **Affected Specs**: `back-structure.md` (will be strictly enforced).
- **Affected Code**: `src/main.py`, `src/api/*`, `src/domain/*`, `src/application/*`, `src/modules/*`, `src/shared/*`.

## ADDED Requirements
### Requirement: Strict Modular Structure
The system SHALL NOT contain `src/api`, `src/domain`, `src/application` directories at the root level. All code must reside in `src/modules/{module_name}` or `src/shared`.

#### Scenario: Module Isolation
- **WHEN** a new feature is added
- **THEN** it must be placed within `src/modules/{domain}` using the standard layers (`api`, `application`, `domain`, `infrastructure`).

## MODIFIED Requirements
### Requirement: Router Registration
The `src/main.py` file SHALL import routers exclusively from `src/modules/{module}/api`.

## REMOVED Requirements
### Requirement: Legacy API Structure
**Reason**: `src/api` promotes a "Layered Architecture" (Controller-Service-Dao) which couples modules tightly. We are moving to "Modular Monolith" (Vertical Slices).
**Migration**: All files in `src/api` are moved to `src/modules`.
