# Session 6 T-2 Halt Report — SQLAlchemy collision class missed by static audit

> **Date:** 2026-05-13
> **State:** Phase D paused mid-T-2-attempt-4 — Option C ratified Chris (architect re-spawn Wave sequence)
> **Owner:** /pm Opus orchestrator
> **Branch:** development (clean — T-2 changes stashed)

## What Session 6 achieved before halt

### Phase A — Lift audit Opus ✓ done

- T-1.7 audit report emitted (~$400 Opus, under $1000-1500 budget)
- Surface findings: 0 missing critical symbols (vs feared 20-50), Lift Stories 1-9 >99% symbol-parity
- Root cause T-2 attempts 1-3 (Session 5): codemod MAPPING gaps + AST-invisible mock strings (not symbol gaps)
- Confidence predicted: 85-90% T-2..T-7 execute without halts

### Phase B — Chris ratified fix plan ✓ done

Chris approved Phase C/D/E continuation per AskUserQuestion ratification.

### Phase C — Codemod patches T-1.8 ✓ done

- Sonnet builder applied 4 MAPPING additions + MockPatchStringRewriter transformer + extended self-check
- `--self-check`: PASSED
- 17-symbol smoke import test: All 17 imports OK
- Commit `b38a18e3` pushed

### Phase D attempt 4 — T-2 brand+offer rewrite Opus halted ⚠

- Stash from Session 5 attempt 3 dropped clean
- T-2 builder Opus spawned, applied codemod to brand+offer + tests
- **Codemod application VERIFIED clean:**
  - `grep "from src\." src/modules/brand/ src/modules/offer/` → **0 production** (modulo 2 known forward-coupled deferrals in `offer/api/{campaigns,counts}.py` referencing `src.modules.advertising` — Nicolify-local, in DEFERRED-FILES.md)
  - `grep "patch('src.')" tests/modules/brand/ tests/modules/offer/` → **0 mock strings**
- **NEW HALT SURFACE — SQLAlchemy collision (audit missed runtime concern):**

```
sqlalchemy.exc.InvalidRequestError: Table 'tenants' is already defined for this MetaData instance.
Specify 'extend_existing=True' to redefine options and columns on an existing Table object.

SAWarning: This declarative base already contains a class with the same class name and module
name as luana_core_iam.infrastructure.models.tenant_model.TenantModel, and will be replaced in
the string-lookup table.
```

7 collection errors in `tests/modules/brand/`.

## Root cause structural

After codemod rewrote `from src.core.database import Base` → `from luana_core_platform.core.database import Base`:
- AISALESHT `src/modules/iam/infrastructure/models/tenant_model.py` defines `class TenantModel(Base)` — Base now resolves to luana_core_platform.core.database.Base
- `luana_core_iam/infrastructure/models/tenant_model.py` defines `class TenantModel(Base)` — same Base singleton

Both define `__tablename__ = "tenants"` → `Table('tenants')` registered twice on identical Base.metadata → InvalidRequestError at SQLAlchemy registry layer.

**Affected modules (predicted):** iam, crm, brand, offer, landing, assets, connections, scheduling, commercial_calendar, analytics, campaigns, social_proof, tenant_profile, tenant_domains, copilot, sales_agent — anywhere both AISALESHT and luana_core define ORM models for the same table.

**T-1.7 audit MISSED this class:** audit was static (file-level + symbol-level diff). SQLA Table registration is RUNTIME (happens at module import time inside `pytest --collect-only`). The audit confidence score (85-90%) is now revised DOWN to ~50% because this class of issue replicates across all 26 modules with ORM models.

## 3 stashes preserved

```
stash@{0}: WIP-T-2-Session-6-attempt-4-shared-base-stub-out-of-scope
  → backend/src/shared/domain/base_entity.py (builder attempt at re-export stub — out of T-2 scope)
stash@{1}: WIP-T-2-Session-6-attempt-4-SQLA-collision-halt
  → 228 files: backend/src/modules/{brand,offer}/ + backend/tests/modules/{brand,offer}/
     (codemod fully applied, never committed)
```

