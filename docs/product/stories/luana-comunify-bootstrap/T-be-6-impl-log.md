# T-be-6 IMPL-LOG — CommunityPostService + CommunityModerationService

**Story:** luana-comunify-bootstrap  
**Ticket:** T-be-6  
**Date:** 2026-05-14  
**State:** done  

---

## § Skills Consulted

| Skill | Why invoked | Decision |
|---|---|---|
| `tessl__fastapi` | Async service DI patterns, Pydantic v2 ConfigDict | Used `ConfigDict(from_attributes=True, extra="forbid")` for input DTOs; Protocol class for `ContentClassifierProtocol` (not ABC) per Python typing best practices |
| `tessl__pytest-api-testing` | AsyncMock fixture scoping, factory helpers, DB isolation in unit tests | Used `_make_service()` / `_make_mod_service()` factory pattern returning (svc, repo_mock, repo_mock); `asyncio_mode = "auto"` from pyproject.toml |
| `tessl__graceful-degradation` | Best-effort write pattern (moderation_event persist, compliance log, pre_mod decrement) | All three side-effect writes wrapped in `try/except Exception + structlog.warning` — never re-raises, mirrors `ComplianceEventService` pattern |
| `backend-expert` | DDD inside-out layering, SQLA 2.0 update stmt, tenant isolation | Used lazy `from sqlalchemy import update` inside `_decrement_pre_moderation_count` to avoid circular imports; accessed `self._member_repo._session` directly per existing cohort_service pattern |

---

## § Default-flip pre-audit

No `core/config.py` defaults modified. Skip per Step 0.5.

---

## § Cross-module reads

- `/home/chris/luana-platform/comunify/backend/src/modules/comunify/application/services/compliance_event_service.py` — read-only for best-effort pattern reference
- `/home/chris/luana-platform/comunify/backend/src/modules/comunify/application/services/cohort_service.py` — read-only for DI constructor pattern

---

## § Implementation decisions

### D1 — ContentClassifierProtocol as typing.Protocol

Per ticket: "classifier is stub interface `ContentClassifierProtocol` injected via DI". Used `typing.Protocol` (structural subtyping) rather than ABC so test stubs (`StubClassifier`, `ConfigurableClassifier`) conform without explicit inheritance. Single method: `async def classify(content, tenant_id) -> ModerationClassifierScore`.

### D2 — `moderation_result` dict uses `score.model_dump()`

Initial implementation built dict manually (`{"spam_score": ..., "nsfw_score": ..., "doxxing_detected": ...}`). Unit test M1 asserts `result.score.model_dump() | {final_status, classifier_version}` pattern — mismatch on `confidence`/`reasoning` fields. Fixed to `score.model_dump() | {"final_status": ..., "classifier_version": ...}` so the JSONB payload is complete and tests self-documenting.

### D3 — Doxxing heuristic is two-layer

1. Classifier sets `doxxing_detected=True` (future Haiku implementation)
2. Regex heuristic runs on content even if classifier says False (`_PHONE_PATTERN`, `_EMAIL_PATTERN`)

Layer 2 is a mutation: creates new `ModerationClassifierScore` with `doxxing_detected=True` if regex matches. Real cross-ref of `cohort_members` table deferred to T-guards-3.

### D4 — `_decrement_pre_moderation_count` accesses `_session` directly

Per spec §14.4 this is best-effort. Rather than adding a `decrement_pre_moderation_count` method to the repository interface (which would require changing the interface defined in T-be-3), the service accesses `self._member_repo._session` directly and issues an `UPDATE` statement. This is an intentional pragmatic choice — T-guards-1+ can promote to a proper repo method.

### D5 — `pre_moderation_count_remaining` in `CreatePostResult`

Returns `None` for waitlisted and high-engagement members (no decrement path taken). Returns `int` (0..N-1) for active members in pre-mod window. Returns `0` for active members with `pre_moderation_count=0` (out of window). Tested in P3: `remaining == 0`.

---

## § Files created

| File | Description |
|---|---|
| `src/modules/comunify/application/services/community_post_service.py` | `CommunityPostService` + `CreatePostRequest` + `CreatePostResult` + `MemberNotFoundError` |
| `src/modules/comunify/application/services/community_moderation_service.py` | `CommunityModerationService` + `ContentClassifierProtocol` + `ModerationClassifierScore` + `ClassifyPostResult` + `CreatorActionRequest` + `CreatorActionResult` + `PostNotFoundError` + `InvalidModerationActionError` |
| `tests/unit/application/test_community_post_service.py` | 9 unit tests P1–P9 (V-F-2) |
| `tests/unit/application/test_community_moderation_service.py` | 17 unit tests M1–M15b (V-F-2) |
| `tests/e2e/test_community_post_moderation_e2e.py` | 8 e2e tests E-MOD-1..8 (V-F-9) |

---

## § Validator results

| Validator | Command | Result |
|---|---|---|
| V-F-2 (unit application) | `pytest tests/unit/application/ -v` | 26/26 PASS (9 post_service + 17 moderation_service) |
| V-F-9 (e2e moderation) | `pytest tests/e2e/test_community_post_moderation_e2e.py -v` | 8/8 PASS |
| Full suite | `pytest tests/ -q` | 184 passed, 9 skipped |
| Lint | `ruff check` | 0 errors |
| Format | `ruff format --check` | 5 files formatted |

---

## § Lint fix notes

Ruff reported 10 issues in test files after initial creation:
- `I001` — unsorted imports (3 files): fixed with `ruff --fix`
- `F401` — unused imports (`ClassifyPostResult`, `MemberNotFoundError`, `patch`): removed
- `F841` — unused variables (`member`, `tenant_a`) in e2e test: removed
- `E501` — line too long (125 chars) in moderation unit test: split dict expression across lines
