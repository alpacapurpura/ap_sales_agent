# Tasks

- [x] Task 1: Create New Directory Structure
  - [x] SubTask 1.1: Create `backend/src/domain`
  - [x] SubTask 1.2: Create `backend/src/application/services`
  - [x] SubTask 1.3: Create `backend/src/application/orchestrators`
  - [x] SubTask 1.4: Create `backend/src/application/tools`
  - [x] SubTask 1.5: Create `backend/src/infrastructure` (and subfolders: `db`, `channels`, `marketing`, `llm`, `security`, `external`)
  - [x] SubTask 1.6: Create `backend/src/common`

- [x] Task 2: Move Domain Layer
  - [x] SubTask 2.1: Move `src/core/domain/*` to `src/domain/`.

- [x] Task 3: Move Application Layer
  - [x] SubTask 3.1: Move `src/core/services/chat_orchestrator.py` to `src/application/orchestrators/chat.py`.
  - [x] SubTask 3.2: Move `src/core/services/tools/*` to `src/application/tools/`.
  - [x] SubTask 3.3: Move remaining `src/core/services/*.py` (excluding `llm`) to `src/application/services/`.

- [x] Task 4: Move Infrastructure Layer
  - [x] SubTask 4.1: Move `src/services/db` to `src/infrastructure/db`.
  - [x] SubTask 4.2: Move `src/services/channels` to `src/infrastructure/channels`.
  - [x] SubTask 4.3: Move `src/services/marketing` to `src/infrastructure/marketing`.
  - [x] SubTask 4.4: Move `src/core/services/llm` to `src/infrastructure/llm`.
  - [x] SubTask 4.5: Move `src/core/security.py` to `src/infrastructure/security/auth.py`.
  - [x] SubTask 4.6: Move `src/services/*.py` (clerk, email, etc.) to `src/infrastructure/external/`.

- [x] Task 5: Move Common Layer
  - [x] SubTask 5.1: Move `src/core/logging_config.py` to `src/common/logging.py`.
  - [x] SubTask 5.2: Move `src/core/context.py` to `src/common/context.py`.
  - [x] SubTask 5.3: Move `src/utils` to `src/common/utils`.

- [x] Task 6: Mass Import Refactor (The Hard Part)
  - [x] SubTask 6.1: Update `src.core.domain` -> `src.domain`.
  - [x] SubTask 6.2: Update `src.core.services.chat_orchestrator` -> `src.application.orchestrators.chat`.
  - [x] SubTask 6.3: Update `src.core.services.llm` -> `src.infrastructure.llm`.
  - [x] SubTask 6.4: Update `src.services.db` -> `src.infrastructure.db`.
  - [x] SubTask 6.5: Update `src.core.logging_config` -> `src.common.logging`.
  - [x] SubTask 6.6: Update `src.core.context` -> `src.common.context`.
  - [x] SubTask 6.7: Update `src.core.security` -> `src.infrastructure.security.auth`.
  - [x] SubTask 6.8: Handle all other moved files imports.

- [x] Task 7: Cleanup & Verify
  - [x] SubTask 7.1: Delete empty folders (`src/core/domain`, `src/services`, etc.).
  - [x] SubTask 7.2: Run `audit_project_structure.py` (Update it first).
  - [x] SubTask 7.3: Run `ruff check backend/src` and fix all broken imports.

# Task Dependencies
- Task 6 depends on Tasks 1-5.
- Task 7 depends on Task 6.
