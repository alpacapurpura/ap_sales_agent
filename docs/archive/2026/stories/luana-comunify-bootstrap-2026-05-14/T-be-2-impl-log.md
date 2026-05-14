---
ticket: T-be-2
story: luana-comunify-bootstrap
surface: BE
phase: build
state: done
builder: builder-backend (Sonnet 4.6)
date: 2026-05-15
---

# T-be-2 Implementation Log — SQLAlchemy 2.0 ORM Models (16 Comunify models)

## § Skills Consulted

| Skill | Reason | Decision |
|---|---|---|
| `backend-expert` | Runtime quality checklist (anti-patterns FastAPI/SQLA/tests/migrations) before commit | Confirmed SQLA 2.0 Mapped[] pattern, `server_default=func.now()` for timestamps, `DateTime(timezone=True)` mandatory, no `sa.Enum(create_type=True)`, no `session.query()` |
| `brand-expert` | Not invoked — task touches infrastructure models only, not brand domain | N/A |
| `offer-expert` | Not invoked — task touches infrastructure models only, not offer domain | N/A |
| `offer-type-preset-expert` | Not invoked | N/A |
| `metrics-expert` | Not invoked — no analytics changes | N/A |
| `tessl__fastapi` | Loaded as mandatory — confirmed `response_model=` mandatory, `Annotated` deps pattern | Noted for T-be-8 (routes); no routes in T-be-2 |
| `tessl__pytest-api-testing` | Loaded as mandatory — `httpx.AsyncClient`, conftest scoping, factory fixtures, DB isolation | Confirmed conftest sys.path injection pattern from vitalia precedent; smoke test uses `scope="module"` fixture |
| `tessl__graceful-degradation` | Loaded as mandatory — no external HTTP in this ticket | N/A for models |

## § Step 0 GATE — Anti-duplication grep

Per `.claude/rules/anti-duplication.md` Step 0 GATE, confirmed no existing model classes conflict:
- `find /home/chris/luana-platform -name "*.py" -path "*/infrastructure/models/*"` — confirmed luana-core-copilot, luana-core-brand-studio, luana-core-offer-studio models exist but none with `Comunify` prefix
- Zero blocking collisions. All 16 comunify tables confirmed NEW per § 2 anti-duplication grep results in `03-arch-be.md`

## § TDD — RED → GREEN cycle

**RED phase:** Wrote `tests/infrastructure/models/test_models_importable.py` before models. Test collected 49 test cases; all failed at import stage (`ModuleNotFoundError: No module named 'sqlalchemy'`). Fixed by running `uv add "sqlalchemy>=2.0" "alembic>=1.13"` which updated `pyproject.toml`.

After dependency install, tests fail with `ImportError: cannot import name 'ComunifyCohortModel' from 'src.modules.comunify.infrastructure.models'` — confirming RED.

**GREEN phase:** Implemented 16 model files + `__init__.py`. All 49 tests pass.

## § Implementation decisions

### Pattern source
Story 11 vitalia models (`/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/infrastructure/models/`) used as exact pattern reference:
- `from luana_core_platform.domain.base_entity import Base` (post-Story 10 unified Base)
- `server_default=func.now()` for `created_at` / `updated_at`
- `PgUUID(as_uuid=True)` for all UUID columns
- `Index(...)` in `__table_args__` tuple

### Cross-tenant model (plan_tier_configs)
`ComunifyPlanTierConfigModel` — NO `tenant_id`, NO `deleted_at`. Uses `is_active=True/False` flag to deactivate (pattern from `VitaliaPlanTierConfigModel`).

### Immutable audit log models
`ComunifyCommunityAuditLogModel` — NO `deleted_at`, 5-year retention enforced via separate purge job. Two composite indexes: `(tenant_id, event_type, created_at)` + `(tenant_id, severity, created_at)`.

### Singleton tables (1 per tenant)
- `ComunifyOfferLadderModel` — `tenant_id` has `unique=True` on the column itself (direct property on `mapped_column`, not via `UniqueConstraint`)
- `ComunifyVoiceCloningSamplesModel` — same pattern

