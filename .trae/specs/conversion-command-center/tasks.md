# Tasks

- [ ] Task 1: Backend - Implement CRM Sales Logic (The Transaction Engine)
    - [ ] SubTask 1.1: Create `Sale` domain model in `backend/src/modules/crm/domain/sale.py` with full fields (`offer_id`, `stage`, `transaction_id`, `payment_method`, etc.).
    - [ ] SubTask 1.2: Create `SaleModel` in `backend/src/modules/crm/infrastructure/models/sale_model.py` with Foreign Keys to `customer_profiles` and `products`.
    - [ ] SubTask 1.3: Create `SaleRepository` in `backend/src/modules/crm/infrastructure/repositories/sale_repository.py`.
    - [ ] SubTask 1.4: Create `SaleService` in `backend/src/modules/crm/application/services/sale_service.py` (Include logic for CONVERSION vs EXPANSION check).
    - [ ] SubTask 1.5: Register `sales` router in `backend/src/main.py` (under CRM prefix).

- [ ] Task 2: Backend - Implement Scheduling Infrastructure
    - [ ] SubTask 2.1: Create `AppointmentRepository` in `backend/src/modules/scheduling/infrastructure/repositories/appointment_repository.py`.
    - [ ] SubTask 2.2: Add method `get_appointments_by_date_range(start, end, tenant_id)`.

- [ ] Task 3: Backend - Implement CRM Dashboard Aggregator
    - [ ] SubTask 3.1: Create `backend/src/modules/crm/api/dashboard.py`.
    - [ ] SubTask 3.2: Implement `GET /pipeline` (Lane 1): Fetch leads with high `intent_score` from `LeadRepository`.
    - [ ] SubTask 3.3: Implement `GET /agenda` (Lane 2): Fetch appointments with `time_range` query param (today, week).
    - [ ] SubTask 3.4: Implement `GET /ticker` (Lane 3): Fetch sales with `time_range` query param (default 30d).
    - [ ] SubTask 3.5: Register `dashboard` router in `backend/src/main.py` (under CRM prefix).
    - [ ] SubTask 3.6: Remove old `backend/src/modules/sales_agent/api/dashboard.py`.

- [ ] Task 4: Frontend - Create Conversion Command Center UI (The View)
    - [ ] SubTask 4.1: Scaffold `conversion-command-center` in `frontend/src/features/sales/components/dashboard`.
    - [ ] SubTask 4.2: Implement `OpportunityLane` (Left) - "Nutrición".
    - [ ] SubTask 4.3: Implement `AgendaLane` (Center) - "Conversión" with Week/Today toggle.
    - [ ] SubTask 4.4: Implement `SalesLane` (Right) - "Crecimiento" with 30-day view and goal progress.

- [ ] Task 5: Integration & Cleanup
    - [ ] SubTask 5.1: Create frontend API client `crm-dashboard-api.ts`.
    - [ ] SubTask 5.2: Replace old widgets in `dashboard-page.tsx`.
    - [ ] SubTask 5.3: Verify "Full-Funnel" data flow (Lead -> Appointment -> Sale).

# Task Dependencies
- Task 3 depends on Task 1 and Task 2.
- Task 5 depends on Task 3 and Task 4.
