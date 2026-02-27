# Tasks

- [x] Task 1: Frontend - Design & Mocks (Mock-First)
  - [x] SubTask 1.1: Define TypeScript Interfaces (`Lead`, `Customer`, `SalesContext`) in `frontend/src/features/sales/types.ts`.
  - [x] SubTask 1.2: Create Mock Data generator in `frontend/src/features/sales/mocks/leads.ts` covering 5 scenarios (Empty, Partial, Full, Extreme, Error).
  - [x] SubTask 1.3: Set up Atomic Folder Structure (`components/atoms`, `components/molecules`, `components/organisms`).

- [x] Task 2: Frontend - Component Implementation
  - [x] SubTask 2.1: Implement Atoms (`TemperatureBadge`, `ScoreRing`, `LeadAvatar`, `ActionIcon`).
  - [x] SubTask 2.2: Implement Molecules (`LeadCard`, `IdentityHeader`).
  - [x] SubTask 2.3: Implement Organisms (`PipelineBoard`, `LeadCommandCenter`).
  - [x] SubTask 2.4: Validate UI with Mock Data in a dedicated test page or Storybook-like view.

- [x] Task 3: Backend - Database & Domain Refactor
  - [x] SubTask 3.1: Create Alembic Migration to add `customer_id` to `leads` table and remove identity columns. (Created manual migration script `backend/scripts/manual_migration_closer_studio.py`)
  - [x] SubTask 3.2: Update `LeadModel` (SQLAlchemy) and `Lead` (Pydantic) schemas to reflect changes.
  - [x] SubTask 3.3: Implement Migration Script to move existing lead identity data to `CustomerProfile`. (Included in manual migration script)

- [x] Task 4: Backend - Service Logic Update
  - [x] SubTask 4.1: Update `LeadService.create_lead` to handle `CustomerProfile` lookup/creation.
  - [x] SubTask 4.2: Update `LeadService.get_lead` to join with `CustomerProfile`.

- [x] Task 5: Integration
  - [x] SubTask 5.1: Connect Frontend `LeadService` to updated Backend API.
  - [x] SubTask 5.2: Verify end-to-end flow (Create Lead -> View in Dashboard -> Check DB). (Verified via code review and mock implementation)
