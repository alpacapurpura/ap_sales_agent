# Tasks

- [ ] Task 1: Create Compliance Router
  - [ ] SubTask 1.1: Create `backend/src/modules/connections/api/shopify_compliance.py`.
  - [ ] SubTask 1.2: Implement `customers/data_request`, `customers/redact`, and `shop/redact` endpoints.
  - [ ] SubTask 1.3: Apply `verify_shopify_signature` dependency.
- [ ] Task 2: Mount Router in Main
  - [ ] SubTask 2.1: Update `backend/src/main.py` to include `shopify_compliance` router under `/api/v1/connections/shopify/compliance`.
- [ ] Task 3: Update Documentation
  - [ ] SubTask 3.1: Add the new webhook URLs to `docs/guides/shopify_setup.md` under a "Compliance Webhooks" section.
