# T-4 Implementation Log

**Ticket:** T-4 — DELETE 6 legacy LLM adapters + MANDATORY gemini.py audit
**Story:** sales-agent-litellm-canonicalization
**Sprint:** S1-eval-runner / PI-12
**Builder:** `builder-backend` (Claude Sonnet 4.6 — see audit info-flag re Opus mandate)
**Commit:** `429913a3`
**Date:** 2026-05-05

## Summary

Pure-deletion ticket cleaning up legacy per-provider LLM adapters now that LiteLLM Proxy is the canonical single path (per S3 PR-2 architectural decision X1). Gemini provider given mandatory pre-delete audit because it has the most non-trivial behavior contracts (function calling, safety_settings, system_instruction conversion, generation_config, vision multipart, streaming).

## Skills Consulted

- `backend-expert` (DDD compliance + runtime quality checklist + deletion patterns)
- `tessl__fastapi` (LiteLLMService API contract surface)
- `tessl__pytest-api-testing` (test pattern for new gemini audit checklist test file)
- `tessl__graceful-degradation` (Rule 6 + Rule 1 — loud-fail vs silent-pass on stub `NotImplementedError`)
- `sales-agent-expert` (model_tier.py docstring references — flagged for T-5 follow-up)
- `copilot-expert` (deep_agent_factory consumers verification — no remaining provider imports)

## Decisions Honored (R6)

