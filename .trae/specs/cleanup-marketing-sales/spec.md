# Cleanup & Real Integration Spec

## Why
Currently, the "Marketing Studio" and "Sales Studio" frontends rely heavily on hardcoded mock data (static JSONs, fixed numbers). This creates a false sense of progress and disconnects the UI from the actual Backend logic. The goal is to remove all "fake" data and show ONLY what is truly implemented in the Backend.

## What Changes

### Frontend: Marketing Studio
- **Remove**: `MOCK_PROFILES`, `MOCK_RFM_STATS`, `STAGES` (fixed counts), and static metrics in `GrowthDashboard` (Revenue, Churn, etc.).
- **Modify**: `useMarketingData` hook to fetch real data from `GET /api/v1/marketing/profiles` (or equivalent).
- **UI Behavior**:
  - `GrowthDashboard`: Show "No Data" or `0` if the backend doesn't provide global metrics yet.
  - `PipelineView`: Populate only with real `CustomerProfile` stages.
  - `JourneyExplorer`: Fetch real `JourneyEvent`s via API.

### Frontend: Sales Studio
- **Remove**: `MOCK_CONVERSATIONS` in `SalesInboxSheet` and `ACTIVITIES` in `ActivityFeedWidget`.
- **UI Behavior**:
  - `SalesInbox`: Show empty state or connect to `GET /leads` if applicable.
  - `ActivityFeed`: Show empty state.
  - `Dashboard`: Remove hardcoded "Total Sales" and "Close Rate".

## Impact
- **Visual**: The dashboards will look "empty" initially. This is intentional. It exposes the need for Backend implementations for Aggregations (KPIs).
- **Code**: Deletion of large mock objects in `frontend/src/features/marketing-studio/data/mocks.ts` (or similar).

## ADDED Requirements
### Requirement: Real Data Binding
The system SHALL only display data returned by the Backend API.
- **WHEN** the backend returns an empty list, **THEN** the UI must show an empty state, not a mock list.

## MODIFIED Requirements
### Requirement: Dashboard KPIs
**Old**: Display static `$45,231.89` revenue.
**New**: Display `-` or `0` until a `GET /marketing/stats` endpoint is implemented.

## REMOVED Requirements
### Requirement: Mock Data
**Reason**: Misleading representation of system status.
