<!-- voseo-allowed: arch doc cites .claude/rules glossary + SQLAlchemy doc verbatim per R25 -->
---
story_id: luana-nicolify-migration
arch_version: 1.1                       # addendum bump from 1.0
addendum_to: 03-arch-be.md (Wave sequence revision)
architect_owner: claude-opus-4-7
date: 2026-05-13
ratified_by_chris: false                # PENDING — Chris ratifies recommended Pattern + revised T-2..T-7
trigger: SESSION-6-T-2-HALT-2026-05-13.md (Option C ratified Chris)
parent_docs:
  - 03-arch.md
  - 03-arch-be.md
  - 06-tickets.yaml
binding_decisions_ref: docs/product/outcomes/luana-platform-migration.md §7.6
binding_triggers_ref: docs/product/outcomes/luana-platform-migration.md §7.6.2
---

# 03-arch-be addendum 2026-05-13 — Wave sequence revision (SQLAlchemy collision class)

> **Purpose.** T-2 attempts 1-4 surfaced a runtime collision class invisible to the
> T-1.7 static lift audit: SQLAlchemy `Table` re-registration when two import trees
> (AISALESHT `src.shared.domain.base_entity.Base` vs `luana_core_platform.domain.base_entity.Base`)
> register competing model classes that share `__tablename__`. This addendum revises
> the Wave sequence to handle the entire class atomically.
>
> **Status.** Addendum produced read-only by architect-orchestrator Opus 4.7 on
> 2026-05-13 per `SESSION-6-T-2-HALT-2026-05-13.md` Option C ratification. Chris
> must ratify the **Recommended Pattern (§3)** and **Revised ticket sequence (§4)**
> before any further T-2 retry. No code commits in this run.
>
> **Scope rule.** Revisions are local to T-2..T-7 (the BE imports rewrite wave).
> T-1, T-8..T-14 and the FE/DB/SSoT surfaces are NOT affected by this addendum.

---

## 1. Diagnosis summary (1.5 pages — what audit missed, why)

### 1.1 The collision in one paragraph

