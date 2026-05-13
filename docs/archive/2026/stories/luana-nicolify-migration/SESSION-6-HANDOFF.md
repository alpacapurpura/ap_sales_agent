# Session 6 Handoff Prompt — Story 10 R1 lift audit

> **Date Session 5 closed:** 2026-05-12
> **Ratification:** Chris approved R1 (proactive lift audit) per SESSION-5-HALT-2026-05-12.md
> **Owner Session 6:** /pm orchestrator

---

## Bootstrap Session 6 — read first

```bash
git status --short && git branch --show-current && git log --oneline -5
cat docs/product/BACKLOG-TLDR.md
cat docs/product/stories/luana-nicolify-migration/checkpoint.md
cat docs/product/stories/luana-nicolify-migration/SESSION-5-HALT-2026-05-12.md
cat docs/product/stories/luana-nicolify-migration/T-1.6-mapping-audit.md
git stash list  # should show: stash@{0}: WIP-T-2-third-attempt-cutoff-need-re-exports
```

Verify:
- Story 10 state=`developing` (paused mid-Wave-1A)
- Session 5 cumulative cost ~$2100 ratified
- Chris R1 strategy ratified
- Stash present with T-2 third attempt WIP (review optional, drop after audit complete)

## Session 6 mission — proactive lift audit + revise plan

### Phase A — Audit Opus spawn (~$1000-1500)

Spawn dedicated audit Opus 4.7 with this prompt:

```
You are auditor Opus 4.7 — comprehensive lift audit Stories 1-9 for Story 10 unblock.

## Mission

Generate symbol-by-symbol diff between AISALESHT (`/home/chris/AISALESHT/backend/src/`) and luana-platform/core/ (`/home/chris/luana-platform/core/luana-core-*/`) to identify ALL missing exports/re-exports that would block Story 10 T-2..T-7 import rewrites.

## Read FIRST

1. `docs/product/outcomes/luana-platform-migration.md` §7.6 (10 decisions ratified)
2. `docs/product/stories/luana-nicolify-migration/01-spec.md` (Story 10 spec)
3. `docs/product/stories/luana-nicolify-migration/03-arch.md` + `03-arch-be.md` (migration mechanics)
4. `docs/product/stories/luana-nicolify-migration/T-1.6-mapping-audit.md` (codemod MAPPING corrections applied)
5. `docs/product/stories/luana-nicolify-migration/SESSION-5-HALT-2026-05-12.md` (what surfaced)
6. `docs/archive/2026/stories/luana-shared-lift/07-merge.md` (Story 2 lift scope)
7. `docs/archive/2026/stories/luana-iam-tenancy-content/07-merge.md` (Story 3 lift scope)
8. `docs/archive/2026/stories/luana-crm-analytics-landing-connections/07-merge.md` (Story 4)
9. `docs/archive/2026/stories/luana-brand-offer-studios/07-merge.md` (Story 5)
10. `docs/archive/2026/stories/luana-copilot-engine/07-merge.md` (Story 6)
11. `docs/archive/2026/stories/luana-sales-agent-engine/07-merge.md` (Story 7)

## Audit scope — for EACH luana-core package

For each of 25 packages in `/home/chris/luana-platform/core/luana-core-*/`:

1. **Map source path** — which AISALESHT path did this lift from? (e.g., luana-core-brand-studio ← src/modules/brand)
2. **Enumerate AISALESHT exports** — `grep -rE "^(def |class |[A-Z_]+ =)" {src_path}/` capture all top-level names
3. **Enumerate luana-core exports** — same grep against luana-core target package
4. **Diff** — list (A) symbols in AISALESHT but NOT in luana-core (= missing, must be added) (B) symbols renamed (= migration code change needed) (C) symbols in luana-core extra (= acceptable additions)
5. **Categorize missing symbols:**
   - **Critical** — consumed by other modules (grep `from src.{path}.X` across AISALESHT)
   - **Internal** — only used within module (no consumer outside) → can skip
6. **Generate fix plan per critical missing symbol:**
   - Option α: add to luana-core package as new export (lift completion)
   - Option β: add re-export shim in luana-core (if symbol lives elsewhere)
   - Option γ: defer to Story 14 if not used by Story 10 critical paths

## Special focus areas (high-risk based on Session 5 surface)

- `src.shared.links.ports.*` — verified ALL ports lifted to luana_core_platform.links.ports/ (T-1.6 fixed). Verify ALL 21 port files match symbol-by-symbol.
- `src.shared.domain.events` → `luana_core_platform.domain.events` — was this lift complete? Check exports.
- `src.shared.application.*` → `luana_core_platform.application.*` — likely contains personality_event_handlers + others. Check.
- `src.shared.api.*` → `luana_core_platform.api.*` — Story 5/6 lift surfaced this. Check.
- `src.shared.workers` → DEFERRED Story 10b per T-1 codemod. Verify no critical consumers.
- Cross-module relationships — modules import each other via `src.shared.links.ports.X` only (port pattern). Verify port files cover all cross-module deps.

## Output

Write `docs/product/stories/luana-nicolify-migration/T-1.7-lift-audit-report.md`:

1. Executive summary (counts: N packages audited, M missing symbols critical, K missing internal, J renamed)
2. Per-package diff table (rows = packages, cols = missing count critical / missing internal / renamed / extra)
3. Detailed missing critical symbols list (each with: AISALESHT path, target luana-core path, consumer modules, recommended fix α/β/γ)
4. Re-export shims required (concrete .py file content to add to luana-core packages)
5. Lift completion patches required (symbols to actually lift)
6. Story 14 deferrals (acceptable carry-over)
7. Updated T-1 codemod MAPPING (any new entries needed?)
8. Confidence score: post-fix, what's probability T-2..T-7 execute without halts?

## Last line

`done -> docs/product/stories/luana-nicolify-migration/T-1.7-lift-audit-report.md`
OR `awaiting_chris -> <blocker>` (if audit surfaces something requiring Chris before proceeding)
OR `failed -> <reason>`
```

