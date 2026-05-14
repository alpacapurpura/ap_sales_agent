# T-be-6 Result — CommunityPostService + CommunityModerationService

**Story:** luana-comunify-bootstrap  
**Ticket:** T-be-6  
**Status:** DONE  
**Date:** 2026-05-14  

---

## Validators

| Validator | Command | Result |
|---|---|---|
| V-F-2 (unit application) | `pytest tests/unit/application/ -v --tb=short` | 26/26 PASS |
| V-F-9 (e2e moderation) | `pytest tests/e2e/test_community_post_moderation_e2e.py -v` | 8/8 PASS |
| Full suite | `pytest tests/ -q` | 184 passed, 9 skipped |
| Lint (`ruff check`) | 5 files | 0 errors |
| Format (`ruff format --check`) | 5 files | clean |

---

## Files delivered

**Application services:**

- `comunify/backend/src/modules/comunify/application/services/community_post_service.py`
  - `CommunityPostService.create_post()` — pre-moderation routing + counter decrement (best-effort)
  - `CreatePostRequest`, `CreatePostResult`, `MemberNotFoundError`
  - Pre-mod policy: waitlisted skip, engagement_score>=80 skip, count>0 decrement

- `comunify/backend/src/modules/comunify/application/services/community_moderation_service.py`
  - `CommunityModerationService.classify_post()` — classifier stub + doxxing heuristic + status routing
  - `CommunityModerationService.handle_creator_action()` — approve/reject/delete_and_ban
  - `ContentClassifierProtocol` (typing.Protocol) — DI interface for Haiku (wired in T-guards-1)
  - `ModerationClassifierScore`, `ClassifyPostResult`, `CreatorActionRequest`, `CreatorActionResult`
  - `PostNotFoundError`, `InvalidModerationActionError`

**Tests:**

- `comunify/backend/tests/unit/application/test_community_post_service.py` — 9 tests (P1–P9)
- `comunify/backend/tests/unit/application/test_community_moderation_service.py` — 17 tests (M1–M15b)
- `comunify/backend/tests/e2e/test_community_post_moderation_e2e.py` — 8 tests (E-MOD-1..8)

---

## Status routing implemented

| Condition | Status |
|---|---|
| doxxing_detected (classifier or regex heuristic) | `rejected_doxxing` |
| spam_score >= 0.95 | `rejected_spam` |
| nsfw_score >= 0.85 | `rejected_nsfw` |
| spam_score >= 0.85 OR nsfw_score >= 0.85 | `pending_moderation` |
| otherwise | `auto_approved` |

---

## Blocks unblocked

T-be-8 (post feed API), T-guards-1 (Haiku classifier integration).  
`ContentClassifierProtocol` is the DI seam for T-guards-1.

---

## Impl-log

`docs/product/stories/luana-comunify-bootstrap/T-be-6-impl-log.md`