### Financial records
- `ComunifySubscriptionChargeModel` — `UniqueConstraint("subscription_id", "billing_period", "installment_n", name="uq_charge_period_installment")` prevents duplicate charges
- `gateway_charge_id` and `idempotency_key` have `unique=True` for dedup
- Currency: `String(3)` (ISO 4217) — no hardcoded 'USD' per `currency-handling.md`

### Moderation scores
Used `Float` (Python-level) mapping to `NUMERIC(5,4)` (DB-level per migration). This is intentional — SQLAlchemy `Float` maps to any NUMERIC-compatible type; the migration DDL controls the precision.

### Voice distillation
`compiled_blocks: Mapped[dict | None]` = JSONB `{identidad, dialecto, vocabulario, registro, asíNO, anclajes}` — bridges to PersonalityCompiler v2 input (T-voice-3).

## § Dependencies added to pyproject.toml
```
sqlalchemy>=2.0
alembic>=1.13
```
(communify backend previously lacked these; added via `uv add` per native-first dev rule)

## § Files created

**Models (16 files + __init__.py):**
- `src/modules/comunify/infrastructure/__init__.py`
- `src/modules/comunify/infrastructure/models/__init__.py`
- `src/modules/comunify/infrastructure/models/cohort_model.py`
- `src/modules/comunify/infrastructure/models/cohort_member_model.py`
- `src/modules/comunify/infrastructure/models/cohort_broadcast_model.py`
- `src/modules/comunify/infrastructure/models/cohort_broadcast_recipient_model.py`
- `src/modules/comunify/infrastructure/models/community_post_model.py`
- `src/modules/comunify/infrastructure/models/community_post_attachment_model.py`
- `src/modules/comunify/infrastructure/models/community_moderation_event_model.py`
- `src/modules/comunify/infrastructure/models/subscription_model.py`
- `src/modules/comunify/infrastructure/models/subscription_charge_model.py`
- `src/modules/comunify/infrastructure/models/offer_ladder_model.py`
- `src/modules/comunify/infrastructure/models/voice_cloning_samples_model.py`
- `src/modules/comunify/infrastructure/models/voice_distillation_job_model.py`
- `src/modules/comunify/infrastructure/models/authority_vault_item_model.py`
- `src/modules/comunify/infrastructure/models/lead_qualification_record_model.py`
- `src/modules/comunify/infrastructure/models/community_audit_log_model.py`
- `src/modules/comunify/infrastructure/models/plan_tier_config_model.py`

**Tests:**
- `tests/infrastructure/__init__.py`
- `tests/infrastructure/models/__init__.py`
- `tests/infrastructure/models/test_models_importable.py` (49 tests)

## § Validators result

| Validator | Command | Result |
|---|---|---|
| V-NF-1 | `ruff check src/modules/comunify/ tests/ --no-cache` | PASS — 0 errors |
| V-NF-2 | `ruff format --check src/modules/comunify/ tests/` | PASS — all formatted |
| V-NF-5 (smoke) | `pytest tests/infrastructure/models/ -v` | PASS — 49/49 |

V-NF-5 full arch fitness suite requires `tests/architecture/` directory (created in later tickets per 06-tickets.yaml). Smoke test covers A1 + A2 acceptors.

## § Cross-module reads
- READ (pattern only): `/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/infrastructure/models/` — booking_model.py, plan_tier_config_model.py, medical_audit_log_model.py
- READ (schema): `/home/chris/luana-platform/comunify/backend/alembic/versions/001_comunify_initial_snapshot.py` — all 16 table DDLs verified column-by-column against models
- READ (arch spec): `docs/product/stories/luana-comunify-bootstrap/03-arch-be.md` § 4 — all 10 model patterns consumed

## § Default-flip pre-audit (Step 0.5)
No `core/config.py` default changes in this ticket. N/A.
