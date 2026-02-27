# Tasks
- [x] Task 1: Refactor `shared/domain/schema.py` (The God Object)
  - [x] SubTask 1.1: Identify all models in `shared/domain/schema.py` and their target modules.
  - [x] SubTask 1.2: Move `FunnelStage`, `LeadStatus`, `ProductLaunchStage`, `BusinessStage` to `src/modules/sales/domain/lead_enums.py` (or create if needed).
  - [x] SubTask 1.3: Move `UserProfile` to `src/modules/sales/domain/lead_models.py`.
  - [x] SubTask 1.4: Move `IncomingMessage`, `OutgoingMessage` to `src/modules/communication/domain/message_models.py`.
  - [x] SubTask 1.5: Move `AISettings`, `TenantSettingsUpdate`, `TenantPermissionUpdate`, `TenantProfile`, `SystemUserProfile` to `src/modules/iam/domain/tenant_models.py`.
  - [x] SubTask 1.6: Move `BrandIdentity`, `BrandStrategy`, `BrandStory`, `BrandTeam` to `src/modules/marketing/domain/brand_models.py`.
  - [x] SubTask 1.7: Move `AIProvider`, `PromptSource` to `src/shared/domain/ai_enums.py` (since these are truly shared/core).
  - [x] SubTask 1.8: Update ALL imports across the codebase to point to the new locations. (Use `grep` to find usages).
  - [x] SubTask 1.9: Delete `shared/domain/schema.py`.

- [x] Task 2: Rename Generic "schema.py" Files
  - [x] SubTask 2.1: Rename `src/modules/content/domain/landing_page/schema.py` to `src/modules/content/domain/landing_page/content_schemas.py`.
  - [x] SubTask 2.2: Rename `src/modules/content/domain/offer/schema.py` to `src/modules/content/domain/offer/offer_schemas.py`.
  - [x] SubTask 2.3: Rename `src/modules/content/domain/offer/ai_schema.py` to `src/modules/content/domain/offer/offer_ai_schemas.py`.
  - [x] SubTask 2.4: Rename `src/modules/marketing/domain/brand_schema.py` to `src/modules/marketing/domain/brand_models.py`.
  - [x] SubTask 2.5: Update imports for these renamed files.

- [x] Task 3: Centralize Tenant Logic (Admin Refactor)
  - [x] SubTask 3.1: Create `TenantService` in `src/modules/iam/application/services/tenant_service.py` with methods: `create_tenant`, `update_tenant`, `get_tenants`.
  - [x] SubTask 3.2: Refactor `src/admin/modules/tenants.py` to use `TenantService` instead of direct DB calls. (Ensure Admin app can import and use the service).

- [x] Task 4: Verify Architecture Compliance
  - [x] SubTask 4.1: Run `back-arch-auditor` skill checks again (manually or via tool) to ensure no generic names remain.
  - [x] SubTask 4.2: Ensure all tests pass (if any).
