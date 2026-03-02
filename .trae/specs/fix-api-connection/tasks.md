# Tasks

- [x] Task 1: Fix Backend Router Prefixes
  - [x] SubTask 1.1: Remove `prefix="/calendar"` from `backend/src/modules/connections/api/calendar.py`
  - [x] SubTask 1.2: Remove `prefix="/gmail"` from `backend/src/modules/connections/api/gmail.py`
  - [x] SubTask 1.3: Remove `prefix="/leads"` from `backend/src/modules/crm/api/leads.py`
  - [x] SubTask 1.4: Remove `prefix="/event-types"` from `backend/src/modules/scheduling/api/event_types.py`
  - [x] SubTask 1.5: Refactor `backend/src/modules/connections/api/telegram.py` endpoints to remove `/channels/telegram` prefix (use `/status`, `/connect`, `/test`, `/disconnect` instead)

- [x] Task 2: Update Frontend API Clients
  - [x] SubTask 2.1: Update `frontend/src/lib/api/assets.ts` (verify paths)
  - [x] SubTask 2.2: Update `frontend/src/lib/api/avatar.ts` to `/api/v1/brand/avatars`
  - [x] SubTask 2.3: Update `frontend/src/lib/api/settings.ts` to use `/api/v1/iam/*` and `/api/v1/brand/*`
  - [x] SubTask 2.4: Update `frontend/src/lib/api/whatsapp.ts` to `/api/v1/connections/whatsapp`
  - [x] SubTask 2.5: Update `frontend/src/lib/api/public.ts` to `/api/v1/scheduling/public`
  - [x] SubTask 2.6: Update `frontend/src/lib/api/leads.ts` to `/api/v1/crm/leads`
  - [x] SubTask 2.7: Update `frontend/src/lib/api/event-types.ts` to `/api/v1/scheduling/event-types`
  - [x] SubTask 2.8: Update `frontend/src/lib/api/connections.ts` (Telegram, Calendar, Gmail) to `/api/v1/connections/*`
  - [x] SubTask 2.9: Update `frontend/src/lib/api/booking-links.ts` to `/api/v1/connections/calendar/personalized-link`
  - [x] SubTask 2.10: Update `frontend/src/lib/api/availability.ts` to `/api/v1/connections/calendar/schedules`
  - [x] SubTask 2.11: Update `frontend/src/lib/api/offer-gallery.ts` to `/api/v1/assets/offers`
  - [x] SubTask 2.12: Update `frontend/src/lib/api/admin.ts` to `/api/v1/iam/tenants`

- [x] Task 3: Verification
  - [x] SubTask 3.1: Verify all API endpoints are reachable and return 200/201.
