# Tasks

- [x] Task 1: Migrate Growth Module to CRM
  - [x] Move `growth/domain/*` to `crm/domain/` (lead.py, customer.py, enums.py, event.py)
  - [x] Move `growth/infrastructure/models/*` to `crm/infrastructure/models/`
  - [x] Move `growth/infrastructure/repositories/*` to `crm/infrastructure/repositories/`
  - [x] Move `growth/infrastructure/engines/*` to `crm/infrastructure/engines/`
  - [x] Move `growth/application/services/*` to `crm/application/services/` (lead_service, customer_service, identity_service)
  - [x] Move `growth/api/leads.py` and `growth/api/cdp.py` to `crm/api/`
  - [x] Move `growth/api/dto/*` to `crm/api/dto/`
  - [x] Update imports in moved files to point to `src.modules.crm` instead of `src.modules.growth` or `src.modules.sales`

- [x] Task 2: Migrate Growth Metrics to Analytics
  - [x] Move `growth/api/metrics.py` to `analytics/api/metrics.py`
  - [x] Move `growth/application/services/metrics_service.py` to `analytics/application/services/metrics_service.py`
  - [x] Update imports in metrics files to point to `src.modules.analytics`

- [x] Task 3: Migrate Communication Module to Scheduling
  - [x] Move `communication/domain/*` to `scheduling/domain/`
  - [x] Move `communication/infrastructure/models/*` to `scheduling/infrastructure/models/`
  - [x] Move `communication/application/services/*` to `scheduling/application/services/`
  - [x] Move `communication/api/*` (including DTOs) to `scheduling/api/`
  - [x] Update imports in moved files to point to `src.modules.scheduling` instead of `src.modules.communication`

- [x] Task 4: Update Main Application Entry Point
  - [x] Update `backend/src/main.py` to import routers from `crm`, `analytics`, and `scheduling`
  - [x] Remove imports from `communication`, `marketing`, and `sales` (if related to growth)

- [x] Task 5: Cleanup and Verification
  - [x] Verify no references to `src.modules.growth` remain
  - [x] Verify no references to `src.modules.communication` remain
  - [x] Delete `backend/src/modules/growth` directory
  - [x] Delete `backend/src/modules/communication` directory
