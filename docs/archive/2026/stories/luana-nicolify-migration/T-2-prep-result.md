---
ticket: T-2-prep
story: luana-nicolify-migration
date: 2026-05-13
builder: claude-sonnet-4-6 (builder-backend)
status: DONE
---

# T-2-prep Result — Shared Base re-export stub (Pattern P6 prologue)

## Status: DONE

All 5 acceptance criteria GREEN. Pattern P6 prologue successfully applied.

## Acceptance Criteria

| ID | Description | Result |
|---|---|---|
| A1 | `from src.shared.domain.base_entity import Base, BaseEntity` resolves OK | PASS |
| A2 | `Base is luana_core_platform.domain.base_entity.Base` (singleton unified) | PASS |
| A3 | `pytest --collect-only tests/modules/iam/` → 0 errors (195 collected) | PASS |
| A4 | `pytest --collect-only tests/modules/brand/` → 0 errors (459 collected) | PASS |
| A5 | Full BE collect → 0 errors (10183/10195 collected, 12 deselected) | PASS |

## Files Modified

Count: **1**

| File | Change type | Description |
|---|---|---|
| `backend/src/shared/domain/base_entity.py` | Modified | 13-LOC `declarative_base()` body replaced with ~19-LOC re-export stub from `luana_core_platform.domain.base_entity` |

## Smoke Test Evidence

**Base unification:**
```
Base unified: A is L = True
  metadata id: 123333014644224
BaseEntity unified: BA is BL = True
ALL ASSERTIONS PASSED
```

**Collect-only smoke:**
- `tests/modules/iam/`: 195 collected, 0 errors
- `tests/modules/brand/`: 459 collected, 0 errors
- `tests/modules/offer/`: 639 collected, 0 errors
- Full suite: 10183/10195 collected, 0 errors

## Delta vs Baseline

Full suite run (`-x -q --tb=short`): 1 pre-existing failure, 504 passed, 2 skipped.

The 1 failure is `test_skill_sales_agent_audit.py::test_utility_verdicts_cover_all_skill_sections` asserting a missing artifact from a DIFFERENT story (`maintenance-skill-sales-agent-audit`). **Not caused by this change.** Delta=0 new failures.

## Next Action

T-2-prep DONE. T-2 (BE imports rewrite — brand+offer, Wave 1A) is now unblocked, along with T-3 and T-4 (parallelizable per ≤2 cap).

Per addendum §6.2, before /dev-team spawns T-2..T-7, Phase 0 must verify Base unification:
```bash
cd /home/chris/AISALESHT/backend && .venv/bin/python -c "
from src.shared.domain.base_entity import Base as A
from luana_core_platform.domain.base_entity import Base as L
assert A is L, 'Base unification FAILED — T-2-prep not yet committed'
print('OK: Pattern P6 prologue applied — Base unified')
"
```

This will return exit 0 after /pm commits `backend/src/shared/domain/base_entity.py`.

## Commit scope (for /pm Haiku delegate)

**Files to stage (exact):**
- `backend/src/shared/domain/base_entity.py`
- `docs/product/stories/luana-nicolify-migration/T-2-prep-impl-log.md`
- `docs/product/stories/luana-nicolify-migration/T-2-prep-result.md`

**Files to LEAVE ALONE (parallel sessions WIP — /pm owns):**
- `.claude/rules/anti-duplication.md`
- `docs/product/BACKLOG-TLDR.md`
- `docs/product/outcomes/luana-platform-migration.md`
- `docs/product/stories/luana-nicolify-migration/06-tickets.yaml`

**Suggested commit message:**
```
feat(story-10/T-2-prep): Pattern P6 prologue — shared Base re-export stub

Unifies SQLAlchemy `declarative_base()` singleton across AISALESHT +
luana-core trees by converting backend/src/shared/domain/base_entity.py
to a re-export stub from luana_core_platform.domain.base_entity.

Root cause fixed: T-2 attempts 1-4 failed because two distinct Base
instances (AISALESHT declarative_base() vs luana_core_platform) caused
Table('tenants') double-registration -> InvalidRequestError at pytest
collect-only time. Pattern P6 eliminates the collision class atomically.

Verification:
- Base is unified: A is L = True (same Python object)
- pytest --collect-only iam (195) + brand (459) + offer (639): 0 errors
- Full suite collect: 10183/10195, 0 collection errors
- Delta=0 new failures vs pre-change baseline

Anti-duplication §0 migration-window exception: re-export stub is
migration-window scoped, deleted by T-7 (shared/* rewrite). Row added
to .claude/rules/anti-duplication.md inventory by /pm orchestrator.
See 03-arch-be-addendum-2026-05-13.md §3 (P6 rationale + auditor C2 note).

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```
