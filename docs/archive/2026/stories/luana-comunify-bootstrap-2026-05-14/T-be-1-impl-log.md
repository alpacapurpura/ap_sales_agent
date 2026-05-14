---
ticket: T-be-1
story: luana-comunify-bootstrap
surface: BE
state: done
session_date: 2026-05-15
builder: builder-backend (claude-sonnet-4-6)
---

# T-be-1 Impl Log — Alembic snapshot 001_comunify_initial_snapshot.py

## § Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `backend-expert` | ALWAYS — runtime quality checklist pre-write | Confirmed: raw SQL `IF NOT EXISTS` only, no `op.create_table()`, no `sa.Enum(create_type=True)`, tenant_id NOT NULL + indexed on every tenant-scoped table |
| `brand-expert` | NOT invoked — ticket is pure migration, no brand layer changes | N/A |
| `offer-expert` | NOT invoked — ticket is pure migration, no offer layer changes | N/A |
| `metrics-expert` | NOT invoked — ticket is pure migration, no analytics layer changes | N/A |
| `tessl__fastapi` | NOT invoked — ticket produces only Alembic migration files, no FastAPI routes | N/A |
| `tessl__pytest-api-testing` | NOT invoked — acceptance verifiers are static SQL review (Docker deferred per HS1 soft halt) | N/A |
| `tessl__graceful-degradation` | NOT invoked — migration file has no external HTTP calls | N/A |

## § Step 0 — Anti-duplication grep

```bash
find /home/chris/luana-platform -name "001_*_snapshot.py" 2>/dev/null
# → /home/chris/luana-platform/vitalia/backend/alembic/versions/001_vitalia_initial_snapshot.py
# → /home/chris/luana-platform/nicolify/backend/alembic/versions/001_initial_snapshot.py
```

