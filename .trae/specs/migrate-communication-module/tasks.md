# Tasks

- [x] Task 1: Create Domain Enums in Connections
    - [ ] Create `backend/src/modules/connections/domain/enums.py`.
    - [ ] Move `ChannelType` from `backend/src/modules/sales_agent/domain/enums.py` (or define it if missing) to `connections/domain/enums.py`.

- [x] Task 2: Migrate Scheduling Files
    - [ ] Move `communication/domain/appointment.py` -> `scheduling/domain/appointment.py`.
    - [ ] Move `communication/domain/availability_schema.py` -> `scheduling/domain/availability_schema.py`.
    - [ ] Move `communication/domain/event_type_schema.py` -> `scheduling/domain/event_type_schema.py`.
    - [ ] Move `communication/domain/enums.py` (AppointmentStatus) -> `scheduling/domain/enums.py`.
    - [ ] Move `communication/infrastructure/models/appointment_model.py` -> `scheduling/infrastructure/models/appointment_model.py`.
    - [ ] Move `communication/infrastructure/models/booking_link.py` -> `scheduling/infrastructure/models/booking_link.py`.
    - [ ] Move `communication/application/services/availability_service.py` -> `scheduling/application/services/availability_service.py`.
    - [ ] Move `communication/application/services/event_type_service.py` -> `scheduling/application/services/event_type_service.py`.
    - [ ] Move `communication/api/event_types.py` -> `scheduling/api/event_types.py`.
    - [ ] Move `communication/api/public_links.py` -> `scheduling/api/public_links.py`.
    - [ ] Move `communication/api/dto/public_links.py` -> `scheduling/api/dto/public_links.py`.
    - [ ] Move `communication/api/dto/calendar.py` -> `scheduling/api/dto/calendar.py`.

- [x] Task 3: Migrate Connection Files
    - [ ] Move `communication/api/dto/gmail.py` -> `connections/api/dto/gmail.py` (create directory if needed).
    - [ ] Move `sales_agent/domain/channel.py` (if it contains ChannelConnection) to `connections/domain/channel.py`.

- [x] Task 4: Update Imports
    - [ ] Update imports in `backend/src/modules/sales_agent` to use `src.modules.connections.domain.channel`.
    - [ ] Update imports in `backend/src/modules/connections/api/calendar.py` to use `src.modules.scheduling`.
    - [ ] Update imports in `backend/src/main.py`.
    - [ ] Global search and replace for `src.modules.communication` to `src.modules.scheduling` (verify each case).

- [x] Task 5: Cleanup
    - [ ] Delete `backend/src/modules/communication` directory.
    - [ ] Verify application startup.

# Task Dependencies
- Task 4 depends on Task 1, Task 2, Task 3.
- Task 5 depends on Task 4.
