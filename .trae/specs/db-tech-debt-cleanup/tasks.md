# Tasks

- [x] Task 1: Audit and Create Migration for Missing Indexes
  - [x] SubTask 1.1: Identify all tables missing `tenant_id` index (Lead, Message, AgentTrace, LLMCallLog, etc.).
  - [x] SubTask 1.2: Generate Alembic migration script to add `tenant_id` indexes using `postgresql_concurrently=True` pattern.
  - [x] SubTask 1.3: Verify the migration script locally.

- [x] Task 2: Clean Up Redundant Indexes
  - [x] SubTask 2.1: Identify redundant indexes (e.g., `User.clerk_id`, `Tenant.slug`).
  - [x] SubTask 2.2: Generate migration to drop redundant indexes using `concurrently=True` (if applicable/safe).
  - [x] SubTask 2.3: Update SQLAlchemy models (`User`, `Tenant`) to remove `index=True` where `unique=True` is present.

- [ ] Task 3: Enforce Referential Integrity in Marketing Module
  - [ ] SubTask 3.1: Generate migration to add FK constraints to `CustomerProfile`, `CustomerIdentity`, `JourneyEvent` linking `tenant_id` to `tenants`.
  - [ ] SubTask 3.2: Use `NOT VALID` followed by `VALIDATE CONSTRAINT` pattern in the migration to avoid locking.
  - [ ] SubTask 3.3: Update `marketing.py` models to include `ForeignKey` definitions.

- [ ] Task 4: Verify Database Performance
  - [ ] SubTask 4.1: Run `EXPLAIN ANALYZE` on a sample query filtering by `tenant_id` to confirm index usage.
  - [ ] SubTask 4.2: Ensure no table locks persist after migration.

# Task Dependencies
- [Task 4] depends on [Task 1] and [Task 3].
- [Task 3] depends on [Task 1] (indexes first is generally safer/better practice though not strictly required for FKs unless enforcing uniqueness).
