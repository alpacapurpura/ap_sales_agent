# Fix Availability View Spec

## Why
The "Availability" view in the frontend is not displaying the configured schedules, even though the backend logic seems to exist. Users report that the view remains empty or doesn't show the expected default availability.

## What Changes
- **Backend (Scheduling Module)**:
  - Robustify `AvailabilityService` to handle `tenant.config_json` being `None` or malformed.
  - Ensure `list_schedules` correctly initializes and persists a default schedule if none exists.
  - Add detailed logging to `list_schedules` and `create_schedule` to trace data flow.
- **Testing**:
  - Add integration tests for `AvailabilityService` to verify CRUD operations on `config_json`.
  - Add E2E API tests to verify the `/api/v1/connections/calendar/schedules` endpoint returns the expected JSON structure.

## Impact
- **Affected Specs**: Scheduling, Availability.
- **Affected Code**: 
  - `backend/src/modules/scheduling/application/services/availability_service.py`
  - `backend/src/modules/connections/api/calendar.py`

## ADDED Requirements
### Requirement: Default Schedule Initialization
The system SHALL automatically create and persist a default "Business Hours" schedule (Mon-Fri 9-17) if a tenant has no schedules configured.

#### Scenario: First Access
- **WHEN** a user accesses the Availability view for the first time (or API requests schedules).
- **THEN** the system checks for existing schedules.
- **IF** none found, it creates the default schedule in `tenant.config_json`.
- **AND** returns the newly created schedule in the response.

### Requirement: Robust Configuration Handling
The system SHALL handle cases where `tenant.config_json` is `None` or missing the `availability_schedules` key without crashing.

## MODIFIED Requirements
### Requirement: List Schedules
The `list_schedules` method in `AvailabilityService` will be updated to ensure robust handling of JSON storage and correct serialization of `AvailabilitySchedule` objects.
