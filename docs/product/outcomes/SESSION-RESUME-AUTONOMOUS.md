<!-- voseo-allowed: internal pm session resume doc -->
# SESSION-RESUME — Luana migration autonomous batch (1 conversation runway)

> **Read this FIRST when bootstrapping a new conversation to execute the autonomous batch.**
> Created 2026-05-11 by /pm Opus 4.7. Chris ratificó autonomous policies (outcome §7.2-§7.4).
> Scope: Stories 1-4 of outcome luana-platform-migration in ONE conversation.

## 1. What this session does (start-to-finish autonomous)

| Story | Phase | Modelo | Costo aprox | Tool-time |
|---|---|---|---|---|
| 1 luana-foundation | /dev-team build (T-1..T-7) → /auditor → /pm merge | Sonnet (build) + Opus (auditor) | ~$30-100 | ~6-7h |
| 2 luana-shared-lift | /pm refine (auto-spec) → /architect ready package → /dev-team build → /auditor → /pm merge | Sonnet + Opus puntual | ~$200-500 | ~8-12h |
| 3 luana-iam-tenancy-content | idem Story 2 | Sonnet + Opus puntual | ~$200-500 | ~8-12h |
| 4 luana-crm-analytics-landing-connections | idem Story 2 | Sonnet + Opus puntual | ~$200-500 | ~8-12h |
| **Total** | 4 stories closed | mixed | **~$700-1600** | **~30h tool-time wall** |

## 2. Pre-authorizations Chris ratificó 2026-05-11 (DO NOT re-ask)

Per outcome §7.2:

| Policy | Valor |
|---|---|
| Spec/design ratification Stories 2-4 | AUTO if stays within ADR-001 + lift mode §7.3 |
| Audit failure response | Auto-fix Opus cap 3 iter, después escalar |
| Sonnet cap_reached | Auto-rescate Opus puntual SOLO ese ticket |
| Budget per session | NO HARD CAP. Soft check-ins $500/$1000/$1500 cumulative (report + continue, no stop) |

## 3. Lift mode constraint (Stories 2-4) — escalate if violated

Per outcome §7.3:

**MUST DO:** lift verbatim, preserve boundaries DDD + names + APIs + tests, add per-package pyproject/package.json (0.0.1-alpha), update import paths only.

**MUST NOT DO:** scope expansion, refactor boundaries, rename modules, change tech stack, new patterns, schema migration changes, cross-brand decisions.

**Halt criteria (auto-stop + escalate Chris):**
1. Scope expansion needed (mechanical lift impossible)
2. Cross-brand architecture decision discovered
3. New tech stack decision required
4. Auditor REJECTED + 3 auto-fix Opus iter fail
5. Cascade fail: Sonnet cap_reached → Opus rescue fail
6. Cumulative cost > $1500 → soft check-in (continue + report)

## 4. Bootstrap commands (next conversation Step 1)

```bash
# Single-read bootstrap
git status --short && git branch --show-current && git log --oneline -3
cat docs/product/BACKLOG-TLDR.md
cat docs/product/outcomes/luana-platform-migration.md  # full ADR + scope + policies
cat docs/product/outcomes/SESSION-RESUME-AUTONOMOUS.md  # this file
cat docs/product/stories/luana-foundation/checkpoint.md
cat docs/product/stories/luana-foundation/06-tickets.yaml
```

Verify gh auth still active:

```bash
gh auth status
gh api /repos/alpacapurpura/luana-platform --jq '.permissions'
```

If gh auth lapsed → re-run `gh auth refresh -h github.com -s repo,workflow,admin:org` and continue.

## 5. Execution sequence

### Phase A — Story 1 luana-foundation (autonomous build)

```
1. /pm transition state ready → developing
2. Spawn /dev-team for Story 1 (Sonnet, no R23)
   - T-1 clone monorepo + branch protection + CODEOWNERS + PR template + ADR folder
   - T-2 monorepo skeleton
   - T-3 CI workflow
   - T-4 lift .claude-shared from AISALESHT
   - T-5 subfolders core/ + 4 brand placeholders
   - T-6 docs seed
   - T-7 arch fitness tests
3. On all tickets GREEN → /pm transition developing → developed
4. Spawn /auditor (auditor-agentic if .claude-shared touched, else auditor-backend for infra)
5. On APPROVED → /pm merge → state developed → reviewing → done
6. Archive story → docs/archive/2026/stories/luana-foundation/
7. Regen BACKLOG
```

Estimated: ~6-7h tool-time, ~$30-100.

### Phase B — Story 2 luana-shared-lift (autonomous lift mode)

```
1. /pm refine: state parked → refining
2. Self-draft 01-spec.md per lift mode constraint (lift shared/ to luana-core/python/luana-core-shared-{name}/)
   - 10 packages: observability, billing, compliance, idempotency, llm, events, channels, extraction, platform, ui-kit-base
3. Self-ratify (per pre-auth § 7.2) — write ratified_by_chris: true (auto)
4. Spawn /architect orchestrator → ready package (03-arch + 04-validators + 05-guidelines + 06-tickets)
5. /pm transition refined → ready
6. Spawn /dev-team (Sonnet, lift code mechanical)
7. On GREEN → /auditor → /pm merge → done
```

Estimated: ~8-12h tool-time, ~$200-500.

**HALT CHECK before Phase B:** if Story 1 audit found CHANGES_REQUESTED non-trivial AFTER 3 Opus iter → STOP autonomous batch. Phase B onwards deferred.

### Phase C, D — Stories 3, 4 (idem Phase B)

Same flow. Each story ~$200-500, ~8-12h.

## 6. Soft check-in protocol

At each cumulative cost threshold, write a brief status report (no Chris pause):

| Threshold | Action |
|---|---|
| $500 cumulative | Report progress + cost breakdown + estimated remaining. Continue. |
| $1000 cumulative | Report idem. Continue. |
| $1500 cumulative | Report idem + flag if approaching halt criteria. Continue. |
| $2000 cumulative | Hard pause + escalate Chris ("we're past expected window, want to continue?"). |

Reports written to `docs/product/outcomes/luana-platform-migration-session-1-progress.md` (append-only).

## 7. Final report (end of session)

Write `docs/product/outcomes/luana-platform-migration-session-1-summary.md` with:

- Stories closed (1, 2, 3, 4 — or partial)
- Capabilities promoted (luana-core/* new caps)
- Total cost
- Total tool-time
- Halt reason if stopped early
- Next session recommendation (Story 5 next? other stories?)

## 8. What needs Chris in NEXT session (after this batch)

- Stories 5-7 (brand-offer-studios + copilot-engine + sales-agent-engine) — design decisions per story, R23 Opus, Chris check-in mid-flight per story
- Stories 8-14 (extension SDK + brand bootstraps) — vertical decisions per story, ratificación obligatoria

## 9. Anti-patterns prohibited (autonomous mode)

- ❌ Skip /architect ready package (architect orchestrator MANDATORY before /dev-team)
- ❌ Spawn /dev-team without checkpoint state=ready
- ❌ Promote capability YAML without /auditor APPROVED
- ❌ Archive story before /pm merge applied (07-merge.md must exist)
- ❌ Skip pre-commit hook (NEVER --no-verify)
- ❌ Skip downstream regression scope check per .claude/rules/auditor-downstream-regression.md
- ❌ Mix git mv with scope expansion in same commit (R9 — split into 2 commits)
- ❌ Make architectural decisions outside lift mode constraint without escalating
