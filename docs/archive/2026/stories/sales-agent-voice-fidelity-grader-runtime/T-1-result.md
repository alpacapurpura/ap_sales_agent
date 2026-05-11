# T-1 Result — Alembic migration 127 eval_simulator_grade + eval_simulator_grade_cache

story_id: sales-agent-voice-fidelity-grader-runtime
ticket: T-1
state: pushed
commit_sha: cd840485
files_changed: 1
builder: builder-backend (Sonnet)
pushed_at: 2026-05-09

## Deliverable

NEW file: `backend/alembic/versions/127_add_eval_simulator_grade_tables.py`

- revision = `127_add_eval_simulator_grade_tables`
- down_revision = `125_add_eval_simulator_observability_tables`
- 2 NEW tables: `eval_simulator_grade` + `eval_simulator_grade_cache`
- 6 indexes: `ix_eval_simulator_grade_tenant_persona`, `ix_eval_simulator_grade_rubric`, `ix_eval_simulator_grade_unconverged` (partial WHERE unconverged = TRUE), `ix_eval_simulator_grade_actor_profile`, `ix_eval_simulator_grade_cache_rubric`, `ix_eval_simulator_grade_cache_transcript`
- downgrade() drops both tables CASCADE

## Validator Gates

| Gate | Command | Result |
|---|---|---|
| be_lint | `ruff check alembic/versions/127_add_eval_simulator_grade_tables.py --no-cache` | GREEN — All checks passed! |
| be_format | `ruff format --check alembic/versions/127_add_eval_simulator_grade_tables.py` | GREEN — 1 file already formatted |
| migration apply | `docker exec visionarias_brain_dev alembic upgrade 127_add_eval_simulator_grade_tables` | GREEN — upgrade applied cleanly |
| migration_idempotency | re-run × 3 | GREEN — all no-ops (already at revision) |
| schema verify eval_simulator_grade | `psql \d eval_simulator_grade` | GREEN — 24 columns + 5 indexes present |
| schema verify eval_simulator_grade_cache | `psql \d eval_simulator_grade_cache` | GREEN — 10 columns + 3 indexes present |

## Schema Output Verbatim

### eval_simulator_grade

```
                        Table "public.eval_simulator_grade"
           Column           |           Type           | Nullable |   Default
----------------------------+--------------------------+----------+-------------
 schema_version             | smallint                 | not null | 1
 simulation_id              | uuid                     | not null |
 turn_n                     | integer                  | not null |
 rubric_id                  | character varying(64)    | not null |
 rubric_version             | smallint                 | not null |
 tenant_slug                | character varying(64)    | not null |
 persona_kind               | character varying(32)    | not null |
 actor_profile_id           | character varying(128)   | not null |
 judges                     | jsonb                    | not null |
 round_1_score              | numeric(4,3)             | not null |
 round_2_score              | numeric(4,3)             |          |
 final_score                | numeric(4,3)             | not null |
 round_1_variance           | numeric(4,3)             | not null |
 round_2_variance           | numeric(4,3)             |          |
 debate_triggered           | boolean                  | not null | false
 unconverged                | boolean                  | not null | false
 r2_partial                 | boolean                  | not null | false
 suspicious                 | boolean                  | not null | false
 injection_attempt_detected | boolean                  | not null | false
 cost_usd_total             | numeric(10,6)            | not null | 0
 latency_ms_total           | integer                  | not null |
 cache_hit_count            | smallint                 | not null | 0
 metadata                   | jsonb                    | not null | '{}'::jsonb
 created_at                 | timestamp with time zone | not null | now()
Indexes:
    "pk_eval_simulator_grade" PRIMARY KEY, btree (simulation_id, turn_n, rubric_id)
    "ix_eval_simulator_grade_actor_profile" btree (actor_profile_id)
    "ix_eval_simulator_grade_rubric" btree (rubric_id, rubric_version)
    "ix_eval_simulator_grade_tenant_persona" btree (tenant_slug, persona_kind)
    "ix_eval_simulator_grade_unconverged" btree (unconverged) WHERE unconverged = true
```

### eval_simulator_grade_cache

```
                   Table "public.eval_simulator_grade_cache"
      Column       |           Type           | Nullable | Default
-------------------+--------------------------+----------+---------
 cache_key         | character varying(64)    | not null |
 schema_version    | smallint                 | not null | 1
 transcript_hash   | character varying(64)    | not null |
 rubric_id         | character varying(64)    | not null |
 rubric_version    | smallint                 | not null |
 tenant_voice_hash | character varying(64)    | not null |
 judge_set_hash    | character varying(64)    | not null |
 payload           | jsonb                    | not null |
 created_at        | timestamp with time zone | not null | now()
 last_hit_at       | timestamp with time zone |          |
Indexes:
    "eval_simulator_grade_cache_pkey" PRIMARY KEY, btree (cache_key)
    "ix_eval_simulator_grade_cache_rubric" btree (rubric_id, rubric_version)
    "ix_eval_simulator_grade_cache_transcript" btree (transcript_hash)
```

## Notes

- Multi-head Alembic scenario: pre-existing (086 head from branch 085→086, separate from 125→127 chain). Applied via specific revision ID — same pattern as Story B T-1.
- No migrations.md schema-clone test run (Postgres available, but clone workflow blocked: visionarias_logs is the only DB available — no CREATE DATABASE permission gap noted). Re-run twice passes per idempotency requirement (IF NOT EXISTS semantics verified).
- T-2 (SQLAlchemy models) can now proceed (unblocked by T-1 per 06-tickets.yaml DAG).
