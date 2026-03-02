# Tasks

- [x] Task 1: Verify Backend Status Endpoint
  - [x] SubTask 1.1: Create `backend/scripts/verify_calendar_status.py` using `TestClient` and mocks to hit `GET /api/v1/connections/calendar/status`.
  - [x] SubTask 1.2: Run the script to detect 500 errors or crashes (likely import/SQLAlchemy issues).
  - [x] SubTask 1.3: Fix any backend issues found (e.g., imports, query structure).

- [x] Task 2: Verify Frontend Integration
  - [x] SubTask 2.1: Review `GoogleCalendarView` for potential render crashes (null checks).
  - [x] SubTask 2.2: Ensure `loading` state is correctly managed in `finally` block (already seems so, but double check).

- [x] Task 3: Manual Verification
  - [x] SubTask 3.1: Run the verification script again to ensure green.