Post-codemod, brand+offer ORM model files import `Base` from
`luana_core_platform.domain.base_entity` (via MAPPING `src.shared.domain` →
`luana_core_platform.domain`). luana-core packages (`luana_core_brand_studio`,
`luana_core_iam`, …) already import that same `Base`. AISALESHT modules NOT
yet touched by T-2 (iam, crm, landing, copilot, sales_agent, etc.) still
import `Base` from `src.shared.domain.base_entity`. `declarative_base()` is
called **twice** — once per source file — producing **two distinct `Base`
instances with two distinct `MetaData` collections**. When pytest collects
brand tests, `tests/conftest.py` activates `model_registry.py` (registers
all AISALESHT models on Base #1) AND triggers the codemod-rewritten brand
stubs which pull luana_core_brand_studio + luana_core_iam (registers tables
on Base #2). Two effects:

1. **Foreign-key resolution fails on Base #2** — brand_summary refers to
   `tenants(id)` but `tenants` was only registered on Base #1 (AISALESHT
   iam). Symptom: `NoReferencedTableError: Foreign key associated with
   column 'sales.offer_id' could not find table 'products'` (verified
   live by reproducing stash apply 2026-05-13).
2. **Same-name class re-registration warning** — when a transitive import
   path reloads `luana_core_iam.tenant_model` after AISALESHT
   `src.modules.iam.tenant_model` was already loaded, `Base #1` sees a
   `TenantModel` class registered, then a SECOND `TenantModel` from
   luana_core_iam (via the brand stub) is registered on `Base #2`. The
   sqla string-lookup table reports the warning even when metadata is
   distinct because the lookup keys (class name + module name) collide
   across registries that share the same singleton dict. Once
   `Base.metadata.create_all(bind=engine)` runs, the duplicate `Table('tenants')`
   resolves into an `InvalidRequestError`.

In short: **the codemod produced a half-migrated state where one Base
governs N tables and another Base governs M tables. SQLAlchemy can only
operate when ALL related models share the same metadata** (per official
docs, [SQLAlchemy 2.0 Declarative Tables](https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html)
accessed 2026-05-13). Half-migrated = broken-by-construction.

### 1.2 Why static audit missed it

T-1.7 lift audit was symbol-level static (`grep` declarations + file
counts). The audit verified:

| Class | Audit covered |
|---|---|
| Path mismatches in MAPPING | ✓ |
| Missing exports at lifted target | ✓ |
| Test mock string literals | ✓ |

Audit DID NOT execute Python — that would have required `pytest --collect-only`
on a representative module. SQLAlchemy `Table.__init__` and
`declarative_base().metadata.tables[name] = table` run at IMPORT TIME inside
the class body. Static grep cannot observe runtime side-effects.

**Audit gap (codified post-incident as §7 of this addendum):** any
future static lift audit MUST include `pytest --collect-only` smoke run
on at least 1 representative consumer module BEFORE declaring confidence.
Cost ~$0 (~30 seconds local Python), catches an entire class of runtime
collisions.

### 1.3 Predicted blast radius pre-revision

Without revising the Wave sequence: collision repeats on every module
pair where AISALESHT ORM files and luana-core ORM files share a
`__tablename__`. Cross-codebase grep:

```
115 AISALESHT model files import "from src.shared.domain.base_entity import Base"
   distributed across iam, crm, brand, offer, landing, assets, connections,
   scheduling, commercial_calendar, analytics, campaigns, social_proof,
   tenant_profile, tenant_domains, copilot, sales_agent
```

26 luana-core packages mirror these. Predicted runtime collisions across
**16+ table-defining module pairs** if T-3, T-4, T-5, T-6 proceed
incrementally on the current arch.

---

## 2. Pattern evaluation (P1..P5 + hybrid P6)

Six criteria scoring (1=worst, 5=best):

| Criterion | Definition |
|---|---|
| Atomicity | Probability the migration leaves the DB-test-pytest-suite in a green state at every commit boundary |
| Blast radius | Number of files touched in the largest single commit (≤500=5, ≤1500=3, >1500=1) |
| Reviewability | How tractable a human or auditor review of the largest single commit (Opus reads in 1 pass=5, needs decomposed inspection=2) |
| Rollback | Can a single ticket be reverted via `git revert` without cascading failures (clean=5, complex=2) |
| Cap ≤2 paralelo honor | Honor of Decisión 1A cap (≤2 simultaneous sub-agents in /dev-team) |
| Cost | Estimated total Opus + Sonnet spend for the revised Wave 1+2 (lower=better) |

### 2.1 Pattern P1 — Big-bang single commit

Single Opus mega-ticket rewrites ALL modules + tests (~1500 files) and
deletes redundant AISALESHT model files (or converts to re-export stubs)
in **one atomic commit**.

| Criterion | Score | Note |
|---|---|---|
| Atomicity | **5** | Single commit = single boundary; pytest never sees partial state |
| Blast radius | **1** | ~1500 files — review impossible in 1 pass |
| Reviewability | **2** | Auditor C1-C5 must decompose by module post-hoc |
| Rollback | **2** | One revert undoes everything — but reset has to be all-or-nothing |
| Cap ≤2 paralelo honor | **1** | Single Opus builder — cannot paralelizar |
| Cost | **2** | Single Opus run ~$1500-2500 (large blast = high token retention) |
| **Total** | **13/30** | Atomic but unwieldy |

**Risk:** if mid-build the Opus session crashes (R27 risk), partial work
in-flight is brand+offer state already stashed across 4 attempts. P1
encourages "throw it all at one prompt" — Opus might miss subtle anti-
duplication mirrors, audit Cat 12 fails post-merge.

### 2.2 Pattern P2 — Per-module re-export stub strategy (T-2 expands transitively)

Each ticket T-2..T-7 ALSO converts its **ORM transitive closure** AISALESHT
files to re-export stubs (e.g., T-2 brand+offer ALSO converts AISALESHT
iam/crm models to stubs because brand_repository transitively imports
luana_core_iam.tenant_model).

| Criterion | Score | Note |
|---|---|---|
| Atomicity | **3** | Each ticket atomic AS LONG AS transitive closure is correctly identified — easy to miss a transitive |
| Blast radius | **3** | Per-ticket ~200-400 files including stubs |
| Reviewability | **4** | Per-ticket review tractable |
| Rollback | **3** | Stubs in 7+ modules complicate revert |
| Cap ≤2 paralelo honor | **5** | T-2 and T-3 can run paralelo |
| Cost | **3** | Total ~$1800-2500 across 6 tickets |
| **Total** | **21/30** | Best paralelizable but transitive closure fragile |

**Risk:** transitive closure detection requires per-ticket grep. Building
this DAG manually error-prone. If T-2 missed `connections` (which brand
indirectly references via OAuth integrations), T-3 surface NEW collision
class no one anticipated.

### 2.3 Pattern P3 — Base.metadata isolation (do NOT unify Base)

Codemod is **modified** to NOT rewrite `from src.shared.domain.base_entity`
nor `from src.core.database.Base`. AISALESHT modules keep Base #1.
luana-core modules use Base #2. Foreign keys across bases require
explicit column object refs (per [SQLAlchemy 2.0 FK across bases](https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html)).

| Criterion | Score | Note |
|---|---|---|
| Atomicity | **2** | Each ticket atomic but final state is **two SSoT** for Base — violates anti-duplication.md §0 |
| Blast radius | **4** | Minimal per ticket |
| Reviewability | **5** | Each ticket clean ORM imports rewrite, no cross-cutting metadata |
| Rollback | **5** | Single ticket revert trivial |
| Cap ≤2 paralelo honor | **5** | Wave 1A-1C paralelizables |
| Cost | **4** | Total ~$1500 (cheap) |
| **Total** | **25/30** | Cheap + paralelizable BUT permanent dual-Base — kicks can down road |

**Fatal flaw:** two Base instances persist into Story 10 closure. Future
Story 11-13 vertical brands (Vitalia, Comunify, Lupulo) cannot bootstrap
without resolving Base unification. Defers debt to next-quarter. Also,
Alembic migrations would need to manage two metadata trees (T-10 alembic
snapshot consolidation becomes "consolidate WHICH metadata?"). Hard
NO from anti-duplication.md §0 invariant.

### 2.4 Pattern P4 — Delete-then-rewrite per-module (FK-DAG topology order)

Each module ticket FIRST deletes (or stubs) its AISALESHT model files,
THEN runs codemod on the module. Ordering is topological by FK dependency:
shared (no ORM) → iam (no FKs) → tenant_profile → tenant_domains → brand,
crm (depend on iam) → offer (depends on brand+iam) → ...

| Criterion | Score | Note |
|---|---|---|
| Atomicity | **4** | Each ticket atomic post-FK-DAG sort |
| Blast radius | **4** | Per-ticket ~100-300 files |
| Reviewability | **5** | Per-ticket review tractable |
| Rollback | **3** | Revert OK at boundaries but FK order matters |
| Cap ≤2 paralelo honor | **3** | Wave 1 modules with no FK dependence between them paralelizables; FK leaves serialise |
| Cost | **3** | Total ~$1800-2500 |
| **Total** | **22/30** | Robust ordering but requires FK-DAG analysis |

**Risk:** FK topology sort requires module-level FK graph extraction.
At intermediate state (post-iam-rewrite, pre-brand-rewrite), brand
tests would fail because AISALESHT brand models reference `tenants` on
Base #1 but `tenants` is now only on Base #2. Tests at intermediate
states break — auditor C5 fails delta=0.

### 2.5 Pattern P5 — Hybrid invention zone

(Reserved for architect's hybrid synthesis.)

### 2.6 Pattern P6 — RECOMMENDED HYBRID: Two-phase Wave 1 with shared-base lift first

**Phase 1 (Wave 1A NEW):** Lift `shared/domain/base_entity.py` to a **re-export
stub from luana_core_platform.domain.base_entity** in a SINGLE small ticket
(T-2-prep). This unifies Base across AISALESHT + luana from the ground up
WITHOUT touching any ORM model file. After T-2-prep:

- `src.shared.domain.base_entity.Base` IS `luana_core_platform.domain.base_entity.Base` (same Python object via re-export)
- All 115 AISALESHT model files still import `from src.shared.domain.base_entity import Base` (no rewrites yet) — but Base is now Base #2 (the luana one) via re-export passthrough
- All 26 luana-core packages already use Base #2 directly
- ONE Base. ONE metadata. ZERO collisions.

**Phase 2 (Wave 1B-1C + Wave 2):** Codemod runs as originally designed across
brand/offer/etc. Because everyone shares Base #2, the rewrites can happen
in any order without runtime collision. Per-module tickets remain
paralelizable per ≤2 cap.

| Criterion | Score | Note |
|---|---|---|
| Atomicity | **5** | Each ticket atomic AND test-suite green at every commit |
| Blast radius | **4** | T-2-prep = 1 file, 13 LOC; other tickets unchanged |
| Reviewability | **5** | T-2-prep is 1 file review (5 min), rest unchanged |
| Rollback | **5** | T-2-prep trivial revert |
| Cap ≤2 paralelo honor | **5** | After T-2-prep, T-2/T-3/T-4 paralelizables per existing plan |
| Cost | **4** | T-2-prep ~$30 Sonnet; total ~$1700 (matches original budget +$30) |
| **Total** | **28/30** | **WINNER** |

**Why this works structurally:**

```python
# AFTER T-2-prep, AISALESHT/backend/src/shared/domain/base_entity.py:
"""Shared Base entity — re-export from luana-core during migration.

Story 10 migration cement: Base singleton MUST be unique across AISALESHT
and luana_core_* trees. This stub re-exports from canonical SSoT in
luana_core_platform. Post-Story-10 closure (T-7+T-13), this file is deleted
along with AISALESHT/backend/src/shared/.
"""
from luana_core_platform.domain.base_entity import Base, BaseEntity

__all__ = ["Base", "BaseEntity"]
```

Python's import system caches modules in `sys.modules`. After T-2-prep:

```python
import src.shared.domain.base_entity as A
import luana_core_platform.domain.base_entity as L
assert A.Base is L.Base  # True — single class instance
```

All subsequent codemod waves freely rewrite `from src.X import Base` →
`from luana_core_X import Base` because both Base references point at
the same memory. Foreign keys resolve. Tests pass at every intermediate
state.

**Mirror-vs-stub anti-duplication note:** This stub is the **inverse**
direction of the §0 cardinal rule. anti-duplication.md §0 forbids
**mirroring shared → modules** (canonical lives in shared, modules
mirror). T-2-prep is the OPPOSITE direction: AISALESHT shared is
itself being made obsolete (Story 10 archives AISALESHT entirely),
so re-exporting from the future SSoT (luana_core_platform) for the
duration of the migration window is the canonical anti-duplication
pattern (avoid TWO Base implementations). Stub is deleted in T-7
when shared/ itself is rewritten. Auditor C2 approves this as
migration-window scoped, not permanent.

### 2.7 Scoring summary

| Pattern | Atomicity | Blast | Review | Rollback | Cap≤2 | Cost | Total |
|---|---|---|---|---|---|---|---|
| P1 big-bang | 5 | 1 | 2 | 2 | 1 | 2 | 13 |
| P2 transitive stubs | 3 | 3 | 4 | 3 | 5 | 3 | 21 |
| P3 dual-Base | 2 | 4 | 5 | 5 | 5 | 4 | 25 (FAILS anti-duplication §0) |
| P4 delete-then-rewrite | 4 | 4 | 5 | 3 | 3 | 3 | 22 |
| **P6 (hybrid — shared-base lift first)** | **5** | **4** | **5** | **5** | **5** | **4** | **28** ★ |

---

## 3. Recommended pattern + rationale + risks + mitigations

### 3.1 Recommendation: **Pattern P6 — shared-base lift first (T-2-prep) then resume original waves**

**Why this and not the alternatives:**

- P1 violates Decisión 1A cap ≤2 paralelo (single Opus).
- P2 transitive closure detection error-prone (the failure mode we already
  hit 4 times). Fragile.
- P3 violates anti-duplication.md §0 cardinal (permanent dual Base).
- P4 breaks intermediate test states. Delta=0 (D5) fails per ticket.
- P6 surgical, cheap, preserves cap, preserves test parity at every
  commit, addresses root cause not symptoms.

### 3.2 Risks (3 material) + mitigations

**R-A1. Risk:** T-2-prep re-export stub could itself mask other unification
needs (e.g., `src.core.database.SessionLocal`, `src.core.config.Settings`).
**Mitigation:** the existing codemod MAPPING already rewrites `src.core` →
`luana_core_platform.core` (per T-1.7 audit fix). So `Settings`,
`SessionLocal`, `redis_client` are NOT shared-base issues. Only the
`Base = declarative_base()` singleton needed unification. We verified
this via `grep -rn "declarative_base\|Base = " backend/src/shared/` and
`grep -rn "declarative_base()" /home/chris/luana-platform/core/luana-core-*/src/` —
both have ONLY the single `Base = declarative_base()` in `domain/base_entity.py`.

**R-A2. Risk:** `_VOSEO_RE` or similar regex/SSoT constants defined in
`src.shared.X` may also need pre-T-2 stubbing.
**Mitigation:** these are NOT runtime-collision-class issues (they don't
register globally). Codemod rewrites them in normal flow. No T-2-prep
required.

**R-A3. Risk:** Auditor C2 (anti-duplication §0) may flag the re-export
stub as a mirror violation.
**Mitigation:** Codify in CONTRACT/T-2-prep that this stub is
**migration-window scoped**, deleted by T-7 (shared/ rewrite final wave).
Auditor C2 reads "migration-window scope" attribute and approves. Update
anti-duplication.md inventory to add a temporary exception row pointing
at this addendum for the duration of Story 10 only.

### 3.3 Implementation outline of T-2-prep (new ticket, ~30 min Sonnet)

1. Verify luana_core_platform.domain.base_entity exists and exports `Base` + `BaseEntity`
2. Replace AISALESHT `backend/src/shared/domain/base_entity.py` body with re-export from luana_core_platform
3. Run `pytest --collect-only` on `tests/modules/iam/`, `tests/modules/brand/` to verify Base unification works pre-codemod
4. Run full BE pytest suite — should be GREEN delta=0 (no code changes beyond Base unification)
5. Commit with body documenting Pattern P6 rationale + cross-ref this addendum + auditor exception note for anti-duplication.md §0

---

## 4. Revised ticket sequence (T-2..T-7 → T-2-prep + T-2..T-7 unchanged in code mechanics, just safer ordering)

### 4.1 Diff vs current 06-tickets.yaml

The Wave 1 prologue gains ONE new ticket (T-2-prep). T-2..T-7 are **mechanically
unchanged** but now operate against a unified Base. Validators V-F-1, V-F-2,
V-F-3, V-F-4, V-F-5 unchanged. New validators V-F-1a (Base unification verified)
+ V-NF-X (collision smoke test) added.

### 4.2 Revised summary table

| Ticket | Title | Owner | Hrs | Cost USD | Blocked by | Parallelizable with | Δ |
|---|---|---|---|---|---|---|---|
| T-1 | Baseline + codemod + arch tests | sonnet | 2 | 150-250 | — | — | UNCHANGED |
| **T-2-prep** ★ | **Shared Base re-export stub (Pattern P6 prologue)** | **sonnet** | **0.5** | **30-50** | **T-1** | — | **NEW** |
| T-2 | BE imports rewrite — brand+offer (Wave 1A) | opus | 3 | 500-750 | T-1, T-2-prep | T-3 | depends_on +T-2-prep |
| T-3 | BE imports rewrite — landing/assets/conn/sched/iam/crm/cc (Wave 1B) | opus | 3 | 500-750 | T-1, T-2-prep | T-2 | depends_on +T-2-prep |
| T-4 | BE imports rewrite — analytics/campaigns/social_proof/tenant_*/adv/sm (Wave 1C) | opus | 3 | 500-750 | T-1, T-2-prep, T-3 | — | depends_on +T-2-prep |
| T-5 | BE imports rewrite — copilot (Wave 2 agentic) | opus | 4 | 700-1000 | T-1, T-2-prep, T-4 | T-6 | depends_on +T-2-prep |
| T-6 | BE imports rewrite — sales_agent (Wave 2 agentic) | opus | 4 | 700-1000 | T-1, T-2-prep, T-4 | T-5 | depends_on +T-2-prep |
| T-7 | BE imports rewrite — shared/* (Wave 2 sharded 11 sub-subsystems) **+ delete base_entity.py stub** | opus | 6 | 1000-1500 | T-1, T-2-prep, T-5, T-6 | — | scope: also delete base_entity stub created T-2-prep (closure) |
| T-8 | FE git mv + workspace + jscodeshift | opus | 4 | 700-1000 | T-7 | T-10 | UNCHANGED |
| T-9 | Vercel reconfig + CF tunnel | opus | 2 | 300-500 | T-8 | — | UNCHANGED |
| T-10 | Fresh nicolify_dev DB + alembic snapshot | opus | 4 | 700-1000 | T-7 | T-8 | UNCHANGED |
| T-11 | Playwright smoke E2E | sonnet | 3 | 300-500 | T-9, T-10 | T-12 | UNCHANGED |
| T-12 | make ci-parity root migration | sonnet | 2 | 200-300 | T-9, T-10 | T-11 | UNCHANGED |
| T-13 | /pm SSoT atomic git mv | opus | 2 | 400-600 | T-11, T-12 | — | UNCHANGED |
| T-14 | AISALESHT archive + DB drop + Story 10 archive | sonnet | 2 | 200-400 | T-13 | — | UNCHANGED |
| **Total** | | | **~44.5** | **~6900-10350** | | | +T-2-prep |

### 4.3 T-2-prep ticket spec (full text — to be inserted into 06-tickets.yaml between T1 and T2)

```yaml
T2prep:
  id: T-2-prep
  title: "Shared Base re-export stub (Pattern P6 prologue — fixes SQLA collision class)"
  type: backend
  surface: BE
  wave_position: 0.5                          # between baseline T-1 and Wave 1 T-2
  production_code: false                      # Single-file re-export stub — zero business logic
  state: draft
  owner_eligibility:
    qwen_opencode: false                      # Anti-duplication scope nuance — needs Claude
    claude_sonnet: true                       # PREFERRED — mechanical 13-LOC replacement + verification suite
    claude_opus_required: false               # No agentic surface, no complex DDD reasoning
  priority: 1                                  # blocks ALL Wave 1+2 tickets
  estimate_hours: 0.5
  estimated_cost_usd_range: [30, 50]
  estimated_duration_minutes: 20-30
  parallelizable_with: []                     # Sequential — pre-Wave-1
  decisions_applicable: [D5, D1]               # D5=fix-on-discovery / D1=big-bang scope (T-2-prep is the prologue to atomic Wave 1+2)
  halt_triggers_applicable: [12]              # NEW Trigger #12 (SQLA collision class — see §6 below)
  repro_verified: true                        # SQLA collision reproduced live 2026-05-13 (architect addendum §1.1)
  repro_evidence:
    command: "cd /home/chris/AISALESHT/backend && git stash apply 'stash@{1}' && .venv/bin/pytest tests/modules/brand/test_brand_repository.py --override-ini=\"addopts=\" -x --tb=short"
    output: |
      sqlalchemy.exc.NoReferencedTableError: Foreign key associated with column
      'sales.offer_id' could not find table 'products' with which to generate
      a foreign key to target column 'id'
    diagnosis_validates_handoff: true
    diagnosis_correction: "Root cause = two Base instances (AISALESHT vs luana). Fix = re-export AISALESHT Base from luana_core_platform.domain.base_entity to unify singleton."
  inputs:
    spec: "../01-spec.md §5 Feature 1 (prerequisite for clean Wave 1)"
    arch_doc: "../03-arch.md §3 Wave 1 (revised by addendum 2026-05-13)"
    arch_be_doc: "../03-arch-be-addendum-2026-05-13.md §3 + §4.3"
    guidelines: "../05-guidelines.md §1.5 (skills) — anti-duplication.md migration-window exception"
    rules:
      - ".claude/rules/backend-ddd.md"
      - ".claude/rules/anti-duplication.md"
      - ".claude/rules/tdd-mandatory.md"
    domain_skills: ["backend-expert"]
  description: |
    Unify SQLAlchemy `Base` singleton across AISALESHT and luana_core_* trees
    by converting `backend/src/shared/domain/base_entity.py` to a re-export stub
    from `luana_core_platform.domain.base_entity`. This is the prologue to
    Wave 1+2 BE imports rewrite — without this stub, every subsequent codemod
    application produces SQLAlchemy Table/Mapper collisions (verified 2026-05-13
    Session 6 attempt 4 halt).

    **Exact change (13 LOC body → ~5 LOC re-export):**

    BEFORE (`backend/src/shared/domain/base_entity.py`):
    ```python
    """Base entities for SQLAlchemy and Pydantic domain models."""

    from pydantic import BaseModel, ConfigDict
    from sqlalchemy.orm import declarative_base

    Base = declarative_base()


    class BaseEntity(BaseModel):
        """Base Pydantic model for domain entities with ORM mode enabled."""

        model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    ```

    AFTER:
    ```python
    """Shared Base entity — re-export from luana-core (Story 10 migration window).

    Pattern P6 prologue (T-2-prep, addendum 2026-05-13). Unifies the SQLAlchemy
    `Base` singleton across AISALESHT and luana_core_* trees so that ORM model
    files in BOTH trees register tables to the SAME `MetaData` instance during
    the Story 10 migration window. Deleted by T-7 when shared/ rewrite completes.

    Anti-duplication §0 migration-window exception: this re-export is the
    canonical pattern to avoid TWO `Base = declarative_base()` instances during
    a multi-ticket lift. NOT a permanent mirror. Auditor C2 approves with note.
    """
    from luana_core_platform.domain.base_entity import Base, BaseEntity

    __all__ = ["Base", "BaseEntity"]
    ```

    **Verification sequence:**
    ```bash
    cd /home/chris/AISALESHT/backend
    # 1. Sanity Base unification works
    .venv/bin/python -c "
    from src.shared.domain.base_entity import Base as A
    from luana_core_platform.domain.base_entity import Base as L
    assert A is L, 'Base unification FAILED'
    print('Base unified: same Python object')
    "

    # 2. pytest --collect-only on highest-FK-density module
    .venv/bin/pytest tests/modules/iam/ tests/modules/brand/ --collect-only -q

    # 3. Full BE suite delta=0 vs T-1 baseline
    .venv/bin/pytest --tb=short -q 2>&1 | tail -10
    # Expected: same pass/fail/skip counts as baseline-be-tests.json
    ```

    **Anti-duplication.md migration-window exception note** (auditor C2 input):
    - Add row to `.claude/rules/anti-duplication.md` inventory table (or
      reference this addendum) marking `src.shared.domain.base_entity.Base`
      re-export as **migration-window scoped — closure T-7**.
    - Post-Story-10 (archive AISALESHT), the entire `src.shared.domain.base_entity`
      file ceases to exist, so the exception is self-cleaning.

  blast_radius:
    files_affected_count: 1
    paths:
      - /home/chris/AISALESHT/backend/src/shared/domain/base_entity.py
  deliverables:
    - "src/shared/domain/base_entity.py converted to 5-LOC re-export stub"
    - "Sanity smoke: `A.Base is L.Base` returns True (single Python object)"
    - "pytest --collect-only on iam + brand modules: 0 SQLA InvalidRequestError"
    - "pytest BE delta=0 vs T-1 baseline"
    - "T-2-prep-impl-log.md + T-2-prep-result.md"
  validators_referenced: [V-NF-1, V-NF-5, V-F-1a-NEW]
  out_of_scope:
    - "Any rewrite of model files (deferred T-2+)"
    - "Any luana-core package modification (read-only on luana tree)"
    - "Codemod modification (T-1.9 if needed addendum)"
  acceptance:
    - id: A1
      description: "base_entity.py is now 5-LOC re-export from luana_core_platform"
      verifier:
        type: shell
        cmd: "grep -q 'from luana_core_platform.domain.base_entity import Base, BaseEntity' /home/chris/AISALESHT/backend/src/shared/domain/base_entity.py"
    - id: A2
      description: "Base unification verified at Python runtime (single object)"
      verifier:
        type: shell
        cmd: "cd /home/chris/AISALESHT/backend && .venv/bin/python -c \"from src.shared.domain.base_entity import Base as A; from luana_core_platform.domain.base_entity import Base as L; assert A is L\""
    - id: A3
      description: "pytest collect-only iam + brand GREEN (no SQLA errors)"
      verifier:
        type: shell
        cmd: "cd /home/chris/AISALESHT/backend && .venv/bin/pytest tests/modules/iam/ tests/modules/brand/ --collect-only -q 2>&1 | grep -E 'error|InvalidRequest' && exit 1 || exit 0"
    - id: A4
      description: "pytest full suite delta=0 vs baseline"
      verifier:
        type: shell
        cmd: "cd /home/chris/AISALESHT/backend && .venv/bin/pytest --tb=no -q 2>&1 | tail -3 # compared by /dev-team vs baseline-be-tests.json"
  quality_gates:
    - "Single-file commit — `git diff --name-only HEAD~1..HEAD | wc -l` = 1"
    - "Commit body cites Pattern P6 + addendum 2026-05-13 + auditor C2 exception"
    - "anti-duplication.md updated with migration-window exception row OR commit body references this addendum verbatim"
  depends_on: ["T-1"]
  blocks: ["T-2", "T-3", "T-4", "T-5", "T-6", "T-7"]
  assigned_to: null
```

### 4.4 T-7 amended scope

T-7 (`BE imports rewrite — shared/* cross-cutting`) gains ONE new sub-step in
description:

> **Step 12 (NEW — addendum 2026-05-13 closure):** Delete the migration-window
> stub `backend/src/shared/domain/base_entity.py` created in T-2-prep. After
> T-7, all AISALESHT shared imports are rewritten to `luana_core_platform.*`,
> so the stub is no longer transitively imported. Final closure of Pattern P6
> migration window.

Acceptance A4 added to T-7:

```yaml
- id: A4
  description: "Migration-window stub deleted (Pattern P6 closure)"
  verifier:
    type: shell
    cmd: "test ! -f /home/chris/AISALESHT/backend/src/shared/domain/base_entity.py"
```

### 4.5 T-2..T-6 mechanics unchanged

Codemod application unchanged. Halt Triggers #1 (missing symbol), #2 (test
mocks), #11 (mock missing) workflows unchanged. The new Trigger #12 (SQLA
collision class) added BUT not expected to fire because T-2-prep eliminates
the class entirely.

---

## 5. Codemod implications

**No changes required to `scripts/codemod_be_imports.py` MAPPING.** The
existing entry `"src.shared.domain": "luana_core_platform.domain"` continues
to rewrite imports as designed. The re-export stub created in T-2-prep
simply means that BEFORE the rewrite happens (when modules still
import `from src.shared.domain.base_entity`), the import resolves to the
same Base as the post-rewrite target.

**Optional codemod hardening (RECOMMENDED — to be added to T-2-prep scope OR T-1.9):**

Add a self-check assertion to `scripts/codemod_be_imports.py --self-check`:

```python
# In SELF_CHECK_ASSERTIONS (or equivalent test block):
def _self_check_base_unification():
    """Verify shared/domain/base_entity.py is a re-export stub before codemod runs."""
    from pathlib import Path
    p = Path("backend/src/shared/domain/base_entity.py")
    if not p.exists():
        return  # T-7 closure done — stub deleted
    content = p.read_text()
    if "declarative_base()" in content:
        raise AssertionError(
            "shared/domain/base_entity.py still declares declarative_base() — "
            "T-2-prep must run before codemod (Pattern P6, addendum 2026-05-13). "
            "Run /dev-team T-2-prep first."
        )
    if "from luana_core_platform.domain.base_entity import Base" not in content:
        raise AssertionError(
            "shared/domain/base_entity.py is not a Pattern P6 re-export stub. "
            "See docs/.../03-arch-be-addendum-2026-05-13.md §4.3"
        )
```

This guards against running T-2..T-6 codemod on an un-prepped tree.

**Cost of this hardening:** ~$20 Sonnet (add ~10 LOC to codemod + 1 pytest
assertion). Can fold into T-2-prep ticket without changing budget.

---

## 6. Pre-spawn smoke test (audit gap remediation — codified)

### 6.1 NEW ratified Halt Trigger #12 — SQLA collision class

Add to outcome §7.6.2 trigger list (architect proposes — Chris ratifies
during this addendum review):

> **12. Sub-agent during T-2..T-7 codemod application encounters
> SQLAlchemy runtime collision** (`InvalidRequestError: Table 'X' is
> already defined`, `NoReferencedTableError`, `SAWarning declarative base
> already contains class`). Halt-and-ask Chris between: (A) Pattern P6
> shared-base lift first (if not already done in T-2-prep — verify it
> was applied), (B) Pattern P2 transitive stub closure (per-module),
> (C) Pattern P3 dual-Base isolation (rejects anti-duplication §0 —
> normally NOT chosen). **Ratified Chris 2026-05-13 Session 6 Phase D
> + addendum 2026-05-13 §6.**

### 6.2 Pre-spawn smoke test (NEW step in /dev-team workflow before T-2..T-7 spawn)

Before /dev-team spawns ANY of T-2..T-7, /dev-team Phase 0 MUST run:

```bash
cd /home/chris/AISALESHT/backend
.venv/bin/python -c "
# Pattern P6 verification — Base unification
import sys
try:
    from src.shared.domain.base_entity import Base as A
    from luana_core_platform.domain.base_entity import Base as L
    assert A is L, 'Base instances are DISTINCT — T-2-prep not yet applied (Pattern P6)'
    print('OK: Pattern P6 prologue applied — Base unified')
    sys.exit(0)
except AssertionError as e:
    print(f'FAIL: {e}')
    print('Action: spawn /dev-team T-2-prep BEFORE T-2..T-7')
    sys.exit(1)
"
```

If this returns non-zero → /dev-team REFUSES to spawn T-2..T-7 until
T-2-prep is closed `done`. Codified as `06-tickets.yaml::T2.depends_on:
[T-1, T-2-prep]` (and so on for T-3..T-7).

### 6.3 Pre-spawn smoke test (collect-only)

In addition to the Base-identity check, /dev-team Phase 0 runs:

```bash
cd /home/chris/AISALESHT/backend
.venv/bin/pytest tests/modules/iam/ tests/modules/brand/ tests/modules/offer/ \
  --collect-only -q --no-header 2>&1 | grep -E "error|InvalidRequestError|NoReferencedTableError"
```

If grep returns any line → halt + Trigger #12. This is the **fast canary**
for the entire runtime-collision class (covers Pydantic discriminator,
FastAPI dependency collision, redis singleton — any runtime side-effect
that surfaces at pytest collect-only time).

---

## 7. Audit gap remediation — codified rule

**Proposed addition to `.claude/rules/anti-duplication.md` OR new file
`.claude/rules/lift-audit-completeness.md`** (architect proposes — Chris
ratifies):

> **Rule: static lift audits MUST include `pytest --collect-only` smoke**
>
> **Origin:** Story 10 T-1.7 audit (2026-05-13) declared 85-90% confidence
> based on static symbol-level grep. Audit missed SQLAlchemy
> `Table/Mapper` collision class because runtime registration side-effects
> are invisible to static analysis. T-2 attempt 4 failed at collect-only
> step. ~$200 Opus wasted on builder spawn that immediately halted.
>
> **Cardinal rule:** any lift audit (cross-tree symbol-by-symbol diff,
> codemod parity check, MAPPING verification) MUST include a final
> `pytest --collect-only` step on at least 2 representative consumer
> modules (highest FK-density preferred — e.g., for ORM migrations,
> include the module with most cross-module ports + the module with
> deepest FK chain). Cost: ~$0 (~30 seconds local Python). Catches
> entire class of runtime collisions invisible to grep.
>
> **Enforcement:** auditor-{backend,frontend,agentic} Step 0.5 (pre
> consume_gate_output) verifies that any lift-audit ticket emits a
> `*-collect-only-smoke.txt` artifact in its result folder. If missing
> → audit verdict downgraded automatic from PASS to ESCALATED.

This rule is **codified retroactively** for Story 10 (T-1.7 lacked
it; T-2-prep includes it) and is **forward-binding** for Stories 11-14
(which will face similar lift challenges per §7.6.1 inheritance).

---

## 8. Cost estimate revised

### 8.1 Pre-revision (per current 06-tickets.yaml)

| Wave | Cost USD range |
|---|---|
| T-1 baseline | 150-250 |
| T-2..T-7 (BE) | 3900-5750 |
| T-8..T-9 (FE+Vercel) | 1000-1500 |
| T-10 (DB) | 700-1000 |
| T-11..T-12 (E2E+CI) | 500-800 |
| T-13..T-14 (closure) | 600-1000 |
| **Total** | **6850-10300** |

### 8.2 Post-revision (per Pattern P6 + T-2-prep insertion)

| Wave | Cost USD range | Δ |
|---|---|---|
| T-1 baseline | 150-250 | 0 |
| **T-2-prep** | **30-50** | **+50** |
| T-2..T-7 (BE) | 3900-5750 | 0 (mechanics unchanged) |
| T-8..T-9 (FE+Vercel) | 1000-1500 | 0 |
| T-10 (DB) | 700-1000 | 0 |
| T-11..T-12 (E2E+CI) | 500-800 | 0 |
| T-13..T-14 (closure) | 600-1000 | 0 |
| **Total** | **6880-10350** | **+30-50 (~0.5%)** |

### 8.3 Cost already burned in Session 5 + 6 (sunk)

Per SESSION-6-T-2-HALT-2026-05-13.md:

| Phase | Cost USD |
|---|---|
| Session 5 (T-2 attempts 1-3) | ~$850 |
| Session 6 Phase A (T-1.7 audit) | ~$400 |
| Session 6 Phase C (T-1.8 codemod) | ~$30 |
| Session 6 Phase D (T-2 attempt 4 halt) | ~$200 |
| Haiku commits | ~$50 |
| Architect revision (this run) | ~$200 estimate |
| **Total sunk pre-T-2-prep** | **~$1730** |

**Revised total Story 10 estimate** (sunk + remaining post-T-2-prep):
**~$8610-12080**. Still under the $5000 soft check-in budget per wave
(check-ins at $4000, $4500, $5000 per outcome §7.6.2 trigger #9).

---

## 9. Pre-Chris-ratification questions

**Q1 (material — proceed cannot continue without decision).** Pattern P6
adds a NEW Halt Trigger #12 to outcome §7.6.2 trigger inventory.
**Approve adding Trigger #12 retroactively (ratified by Chris 2026-05-13
as condition for Option C addendum acceptance)?**

> Architect's recommendation: YES. The SQLA collision class is now
> documented; future Stories 11-14 will face similar lift challenges,
> and Trigger #12 codifies the escape hatch. Cost of adding: 0.
>
> Inheritance per §7.6.1: Trigger #12 inherits forward to Stories 11-14
> by default (lift challenges expected). One-time decision.

**Q2 (clarifying — not blocking but architect prefers explicit).** The
T-2-prep ticket re-export pattern creates a migration-window-scoped
exception to `.claude/rules/anti-duplication.md §0` cardinal. The exception
auto-closes when T-7 deletes the stub.
**Approve codifying the migration-window scoped exception as a NEW
inventory row in anti-duplication.md (visible to future auditors)?**

> Architect's recommendation: YES with auto-closure. Add row to
> anti-duplication.md inventory:
> > | `src.shared.domain.base_entity.Base` | re-export stub | shared
> > base singleton unification during multi-ticket lift | DELETED at
> > T-7 — Story 10 migration window only |
>
> Auditor-{backend,agentic} reads this row + understands the stub is
> intentional during migration, not a permanent mirror.

**Q3 (clarifying — escape hatch only).** If a future audit reveals
another runtime collision class beyond SQLA (e.g., Pydantic Field
discriminator clash, FastAPI dependency override conflict — none
detected so far in this addendum review), Pattern P6 generalises:
"lift the shared singleton FIRST, then rewrite consumers".
**Confirm pattern generalisation is implicit (no separate ratification
per future surprise class — Trigger #12 catches them all)?**

> Architect's recommendation: YES. Trigger #12 wording is intentionally
> broad ("SQLAlchemy runtime collision OR equivalent runtime
> singleton conflict surfaced at pytest --collect-only"). One trigger
> covers all runtime-singleton classes.

If Q1+Q2+Q3 are YES → proceed to /pm regenerate revised 06-tickets.yaml
+ inject T-2-prep + update outcome §7.6.2 with Trigger #12.

---

## 10. Cross-reference

- `SESSION-6-T-2-HALT-2026-05-13.md` — halt context (Option C ratified)
- `T-1.7-lift-audit-report.md` — static audit (§7 codified as gap)
- `T-2-impl-log.md` — 4 attempts cumulative
- `T-2-result.md` — current FAIL status
- `06-tickets.yaml` — revised by §4 of this addendum
- `03-arch-be.md` — parent doc (Wave sequence amended here)
- `docs/product/outcomes/luana-platform-migration.md §7.6` — 10 binding
  decisions (preserved verbatim — this addendum adds Trigger #12 only)
- `.claude/rules/anti-duplication.md` — migration-window exception row
  to be added (Q2)
- `.claude/rules/backend-ddd.md` — schema-mirror exception (no change)
- [SQLAlchemy 2.0 Declarative Tables](https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html)
  accessed 2026-05-13 — single Base = single MetaData invariant cited
  in §1.1 + §2.6
- [SQLAlchemy GitHub Discussion #7711 "Share class registry"](https://github.com/sqlalchemy/sqlalchemy/discussions/7711)
  accessed 2026-05-13 — cross-Base registry sharing patterns reviewed
  for Pattern P3 evaluation
- `scripts/codemod_be_imports.py` — MAPPING unchanged (per §5)
- `.tessl/tiles/maria/fastapi/rules/pii-sanitisation.md` — N/A this
  addendum (no API changes)

---

## 11. Knowledge cutoff disclosure

Architect run via Claude Opus 4.7 (model knowledge cutoff January 2026).
SQLAlchemy 2.0 + Python 3.12 patterns researched live via WebSearch on
2026-05-13 to validate Pattern P6 against current canonical docs.
Reproduction of T-2 halt symptoms verified by applying stash@{1} on
local AISALESHT clone + running pytest collect (output captured in
§3.2 R-A1 verification + repro_evidence block of T-2-prep ticket spec).

---

**END OF ADDENDUM — awaits Chris ratification on Q1, Q2, Q3 before
/pm regenerates 06-tickets.yaml with T-2-prep insertion + outcome
§7.6.2 with Trigger #12.**
