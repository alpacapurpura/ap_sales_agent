# T-1 Impl Log — Alembic migration 127 eval_simulator_grade + eval_simulator_grade_cache

story_id: sales-agent-voice-fidelity-grader-runtime
ticket: T-1
builder: builder-backend (Sonnet)
started_at: 2026-05-09

## Skills Consulted

- `backend-expert` — invoked Step 0 SOP. Loaded `runtime-quality-checklist.md` antes commit. Key decision: migration must use `op.execute()` raw SQL `IF NOT EXISTS` only — `op.create_table()` forbidden (non-idempotent). Confirmed precedent 125 pattern.
- `brand-expert` — invoked per Step 0 GATE routing. N/A for T-1 (migration only, no brand module touched).
- `offer-expert` — invoked per Step 0 GATE routing. N/A for T-1.
- `offer-type-preset-expert` — invoked per Step 0 GATE routing. N/A for T-1.
- `metrics-expert` — invoked per Step 0 GATE routing. N/A for T-1 (no analytics ETL touched).
- `tessl__fastapi` — invoked per Step 0 GATE. N/A for T-1 (no FastAPI routes/DTOs).
- `tessl__pytest-api-testing` — invoked per Step 0 GATE. N/A for T-1 (migration-only ticket).
- `tessl__graceful-degradation` — invoked per Step 0 GATE. N/A for T-1 (no external HTTP calls).

## Step 0.5 Default-Flip Detection

Not applicable — T-1 touches no `backend/src/core/config.py` defaults. Migration-only ticket.

## CONTEXT-BRIEF.md verification

- Validator pass: `/home/chris/AISALESHT/docs/product/stories/sales-agent-voice-fidelity-grader-runtime/CONTEXT-BRIEF-validation.md` (PASS verdict)
- Faithfulness flag: **clean** (zero discrepancies)
- R24 acceptance gate: PASS — both conditions met.

## Iteration Log

### iter-1 — 2026-05-09

**Action**: Read CONTEXT-BRIEF.md, 03-arch.md §3.1 reference impl, precedent migration 125.

**Decisions captured**:
- D-BE-1: schema_version column = 1 cement; future bumps via SCHEMA_MIGRATIONS registry H1 reuse
- D-BE-2: cache table separate (D9/DQ7) — independent invalidation lifecycle vs grade rows
- D-BE-3: judges JSONB stored verbatim (audit trail) — no per-judge column explosion
- down_revision = '125_add_eval_simulator_observability_tables' (current DB head at T-1 start)
- 2 tables: eval_simulator_grade (composite PK) + eval_simulator_grade_cache (varchar PK)
- 6 indexes: 4 on grade table (tenant_persona, rubric, unconverged WHERE TRUE, actor_profile) + 2 on cache table (rubric, transcript)

**Validator results**:
- be_lint: `ruff check alembic/versions/127_add_eval_simulator_grade_tables.py --no-cache` → **GREEN** (All checks passed!)
- be_format: `ruff format --check alembic/versions/127_add_eval_simulator_grade_tables.py` → **GREEN** (1 file already formatted)

**Migration apply**:
- Note: Pre-existing multi-head scenario (086 + 127 heads) — same pattern as Story B 125 (branches from 085 branchpoint). Applied via `alembic upgrade 127_add_eval_simulator_grade_tables` (specific revision ID).
- First apply: `Running upgrade 125_add_eval_simulator_observability_tables -> 127_add_eval_simulator_grade_tables` ✅
- Second apply (idempotency): No-op (already at revision) ✅
- Third apply (idempotency): No-op ✅

**Schema verification** (visionarias_logs DB):
- `eval_simulator_grade`: 24 columns confirmed + 5 indexes (PK composite + 4 named indexes) ✅
- `eval_simulator_grade_cache`: 10 columns confirmed + 3 indexes (PK + 2 named indexes) ✅

**Result**: GREEN — all validators pass, 2 tables + 6 indexes present, idempotent ✅

## Commit

SHA: (pending push)
Files: 1 (backend/alembic/versions/127_add_eval_simulator_grade_tables.py)
