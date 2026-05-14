# T-be-7 Impl Log — BE endpoints + DTOs Pydantic v2 + FastAPI routes

## Ticket
T-be-7: BE endpoints + DTOs Pydantic v2 + FastAPI routes (response_model mandatory)

## Skills Consulted
- `tessl__fastapi`: Annotated header deps, response_model mandatory, redirect_slashes=False on app not router, StreamingResponse exception for CSV export
- `tessl__pytest-api-testing`: httpx.AsyncClient + ASGITransport pattern, asyncio_mode=auto, fixture scoping
- `.claude/rules/tenant-isolation.md`: tenant_id from X-Tenant-ID header (authoritative), extra="forbid" on request DTOs

## Files Created
- `vitalia/backend/src/modules/vitalia/api/__init__.py`
- `vitalia/backend/src/modules/vitalia/api/dtos/__init__.py`
- `vitalia/backend/src/modules/vitalia/api/dtos/onboarding_dtos.py` — CreateClinicProfileRequest, PlanTierListResponse, OfferPresetResponse, SubscribeRequest/Response, OnboardingStatusResponse
- `vitalia/backend/src/modules/vitalia/api/dtos/booking_dtos.py` — 11 DTOs (create/list/confirm-payment/consent-sign/cancel/reschedule/available-slots), currency: str | None = None
- `vitalia/backend/src/modules/vitalia/api/dtos/consent_dtos.py` — ConsentRecordResponse (signed_ip excluded), ConsentRecordListResponse
- `vitalia/backend/src/modules/vitalia/api/dtos/treatment_dtos.py` — PatientSummary (phone_masked/email_masked/name_last_initial), PatientDetailResponse, TreatmentSummary/Detail/FollowupState, ManualHandoff/ReleaseHandoff/UploadMedicalPdf
- `vitalia/backend/src/modules/vitalia/api/dtos/compliance_dtos.py` — ComplianceEventItem (payload_redacted only)
- `vitalia/backend/src/modules/vitalia/api/routes.py` — 20+ endpoints, response_model= mandatory, TenantIdHeader Annotated, _parse_tenant_id() → 422
- `vitalia/backend/src/main.py` — FastAPI(redirect_slashes=False), include_router(vitalia_router)
- `vitalia/backend/tests/unit/api/__init__.py`
- `vitalia/backend/tests/unit/api/test_patient_dtos.py` — A4 PII masking 12 tests
- `vitalia/backend/tests/e2e/__init__.py`
- `vitalia/backend/tests/e2e/test_onboarding_dental_e2e.py` — 8 tests (A3 + V-F-5)
- `vitalia/backend/tests/e2e/test_booking_prepaid_dental_e2e.py` — 13 tests (V-F-6)
- `vitalia/backend/tests/e2e/test_cross_tenant_isolation_e2e.py` — 12 tests (A2 + V-F-9)

## Key Decisions
- `redirect_slashes=False` on FastAPI app (main.py), NOT on APIRouter (per arch test enforcement)
- `extra="forbid"` on all request DTOs — prevents tenant_id body injection attack
- CSV export uses StreamingResponse (no response_model= allowed) — PII guard at ComplianceEventService.sanitize_payload() write time
- PatientSummary: phone_masked/email_masked/name_last_initial only (HIPAA-lite per 03-arch-be.md § 7.2)
- currency: str | None = None on monetary DTOs (never hardcoded 'USD')
- Stub implementations (no live DB) — real DI wiring in integration phase
- FastAPI + starlette + python-multipart + structlog added to pyproject.toml via uv add

## Validators Result
- V-F-5 (test_onboarding_dental_e2e.py): 8/8 PASS
- V-F-6 (test_booking_prepaid_dental_e2e.py): 13/13 PASS
- V-F-9 (test_cross_tenant_isolation_e2e.py): 12/12 PASS
- A4 unit (test_patient_dtos.py): 12/12 PASS
- Total: 45/45 PASS
- Architecture fitness: 151/151 PASS
- Ruff lint + format: clean
