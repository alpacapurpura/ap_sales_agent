# Database Technical Debt Cleanup Spec

## Why
The current database schema lacks critical indexes on foreign keys (specifically `tenant_id`), which severely impacts query performance in a multi-tenant architecture. Additionally, recent migrations have introduced blocking operations and redundant indexes, violating high-availability best practices. Fixing this is essential for system stability and scalability.

## What Changes
- **Add Indexes**: Create B-tree indexes on `tenant_id` for all tenant-scoped tables (Leads, Messages, Traces, etc.).
- **Optimize Indexes**: Remove redundant indexes where a Unique Constraint already exists (e.g., `User.clerk_id`, `Tenant.slug`).
- **Standardize FKs**: Enforce Foreign Key constraints on Marketing models (`CustomerProfile`, `JourneyEvent`) which currently lack them.
- **Migration Safety**: Implement a strict "Safe Migration" pattern using `concurrently` for indexes and `NOT VALID` for constraints in all new migrations.

## Impact
- **Affected specs**: Backend Database Performance, Multi-tenancy.
- **Affected code**: `backend/src/services/db/models/`, `backend/alembic/versions/`.
- **Breaking Changes**: None. The changes are additive (indexes/constraints) or optimizations.

## ADDED Requirements
### Requirement: Tenant ID Indexing
All tables with a `tenant_id` column SHALL have a non-unique B-tree index on that column to optimize tenant-scoped queries.

#### Scenario: Query Performance
- **WHEN** filtering `Leads` by `tenant_id`
- **THEN** the database uses an Index Scan instead of a Sequential Scan.

### Requirement: Marketing Integrity
`CustomerProfile`, `CustomerIdentity`, and `JourneyEvent` tables SHALL have foreign key constraints linking `tenant_id` to the `tenants` table.

## MODIFIED Requirements
### Requirement: Unique Index Definition
**Modified**: Models SHALL NOT define `index=True` on columns that already have `unique=True`, as this creates redundant indexes.

## REMOVED Requirements
### Requirement: Redundant Indexes
**Reason**: Postgres automatically creates a unique index for Unique Constraints.
**Migration**: Drop the explicit extra index if it exists separately.
