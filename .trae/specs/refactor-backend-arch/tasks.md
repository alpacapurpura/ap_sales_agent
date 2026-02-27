# Tasks

- [x] Task 1: Move AI Services to Core
  - [x] SubTask 1.1: Create `src/core/services` if needed (it exists).
  - [x] SubTask 1.2: Move `landing_generator_service.py`, `offer_generator_service.py`, `image_analysis_service.py`, `semantic_router.py`, `chat_orchestrator.py` to `src/core/services/`.
  - [x] SubTask 1.3: Update imports within these moved files (fix relative imports).
  - [x] SubTask 1.4: Search and update all references to these services in the codebase (using `grep`).

- [x] Task 2: Move Channels to Infrastructure
  - [x] SubTask 2.1: Move `src/channels/` to `src/services/channels/`.
  - [x] SubTask 2.2: Update imports in channel files.
  - [x] SubTask 2.3: Update references to `src.channels` in `main.py`, `routers`, etc.

- [x] Task 3: Refactor Telegram API
  - [x] SubTask 3.1: Rename `src/api/routers/channels.py` to `src/api/routers/telegram.py`.
  - [x] SubTask 3.2: Move `telegram_webhook_legacy` and `telegram_webhook_tenant` from `src/api/routes.py` to `src/api/routers/telegram.py`.
  - [x] SubTask 3.3: Ensure `telegram.py` handles both management (`/channels/telegram`) and webhooks (`/webhooks/telegram`) paths correctly.

- [x] Task 4: Refactor WhatsApp API
  - [x] SubTask 4.1: Move `verify_whatsapp_webhook` and `whatsapp_webhook` from `src/api/routes.py` to `src/api/routers/whatsapp.py`.
  - [x] SubTask 4.2: Refactor `whatsapp.py` to use `prefix="/whatsapp"` for management routes and explicit paths for webhooks to match `/webhooks/whatsapp`.
  - [x] SubTask 4.3: Ensure no logic is left in `src/api/routes.py`.

- [x] Task 5: Update Main and Cleanup
  - [x] SubTask 5.1: Update `src/main.py` to import new routers and remove `api_router` (old routes.py).
  - [x] SubTask 5.2: Delete `src/api/routes.py`.
  - [x] SubTask 5.3: Run `ruff check backend/src --fix` to verify imports and syntax.