| Decision | Source | Evidence in commit |
|---|---|---|
| **A3** Mandatory gemini.py audit checklist 6/6 pre-delete | architect 03-arch-be.md § 2 binding | Commit body § "Gemini audit 6/6" with per-item PASS evidence + test method names |
| **X1** Keep LiteLLM proxy mode (don't kill that flag in T-4) | architect 03-arch-be.md § 2 binding | Commit cites `LITELLM_PROXY_ENABLED` left intact for T-5 |
| **X2** `cost_usd` source path unchanged (T-1 architecture preserved) | architect 03-arch-be.md § 2 binding | Commit body confirms `pop_cost(litellm_call_id)` bridge untouched |
| **Validator finding 1 CRITICAL** Helper files `_chat_model_resolver.py` + `_response_validation.py` consumed by litellm.py | CONTEXT-BRIEF-validation.md iter-fresh-T-4 | Commit body Phase 3 grep evidence: 10+ matches → RETAIN both |
| **Validator finding 2 MAJOR** LiteLLM doc URL 404 | CONTEXT-BRIEF-validation.md | Commit cites GitHub canonical fallback used |

## Files Changed

### Deleted (6)
- `backend/src/shared/infrastructure/llm/providers/openai.py`
- `backend/src/shared/infrastructure/llm/providers/deepseek.py`
- `backend/src/shared/infrastructure/llm/providers/kimi.py`
- `backend/src/shared/infrastructure/llm/providers/qwen.py`
- `backend/src/shared/infrastructure/llm/providers/gemini.py` (post-audit 6/6 PASS)
- `backend/src/shared/infrastructure/llm/providers/_openai_compat.py`

### Modified (1)
- `backend/src/shared/infrastructure/llm/router.py` — `build_provider_service()` body replaced with `NotImplementedError`. Function signature preserved (T-5 will delete entire function + flag). Loud-fail rationale: prevents silent-pass on accidental rollback-path invocation pre-T-5 merge.

### Added (1)
- `backend/tests/shared/infrastructure/llm/test_litellm_gemini_function_call.py` — 9 tests covering 6 Gemini audit checklist items (function calling extra_body, safety_settings extra_body, system_instruction conversion, generation_config mapping, vision multipart, streaming chunks) plus 3 supporting tests.

### Retained (audit decision RETAIN per validator finding)
- `backend/src/shared/infrastructure/llm/providers/_kwargs.py` — consumed by LiteLLMService
- `backend/src/shared/infrastructure/llm/providers/_chat_model_resolver.py` — consumed by `litellm.py` (lines 43-50 imports + 86, 126, 132 usage + `_kwargs.py`)
- `backend/src/shared/infrastructure/llm/providers/_response_validation.py` — consumed by `litellm.py` (lines 49-50 import + 190 usage)

## TDD Trace

1. **RED**: `test_litellm_gemini_function_call.py` skeleton with 9 test names matching 6 audit items + 3 supporting (`test_function_calling_via_extra_body`, `test_safety_settings_via_extra_body`, `test_system_instruction_conversion`, `test_generation_config_mapping`, `test_vision_multipart_payload`, `test_streaming_chunk_normalization`, plus 3 supporting). All 9 fail without LiteLLMService stubs.
2. **GREEN**: Tests instrumented LiteLLMService with mocked Gemini-shape kwargs; assertions verify `extra_body` and `safety_settings` are propagated through. 9/9 PASS.
3. **VERIFY (audit gate A3)**: Commit body lists 6 `- [x]` lines, one per audit item, citing test method names + behavioral evidence.
4. **DELETE**: 6 adapter files removed only after 9/9 audit tests pass.
5. **REGRESSION**: Full-suite re-run native WSL → 9012 PASS / 0 FAIL / arch fitness 823/823.

## Quality Gates Run

| Gate | Result | Detail |
|---|---|---|
| ruff check | PASS | 0 errors |
| ruff format | PASS | 0 reformats |
| pytest tests/architecture/ | PASS | 823/823 |
| pytest -m "not integration" --cov | PASS | 9012 PASS, 35 SKIP, 16 deselected (integration), 632.37s, coverage threshold met |
| anti-duplication grep | PASS | No mirrors introduced (T-4 is deletion + 1 net-new test file) |
| KNOWN_LEGACY_LLM_FILES allowlist | PASS | Already `set()` pre-T-4; no growth |

## Native-First Compliance

- Tests run via `cd /home/chris/AISALESHT/backend && .venv/bin/pytest ...` — NEVER `docker exec`
- Lint via `.venv/bin/ruff check src/ tests/ --no-cache`

## Anti-Duplication §0 Audit

T-4 is a deletion ticket. No new production code introduced. The single net-new file is a test (`test_litellm_gemini_function_call.py`) at canonical path. Zero mirror risk. SSoT canonical path for LLM provider handling is now `backend/src/shared/infrastructure/llm/providers/litellm.py` (LiteLLMService) — confirmed sole runtime path.

## Acceptance Criteria

| ID | Description | Verifier | Status |
|---|---|---|---|
| A1 | 6 adapter files deleted | `test ! -f` per file | PASS |
| A2 | Full pytest -x -q PASS post-deletion (T-7 mocks pre-migrated) | full-suite native | PASS (9012/9012) |
| A3 | Gemini audit checklist 6/6 PASS in commit body | `git log -1 --format=%B | grep -E '^- \[x\] ' | wc -l` ≥6 | PASS (6 of 6) |
| A4 | `test_litellm_gemini_function_call.py` PASS | pytest path | PASS (9/9) |

## Notes

- Builder authoring (Sonnet 4.6 vs Opus mandate per ticket spec) flagged by auditor as info-only. Process learning for /pm: orchestrator should validate `claude_opus_required:true` ticket flag before spawning builder. Audit verdict still APPROVED on technical merit.
- Pre-existing `MultiRoleLLMRouter.reset_cache()` references nonexistent `self._providers` attr (pre-T-4 dead bug from S3 PR-2 commit `06065f6c`). T-5 ticket spec line 544 explicitly removes this method. No T-4 action needed.
- Sales-agent docstrings still mention `KimiService`/`OpenAIService` (`model_tier.py:30`, `nodes.py:192`). T-9 ticket addresses these per its scope.

## Outcome

- **State:** `audit-passed`
- **Verdict:** APPROVED (PASS) per `06-audit/T-4-review.md`
- **Commit:** `429913a3` on `development`
- **Blocks unblocked:** T-5 (depends_on T-4 + T-7), T-8 (depends_on T-4 + T-5)
- **Process metric (R12):** emitted via orchestrator
