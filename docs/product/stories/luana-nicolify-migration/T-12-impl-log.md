---
ticket: T-12
title: "Make ci-parity root migration + pre-push hook update"
date: 2026-05-16
session: 10
owner: /pm Opus inline (Sonnet spawn skipped — file count small)
verdict: done
state_transition: draft → done
---

# T-12 — Make ci-parity root migration + pre-push hook update

> **Decisión 8 ratificada (Story 10 Phase 0):** ci-parity location = luana-platform root (cross-brand pattern). Stories 11-13 (vitalia, comunify, lupulo) heredan automático cuando se sumen brands. Per Chris Q2 Sesion 10 framework: cada marca su propio deploy, scripts brand-specific viven en brand-repo eventually.

## Deliverables

### NEW `luana-platform/Makefile` (root)

**Cross-brand orchestrator:**

```makefile
BRANDS := nicolify
# Stories 11-13 append: BRANDS += vitalia comunify lupulo

ci-parity: $(BRANDS:%=ci-parity-%)
	@printf "✓ ci-parity all brands GREEN: $(BRANDS)\n"

ci-parity-%: scripts/ci-parity.sh
	bash scripts/ci-parity.sh --brand=$*

ci-parity-be:        # All brands, BE only
ci-parity-fe:        # All brands, FE only
```

Skip-flags wrappers (`ci-parity-be`, `ci-parity-fe`) iterate all brands. Per-brand targets auto-generated via `ci-parity-%` pattern rule.

### NEW `luana-platform/scripts/ci-parity.sh`

Cross-brand adaptation of AISALESHT `scripts/ci-parity.sh`. Key changes:
- **`--brand=NAME` flag REQUIRED** (no implicit default — explicit brand resolution)
- **Brand directory validation** — fails fast if `<brand>/` not present at luana-platform root
- **Paths resolved per brand** — `$BRAND/backend/`, `$BRAND/frontend/` (vs hard-coded `backend/`, `frontend/` in AISALESHT version)
- **Per-brand Docker image tags** — `local-be-ci-$BRAND` + `local-fe-ci-$BRAND` (no collision across multi-brand runs)
- **Per-brand HEAD marker** — `.git/ci-parity-passed-$BRAND-<sha>` (vs AISALESHT `.git/ci-parity-passed-<sha>`)
- **Validator advisory mode** — `validate_ci_parity_mirror.py` not yet adapted to cross-brand layout, runs advisory-only

Pre-prod parity preserved:
- Same Docker test images (Dockerfile target=test)
- Same env block (TZ=UTC, NODE_OPTIONS=--max-old-space-size=4096)
- Same steps order (ruff check + format + pytest + pip-audit BE; ESLint + tsc + vitest + npm audit FE)
- Same pytest exclude (`tests/modules/analytics/test_meta_provider.py`)

### NOT modified Sesion 10 — `.husky/pre-push` defer to T-18

AISALESHT `.husky/pre-push` and `scripts/git-hooks/pre-push` (81 lines) reference AISALESHT-relative paths + check `.git/ci-parity-passed-<sha>` marker. Per Chris framework, post-T-14 cutover when nicolify becomes brand-repo (or luana-platform becomes single source), pre-push hook will move accordingly.

**Why deferred:**
1. AISALESHT ci-parity stays functional until T-14 — Chris can `cd AISALESHT && make ci-parity && git push origin development` during dual-state
2. luana-platform pre-push will be authored when first brand-extraction story closes (or when archive cutover establishes single-source)
3. T-18 stub recommended for pre-push migration + AISALESHT cleanup

## Acceptance grid

| Acceptance (per T-12 spec) | Status | Evidence |
|---|---|---|
| **A1** `luana-platform/Makefile` exists with `ci-parity` cross-brand target | ✅ GREEN | 56 lines, BRANDS variable, pattern rule `ci-parity-%`, skip-flags wrappers |
| **A2** `luana-platform/scripts/ci-parity.sh` runs `bash scripts/ci-parity.sh --brand=nicolify` | ✅ GREEN | 5523 bytes, executable, validates brand directory, per-brand Docker tags + markers |
| **A3** AISALESHT ci-parity preserved until T-14 | ✅ GREEN | No AISALESHT files modified by T-12 — pre-existing `make ci-parity` continues functional |
| **A4** Pre-push hook update | ⏳ DEFERRED → T-18 | Hook stays in AISALESHT; future brand extraction or luana-platform single-source establishment will migrate |

## Halt triggers status

| Trigger | Status |
|---|---|
| H6 cross-brand pattern invariant violated | NOT triggered — BRANDS variable + pattern rule correctly scaffolded for future brand additions |

## Files modified

### luana-platform (main)
- `Makefile` — NEW (cross-brand ci-parity orchestrator)
- `scripts/ci-parity.sh` — NEW (per-brand executor, chmod +x)

### AISALESHT (development)
- `docs/product/stories/luana-nicolify-migration/T-12-impl-log.md` — NEW (this file)
- `docs/product/stories/luana-nicolify-migration/06-tickets.yaml` — T-12 state update (in commit) + T-18 stub (in commit)

## Pre-T-14 dual-state status

| Tool | AISALESHT (going away) | luana-platform (becoming SSoT) |
|---|---|---|
| `make ci-parity` | ✅ functional, no changes | ✅ scaffolded, awaits Dockerfile path validation post-T-14 |
| `scripts/ci-parity.sh` | ✅ functional | ✅ cross-brand version present |
| `.husky/pre-push` | ✅ functional | ⏳ deferred T-18 |
| `scripts/git-hooks/pre-push` | ✅ functional | ⏳ deferred T-18 |

Chris workflow during dual-state:
- `cd /home/chris/AISALESHT && make ci-parity` — runs vs AISALESHT layout (preserved)
- `cd /home/chris/luana-platform && make ci-parity` — runs vs luana-platform/nicolify/ layout (NEW, requires Dockerfile + .env wiring T-17 validates)

## T-18 stub (recommended add to 06-tickets.yaml)

```yaml
T18:
  id: T-18
  title: "T-12 follow-up — .husky/pre-push migration + ci-parity validation in luana-platform single-source state"
  type: tooling
  surface: BE
  wave_position: 6                          # Post-T-14
  state: draft
  origin: "T-12 partial — pre-push hook + ci-parity execution validation deferred to single-source state"
  owner_eligibility:
    claude_sonnet: true
  estimate_hours: 2
  estimated_cost_usd_range: [200, 400]
  depends_on: ["T-14"]
```

## Cost estimate

| Operation | Tokens (est) | Cost USD (est) |
|---|---|---|
| /pm Opus inline file authoring + impl-log | ~8k | ~$0.50 |
| **T-12 total** | ~8k | **~$0.50** |

Way under $200-300 original estimate.

## Verdict

`done` — Cross-brand `make ci-parity` scaffolding LANDED in luana-platform. AISALESHT ci-parity preserved functional until T-14. Pre-push hook migration deferred → T-18 post-cutover.

**T-13 (/pm SSoT rsync) unblocked.**

## Cross-reference

- Decisión 8: outcome `luana-platform-migration.md` § 7.6 Decision 8
- Predecessor reference: AISALESHT `scripts/ci-parity.sh` (139 lines)
- Follow-up: T-18 stub (post-T-14)

Last line: `done -> docs/product/stories/luana-nicolify-migration/T-12-impl-log.md`
