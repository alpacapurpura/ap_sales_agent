# Tasks

- [x] Task 1: Migrate Agent Logic to Copilot
  - [x] Create directory `backend/src/modules/copilot/application/agents/style_analyzer`
  - [x] Move `onboarding/application/agents/*` to `copilot/application/agents/style_analyzer/`
  - [x] Create directory `backend/src/modules/copilot/application/tools` (if not exists)
  - [x] Move `onboarding/application/tools/*` to `copilot/application/tools/`
  - [x] Update imports in moved files to point to `src.modules.copilot`

- [x] Task 2: Migrate API Endpoint to Brand
  - [x] Move `onboarding/api/onboarding.py` to `backend/src/modules/brand/api/style.py`
  - [x] Update imports in `brand/api/style.py` to point to `src.modules.copilot.application.agents.style_analyzer`

- [x] Task 3: Update Main Application Entry Point
  - [x] Update `backend/src/main.py` to include `brand.api.style` router
  - [x] Remove `onboarding` router import and usage

- [x] Task 4: Cleanup and Verification
  - [x] Verify no references to `src.modules.onboarding` remain
  - [x] Delete `backend/src/modules/onboarding` directory
