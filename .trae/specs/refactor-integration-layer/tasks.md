# Tasks

- [x] Task 1: Move Marketing Webhooks
  - [x] SubTask 1.1: Create `backend/src/modules/integration/api/marketing_webhooks.py` with content from `backend/src/modules/communication/api/webhooks_cdp.py`.
  - [x] SubTask 1.2: Delete `backend/src/modules/communication/api/webhooks_cdp.py`.
  - [x] SubTask 1.3: Update `backend/src/main.py` to import `marketing_webhooks` from `integration` and register the router.

- [x] Task 2: Move Marketing Connectors
  - [x] SubTask 2.1: Create directory `backend/src/modules/integration/infrastructure/marketing_connectors`.
  - [x] SubTask 2.2: Move `base.py`, `mailerlite.py`, and `shopify.py` from `backend/src/modules/marketing/infrastructure/connectors/` to the new directory.
  - [x] SubTask 2.3: Delete the old `connectors` directory in `marketing` (or keep empty if needed, but preferably remove).
  - [x] SubTask 2.4: Update imports in the moved files (if they refer to each other relatively).

- [x] Task 3: Verify and Cleanup
  - [x] SubTask 3.1: Check for any remaining references to the old paths using `grep`.
  - [x] SubTask 3.2: Run a quick check (e.g., `ruff check`) to ensure no import errors.