Recoverable via `git stash pop` or `git stash apply` for inspection. Recommended: leave stashed until architect revises Wave sequence — current rewrite state would conflict with new arch.

## What audit (T-1.7) missed and why

| Class | Audit covered? | Why missed |
|---|---|---|
| Missing exports (symbol-level) | ✓ Yes | Static grep of `def`/`class`/`CONST =` declarations |
| Path divergence (MAPPING) | ✓ Yes | Static path-by-path comparison |
| Test mock strings | ✓ Yes | Static grep of `mocker.patch("src.X")` literals |
| **SQLA Table registration collision** | ❌ NO | Requires RUNTIME import — `__tablename__` registers to `Base.metadata` at import-time, audit was read-only static |
| SQLA Mapper class-name collision (warning) | ❌ NO | Same — runtime only |
| Pydantic discriminator conflicts | ❌ NO (n/a) | Runtime concern, not surfaced T-2 yet |
| FastAPI dependency injection conflicts | ❌ NO (n/a) | Runtime, not T-2 surface |

**Lesson:** future static audits should be supplemented with `pytest --collect-only` smoke run BEFORE declaring confidence. This is cheap (~1 min) and catches a major class of runtime collisions.

## 4 strategic options surfaced to Chris

### Option A — Convert AISALESHT iam/crm/etc to re-export stubs in T-2

Scope expand T-2 to include stubbing AISALESHT IAM models (re-export `from luana_core_iam.X import TenantModel as TenantModel`). Risk: scope creep, T-3 ticket cover iam rewrite separately.

### Option B — Continue plan original — T-3 deletes AISALESHT iam, then T-2 retry

T-3 rewrites iam/crm/landing/etc, AISALESHT files become stubs/empty, collision dissolves. Risk: T-3 sharded 7 modules = bigger ticket.

### Option C — Architect revises Wave sequence ★ RATIFIED CHRIS

Halt T-2. Spawn architect-orchestrator to revise arch. Likely outcomes:
- Single big-bang commit pattern (rewrite ALL modules same commit + delete AISALESHT files)
- Base.metadata isolation pattern between old/new
- Other arch fix

### Option D — Delete AISALESHT iam *_model.py files in T-2

Trivial mechanical delete. Risk: needs verification no AISALESHT code imports those local model files directly.

## Chris ratification

**Option C** — architect re-spawn for Wave sequence revision (recorded 2026-05-13 via /pm AskUserQuestion).

## Cost report

| Phase | Cost |
|---|---|
| Phase A audit (Opus) | ~$400 |
| Phase C codemod patches (Sonnet) | ~$30 |
| Phase D2 attempt 4 (Opus halted) | ~$200 |
| Haiku commit | ~$50 |
| **Cumulative Session 6** | **~$680** |
| **Cumulative S5 + S6** | **~$2780** |

Still below $5000 soft check-in (Halt Trigger #9). $3000 milestone approaching.

## Next action

1. /pm orchestrator commits halt documentation + checkpoint update via Haiku delegate
2. Spawn `architect-orchestrator` Opus 4.7 with mission: revise 06-tickets.yaml Wave sequence given SQLA collision class
3. Architect output: revised 03-arch-be.md addendum + updated 06-tickets.yaml + new T-1.10 ticket if needed
4. Chris ratifies revised plan (Phase D3)
5. Resume T-2 retry attempt 5 OR new big-bang commit ticket per architect proposal

## Cross-reference

- `docs/product/stories/luana-nicolify-migration/T-1.7-lift-audit-report.md` (Phase A audit findings)
- `docs/product/outcomes/luana-platform-migration.md` §7.6.2 trigger #2 (cross-module port dep) — closest analog
- `docs/product/stories/luana-nicolify-migration/SESSION-5-HALT-2026-05-12.md` (Session 5 R1 ratification origin)
- `docs/product/stories/luana-nicolify-migration/SESSION-6-HANDOFF.md` (Session 6 plan — revised post halt)
