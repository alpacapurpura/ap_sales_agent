---
ticket: T-be-2
story: luana-vitalia-bootstrap
title: "SQLAlchemy 2.0 ORM models (11 Mapped[] models)"
state: done
verdict: tests-passing
impl_date: 2026-05-14
builder: claude-sonnet-4-6
---

# T-be-2 Result

## Summary

11 SQLAlchemy 2.0 ORM model classes created with full `Mapped[]` declarations,
mirroring the T-be-1 Alembic migration DDL exactly. All inherit from
`luana_core_platform.domain.base_entity.Base`. 89 new tests pass (25 unit +
64 architecture). No Postgres required.

## Deliverables

| File | Status |
|---|---|
| `vitalia/backend/conftest.py` | modified (sys.path for luana_core_platform) |
| `vitalia/backend/src/__init__.py` | created |
| `vitalia/backend/src/modules/__init__.py` | created |
| `vitalia/backend/src/modules/vitalia/infrastructure/__init__.py` | created |
| `vitalia/backend/src/modules/vitalia/infrastructure/models/__init__.py` | created |
| `vitalia/backend/src/modules/vitalia/infrastructure/models/booking_model.py` | created |
| `vitalia/backend/src/modules/vitalia/infrastructure/models/treatment_followup_model.py` | created |
| `vitalia/backend/src/modules/vitalia/infrastructure/models/consent_record_model.py` | created |
| `vitalia/backend/src/modules/vitalia/infrastructure/models/medical_audit_log_model.py` | created |
| `vitalia/backend/src/modules/vitalia/infrastructure/models/payment_intent_model.py` | created |
| `vitalia/backend/src/modules/vitalia/infrastructure/models/payment_schedule_model.py` | created |
| `vitalia/backend/src/modules/vitalia/infrastructure/models/adherence_record_model.py` | created |
| `vitalia/backend/src/modules/vitalia/infrastructure/models/doctor_extension_model.py` | created |
| `vitalia/backend/src/modules/vitalia/infrastructure/models/medical_history_model.py` | created |
| `vitalia/backend/src/modules/vitalia/infrastructure/models/plan_tier_config_model.py` | created |
| `vitalia/backend/tests/unit/__init__.py` | created |
| `vitalia/backend/tests/unit/test_models_import.py` | created (25 tests) |
| `vitalia/backend/tests/architecture/__init__.py` | created |
| `vitalia/backend/tests/architecture/test_vitalia_no_query_without_tenant_filter.py` | created (64 tests) |

## Test results

```
102 passed, 3 skipped
(3 skipped = @pytest.mark.integration requiring live Postgres — expected)
```

## Acceptance criteria

| A | Description | Status |
|---|---|---|
| A1 | All 11 models importable + register to Base.metadata | PASS (25 unit tests) |
| A2 | All models have tenant_id index (except plan_tier cross-tenant) | PASS (64 arch tests) |

## Quality gates

- `Mapped[]` SQLA 2.0 style — no `Column()`, no `session.query()` ✓
- `DateTime(timezone=True)` UTC, `server_default=func.now()` — no `datetime.utcnow()` ✓
- `tenant_id NOT NULL + index=True` on all 10 tenant-scoped models ✓
- `VitaliaPlanTierConfigModel` has NO `tenant_id` (CROSS-TENANT) ✓
- `VitaliaMedicalAuditLogModel` has NO `deleted_at` (IMMUTABLE) ✓
- Soft-delete via `deleted_at` nullable on 5 tenant-scoped models ✓
- `UniqueConstraint("tenant_id", "doctor_id")` on `VitaliaDoctorExtensionModel` ✓
- `VitaliaPatientMedicalHistoryModel` + `VitaliaPatientDentalHistoryModel` in one file (per § 3.1) ✓
- All inherit from `luana_core_platform.domain.base_entity.Base` (D1 decision) ✓
- Ruff: 0 errors (16 auto-fixed I001/F401) ✓
- No `print()` / `logging.*` in model files ✓
- No Pydantic `BaseModel` / `BaseEntity` inheritance on ORM models ✓

## Model summary

| Model | Table | tenant_id | deleted_at | Special |
|---|---|---|---|---|
| VitaliaBookingModel | vitalia_bookings | ✓ NOT NULL | ✓ | 3 composite indexes |
| VitaliaTreatmentFollowupModel | vitalia_treatment_followups | ✓ NOT NULL | ✓ | |
| VitaliaConsentRecordModel | vitalia_consent_records | ✓ NOT NULL | — | Legal record |
| VitaliaMedicalAuditLogModel | vitalia_medical_audit_log | ✓ NOT NULL | — | IMMUTABLE, 2 composite indexes |
| VitaliaPaymentIntentModel | vitalia_payment_intents | ✓ NOT NULL | — | Financial, gateway_payment_id UNIQUE |
| VitaliaPaymentScheduleModel | vitalia_payment_schedules | ✓ NOT NULL | — | Financial |
| VitaliaAdherenceRecordModel | vitalia_adherence_records | ✓ NOT NULL | — | |
| VitaliaDoctorExtensionModel | vitalia_doctor_extensions | ✓ NOT NULL | ✓ | UniqueConstraint(tenant_id, doctor_id) |
| VitaliaPatientMedicalHistoryModel | vitalia_patient_medical_histories | ✓ NOT NULL | ✓ | |
| VitaliaPatientDentalHistoryModel | vitalia_patient_dental_histories | ✓ NOT NULL | ✓ | FDI odontogram fields |
| VitaliaPlanTierConfigModel | vitalia_plan_tier_configs | — | — | CROSS-TENANT, is_active flag |

## Blocks unblocked

- T-be-3 (Async repositories) — can proceed
- T-be-4 (Booking + Payment services) — can proceed

## Notes

- SQLAlchemy 2.0.49 + pydantic 2.13.4 installed in vitalia venv (were missing)
- `conftest.py` uses `sys.path.insert` for `luana_core_platform` workspace package
  (cyclic workspace deps prevent `pip install luana-core-platform`)
- Parallel T-extensions-1 test file excluded from scoped run (requires `luana_core_extension_sdk`)
- Integration tests (Postgres) remain 3 skipped — will pass with Docker runtime