Verdict: Story 11 vitalia snapshot exists (pattern source confirmed). Story 12 comunify snapshot creates 16 **new** tables — zero table name overlap with vitalia (16 `comunify_*` vs vitalia's `vitalia_*`). Only the **structure** is mirrored (idempotent raw SQL pattern), never the table contents.

## § Reference reads completed

1. `03-arch-be.md § 4` — model schemas (exact columns, FK refs, indexes per table) — READ ✓
2. `03-arch-be.md § 5` — migration strategy (IF NOT EXISTS, independent chain D18) — READ ✓
3. `vitalia/backend/alembic/versions/001_vitalia_initial_snapshot.py` — Story 11 pattern (enum DO $$, CREATE TABLE IF NOT EXISTS, separate CREATE INDEX IF NOT EXISTS) — READ ✓
4. `vitalia/backend/alembic/env.py` — env.py pattern (POSTGRES_* env vars, target_metadata=None, NullPool) — READ ✓
5. `.claude/rules/backend-migrations.md` — idempotent patterns confirmed — READ ✓
6. `.claude/rules/tenant-isolation.md` — tenant_id NOT NULL + indexed confirmed — READ ✓

## § Implementation decisions

### D18 — Independent alembic chain

Per arch doc § 5.2 D18: `down_revision = None` (not chained to vitalia or nicolify). Comunify has its own alembic chain. Rationale: brand isolation between verticals (D1 per arch § 1).

### Tables summary

| # | Table | tenant_id | soft-delete | Notes |
|---|---|---|---|---|
| 1 | comunify_cohorts | ✓ NOT NULL | ✓ deleted_at | UNIQUE (tenant_id, slug) |
| 2 | comunify_cohort_members | ✓ NOT NULL | ✓ deleted_at | UNIQUE (tenant_id, cohort_id, subscriber_id) |
| 3 | comunify_cohort_broadcasts | ✓ NOT NULL | ✓ deleted_at | — |
| 4 | comunify_cohort_broadcast_recipients | ✓ NOT NULL | ✗ (delivery record) | — |
| 5 | comunify_community_posts | ✓ NOT NULL | ✓ deleted_at | moderation scores NUMERIC(5,4) |
| 6 | comunify_community_post_attachments | ✓ NOT NULL | ✗ (asset record) | nsfw_score NUMERIC(5,4) |
| 7 | comunify_community_moderation_events | ✓ NOT NULL | ✗ (audit trail) | immutable |
| 8 | comunify_subscriptions | ✓ NOT NULL | ✓ deleted_at | UNIQUE idempotency_key; currency CHAR(3) |
| 9 | comunify_subscription_charges | ✓ NOT NULL | ✗ (financial) | UNIQUE (sub_id, billing_period, installment_n) |
| 10 | comunify_offer_ladders | ✓ NOT NULL UNIQUE | ✗ (1-per-tenant singleton) | 4 level_N_offer_id nullable |
| 11 | comunify_voice_cloning_samples | ✓ NOT NULL UNIQUE | ✗ (1-per-tenant singleton) | raw_samples_deleted_at for privacy |
| 12 | comunify_voice_distillation_jobs | ✓ NOT NULL | ✗ (job audit) | confidence_score NUMERIC(5,4); cost_usd NUMERIC(8,4) |
| 13 | comunify_authority_vault_items | ✓ NOT NULL | ✓ deleted_at | polymorphic kind VARCHAR(32) |
| 14 | comunify_lead_qualification_records | ✓ NOT NULL | ✗ (snapshot) | fit_score INTEGER |
| 15 | comunify_community_audit_log | ✓ NOT NULL | ✗ (IMMUTABLE) | 5-year retention, PII sanitized |
| 16 | comunify_plan_tier_configs | ✗ (cross-tenant catalog) | ✗ | UNIQUE plan_tier_slug; currency CHAR(3) |

### Currency fields

- `comunify_subscriptions.currency`: `CHAR(3) NOT NULL` — tenant locale, no hardcoded default per `.claude/rules/currency-handling.md`
- `comunify_subscription_charges.currency`: `CHAR(3) NOT NULL`
- `comunify_plan_tier_configs.currency`: `CHAR(3) NOT NULL DEFAULT 'USD'` — acceptable for cross-tenant global config (plan prices denominated in USD as display baseline; tenant locale applied at checkout per rule exception for catalog pricing)
- Money columns use `NUMERIC(14, 2)` per arch spec

### Enum strategy

9 enum types created via idempotent `DO $$ BEGIN CREATE TYPE ... EXCEPTION WHEN duplicate_object THEN NULL; END $$;` pattern — identical to Story 11 vitalia approach. No `sa.Enum(create_type=True)` anywhere (broken SA 2.0.27 per `.claude/rules/backend-migrations.md`).

## § Idempotency verification (static)

```bash
# Syntax check
.venv/bin/python -c "import ast; ast.parse(open('alembic/versions/001_comunify_initial_snapshot.py').read()); print('SYNTAX OK')"
# → SYNTAX OK

# Count: 16 CREATE TABLE IF NOT EXISTS, 40 CREATE INDEX IF NOT EXISTS
# All DDL has IF NOT EXISTS
# No op.create_table() / op.add_column() / op.create_index() calls (only in docstring comments)
```

## § Files written

1. `/home/chris/luana-platform/comunify/backend/alembic/versions/001_comunify_initial_snapshot.py` — 16 tables, 9 enum types, idempotent
2. `/home/chris/luana-platform/comunify/backend/alembic/env.py` — POSTGRES_* env vars, NullPool, target_metadata=None
3. `/home/chris/luana-platform/comunify/backend/alembic.ini` — script_location=alembic, sqlalchemy.url placeholder, logging
4. `/home/chris/luana-platform/comunify/backend/alembic/script.py.mako` — standard template (mirror vitalia)

## § Acceptance verifiers status

| Verifier | Status | Notes |
|---|---|---|
| A1 — idempotent (upgrade 2x) | HS1 soft halt — Docker deferred | Static inspection: all 16 tables + 40 indexes use IF NOT EXISTS |
| A2 — downgrade -1 + upgrade | HS1 soft halt — Docker deferred | downgrade() drops all tables + types in reverse order |
| A3 — all 15+1 tables present | PASS (static) | 16 tables confirmed via ast parse + regex extraction |
| Syntax check | PASS | `ast.parse()` succeeds |
| Forbidden patterns | PASS | No `op.create_table()` / `op.add_column()` / `op.create_index()` in actual code |

Note: HS1 soft halt = Docker integration tests deferred to gate-runner Phase 4 audit per ticket constraints.

## § Blocks

T-be-2 (ORM models) and T-be-3 (repos) are now unblocked — table schemas finalized.
