---
ticket: T-be-2
story: luana-comunify-bootstrap
surface: BE
state: done
date: 2026-05-15
---

# T-be-2 Result — SQLAlchemy 2.0 ORM Models (16 Comunify models)

## Status

DONE — all acceptance verifiers GREEN, native ticket tests 49/49 PASS.

## Deliverables

### 16 ORM model files

All in `/home/chris/luana-platform/comunify/backend/src/modules/comunify/infrastructure/models/`:

| File | Table | Notes |
|---|---|---|
| `cohort_model.py` | `comunify_cohorts` | tenant-scoped, soft-delete, composite indexes on (tenant,status) + UniqueConstraint(tenant,slug) |
| `cohort_member_model.py` | `comunify_cohort_members` | tenant-scoped, soft-delete, UniqueConstraint(tenant,cohort,subscriber) |
| `cohort_broadcast_model.py` | `comunify_cohort_broadcasts` | tenant-scoped, soft-delete |
| `cohort_broadcast_recipient_model.py` | `comunify_cohort_broadcast_recipients` | tenant-scoped, no deleted_at (delivery audit) |
| `community_post_model.py` | `comunify_community_posts` | tenant-scoped, soft-delete, spam/nsfw float scores |
| `community_post_attachment_model.py` | `comunify_community_post_attachments` | tenant-scoped, no deleted_at (asset record) |
| `community_moderation_event_model.py` | `comunify_community_moderation_events` | tenant-scoped, no deleted_at (audit trail) |
| `subscription_model.py` | `comunify_subscriptions` | tenant-scoped, soft-delete, Decimal(14,2) currency |
| `subscription_charge_model.py` | `comunify_subscription_charges` | tenant-scoped, no deleted_at, UniqueConstraint(subscription_id, billing_period, installment_n) |
| `offer_ladder_model.py` | `comunify_offer_ladders` | tenant-scoped, UNIQUE tenant_id (singleton), no deleted_at |
| `voice_cloning_samples_model.py` | `comunify_voice_cloning_samples` | tenant-scoped, UNIQUE tenant_id (singleton), no deleted_at |
| `voice_distillation_job_model.py` | `comunify_voice_distillation_jobs` | tenant-scoped, no deleted_at, Decimal(8,4) cost_usd |
| `authority_vault_item_model.py` | `comunify_authority_vault_items` | tenant-scoped, soft-delete, polymorphic kind JSONB content |
| `lead_qualification_record_model.py` | `comunify_lead_qualification_records` | tenant-scoped, no deleted_at (snapshot) |
| `community_audit_log_model.py` | `comunify_community_audit_log` | tenant-scoped, IMMUTABLE (no deleted_at), 5-yr retention |
| `plan_tier_config_model.py` | `comunify_plan_tier_configs` | CROSS-TENANT (no tenant_id), no deleted_at |

### Package init

`src/modules/comunify/infrastructure/models/__init__.py` — exports all 16 model classes via `__all__`.

### Tests

`tests/infrastructure/models/test_models_importable.py` — 49 tests:
- A1: all 16 models importable + registered in Base.metadata
- A2: all tenant-scoped models have tenant_id column + index
- Soft-delete tables have nullable deleted_at
- Immutable/audit tables have NO deleted_at
- Cross-tenant table (plan_tier_configs) has NO tenant_id

## Acceptance verifiers (A1, A2)

```
A1 — python -c "from src.modules.comunify.infrastructure.models import *; ..."
     Result: 16 tables registered in Base.metadata ✓

A2 — parametrized tests for 15 tenant-scoped tables
     Result: all have tenant_id column + index ✓
```

## Quality gates

| Gate | Command | Result |
|---|---|---|
| V-NF-1 Lint | `ruff check src/modules/comunify/ tests/ --no-cache` | PASS — 0 errors |
| V-NF-2 Format | `ruff format --check src/modules/comunify/ tests/` | PASS — 23 files clean |
| Tests (native) | `pytest tests/infrastructure/models/ -v` | PASS — 49/49 |

## Architecture invariants honored

- All models inherit `luana_core_platform.domain.base_entity.Base` (Story 10 unified base)
- `DateTime(timezone=True)` on all datetime columns (no naive datetimes)
- `server_default=func.now()` on created_at / updated_at
- No `sa.Enum(create_type=True)` — Postgres enum types created in migration only
- No `session.query()` / no `Column()` legacy patterns
- Tenant isolation: `tenant_id` NOT NULL + indexed on all 15 tenant-scoped tables
- Cross-tenant exception documented: `comunify_plan_tier_configs`
- Soft-delete only (no hard delete pattern)
- Currency: `String(3)` — never hardcoded 'USD' per currency-handling.md
- Money: `Numeric(precision, scale)` for financial amounts

## Blocks unblocked

- T-be-3 (repositories) — can now import models
- T-be-4 (services/Onboarding) — can now reference model classes in repos
