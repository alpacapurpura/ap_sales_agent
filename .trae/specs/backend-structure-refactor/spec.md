# Backend Total Order Refactor Spec

## Why
The user requested a "total ordering" of the backend to achieve "zero errors" in architectural alignment. The current structure mixes Domain, Application, and Infrastructure concerns within `src/core` and `src/services`, causing confusion about where logic resides. This refactor implements a strict Clean Architecture layout where `src/core` is reserved exclusively for AI Agents.

## What Changes
We will reorganize `backend/src` into 5 distinct layers:

### 1. `src/domain` (The "What")
**Content**: Pure Pydantic entities and Enums.
**Source**: `src/core/domain/`
- `schema.py`, `brand_schema.py`, etc.
**Goal**: No external dependencies (SQLAlchemy, HTTP).

### 2. `src/application` (The "How")
**Content**: Business Logic and Orchestration.
**Source**: `src/core/services/`
- **Services**: `user_service.py`, `offer_gallery_service.py`, `landing_generator.py`, etc. -> `src/application/services/`
- **Orchestration**: `chat_orchestrator.py` -> `src/application/orchestrators/chat.py`
- **Tools**: `tools/` -> `src/application/tools/`

### 3. `src/infrastructure` (The "Where")
**Content**: External adapters, Database, and 3rd Party APIs.
**Source**: `src/services/` (Renamed) + `src/core/services/llm` + `src/core/security.py`
- `db/` -> `src/infrastructure/db/`
- `channels/` -> `src/infrastructure/channels/`
- `marketing/` -> `src/infrastructure/marketing/`
- `llm/` (from core) -> `src/infrastructure/llm/`
- `security.py` (from core) -> `src/infrastructure/security/auth.py`
- `clerk.py`, `email.py`, `s3.py` -> `src/infrastructure/external/`

### 4. `src/core` (The "Brain")
**Content**: AI Agents and Cognitive Logic.
- `agents/` (Keep here)
- `prompts/` (Keep here)
- `semantic/` (Keep here)
- `state.py` (Agent State)

### 5. `src/common` (The "Glue")
**Content**: Cross-cutting concerns.
- `logging_config.py` (from core) -> `src/common/logging.py`
- `context.py` (from core) -> `src/common/context.py`
- `utils/` -> `src/common/utils/`

## Impact
- **Breaking Changes**: ALL imports project-wide will change. This is a massive refactor.
- **Affected Specs**: `backend-structure-refactor`.
- **Affected Code**: Entire `backend/src` tree.

## ADDED Requirements
### Requirement: Strict Layering
- **Domain** MUST NOT import from Application or Infrastructure.
- **Application** MAY import Domain and Infrastructure (Pragmatic).
- **Core (Agents)** MAY import Domain and Application (Tools).

## REMOVED Requirements
### Requirement: Mixed Core
- `src/core` shall no longer contain general business services or domain models.

## Migration Plan
1.  **Prepare**: Create new folder structure.
2.  **Move**: Execute file moves.
3.  **Refactor**: Run global search/replace for imports.
4.  **Verify**: Run `ruff` and tests.
