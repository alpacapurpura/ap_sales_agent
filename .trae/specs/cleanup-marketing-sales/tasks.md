# Tasks

- [x] Task 1: Clean Marketing Studio Frontend
  - [x] SubTask 1.1: Identify and delete mock data files (e.g., `MOCK_PROFILES`, `mockData.ts`) in `frontend/src/features/marketing-studio`.
  - [x] SubTask 1.2: Refactor `useMarketingData` hook to attempt a fetch to `/api/v1/marketing/profiles` (or verify if endpoint exists and connect). If no endpoint exists for global stats, return empty/null values.
  - [x] SubTask 1.3: Update `GrowthDashboard` to handle `null`/`undefined` data gracefully (show loaders or empty states instead of hardcoded numbers).

- [x] Task 2: Clean Sales Studio Frontend
  - [x] SubTask 2.1: Remove `MOCK_CONVERSATIONS` usage in `SalesInboxSheet`. Replace with empty array or real `useLeads` hook call.
  - [x] SubTask 2.2: Remove `ACTIVITIES` constant usage in `ActivityFeedWidget`.
  - [x] SubTask 2.3: Remove hardcoded KPI numbers in `SalesDashboard` (replace with 0 or hidden).

- [x] Task 3: Verify Connections
  - [x] SubTask 3.1: Ensure `CalendarWidget` and `EventTypeView` (which are implemented) remain functional.
  - [x] SubTask 3.2: Verify that the "Empty" dashboards do not crash the application.
