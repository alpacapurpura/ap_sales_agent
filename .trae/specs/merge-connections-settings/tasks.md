# Tasks

- [x] Task 1: Update Sidebar Navigation
  - [x] Remove "Conexiones" item from `getNavItems` in `frontend/src/components/shared/layout/app-sidebar.tsx`.

- [x] Task 2: Refactor SettingsView
  - [x] Import all connection components (`WhatsAppView`, `GmailView`, `TelegramView`, etc.) into `SettingsView.tsx`.
  - [x] Implement `isPopupCallback` logic in `SettingsView` (copy from `ConnectionsView`).
  - [x] Rebuild `SettingsContent` sidebar to use `Tabs` with grouped headers (Principal, Canales, etc.).
  - [x] Ensure all `TabsContent` sections are present and mapped to the correct values.
  - [x] Verify `activeTab` state management and URL query parameter sync (`?tab=...`).

- [x] Task 3: Cleanup Old Connections Module
  - [x] Delete `frontend/src/features/connections/components/ConnectionsView.tsx`.
  - [x] Delete `frontend/src/app/(main)/[tenantId]/(dashboard)/connections` directory.
