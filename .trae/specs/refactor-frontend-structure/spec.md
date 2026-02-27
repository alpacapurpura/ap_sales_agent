# Refactor Frontend Structure Spec

## Why
The current frontend structure is inconsistent. The `marketing-studio` feature is located in a root-level `(dashboard)` directory, isolated from the main tenant dashboard context. This violates the project's multi-tenant architecture where dashboard features should be scoped to a `tenantId`. Additionally, there is a redundant `(dashboard)` directory at the root level, causing confusion with `(main)/[tenantId]/(dashboard)`.

## What Changes
- Move `src/app/(dashboard)/marketing-studio` to `src/app/(main)/[tenantId]/(dashboard)/marketing-studio`.
- Remove the now empty `src/app/(dashboard)` directory.
- Update any hardcoded links to `/marketing-studio` to dynamic links including `tenantId`.

## Impact
- **Routes**: The route `/marketing-studio` will likely cease to exist or be redirected. The new route will be `/[tenantId]/marketing-studio`.
- **Code**: `page.tsx` for marketing studio will now inherit the `[tenantId]` param and the `DashboardLayout` from `(main)/[tenantId]/(dashboard)/layout.tsx`.

## ADDED Requirements
### Requirement: Tenant Scoped Marketing Studio
The Marketing Studio page SHALL be accessible via `/[tenantId]/marketing-studio` and SHALL inherit the authenticated dashboard layout with sidebar.

## REMOVED Requirements
### Requirement: Root Level Dashboard
**Reason**: Redundant and inconsistent with multi-tenant architecture.
**Migration**: Moved content to tenant-scoped dashboard.
