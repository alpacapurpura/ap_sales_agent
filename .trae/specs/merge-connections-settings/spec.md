# Merge Connections into Settings Spec

## Why
Currently, "Settings" and "Connections" are two separate top-level modules. To improve user experience and simplify navigation, the user requests to merge "Connections" into "Settings". This aligns with the "Clean Code" principle of grouping related configuration responsibilities. The "Settings" module will now act as a centralized hub for both application configuration and external integrations.

## What Changes
- **SettingsView**: Will be significantly expanded to include a categorized sidebar (Principal, Sales Channels, Closing Tools, Developers).
- **AppSidebar**: The "Connections" link will be removed.
- **ConnectionsView**: Logic and components will be migrated to `SettingsView`, and the original file/route will be removed.
- **Routing**: The `/connections` route will be removed. Deep links to connections should now point to `/settings?tab=...`.

## Impact
- **Affected specs**: Navigation, Settings, Connections.
- **Affected code**:
  - `frontend/src/components/shared/layout/app-sidebar.tsx`
  - `frontend/src/features/settings/components/SettingsView.tsx`
  - `frontend/src/features/connections/components/ConnectionsView.tsx` (Deleted)
  - `frontend/src/app/(main)/[tenantId]/(dashboard)/connections/` (Deleted)

## ADDED Requirements
### Requirement: Unified Settings Sidebar
The `SettingsView` sidebar SHALL be organized into the following sections:
- **Principal**:
  - General (Existing)
  - Perfil (Existing)
  - Equipo (Existing)
  - LLM API Keys (Existing)
- **Canales de Venta** (Migrated from Connections):
  - WhatsApp
  - Correo Electrónico
  - TikTok
  - Instagram
  - Messenger
  - Telegram
  - Web Widget
- **Cierre de ventas** (Migrated from Connections):
  - Calendario
  - CRM
  - Pasarela de Pagos
- **Desarrolladores** (Migrated from Connections):
  - Webhooks

### Requirement: Google OAuth Callback
The `SettingsView` SHALL handle the `isPopupCallback` logic for Google OAuth redirects, which was previously in `ConnectionsView`.

## MODIFIED Requirements
### Requirement: Sidebar Navigation
The application sidebar SHALL NOT display "Conexiones". "Configuración" remains the entry point for all settings.

## REMOVED Requirements
### Requirement: Standalone Connections Module
The standalone `/connections` route and `ConnectionsView` component are removed.
