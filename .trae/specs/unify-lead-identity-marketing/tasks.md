# Tasks

- [x] Task 1: Database Schema & Migration (PostgreSQL Expert)
  - [x] SubTask 1.1: Update `IdentityType` enum in `customer.py` to include `whatsapp`, `telegram`, `instagram`, `tiktok`.
  - [x] SubTask 1.2: Create Alembic migration to add these types to the DB enum type (if using native PG Enum) or application check.
  - [x] SubTask 1.3: Create Alembic migration to migrate data from `leads` columns (`telegram_id`, etc.) to `customer_identities` table.
  - [x] SubTask 1.4: Create Alembic migration to remove/nullable old columns in `leads`.

- [x] Task 2: Implement Identity & Customer Services (Backend Architect)
  - [x] SubTask 2.1: Create `IdentityService` in `marketing/application/services`. Methods: `get_or_create_customer_by_identity(type, value)`.
  - [x] SubTask 2.2: Update `CustomerRepository` to support efficient lookups by identity join.
  - [x] SubTask 2.3: Ensure `LeadRepository` methods for "find active lead for customer" are optimized.

- [x] Task 3: Refactor Chat Orchestrator (Backend Expert)
  - [x] SubTask 3.1: Modify `ChatOrchestrator.process_chat_flow` to use `IdentityService` instead of direct `LeadRepository` lookup.
  - [x] SubTask 3.2: Verify that new flows correctly map to existing customers.
  - [x] SubTask 3.3: Ensure profile data updates (e.g. from conversation) are saved to `CustomerProfile.traits` (persistent) AND `Lead.profile_data` (contextual) if needed, or just `CustomerProfile`.

- [x] Task 4: Marketing Metrics Foundation (Data Engineer)
  - [x] SubTask 4.1: Implement `JourneyEventRepository` helpers to log standard events (page_view, mql_converted, sale_closed).
  - [x] SubTask 4.2: Create `MarketingMetricsService` with methods to calculate counts/sums for the 7 nodes (Adquisition, Activation, etc.).
  - [x] SubTask 4.3: Expose a basic API endpoint (or just service method for now) to test the aggregation queries.

- [x] Task 5: AI Architecture Documentation
  - [x] SubTask 5.1: Create `backend/src/modules/marketing/ARCHITECTURE_IA.md` explaining the conceptual model (Customer vs Identity vs Lead) and usage rules for future agents.

# Task Dependencies
- Task 2 depends on Task 1.
- Task 3 depends on Task 2.
- Task 4 is independent but relies on the new schema stability.
