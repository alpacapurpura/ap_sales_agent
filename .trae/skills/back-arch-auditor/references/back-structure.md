---
alwaysApply: false
description: |
  Defines the project structure for the backend, following Domain-Driven Design (DDD) and Modular Monolith principles.
---
# Backend Project Structure

The backend follows a **Modular Monolith** architecture. This structure is designed to support multiple autonomous business domains (Bounded Contexts) within a single codebase.

Root: `backend/`

## High-Level Organization

- **`src/shared/`**: The Shared Kernel. Contains code shared across all modules (e.g., Auth, Database Config, Base Classes).
- **`src/modules/`**: The Bounded Contexts. Each folder here represents a distinct business domain (e.g., `sales`, `onboarding`).
- **`src/main.py`**: The Application Entry Point. Registers routers and starts the app.
- **`src/config.py`**: Global configuration.

## Module Structure (`src/modules/{context}`)

Each module (e.g., `src/modules/sales`) is self-contained and follows strict Layered Architecture internally:

### 1. Domain Layer (`domain/`)
**Responsibility**: Pure business logic and rules. **NO dependencies on external libraries or frameworks.**
- `entities.py`: Pure Python objects representing business concepts (Pydantic).
- `events.py`: Domain events (e.g., `LeadQualified`, `OfferGenerated`).
- `interfaces.py`: Interfaces (Protocols) for repositories and external services.
- `exceptions.py`: Domain-specific exceptions.

### 2. Application Layer (`application/`)
**Responsibility**: Orchestration and use cases. Connects the Domain to the Infrastructure.
- `services/`: Application services (e.g., `SalesService`).
- `event_handlers/`: Handlers for domain events.

### 3. Infrastructure Layer (`infrastructure/`)
**Responsibility**: Technical implementation of interfaces defined in Domain.
- `models/`: Database models (SQLAlchemy).
- `repositories/`: Database access implementing Domain Interfaces.
- `external/`: Adapters for external services (APIs).

### 4. Interface Layer (`api/`)
**Responsibility**: Exposing the module to the outside world.
- `routers.py`: FastAPI routes specific to this module.
- `dtos.py`: Data Transfer Objects for input/output.

## Shared Kernel (`src/shared/`)

- `domain/`: Universal entities (e.g., `Tenant`, `User`) and exceptions.
- `infrastructure/`:
  - `db/`: Database configuration (`session.py`) and Base Models.
  - `security/`: Authentication and Authorization logic.
  - `monitoring/`: Logging and observability.
- `application/`: Shared application logic (Event Bus).
- `utils/`: Generic helpers (Time, String manipulation).

## Migration Mapping (Old -> New)

| Old Concept | New Location |
|:---|:---|
| `src/core` | `src/shared/core` (Base logic) |
| `src/services/db` | `src/shared/infrastructure/db` (Config) or `src/modules/*/infrastructure` (Models) |
| `src/api/routers` | `src/modules/{name}/api/routers.py` |
| `src/core/prompts` | `src/shared/core/prompts` or `src/modules/{name}/infrastructure/prompts` |
