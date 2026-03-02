# Migration of Communication Module to Scheduling and Connections

## Why
The `communication` module currently contains mixed responsibilities (scheduling logic and channel connection logic) and does not align with the domain architecture defined in `docs/domains/INDEX.md`. The goal is to eliminate the `communication` folder by distributing its contents to `scheduling` and `connections` modules, ensuring a clean separation of concerns.

## What Changes
- **Move Scheduling Logic**: All files related to appointments, availability, and event types will be moved from `backend/src/modules/communication` to `backend/src/modules/scheduling`.
- **Move Connection Logic**: `ChannelConnection` and `ChannelType` entities will be consolidated in `backend/src/modules/connections`.
- **Update Imports**: All references to `src.modules.communication` will be updated to point to the new locations.
- **Delete Folder**: The `backend/src/modules/communication` directory will be deleted.

## Impact
- **Affected Specs**: `module_scheduling.md`, `module_connections.md`.
- **Affected Code**: 
    - `backend/src/modules/communication` (deleted)
    - `backend/src/modules/scheduling` (populated)
    - `backend/src/modules/connections` (populated)
    - `backend/src/modules/sales_agent` (imports updated)
    - `backend/src/main.py` (router registration updated)

## ADDED Requirements
### Requirement: Scheduling Domain Structure
The `scheduling` module SHALL contain:
- Domain: `Appointment`, `AvailabilitySchedule`, `EventType`, `AppointmentStatus`.
- Application: `AvailabilityService`, `EventTypeService`.
- Infrastructure: `AppointmentModel`, `BookingLinkModel`.
- API: `event_types`, `public_links`, `calendar` (scheduling endpoints).

### Requirement: Connections Domain Structure
The `connections` module SHALL contain:
- Domain: `ChannelConnection`, `ChannelType`, `GmailStatus`, `CalendarStatus`.
- Infrastructure: `ChannelRepository` (if applicable), `GoogleCalendarAdapter`, etc.

## MODIFIED Requirements
### Requirement: Refactor Imports
**Reason**: To support the new directory structure.
**Migration**: Use search and replace to update all `from src.modules.communication...` to `from src.modules.scheduling...` or `from src.modules.connections...`.

## REMOVED Requirements
### Requirement: Communication Module
**Reason**: Redundant and ambiguous module name.
**Migration**: Logic moved to `scheduling` and `connections`.
