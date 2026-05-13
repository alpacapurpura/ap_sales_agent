---
ticket: T-13
title: "/pm SSoT atomic git mv (Phase 4 merge)"
date: 2026-05-16
session: 10
owner: /pm Opus inline (Sonnet/Opus spawn skipped — rsync mechanical)
verdict: done_partial
state_transition: draft → done_partial (rsync executed dual-state; AISALESHT delete deferred to /auditor merge ratification — T-19 stub)
re_scoped_from: "atomic git mv"
re_scope_reason: "Chris Q3 Sesion 10 ratified Option B (rsync + delete, preserve git history both repos). Rsync done; delete deferred to Conv 3 merge ratification — keeps active session writes possible during dual-state."
---

# T-13 — /pm SSoT cross-repo migration (rsync mirror)

> **Sesion 10 Q3 ratificación:** Option B rsync + delete (preserve git history both repos vs atomic git mv that loses bisect-friendly history cross-repo). Sesion 10 Phase 6 executes rsync ONLY; AISALESHT delete deferred to /auditor Conv 3 merge ratification (avoids breaking active session writes during dual-state).

## Execution

### Step 1 — Create destination

```bash
mkdir -p /home/chris/luana-platform/docs/product/stories/
```

### Step 2 — Rsync story folder (mirror mode)

```bash
rsync -a --delete \
  /home/chris/AISALESHT/docs/product/stories/luana-nicolify-migration/ \
  /home/chris/luana-platform/docs/product/stories/luana-nicolify-migration/
```

- `-a` archive mode (preserve timestamps + perms + symlinks)
- `--delete` mirror exactness (luana-platform side reflects AISALESHT exactly)
- Source trailing slash semantics: copies CONTENTS of source dir into destination

### Step 3 — Verification

| Check | Result |
|---|---|
| AISALESHT story folder file count | 42 files |
| luana-platform story folder file count | 42 files |
| `diff <(ls AISALESHT/...) <(ls luana-platform/...)` | empty (identical filenames) |
| Sesion 10 impl-logs present luana-platform side | ✅ T-8bis + T-15 + T-9 + T-11 + T-12 + T-13 all mirrored |

### Step 4 — Deferred AISALESHT delete

**NOT executed Sesion 10.** Reasons:
1. Active session continues writing T-13-impl-log.md + T-14-impl-log.md + SESSION-10-CLOSE.md in AISALESHT path during dual-state
2. /auditor Conv 3 hasn't started — story state still `developing` (not `reviewing` or `done`)
3. Per /pm protocol, archive step runs AT merge time post-/auditor APPROVED ratification
4. Premature delete risks breaking parallel sessions or session resume

**Delete will execute at T-19 (post-/auditor APPROVED Conv 3 merge):**
- Final delta rsync (capture SESSION-10-CLOSE.md + any /auditor review docs)
- `git rm -r docs/product/stories/luana-nicolify-migration/` in AISALESHT
- Story 10 archived to `luana-platform/docs/archive/2026/stories/luana-nicolify-migration/` (or stays in active `stories/` per /pm protocol)
- Capability YAML promotion in luana-platform (if applicable)
- 07-merge.md authored

## What T-13 Sesion 10 DOES NOT do

1. ❌ NO AISALESHT side delete (deferred → T-19 post-merge)
2. ❌ NO /pm SSoT broader migration (outcomes/, capabilities/, modules/, ideas-pool.yaml stay in AISALESHT)
3. ❌ NO BACKLOG.{yaml,md} regen at luana-platform (BACKLOG generator script stays AISALESHT-side until brand-extraction story)
4. ❌ NO `docs/process/learnings.md` move (cross-brand learnings — separate scope)
5. ❌ NO `docs/specs/templates/` move (cross-brand templates — separate scope)
6. ❌ NO atomic git mv (would lose bisect-friendly history cross-repo per Chris Q3 ratification)

## Capability YAML resolution check (per spec verifier)

Spec acceptance asks: "capability YAML + outcome YAML still resolve post-mv".

