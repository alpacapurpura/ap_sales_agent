---
ticket: T-be-2
story: luana-vitalia-bootstrap
title: "SQLAlchemy 2.0 ORM models (11 Mapped[] models)"
state: done
impl_date: 2026-05-14
builder: claude-sonnet-4-6
---

# T-be-2 Implementation Log

## Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `backend-expert` | ALWAYS — runtime quality checklist, DDD Inside-Out pattern | Read `runtime-quality-checklist.md`; applied Mapped[] 2.0 style, `DateTime(timezone=True)`, `func.now()` server_default, no `datetime.utcnow()`, no `Column()`, no `session.query()` |
| `tessl__fastapi` | ALWAYS — async patterns, Annotated deps | No routes in this ticket; confirmed pattern for future T-be-7 |
| `tessl__pytest-api-testing` | ALWAYS — fixture scoping, factory fixtures, DB isolation | Used pure-import tests (no Postgres required), parametrize for 11 tables, function-scoped implicit |

## Step 0.5 Default-flip detection

No `core/config.py` changes in this ticket. N/A.

## Anti-duplication Step 0 GATE

```bash
# From 03-arch-be.md § 2 pre-flight (already done by architect):
grep -rln "class.*Booking" backend/src/modules/scheduling/ backend/src/shared/
# → BookingLink (different semantic — lead-gen slot, not medical booking)
# → VitaliaBookingModel: NEW justified
```

No blocking collisions. All 11 vitalia tables are NEW per architect pre-flight.

## Scope verified

Ticket touches only `vitalia/backend/src/modules/vitalia/infrastructure/models/` —
no copilot, no sales_agent, no AISALESHT modules.

## Decisions honored

| Decision | Implementation |
|---|---|
| D1 (brand isolation independent chain) | All models inherit from `luana_core_platform.domain.base_entity.Base` — independent alembic chain |
| tenant_id NOT NULL + indexed on 10 tenant-scoped models | `mapped_column(PgUUID(as_uuid=True), nullable=False, index=True)` on every tenant-scoped model |
| plan_tier_configs CROSS-TENANT | No `tenant_id` column on `VitaliaPlanTierConfigModel` |
| medical_audit_log IMMUTABLE | No `deleted_at` column on `VitaliaMedicalAuditLogModel` |
| DateTime(timezone=True) UTC | All timestamp columns use `DateTime(timezone=True)` + `func.now()` server_default |
| Enum types reference pg types without create_type | Column types use `String(N)` — enum validation is DB-enforced via migration DDL |

## TDD flow

**RED:** ran tests before creating any model files → `ModuleNotFoundError` on all 11
**GREEN:** created 10 model files + `__init__.py` → 89 new tests pass

## Environment setup

- SQLAlchemy 2.0.49 installed in vitalia venv (was missing)
- pydantic 2.13.4 installed
- `conftest.py` extended with `sys.path.insert` for `luana_core_platform` workspace package
  (cyclic deps prevent `pip install luana-core-platform` — workspace pattern)
- luana_core_platform.Base = `declarative_base()` singleton — shared across all vitalia models

## Files created

| File | Description |
|---|---|
| `conftest.py` | Added sys.path.insert for luana_core_platform workspace |
| `src/__init__.py` | Package marker |
| `src/modules/__init__.py` | Package marker |
| `src/modules/vitalia/infrastructure/__init__.py` | Package marker |
| `src/modules/vitalia/infrastructure/models/__init__.py` | Re-exports all 11 model classes |
| `src/modules/vitalia/infrastructure/models/booking_model.py` | VitaliaBookingModel (tenant + soft-delete) |
| `src/modules/vitalia/infrastructure/models/treatment_followup_model.py` | VitaliaTreatmentFollowupModel (tenant + soft-delete) |
| `src/modules/vitalia/infrastructure/models/consent_record_model.py` | VitaliaConsentRecordModel (tenant, no deleted_at — legal) |
| `src/modules/vitalia/infrastructure/models/medical_audit_log_model.py` | VitaliaMedicalAuditLogModel (IMMUTABLE — no deleted_at) |
| `src/modules/vitalia/infrastructure/models/payment_intent_model.py` | VitaliaPaymentIntentModel (tenant, no deleted_at — financial) |
| `src/modules/vitalia/infrastructure/models/payment_schedule_model.py` | VitaliaPaymentScheduleModel (tenant, no deleted_at — financial) |
| `src/modules/vitalia/infrastructure/models/adherence_record_model.py` | VitaliaAdherenceRecordModel (tenant, no deleted_at) |
| `src/modules/vitalia/infrastructure/models/doctor_extension_model.py` | VitaliaDoctorExtensionModel (tenant + soft-delete + UniqueConstraint) |
| `src/modules/vitalia/infrastructure/models/medical_history_model.py` | VitaliaPatientMedicalHistoryModel + VitaliaPatientDentalHistoryModel (2 classes, 1 file) |
| `src/modules/vitalia/infrastructure/models/plan_tier_config_model.py` | VitaliaPlanTierConfigModel (CROSS-TENANT, no tenant_id) |
| `tests/unit/__init__.py` | Package marker |
| `tests/unit/test_models_import.py` | 25 unit tests — A1 acceptance criterion |
| `tests/architecture/__init__.py` | Package marker |
| `tests/architecture/test_vitalia_no_query_without_tenant_filter.py` | 64 arch fitness tests — A2 acceptance criterion |

## Test results

```
102 passed, 3 skipped
(3 skipped = @pytest.mark.integration requiring Postgres — already present from T-be-1)
```

Breakdown:
- 25 unit tests (test_models_import.py)
- 64 architecture tests (test_vitalia_no_query_without_tenant_filter.py)
- 12 migration parse tests (T-be-1, preserved)
- 1 smoke test

## Lint

```
ruff check: All checks passed (16 I001/F401 auto-fixed)
```

## Notes on parallel session

`tests/unit/test_extensions_register_all.py` exists from the parallel T-extensions-1 session.
It requires `luana_core_extension_sdk` which is NOT installed in the vitalia venv.
Per parallel-safety M1 rule, that file was NOT touched — only T-be-2 files staged.
Run `pytest tests/unit/test_models_import.py tests/architecture/ tests/migrations/ tests/test_smoke.py`
to scope tests to T-be-2 (exclude parallel session's test).

## Cross-module reads

None. T-be-2 is self-contained — ORM models are declarative Python classes with no runtime deps.
