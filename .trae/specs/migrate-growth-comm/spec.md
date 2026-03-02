# Migrate Growth and Communication to Domain Structure Spec

## Why
The current `backend/src/modules/growth` and `backend/src/modules/communication` modules are not aligned with the strict domain-driven design defined in `docs/domains/INDEX.md`. To ensure architectural consistency and proper domain boundaries, these modules must be consolidated into the canonical `crm`, `analytics`, and `scheduling` domains. This refactor eliminates ambiguity and centralizes related logic.

## What Changes
- **Migrate Growth Module Content**:
  - `growth/domain/lead.py` -> `crm/domain/lead.py`
  - `growth/domain/customer.py` -> `crm/domain/customer.py`
  - `growth/domain/enums.py` -> `crm/domain/enums.py` (and update references)
  - `growth/domain/event.py` -> `crm/domain/event.py`
  - `growth/api/leads.py` -> `crm/api/leads.py`
  - `growth/api/cdp.py` -> `crm/api/cdp.py`
  - `growth/api/metrics.py` -> `analytics/api/metrics.py` (Sankey funnel metrics belong to Analytics)
  - `growth/application/services/lead_service.py` -> `crm/application/services/lead_service.py`
  - `growth/application/services/customer_service.py` -> `crm/application/services/customer_service.py`
  - `growth/infrastructure/repositories/*` -> `crm/infrastructure/repositories/*`
  - `growth/infrastructure/models/*` -> `crm/infrastructure/models/*`
  - `growth/infrastructure/engines/*` -> `crm/infrastructure/engines/*`

- **Migrate Communication Module Content**:
  - `communication/domain/appointment.py` -> `scheduling/domain/appointment.py`
  - `communication/domain/availability_schema.py` -> `scheduling/domain/availability_schema.py`
  - `communication/domain/enums.py` -> `scheduling/domain/enums.py` (if specific to scheduling)
  - `communication/domain/event_type_schema.py` -> `scheduling/domain/event_type_schema.py`
  - `communication/api/event_types.py` -> `scheduling/api/event_types.py`
  - `communication/api/public_links.py` -> `scheduling/api/public_links.py`
  - `communication/api/dto/*` -> `scheduling/api/dto/*`
  - `communication/application/services/availability_service.py` -> `scheduling/application/services/availability_service.py`
  - `communication/application/services/event_type_service.py` -> `scheduling/application/services/event_type_service.py`
  - `communication/infrastructure/models/appointment_model.py` -> `scheduling/infrastructure/models/appointment_model.py`
  - `communication/infrastructure/models/booking_link.py` -> `scheduling/infrastructure/models/booking_link.py`

- **Update Application Entry Point**:
  - Update `backend/src/main.py` to import routers from new locations (`crm`, `analytics`, `scheduling`) instead of `marketing`, `sales`, or `communication`.

- **Cleanup**:
  - Delete `backend/src/modules/growth` directory.
  - Delete `backend/src/modules/communication` directory.

## Impact
- **Affected Specs**: CRM, Analytics, Scheduling.
- **Affected Code**:
  - `backend/src/main.py`: Router imports.
  - `backend/src/modules/crm/*`: New files added.
  - `backend/src/modules/scheduling/*`: New files added.
  - `backend/src/modules/analytics/*`: New files added.
  - Imports in moved files must be updated to reflect new paths (e.g., `src.modules.growth` -> `src.modules.crm`).

## ADDED Requirements
### Requirement: CRM Domain Consolidation
The system SHALL store Lead and Customer entities within the `crm` module structure.

### Requirement: Scheduling Domain Consolidation
The system SHALL handle Appointments and Availability within the `scheduling` module structure.

## REMOVED Requirements
### Requirement: Growth Module
**Reason**: Replaced by CRM and Analytics domains.
**Migration**: Move files to target domains.

### Requirement: Communication Module
**Reason**: Replaced by Scheduling domain.
**Migration**: Move files to target domain.
