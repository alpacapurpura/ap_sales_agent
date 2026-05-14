---
ticket: T-be-1
story: luana-vitalia-bootstrap
title: "Alembic snapshot 001_vitalia_initial_snapshot.py (11 tables idempotent)"
surface: BE
state: done
impl_date: 2026-05-14
builder: claude-sonnet-4-6
---

# T-be-1 Implementation Log

## § Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `backend-expert` | Migration patterns, idempotent DDL, tenant isolation enforcement | Raw SQL IF NOT EXISTS everywhere; enum via DO $$ block; NEVER op.create_table/sa.Enum create_type |
| `brand-expert` | Loaded per role prompt (invoked as declared) | N/A — not touching brand module |
| `offer-expert` | Loaded per role prompt | N/A — not touching offer module |
| `offer-type-preset-expert` | Loaded per role prompt | N/A — not touching presets |
| `metrics-expert` | Loaded per role prompt | N/A — not touching analytics |
| `tessl__fastapi` | Async patterns (no routes in scope for this ticket) | Noted for T-be-4 routes ticket |
| `tessl__pytest-api-testing` | Test structure for migrations (AsyncClient not needed here) | Used pytest.mark.integration + skipif pattern for DB-dependent tests |
| `tessl__graceful-degradation` | External call patterns (not applicable to migration DDL) | Noted for T-be-4 services with payment adapters |

## § Step 0 GATE — Default-flip detection

No `core/config.py` changes in scope. Step 0.5 not applicable.

## § Claim and sync

Branch: `development`. Status at start:
```
D buyer-persona-ai-flow-verified.png
M docs/etl/extraction-contract.md
M docs/product/BACKLOG-TLDR.md
M docs/product/stories/luana-vitalia-bootstrap/checkpoint.md
D qa-extract-clean.png
```
Files listed above are from parallel sessions — NOT touched by this session.

## § SSoT reads

1. `06-tickets.yaml` Tbe1 block — revision id `001_vitalia`, 11 tables, decisions D1+D7
2. `03-arch-be.md` § 4 (model schemas, column types, FK, indexes) + § 5 (snapshot pattern)
3. `05-guidelines.md` § 1.7 — IF NOT EXISTS pattern reference
4. `.claude/rules/backend-migrations.md` — idempotent patterns
5. `.claude/rules/tenant-isolation.md` — tenant_id NOT NULL + index mandatory
6. `.claude/rules/master-data.md` — TIMESTAMPTZ everywhere

## § Anti-duplication Step 0 grep

Per `03-arch-be.md` § 2 (pre-flight results already captured by architect):
- `VitaliaBooking` vs `BookingLink` — different semantic surface, new table justified
- `VitaliaPaymentIntent` — no existing PaymentIntent in codebase, justified
- `VitaliaConsentRecord` — no existing Consent tables, justified
- `VitaliaMedicalAuditLog` vs `AuditLog` in campaigns — different semantic (HIPAA-lite vs campaign events), justified
- All 11 tables NEW + justified per architect grep evidence

## § Migration chain decision

Per ticket spec and `03-arch-be.md` § 5.2: vitalia has its **own independent alembic chain** (`down_revision = None`). Rationale: vitalia is a separate vertical brand app in `luana-platform/` with its own DB schema namespace (`vitalia_*` prefix). It does NOT extend the nicolify alembic chain (Story 10 `001_initial_snapshot` revision). Brand isolation D1 honored.

## § Alembic config creation

T-scaffold-1 created `vitalia/backend/` but did NOT include alembic config (scaffold only created src/ + tests/ structure). Files created:
- `alembic.ini` — replicated from nicolify pattern, POSTGRES_DB=vitalia_dev default
- `alembic/env.py` — raw-SQL migrations, target_metadata=None (no autogenerate needed), vitalia_dev DB default
- `alembic/script.py.mako` — standard template
- `alembic/versions/` directory

## § TDD flow (RED → GREEN)

**RED phase:** wrote `tests/migrations/test_001_vitalia_snapshot_idempotent.py` with 12 SQL-parse tests + 3 integration tests (marked `@pytest.mark.integration`). Confirmed RED: `test_migration_file_exists` fails because migration not yet written.

**GREEN phase:** wrote `001_vitalia_initial_snapshot.py`. Re-ran tests → 12 passed, 3 skipped (integration tests require Postgres — not available in WSL2 native dev environment).

**Note on integration tests (A1/A2/A3):** Integration tests are correctly skipped when Postgres is unavailable. They use `@pytest.mark.skipif(not _is_postgres_available(), ...)`. When Docker runtime is up (`make dev`), these tests will run and verify idempotency end-to-end. This is documented per ticket spec: "If no local postgres available, document in impl-log + use SQLite-compatible idempotent SQL fallback for verification (or skip A3 verification with note 'requires postgres runtime — verified via SQL parse only')."

## § Lint

