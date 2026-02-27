# Marketing Studio (MKT Studio) Spec

## Why
To enable advanced marketing capabilities within the SaaS platform by implementing a lightweight Customer Data Platform (CDP). This module will support the "Full Lifecycle Framework" (7 Stages: Acquisition to Evangelization), allowing for identity resolution, lead scoring, RFM analysis, and multi-channel integration.

## What Changes
### Backend
- **New Module**: `backend/src/services/marketing/` containing logic for Identity Resolution, Scoring, RFM, and Connectors.
- **New Models**: `backend/src/services/db/models/marketing.py` with `CustomerProfile`, `CustomerIdentity`, `JourneyEvent` and strict Enums.
- **New Repositories**: `backend/src/services/db/repositories/marketing.py` implementing the DAO pattern for the new models.
- **New API**: `backend/src/api/routers/cdp.py` and `webhooks_cdp.py` for frontend consumption and external data ingestion.

### Frontend
- **New Feature**: `frontend/src/features/marketing-studio/` following Feature-Sliced Design.
  - `components/`: UI components (`ConnectionsView`, `PipelineView`, etc.).
  - `hooks/`: Business logic and data fetching (`useMarketingData`, `useJourneyEvents`).
  - `types/`: Domain interfaces mirroring backend models.
  - `index.ts`: Public exports.
- **New Page**: `frontend/src/app/(dashboard)/marketing-studio/page.tsx` (Thin wrapper).

## Impact
- **Affected Specs**: Adds "Marketing Studio" capability.
- **Affected Code**:
  - `backend/src/main.py` (routers).
  - `backend/src/services/db/models/__init__.py` (models).
  - `frontend/src/app/(dashboard)/layout.tsx` (navigation).
- **Breaking Changes**: None.

## ADDED Requirements

### Requirement: Data Taxonomy & Rules
- **Strict Naming**: `snake_case` or `kebab-case`.
- **Lifecycle Stages**: `stage_visitor` to `stage_evangelist` (Mutual exclusivity).
- **Tag Prefixes**: `src_`, `int_`, `bhv_`, `rfm_`, `nps_`.

### Requirement: Multi-Tenancy
- All DB tables MUST include `tenant_id`.

### Requirement: Backend Architecture (Clean Architecture)
- **Domain**: Models in `services/db/models`.
- **Infrastructure**: Repositories in `services/db/repositories` (DAO).
- **Service**: Logic in `services/marketing/` using Repositories.
- **Interface**: Routers in `api/routers/`.

### Requirement: Frontend Architecture (Feature-Sliced Design)
- **Structure**: All code in `frontend/src/features/marketing-studio/`.
- **Logic**: UI logic MUST reside in `hooks/`. Components MUST NOT fetch data directly.
- **Components**: Use `Shadcn UI` primitives and `Lucide React` icons.
- **Typing**: Strict TypeScript interfaces in `types/`.

## MODIFIED Requirements
N/A

## REMOVED Requirements
N/A
