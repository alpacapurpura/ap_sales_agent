# Tasks

- [x] Task 1: Backend Data Model Scaffold
  - [x] SubTask 1.1: Create `backend/src/services/db/models/marketing.py`.
  - [x] SubTask 1.2: Define Enums and Tables (`CustomerProfile`, `CustomerIdentity`, `JourneyEvent`) with `tenant_id`.
  - [x] SubTask 1.3: Export models in `backend/src/services/db/models/__init__.py`.

- [x] Task 2: Backend Repositories Scaffold
  - [x] SubTask 2.1: Create `backend/src/services/db/repositories/marketing.py`.
  - [x] SubTask 2.2: Implement `CustomerRepository` and `JourneyEventRepository` (DAO Pattern).

- [x] Task 3: Backend Services & Engines Scaffold
  - [x] SubTask 3.1: Create `backend/src/services/marketing/engines/` structure.
  - [x] SubTask 3.2: Implement base classes for Engines using Repositories.
  - [x] SubTask 3.3: Create `backend/src/services/marketing/connectors/` with `base.py` and empty implementations.

- [x] Task 4: Backend API Scaffold
  - [x] SubTask 4.1: Create `backend/src/api/routers/cdp.py` and `webhooks_cdp.py`.
  - [x] SubTask 4.2: Register new routers in `backend/src/main.py`.

- [x] Task 5: Frontend Scaffold
  - [x] SubTask 5.1: Create `frontend/src/features/marketing-studio/types/index.ts`.
  - [x] SubTask 5.2: Create `frontend/src/features/marketing-studio/hooks/useMarketingData.ts` (Mocked hook).
  - [x] SubTask 5.3: Create `frontend/src/features/marketing-studio/components/` structure:
    - `ConnectionsView.tsx`
    - `PipelineView.tsx`
    - `JourneyExplorer.tsx`
    - `GrowthDashboard.tsx`
    - Ensure components use the custom hook.
  - [x] SubTask 5.4: Create `frontend/src/features/marketing-studio/index.ts` exporting the main view.
  - [x] SubTask 5.5: Create `frontend/src/app/(dashboard)/marketing-studio/page.tsx` importing from `features/`.

- [x] Task 6: Skill Creation
  - [x] SubTask 6.1: Create `mkt-studio-dev` skill structure (`SKILL.md`, `references/`).
  - [x] SubTask 6.2: Define architecture and taxonomy references.