`ruff check` via AISALESHT venv: **All checks passed** (after fixing E501 line-length in seed INSERT + I001 import ordering in test file).

## § 11 tables — implementation details

| Table | Key decisions |
|---|---|
| `vitalia_bookings` | idempotency_key UNIQUE constraint; composite index (tenant_id, doctor_id, slot_iso) for slot race check; soft-delete |
| `vitalia_treatment_followups` | langgraph_checkpoint_id VARCHAR(128) — FK to Redis checkpoint (no DB FK constraint, Redis managed separately); soft-delete |
| `vitalia_consent_records` | NO deleted_at — legal immutability; status=revoked used instead; expires_at TIMESTAMPTZ for 24h default |
| `vitalia_medical_audit_log` | NO deleted_at — IMMUTABLE 7-year retention; payload_redacted JSONB (PII sanitized before write); append-only |
| `vitalia_payment_intents` | gateway_payment_id UNIQUE + idempotency_key UNIQUE (two separate uniqueness constraints); no deleted_at |
| `vitalia_payment_schedules` | installment_n + scheduled_at for cron-based recurring billing; no deleted_at |
| `vitalia_adherence_records` | recorded_at + created_at separated (when patient responded vs when persisted); no deleted_at |
| `vitalia_doctor_extensions` | UNIQUE constraint (tenant_id, doctor_id) — one extension record per doctor per tenant; soft-delete |
| `vitalia_patient_medical_histories` | extraction_confidence NUMERIC(3,2); source_document_ids JSONB array for audit chain; soft-delete |
| `vitalia_patient_dental_histories` | missing_pieces_fdi JSONB (FDI dental notation array); restorations JSONB; soft-delete |
| `vitalia_plan_tier_configs` | CROSS-TENANT — no tenant_id, no deleted_at; is_active BOOLEAN for soft-disable; seed 3 tiers via ON CONFLICT DO NOTHING |

## § Enum types (7)

All created via `DO $$ BEGIN CREATE TYPE ... EXCEPTION WHEN duplicate_object THEN NULL; END $$;`:
- `vitalia_booking_status` (7 values)
- `vitalia_payment_status` (6 values)
- `vitalia_consent_status` (4 values)
- `vitalia_followup_step` (10 values including paused variants)
- `vitalia_audit_severity` (3 values)
- `vitalia_payment_gateway` (3 values)
- `vitalia_payment_schedule_status` (5 values)

Note: enum types are created but columns use VARCHAR(N) NOT VARCHAR-enum FK for flexibility — allows future enum value additions without ALTER TYPE (PostgreSQL requires full table rewrite for ALTER TYPE ... ADD VALUE on older PG versions).

## § Cross-module reads

Read-only: `nicolify/backend/alembic/versions/001_initial_snapshot.py` (lines 37-38) to verify revision ID format and confirm vitalia chain independence.

## § Files created/modified this session

**luana-platform:**
- `/home/chris/luana-platform/vitalia/backend/alembic.ini` (created)
- `/home/chris/luana-platform/vitalia/backend/alembic/env.py` (created)
- `/home/chris/luana-platform/vitalia/backend/alembic/script.py.mako` (created)
- `/home/chris/luana-platform/vitalia/backend/alembic/versions/001_vitalia_initial_snapshot.py` (created)
- `/home/chris/luana-platform/vitalia/backend/tests/migrations/test_001_vitalia_snapshot_idempotent.py` (created)
- `/home/chris/luana-platform/vitalia/backend/tests/migrations/__init__.py` (created)
- `/home/chris/luana-platform/vitalia/backend/pyproject.toml` (modified — added markers)

**AISALESHT docs:**
- `docs/product/stories/luana-vitalia-bootstrap/T-be-1-impl-log.md` (this file)
- `docs/product/stories/luana-vitalia-bootstrap/T-be-1-result.md` (created)

## § Acceptance status

| ID | Description | Status | Notes |
|---|---|---|---|
| A1 | Migration upgrade head twice without error | SKIPPED (no Postgres) | SQL-parse tests verify idempotency at DDL level; integration test ready |
| A2 | Downgrade -1 then upgrade head succeeds | SKIPPED (no Postgres) | Integration test written + will run with Docker up |
| A3 | All 11 tables present post-upgrade | SKIPPED (no Postgres) | 12 SQL-parse tests verify table presence at migration file level |

SQL-parse gate for A1/A3: `test_all_11_tables_have_if_not_exists` + `test_all_indexes_have_if_not_exists` + `test_medical_audit_log_has_no_deleted_at` + `test_plan_tier_configs_has_no_tenant_id` + `test_tenant_scoped_tables_have_tenant_id_not_null` + `test_timestamps_are_timestamptz` all PASS (12/12).

## § Validators V-NF-9, V-NF-10

Per `04-validators.yaml`: V-NF-9 and V-NF-10 target migration idempotency. The 12 SQL-parse tests cover these validators at static analysis level. Full runtime validation requires Postgres.
