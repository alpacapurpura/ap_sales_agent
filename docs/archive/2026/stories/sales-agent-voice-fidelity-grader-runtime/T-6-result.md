# T-6 Result — cache.py hash composition + lookup/persist + graceful degradation

Story: sales-agent-voice-fidelity-grader-runtime
Ticket: T-6
State: pushed (state: tests-passing — awaiting orchestrator → gate-runner → auditor-agentic)
Builder: builder-agentic Opus 4.7
Completed: 2026-05-09

## Deliverables status

| Deliverable | Status | File |
|---|---|---|
| `_internal/__init__.py` (zero re-exports) | DONE | `backend/tests/agentic_evals/sales_agent/grader/_internal/__init__.py` |
| `_internal/cache.py` (hash composition + lookup/persist + graceful) | DONE | `backend/tests/agentic_evals/sales_agent/grader/_internal/cache.py` |
| `test_cache_unit.py` (19 unit tests across 7 classes) | DONE | `backend/tests/agentic_evals/sales_agent/grader/test_cache_unit.py` |

## Public surface

| Symbol | Purpose |
|---|---|
| `_CACHE_KEY_FIELDS: Final[tuple[str, ...]]` | Frozen 5-field alphabetical composition order — D8 cement |
| `compute_cache_key(...)` | sha256 64-char hex over canonical JSON |
| `compute_transcript_hash(transcript)` | sha256 over role+turn_number+content concatenation |
| `compute_tenant_voice_hash(voice_profile)` | sha256 of `voice_profile.system_instruction` (sales-agent-expert §3 cement) |
| `compute_judge_set_hash(weights)` | sha256 over canonical (sort_keys) judge_id+weight pairs |
| `cache_lookup(session, cache_key) -> MajEvalScore \| None` | SELECT + reconstruct + best-effort UPDATE last_hit_at |
| `cache_persist(*, session, cache_key, score, transcript_hash, rubric_id, rubric_version, tenant_voice_hash, judge_set_hash) -> None` | INSERT ON CONFLICT DO NOTHING (idempotent first-writer-wins) |

## Acceptance criteria

| Criterion | Status | Evidence |
|---|---|---|
| A1: Hash composition deterministic + canonical JSON ordering (D8) | PASS | `TestCacheKeyDeterministicSameRequestSameKey` 3 tests + `_CACHE_KEY_FIELDS` order asserted alphabetical |
| A2: Cache hit deterministic (Scenario 3) | PASS unit | `test_lookup_returns_majeval_on_hit_and_updates_last_hit_at` — Pydantic roundtrip preserves cement fields. Full integration (Scenario 3 with `--run-evals`) lives in T-9. |
| A3: Cache invalidation precision on all 4 change vectors (D8/D16) | PASS | `TestCacheKeyChangesOnTranscriptMutation`, `...OnRubricVersionBump`, `...OnVoiceProfileChange`, `...OnJudgeSetChange` — 4 vectors covered |
| A4: Graceful degradation Rule 2 — DB unavailable bypass | PASS | `test_lookup_returns_none_when_db_raises` + `test_persist_does_not_raise_when_db_raises` — both raise `OperationalError` mocked, neither propagates |
| be_lint | PASS | `ruff check --no-cache` → All checks passed! |
| be_format | PASS | `ruff format --check` → 0 files would be reformatted |
| be_mypy_strict | PASS | `mypy tests/.../cache.py` → Success: no issues found |
| Test count | 19/19 PASS | `pytest tests/agentic_evals/sales_agent/grader/test_cache_unit.py -v` |

## Decisions implemented

- **D8** (5-field composition cement): `_CACHE_KEY_FIELDS` frozen alphabetical (`judge_set_hash`, `rubric_id`, `rubric_version`, `tenant_voice_hash`, `transcript_hash`). Test `test_cache_key_fields_frozen_alphabetical_order` enforces.
- **D9** (cache table separate, independent lifecycle): cache.py reads/writes only `eval_simulator_grade_cache` table — never touches `eval_simulator_grade`.
- **D16** (auto-invalidation precision): rubric_version bump → key changes. Test `test_rubric_version_bump_invalidates_key`.
- **D-BE-2** (cache table separate): same as D9.
- **D-BE-6** (sha256 64-char hex): all hash functions return `hashlib.sha256(...).hexdigest()` length 64. Test `test_key_is_64_char_hex`.
- **DQ7** (cache table TTL=null): cache_persist sets `last_hit_at=None` initially; expiration is never time-based — invalidation is always via key recomposition (D8/D16).
- **Graceful Degradation Rule 2** (`tessl__graceful-degradation`): catch + structlog warn + degrade. Logs include `dependency="eval_simulator_grade_cache"`, `cache_key_prefix` (first 16 chars only — full key not logged for cardinality safety), and `fallback="re-grade"` / `"skip-cache"`. NEVER raises out of the function boundary.

