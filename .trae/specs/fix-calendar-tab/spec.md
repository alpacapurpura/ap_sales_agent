# Fix Calendar Settings Tab Spec

## Why
The "Calendar" tab in Settings (under "Cierre de ventas") is reportedly not loading ("No carga nada"). This suggests a potential failure in fetching the initial status or rendering the component, possibly due to backend API errors or frontend integration mismatches.

## What Changes
- **Backend**:
  - Verify and potentially fix `GET /api/v1/connections/calendar/status`.
  - Ensure all dependencies (Models: `ChannelConnection`, `ShareableLink`) are correctly imported and queried.
  - Add robust error handling to the status endpoint.
- **Frontend**:
  - Verify `GoogleCalendarView` handles API errors gracefully without crashing the UI.
  - Ensure `status` state updates correctly.
- **Verification**:
  - Add `backend/scripts/verify_calendar_status.py` to test the status endpoint end-to-end (simulated).

## Impact
- **Affected Specs**: Connections, Calendar.
- **Affected Code**:
  - `backend/src/modules/connections/api/calendar.py`
  - `frontend/src/features/connections/components/google-calendar-view.tsx`

## ADDED Requirements
### Requirement: Robust Status Fetching
The `GET /status` endpoint SHALL return a valid 200 response even if:
- No connection exists (returns `is_connected=False`).
- No booking link exists (returns `booking_link=None`).
- DB queries return empty results.

### Requirement: Frontend Error Handling
The `GoogleCalendarView` SHALL display an error message (Alert or Toast) if the API call fails, instead of rendering a blank screen.

## MODIFIED Requirements
### Requirement: Connection Status Logic
Refine the backend logic to ensure `ChannelConnection` query uses the correct model attributes and doesn't fail on missing tables/relations (related to recent SQLAlchemy issues observed).
