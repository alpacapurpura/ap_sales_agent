# Tasks

- [x] Task 1: Frontend - Remove Dashboard Navigation and Redirect
  - [x] Edit `frontend/src/components/shared/layout/app-sidebar.tsx`: Remove "Resumen" item from `navItems`.
  - [x] Edit `frontend/src/app/(main)/(dashboard)/page.tsx`: Replace content with a redirect to `/brand-settings`.
- [x] Task 2: Frontend - Delete Dashboard Feature
  - [x] Delete `frontend/src/features/dashboard` directory.
  - [x] Delete `frontend/src/lib/api/dashboard.ts`.
- [x] Task 3: Backend - Remove Dashboard Router Registration
  - [x] Edit `backend/src/main.py`: Remove `dashboard` import and `app.include_router`.
- [x] Task 4: Backend - Delete Dashboard Implementation
  - [x] Delete `backend/src/api/routers/dashboard.py`.
  - [x] Delete `backend/src/services/dashboard_service.py`.
  - [x] Delete `backend/src/core/domain/dashboard_schema.py`.
