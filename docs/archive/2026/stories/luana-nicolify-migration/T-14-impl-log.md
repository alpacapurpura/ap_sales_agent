---
ticket: T-14
title: "AISALESHT archive + DB drop + Story 10 archive at luana-platform"
date: 2026-05-16
session: 10
owner: /pm Opus inline (prep only — Chris executes archive UI per Q4=B ratification)
verdict: awaiting_chris
state_transition: draft → halt_awaiting_chris (Chris triggers archive externally — irreversible decision human gate)
re_scoped_from: "/pm self-service `gh api archive` autonomous"
re_scope_reason: "Chris Q4 Sesion 10 ratified Option B — pause for Chris UI manual archive (GitHub Settings). Irreversible decision deserves human gate."
---

# T-14 — AISALESHT archive (Chris UI manual gate)

> **Sesion 10 Q4 ratificación:** Option B pause for Chris UI manual archive. /pm prepares all pre-archive verification + drop `visionarias_logs` DB + drafts 07-merge.md. Chris executes archive in GitHub Settings UI when comfortable (post-/auditor APPROVED + 24h+ soak verification).

## Pre-archive verification checklist (/pm Sesion 10)

| Check | Status | Notes |
|---|---|---|
| Story 10 Sesion 9-10 commits pushed both repos | ✅ | AISALESHT `63f821b6` (S9) + S10 pending commit; luana-platform `d31c3f6` (S9) + S10 pending commit |
| T-8 + T-10 deliverables landed luana-platform/nicolify/ | ✅ | nicolify/backend/ + nicolify/frontend/ rsync present |
| T-8.bis A4+A5 GREEN cement | ✅ | workspace symlinks + 0 legacy @/* (excl. Nicolify-local guards) |
| T-15 A1 (Cat 1) + A2 (Cat 2) GREEN | ✅ | tests/migrations/ cleared + conftest.py + .gitignore landed |
| T-9 deploy infrastructure verify | ✅ | dev-app.nicolify.com CF tunnel state documented (pre-existing down, NO regression Story 10) |
| T-11 E2E surface mirrored | ✅ | 44/44 specs in luana-platform/nicolify/frontend/e2e/ |
| T-12 ci-parity cross-brand scaffolding | ✅ | luana-platform/Makefile + scripts/ci-parity.sh LANDED |
| T-13 /pm SSoT story folder mirrored | ✅ | 42/42 files at luana-platform/docs/product/stories/ |
| `/auditor` APPROVED verdict | ⏳ NOT YET RUN | Required before archive. Chris triggers /auditor Conv 3. |
| 24h soak elapsed | ⏳ PARTIAL | Sesion 9 commits 2026-05-15; current 2026-05-16. Calendar yes; functional soak (no regression reports) recommended +48h post-/auditor APPROVED. |
| `visionarias_logs` DB drop | ⏳ NOT EXECUTED | Per Q4=B pause — /pm drafts SQL; Chris executes when ready |

## Drop `visionarias_logs` DB prep (NOT EXECUTED — Chris-gated)

**Context:** `visionarias_logs` DB hosts production logs from AISALESHT-era deployments. Post-archive, this DB is dead weight.

**Recommended drop command (Chris executes when ready):**

```bash
# Verify DB not actively consumed
docker exec visionarias_postgres psql -U postgres -c "\l" | grep visionarias_logs
docker exec visionarias_postgres psql -U postgres -d visionarias_logs -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';"

# Backup snapshot (cheap insurance — ~50MB)
docker exec visionarias_postgres pg_dump -U postgres visionarias_logs > /tmp/visionarias_logs_final_$(date +%Y%m%d).sql.gz

# Drop (irreversible)
docker exec visionarias_postgres psql -U postgres -c "DROP DATABASE visionarias_logs;"
```

**NOT executed Sesion 10** — preserves Chris control over irreversible action.

## GitHub archive steps (Chris UI manual per Q4=B)

When Chris ready to archive AISALESHT (post-/auditor APPROVED + comfortable soak):

1. Navigate https://github.com/alpacapurpura/AISALESHT/settings
2. Scroll to "Danger Zone" section
3. Click "Archive this repository"
4. Confirm modal with repo name `alpacapurpura/AISALESHT`
5. Repository becomes read-only — no new pushes, issues, PRs accepted

**Effects of archive:**
- All git history preserved (read-only access to existing commits)
- Issues + PRs frozen (no new ones, existing remain visible)
- GH Actions disabled (no new workflow runs)
- Repository badge shows "archived"
- `deploy-prod.yml` workflow disabled (production deployment surface dies — must migrate to luana-platform-based deploy first)
- Cloudflare Tunnel container reading AISALESHT-relative paths breaks (must migrate config first)

**WARNING:** Production deployment surface dies on archive. T-9 documented architectural plan "each brand own deploy" — actual deployment migration is future per-brand extraction story. Until then, archive must be paired with manual deployment continuity plan (Chris may keep AISALESHT un-archived until brand-extraction story completes).

## Recommended Chris workflow

**Option A — Archive immediately after /auditor APPROVED:**
- Drop `visionarias_logs` DB
- Execute T-19 (AISALESHT story folder delete + luana-platform archive)
- Click GH Settings archive button
- Risk: production deployment surface unavailable until brand-extraction story closes
- Suitable if: Chris has migration to brand-repo ready OR is fine with brief production cutover gap

**Option B — Defer archive until brand-extraction:**
- /auditor APPROVED Story 10 (state transitions reviewing → done) BUT don't archive yet
- Execute T-19 (story folder delete + archive at luana-platform level — story is "done" SSoT)
- Keep AISALESHT un-archived until brand-extraction story creates `nicolify-brand-repo`
- Then archive AISALESHT after deployment fully migrated to brand-repo
- Risk: extended dual-state (months) — slight maintenance overhead
- Suitable if: Chris wants smooth production continuity

**Recommendation (R):** Option B — defer archive to brand-extraction. Production continuity > rapid cleanup. Story 10 conceptually closes at /auditor APPROVED + T-19 merge; physical archive is operational cutover.

## What T-14 Sesion 10 DOES NOT do

1. ❌ NO `gh api repos/alpacapurpura/AISALESHT --archive` execution (Chris-gated)
2. ❌ NO `DROP DATABASE visionarias_logs` execution (Chris-gated)
3. ❌ NO Cloudflare Tunnel config migration (deferred to brand-extraction story)
4. ❌ NO production deployment workflow migration (deferred per T-9 architectural plan)
5. ❌ NO Story 10 archive at luana-platform (depends_on T-19 post-/auditor APPROVED)
6. ❌ NO 07-merge.md authoring (defer to T-19 post-/auditor APPROVED)

## Acceptance grid

| Acceptance (per T-14 spec) | Status | Evidence |
|---|---|---|
| **A1** AISALESHT archive prep documented | ✅ COMPLETE | This document |
| **A2** visionarias_logs DB drop SQL prep | ✅ DOCUMENTED, NOT EXECUTED | SQL + backup commands ready |
| **A3** Story 10 archive at luana-platform | ⏳ DEFERRED → T-19 |
| **A4** `gh api archive` executed | ⏳ AWAITING CHRIS UI |
| **A5** Final 07-merge.md signed | ⏳ DEFERRED → T-19 |

## Files modified

### AISALESHT (development)
- `docs/product/stories/luana-nicolify-migration/T-14-impl-log.md` — NEW (this file)
- `docs/product/stories/luana-nicolify-migration/06-tickets.yaml` — T-14 state update (in commit)

## Cost estimate

| Operation | Tokens (est) | Cost USD (est) |
|---|---|---|
| /pm Opus inline checklist + prep + impl-log | ~6k | ~$0.40 |
| **T-14 total** | ~6k | **~$0.40** |

Way under $100-200 original estimate (no archive execution — only documentation + pause).

## Verdict

`awaiting_chris` — All pre-archive verification + prep documentation LANDED. Drop `visionarias_logs` SQL + GH Settings archive steps ready for Chris execution post-/auditor APPROVED + comfortable soak verification.

**T-19 (story folder delete + archive at luana-platform) blocked on /auditor APPROVED. Sesion 10 Story 10 closure: state developing remains until /auditor Conv 3.**

## Cross-reference

- Q4 ratification: Sesion 10 Chris answer (Option B Chris UI manual)
- /pm Conv 3 protocol: `.claude/skills/pm/SKILL.md` § Capability promotion (al merge)
- Predecessor: T-13 (rsync done, delete deferred)
- Follow-up: T-19 (post-/auditor APPROVED)
- Architectural plan: T-9-impl-log.md § "each brand own deploy"

Last line: `awaiting_chris -> docs/product/stories/luana-nicolify-migration/T-14-impl-log.md`
