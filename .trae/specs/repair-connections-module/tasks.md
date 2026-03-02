# Tasks

- [x] Task 1: Fix `main.py` imports
    - [ ] Update `src.modules.integration` to `src.modules.connections` in `backend/src/main.py`.
- [x] Task 2: Fix `connections` module internal imports
    - [ ] Update `src.modules.integration` to `src.modules.connections` in `backend/src/modules/connections/api/whatsapp.py`.
    - [ ] Update `src.modules.integration` to `src.modules.connections` in `backend/src/modules/connections/api/telegram.py`.
    - [ ] Update `src.modules.integration` to `src.modules.connections` in `backend/src/modules/connections/api/webhook.py`.
    - [ ] Scan and fix other files in `backend/src/modules/connections/` for similar issues.
- [x] Task 3: Fix external module imports
    - [ ] Update `src.modules.integration` to `src.modules.connections` in `backend/src/modules/scheduling/application/services/availability_service.py`.
    - [ ] Run a global grep for `src.modules.integration` and fix any remaining occurrences.
- [x] Task 4: Verify application startup
    - [ ] Run a check (e.g., `python -c "from src.main import app"`) to ensure no ImportErrors remain.