## Out of scope verified

- judge_registry.py (T-4) — concurrent ticket, untouched.
- judge_prompts.py (T-7) — concurrent ticket, untouched (T-7 import error in collection is OUT OF MY SCOPE — separate session owns).
- maj_eval.py state machine (T-5) — depends on T-6, untouched.
- run_simulation hook (T-9) — depends on T-5+T-6+T-7, untouched.
- Migration 127 (T-1) and SQLA models (T-2) — consumed read-only via `EvalSimulatorGradeCacheModel`.

## Anti-duplication audit (Step 0 GATE)

```bash
find backend/src -name "cache.py" -type f
# /home/chris/AISALESHT/backend/src/modules/campaigns/application/services/cache.py  (UNRELATED Redis cache)

grep -rn "def compute_cache_key|def cache_lookup|def cache_persist" backend/src/ backend/tests/ | grep -v __pycache__
# zero matches — genuinely NEW
```

Verdict: CLEAN. No mirror risk against `anti-duplication.md` shared inventory.

## R5 schema-mirror note

cache.py imports `EvalSimulatorGradeCacheModel` from
`src/modules/sales_agent/observability/eval_simulator/persistence/models/`
which is a R5 schema-mirror (T-2 already shipped). cache.py itself lives
in `backend/tests/agentic_evals/sales_agent/grader/_internal/` and does
NOT touch any agentic module domain/application/api layer.

## Files touched

| Path | Action |
|---|---|
| `backend/tests/agentic_evals/sales_agent/grader/_internal/__init__.py` | NEW (zero re-exports) |
| `backend/tests/agentic_evals/sales_agent/grader/_internal/cache.py` | NEW |
| `backend/tests/agentic_evals/sales_agent/grader/test_cache_unit.py` | NEW (19 tests) |
| `docs/product/stories/sales-agent-voice-fidelity-grader-runtime/06-tickets.yaml` | EDIT — T-6 entry transitions: state=pushed |
| `docs/product/stories/sales-agent-voice-fidelity-grader-runtime/T-6-impl-log.md` | NEW |
| `docs/product/stories/sales-agent-voice-fidelity-grader-runtime/T-6-result.md` | NEW |

## Notes for auditor-agentic

- **Composition order is FROZEN cement.** Test `test_cache_key_fields_frozen_alphabetical_order` enforces tuple verbatim — any reorder = breaking change requires Chris ratification + cache wipe.
- **Cache key prefix logged (16 chars only)** — full keys not logged to keep log cardinality bounded. The 16-char prefix is sufficient for debugging (collision space 2^64).
- **`compute_transcript_hash` / `compute_tenant_voice_hash` are duck-typed** — they accept any object with `.role/.turn_number/.content` (transcript items) or `.system_instruction` (voice profile). This is intentional: `RubricGradeRequest` declares `transcript: list[Any]` and `tenant_voice_profile: Any` to avoid circular imports between grader test-infra and Story D `GoldenTurnModel` / Story A `PersonalityProfile`. Tests use lightweight stand-in dataclasses + `BaseModel` to verify the behavior without coupling.
- **`ON CONFLICT DO NOTHING` is idempotent** — verified in test via SQL string compilation. First writer wins; second writer's payload is intentionally discarded (D8 cement: same composition produces same content, so divergence is impossible without a key change).
- **Graceful degradation logs include `dependency` field** per `tessl__graceful-degradation` Rule 6 (structured context). Test mocks `OperationalError` to verify the catch path.
- **No `print` / stdlib `logging`** — only `structlog.get_logger(__name__)`.
- **No `datetime.utcnow()`** — uses `datetime.now(timezone.utc)`.
- **Pure functions (`compute_*`) have zero I/O** — all DB calls live exclusively in `cache_lookup` / `cache_persist`. T-5 state machine uses the pure helpers to compute keys without DB roundtrips per turn.
