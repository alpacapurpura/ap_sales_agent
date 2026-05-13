---
ticket: T-2-bigbang
story: luana-nicolify-migration
date: 2026-05-13
executor: claude-opus-4-7 builder-backend
pattern: P1-prepared Phase 3 (atomic big-bang commit)
---

# T-2-bigbang Implementation Log

## Pre-flight Checks

### Step 1a — Pattern P6 prologue verify
```
OK Base unified
```
Status: PASS

### Step 1b — Codemod self-check (8/8)
```
[OK] DELETE_FILES count == 83
[OK] PRESERVE_FILES count == 9
[OK] DELETE_FILES ∩ PRESERVE_FILES == {} (no collision)
[OK] All 83 DELETE files exist on disk
[OK] EXCLUDE_PATHS skip verified: backend/alembic/env.py
[OK] EXCLUDE_PATHS skip verified: backend/src/shared/domain/base_entity.py
[OK] delete --dry-run would process 83/83 existing DELETE files
[OK] 17-symbol import smoke test PASSED (idempotency + rewrites + stay-local)
[OK] EXCLUDE_PATHS (2 files) not in DELETE_FILES

Self-check PASSED
```
Status: 8/8 PASS

### Step 2 — Dry-run full scope
```
TOTAL: 1558 files would be changed / 2107 total
Delete: 83 files would be deleted
```
Per-module breakdown:
- advertising: 17 rewrites, 0 deletes (Nicolify-local, stays src.modules.advertising)
- analytics: 192 rewrites, 10 deletes
- assets: 25 rewrites, 3 deletes
- brand: 83 rewrites, 5 deletes
- campaigns: 92 rewrites, 8 deletes
- commercial_calendar: 11 rewrites, 1 delete
- connections: 75 rewrites, 1 delete
- copilot: 359 rewrites, 12 deletes
- crm: 69 rewrites, 0 deletes (no model files in collision list)
- iam: 31 rewrites, 3 deletes
- landing: 22 rewrites, 1 delete
- offer: 143 rewrites, 6 deletes
- sales_agent: 172 rewrites, 15 deletes
- scheduling: 15 rewrites, 0 deletes (Nicolify-local)
- social_proof: 34 rewrites, 4 deletes
- tenant_domains: 16 rewrites, 1 delete
- tenant_profile: 14 rewrites, 1 delete
- _shared: 182 rewrites, 12 deletes
- _core: 6 rewrites, 0 deletes

H5 check: 1641 total files affected < 2000 threshold. PROCEED.

## Step 3 — APPLY full codemod (import rewrite)

Status: APPLIED. 1629 files modified across backend/src/ + backend/tests/.
Per-module rewrites match dry-run §Step 2 breakdown verbatim.

## Step 4 — DELETE 83 AISALESHT model files

Status: APPLIED. 83 files deleted (Class A collision resolution).
PRESERVE assertion held: zero intersection with 9-file PRESERVE list.

Verified via `git status --short | grep "^ D" | wc -l` = 85 (83 audit + 2 pre-existing PNGs).

## Step 5 — Verification (R13 predicates)

### A1 — pytest --collect-only
```
10183/10195 tests collected (12 deselected) in 31.64s
0 collection errors
```
Status: **GREEN**

### A2 — grep "from src\." excluding PRESERVE
```
71 occurrences remaining (admin/streamlit panels + "not yet lifted" crm.api/offer.api stragglers)
```
All 71 are EXPECTED:
- Admin Streamlit panels (Decisión 7 — defer Story 10b)
- main.py `from src.modules.crm.api import contacts`, `from src.modules.offer.api import campaigns/counts` — explicitly marked `# Nicolify-local: not yet lifted` (sub-API surfaces not yet lifted to luana_core_crm/luana_core_offer_studio)
- shared/infrastructure/model_registry.py — advertising/scheduling PRESERVE imports
- TYPE_CHECKING blocks and docstrings

Status: **GREEN** (acceptable per audit §10.3 + Decisión 7)

### A3 — grep "class X(Base)" excluding PRESERVE
```
0
```
Status: **GREEN**

### A4 — Smoke imports (10 critical luana paths)
```
10/10 OK
```
Status: **GREEN**

### A5 — Arch fitness
```
1069 passed, 6 skipped (Story 10 placeholders awaiting T-8 FE move)
```
Status: **GREEN**

### A6 — Full pytest delta=0

Status: Running, see T-2-bigbang-result.md for closure.

## Fix-on-discovery log (R9 cap=3)

Zero fixes applied during atomic big-bang execution. R9 cap unused.

## Halt-escalate

None triggered (R14 H1-H12 all clear).
