---
ticket: T-be-1
story: luana-comunify-bootstrap
surface: BE
state: done
session_date: 2026-05-15
---

# T-be-1 Result — Alembic snapshot 001_comunify_initial_snapshot.py

## Verdict

PASS (static verification). Docker integration tests (A1/A2) deferred per HS1 soft halt — gate-runner Phase 4 audit.

## Files produced

| File | Description |
|---|---|
| `/home/chris/luana-platform/comunify/backend/alembic/versions/001_comunify_initial_snapshot.py` | 16-table consolidated snapshot, 9 enum types, all idempotent IF NOT EXISTS |
| `/home/chris/luana-platform/comunify/backend/alembic/env.py` | Independent chain env.py — POSTGRES_* env vars, NullPool, target_metadata=None |
| `/home/chris/luana-platform/comunify/backend/alembic.ini` | Alembic config — script_location=alembic, comunify_dev DB default |
| `/home/chris/luana-platform/comunify/backend/alembic/script.py.mako` | Standard mako template for future revisions |

## Tables (16)

1. `comunify_cohorts` — cohort lifecycle aggregate, tenant-scoped, soft-delete
2. `comunify_cohort_members` — enrollment per subscriber, UNIQUE (tenant, cohort, subscriber)
3. `comunify_cohort_broadcasts` — broadcast metadata, soft-delete
4. `comunify_cohort_broadcast_recipients` — per-recipient delivery, immutable
5. `comunify_community_posts` — community post aggregate, moderation scores
6. `comunify_community_post_attachments` — media assets, nsfw_score
7. `comunify_community_moderation_events` — classifier history, immutable audit
8. `comunify_subscriptions` — recurring subscription root, soft-delete, idempotency_key
9. `comunify_subscription_charges` — financial record, UNIQUE (sub, period, installment)
10. `comunify_offer_ladders` — 4-level ladder singleton per tenant
11. `comunify_voice_cloning_samples` — upload state singleton per tenant
12. `comunify_voice_distillation_jobs` — async job audit, cost_usd tracked
13. `comunify_authority_vault_items` — polymorphic vault (credentials/case_studies/press/awards)
14. `comunify_lead_qualification_records` — qualification snapshot, immutable
15. `comunify_community_audit_log` — compliance + security log, IMMUTABLE, 5-year retention
16. `comunify_plan_tier_configs` — cross-tenant global catalog (no tenant_id)

## Acceptance verifiers

| Verifier | Status |
|---|---|
| A1 — upgrade 2x without error | HS1 deferred (Docker) |
| A2 — downgrade -1 + upgrade | HS1 deferred (Docker) |
| A3 — all 15+1 tables present | PASS — 16 tables confirmed |
| Syntax valid | PASS — `ast.parse()` succeeds |
| All DDL idempotent | PASS — 16 CREATE TABLE IF NOT EXISTS, 40 CREATE INDEX IF NOT EXISTS, 1 CREATE UNIQUE INDEX IF NOT EXISTS |
| No forbidden patterns | PASS — no `op.create_table()` / `op.add_column()` / `op.create_index()` in code |
| Enum types idempotent | PASS — 9 types via `DO $$ ... EXCEPTION WHEN duplicate_object THEN NULL` |
| tenant_id indexed on all tenant-scoped tables | PASS — 15/15 (plan_tier_configs is cross-tenant, exempt) |
| Currency fields correct type | PASS — CHAR(3) NOT NULL; NUMERIC(14,2) for money |

## Unblocks

- T-be-2 (ORM models) — table schemas finalized
- T-be-3 (repos) — table schemas finalized