### Phase B — Chris ratifies audit (interactive)

After audit done:
1. /pm orchestrator reads T-1.7-lift-audit-report.md summary
2. Surfaces to Chris:
   - Total missing symbols count
   - Critical vs internal split
   - Recommended fix mix (α/β/γ counts)
   - Estimated cost to apply fixes
3. Chris ratifies fix plan OR adjusts

### Phase C — Apply lift fixes (Sonnet/Opus per scope)

Spawn fix builders:
- **Generate re-export shims** (Sonnet, mechanical) — add `from luana_core_X.Y import *` lines in target packages
- **Apply lift patches** (Opus, careful) — actually lift missing functions/classes from AISALESHT to luana-core
- **Update T-1 codemod MAPPING** if needed for any newly-discovered path

### Phase D — Drop stash + restart T-2

```bash
git stash drop stash@{0}  # T-2 third attempt WIP no longer relevant
```

Re-spawn T-2 builder-backend Opus with FULL CONFIDENCE that imports resolve. Same prompt structure as Session 5 T-2 attempt 3 but reference T-1.7 audit as proof of readiness.

### Phase E — Continue T-3..T-7 in sequence

After T-2 done (Wave 1A), proceed T-3, T-4, T-5, T-6, T-7. NO PARALLELIZATION until at least 2 tickets done clean back-to-back (build confidence).

Each ticket: same pattern (single Opus builder, halt-and-ask if surprise, fix on discovery trivial only).

### Phase F + onwards — Resume original 14-ticket plan from T-8 onwards

Wave 3 (T-8..T-10), Wave 4 (T-11..T-12), Wave 5 (T-13..T-14) as originally planned.

## Session 6 success criteria

- T-1.7 audit report emitted
- All critical missing symbols addressed (lift OR shim OR deferred)
- T-2 brand+offer rewrite ✓ DONE with delta=0 vs baseline
- T-3 next module rewrite ✓ DONE
- Cumulative Session 6 cost reported transparently

## Session 6 cost estimate

- Phase A audit: ~$1000-1500 Opus
- Phase B Chris ratify: $0 (interactive)
- Phase C fixes: ~$500-1500 depending on missing symbol count
- Phase D-E T-2 + T-3 done clean: ~$600-1000
- **Total Session 6 estimate: ~$2100-4000**

## Story 10b handoff prompt (deferred until Story 10 closes)

Per Decisión 10A Chris explicit request — handoff prompt for Story 10b generated at Story 10 done, NOT mid-Story-10. Session 6/7+ closes Story 10 first.

## Status references

- Session 5 final commit: `dce1eec2 docs(story-10): Session 5 Phase 2 PAUSED`
- Last working state: T-1.6 codemod fix `340fd350`
- Stash with T-2 third attempt WIP: `stash@{0}: WIP-T-2-third-attempt-cutoff-need-re-exports`
- /pm SSoT location: `docs/product/` in AISALESHT (Decisión 4A — migrate to luana-platform at Story 10 close, NOT during)

## Open from Chris ratification needed

None — R1 strategy ratified. Audit can proceed directly Session 6 bootstrap.

---

**Ready for Session 6 fresh-context start.** /pm orchestrator (Opus 4.7) reads this handoff + spawns Phase A audit immediately.