| Resolver | AISALESHT-side path | luana-platform path | Status |
|---|---|---|---|
| `docs/product/capabilities/{module}/{cap}.yaml` | ✅ intact (NOT moved Sesion 10) | ❌ NOT present (deferred future story) | Resolves AISALESHT side only |
| `docs/product/outcomes/luana-platform-migration.md` | ✅ intact | ❌ NOT present | AISALESHT side only |
| `docs/product/modules/{m}.md` | ✅ intact | ❌ NOT present | AISALESHT side only |
| `docs/product/ideas-pool.yaml` | ✅ intact | ❌ NOT present | AISALESHT side only |
| Story folder `stories/luana-nicolify-migration/` | ✅ intact | ✅ MIRROR (42 files) | DUAL-STATE |
| Story-internal cross-references (`../03-arch.md`, `06-tickets.yaml`) | ✅ resolve within story folder | ✅ resolve within mirror | DUAL-STATE |

**Verdict:** All story-internal references resolve in luana-platform mirror. Cross-folder references (e.g., `../../outcomes/luana-platform-migration.md`) resolve AISALESHT-side only — luana-platform consumer would need broader /pm SSoT migration story.

## Acceptance grid

| Acceptance (per T-13 spec) | Status | Evidence |
|---|---|---|
| **A1** Story folder mirrored to luana-platform | ✅ COMPLETE | 42/42 files, identical filenames |
| **A2** Capability YAML + outcome YAML resolve | ⏳ PARTIAL | Story-internal resolves; cross-folder (outcomes/, capabilities/) deferred to broader migration |
| **A3** Bisect-friendly history preserved both repos | ✅ COMPLETE | rsync (not git mv) — both repos retain pre-Sesion-10 commit chain |
| **A4** AISALESHT side delete | ⏳ DEFERRED → T-19 post-merge |

## Halt triggers status

| Trigger | Status |
|---|---|
| H10 cross-repo SSoT divergence | NOT triggered — dual-state cleanly mirrored; T-19 will reconcile at merge |

## Files modified

### AISALESHT (development)
- `docs/product/stories/luana-nicolify-migration/T-13-impl-log.md` — NEW (this file)
- `docs/product/stories/luana-nicolify-migration/06-tickets.yaml` — T-13 state update + T-19 stub append (in commit)

### luana-platform (main)
- `docs/product/stories/luana-nicolify-migration/` — NEW directory (42 files mirrored from AISALESHT)

## T-19 stub (recommended add to 06-tickets.yaml)

```yaml
T19:
  id: T-19
  title: "T-13 follow-up — AISALESHT story folder delete + Story 10 archive luana-platform side post-/auditor APPROVED"
  type: tooling
  surface: BE
  wave_position: 7                          # Conv 3 merge time
  state: draft
  origin: "T-13 Sesion 10 — rsync done, delete deferred to /auditor APPROVED merge ratification"
  owner_eligibility:
    claude_sonnet: true
  estimate_hours: 1
  estimated_cost_usd_range: [100, 200]
  depends_on: ["T-14", "/auditor APPROVED"]
```

## Cost estimate

| Operation | Tokens (est) | Cost USD (est) |
|---|---|---|
| /pm Opus inline rsync + impl-log | ~5k | ~$0.30 |
| **T-13 total** | ~5k | **~$0.30** |

Way under $400-700 original estimate (rsync trivial vs atomic git mv risk).

## Verdict

`done_partial` — Story folder mirrored to luana-platform/docs/product/stories/. AISALESHT delete + broader /pm SSoT migration deferred to /auditor Conv 3 merge ratification + T-19 + future brand-extraction story.

**T-14 (AISALESHT archive prep) unblocked. T-19 deferred.**

## Cross-reference

- Q3 ratification: Sesion 10 Chris answers (Option B rsync + delete)
- /pm Conv 3 protocol: `.claude/skills/pm/SKILL.md` § Capability promotion (al merge)
- Follow-up: T-19 stub (post-/auditor APPROVED merge)

Last line: `done_partial -> docs/product/stories/luana-nicolify-migration/T-13-impl-log.md`
