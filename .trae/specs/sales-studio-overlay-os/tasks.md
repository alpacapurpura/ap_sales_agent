# Tasks

- [ ] Task 1: Setup Sales Studio Structure & Components
  - [ ] SubTask 1.1: Create directory structure `frontend/src/features/sales/components/dashboard` and `overlay`.
  - [ ] SubTask 1.2: Define TypeScript interfaces for Dashboard Metrics and Configuration State.

- [ ] Task 2: Implement Payment Gateway Configuration (Contextual)
  - [ ] SubTask 2.1: Create `PaymentGatewayConfig` component with UI for API Keys (Public/Secret).
  - [ ] SubTask 2.2: Implement Sandbox/Production toggle logic and visual indicators (Green/Yellow).
  - [ ] SubTask 2.3: Add "Test Connection" button with mock validation logic.
  - [ ] SubTask 2.4: Wrap in a Shadcn `Dialog` or `Sheet` triggerable from the dashboard.

- [ ] Task 3: Implement Sales Inbox Overlay
  - [ ] SubTask 3.1: Create `SalesInboxSheet` component using Shadcn `Sheet`.
  - [ ] SubTask 3.2: Build a mock conversation list UI (Avatar, Name, Last Message, Status) optimized for the sidebar.
  - [ ] SubTask 3.3: Implement a simple message view within the sheet for "intervention" simulation.

- [ ] Task 4: Implement Appointment & Availability Contextual Management
  - [ ] SubTask 4.1: Adapt `AppointmentsView` to a Widget format for the Bento Grid (CalendarWidget).
  - [ ] SubTask 4.2: Create `AppointmentSheet` for detailed view and actions (Reschedule, Cancel).
  - [ ] SubTask 4.3: Create `AvailabilitySettingsModal` to house the existing `AvailabilityView` logic in a dialog.

- [ ] Task 5: Construct the Main Sales Dashboard (Bento Grid)
  - [ ] SubTask 5.1: Create `SalesDashboardLayout` using CSS Grid / Tailwind to organize widgets.
  - [ ] SubTask 5.2: Integrate KPI Cards (Sales, Conversion, etc.).
  - [ ] SubTask 5.3: Integrate `CalendarWidget` and `ActivityFeedWidget`.
  - [ ] SubTask 5.4: Add "Quick Actions" floating button or bar for Inbox and Settings.

- [ ] Task 6: Refactor Page Entry Point
  - [ ] SubTask 6.1: Update `frontend/src/app/(main)/(dashboard)/sales/page.tsx` to render the new `SalesDashboardLayout`.
  - [ ] SubTask 6.2: Ensure all previous functionality (tabs) is either migrated to the new layout or accessible via settings.

# Task Dependencies
- Task 5 depends on Task 1, 2, 3, 4 (Components need to be ready to be placed in the grid).
- Task 6 depends on Task 5.
