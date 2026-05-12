<!-- voseo-allowed: merge doc cites voseo strings verbatim from auditor REVIEW per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
---
story_id: luana-campaigns-extension-sdk
outcome: luana-platform-migration
merge_date: 2026-05-12
merged_by: /pm (claude-opus-4-7)
auditor_verdict: APPROVED (26/26 validators PASS, 0 non-trivial findings, 3 trivial PRE-EXISTING Stories 6/7 carry-over)
auditor: auditor-backend Opus 4.7
final_state: done
---

# Merge — luana-campaigns-extension-sdk

## Resumen

Story 8 cierra DONE. 18 luana-platform commits + 0 audit-fix commits + AISALESHT closure commits (impl-logs T-1..T-18 + R3 SSoT + anti-duplication inventory + checkpoint transitions + REVIEW + merge doc).

auditor-backend Opus APPROVED first iter (no auto-fix needed). 3 findings all trivial PRE-EXISTING from Stories 6/7 lift (sales-agent 40 failures + 1 collection error verified PRE-EXISTING via `git checkout 147c61d` repro — zero new failures introduced by Story 8).

Story 8 = (A) `modules/campaigns/` lifted intact to `luana-core-campaigns` v0.0.8-alpha + (B) Formal Extension SDK cemented (`luana-core-extension-sdk` Python + `@luana/extension-sdk` TypeScript) — 18 EPs + 5 CC policies + BrandContext frozen 9-field + 3 exception types + `_adapters.py` READ-ONLY for Stories 6+7 frozen registries byte-stable + (C) `apps/test-brand/` smoke pack 18 registrations + 10 smoke scenarios GREEN + (D) `docs/extension-points.md` §1-§5 complete with per-vertical examples + Vitalia treatment-agent recipe + cross-brand learning principle.

## Cardinal invariants live-verified

- **V-NF-1** AISALESHT `backend/src/modules/campaigns/` source untouched 18 tickets (V-NF-4 invariant 8 stories cement)
- **V-NF-2** luana-core-campaigns + luana-core-extension-sdk + apps/test-brand pyproject version `0.0.8-alpha`
- **V-NF-3** workspace pyproject + pnpm-workspace alphabetical order (26 Python + 7 TS post-Story-8)
- **V-AG-1** Story 7 ToolRegistry contract byte-stable (golden snapshot GREEN post-T-6)
- **V-AG-2** Story 6 5 registries (Tool + Workflow + Extractor + Module + Suggestion) contracts byte-stable (V-AG-3 Story 6 GREEN post-T-6)
- **V-AG-3** EP-2 offer_preset_pack integrates with Story 5 offer-studio PresetCatalog without modifying SSoT
- **V-AG-4** BrandContext frozen dataclass with 9 fields per §7.5.2 D3
- **V-AG-5** CC-4 namespace enforcement — `test_brand_slug_namespace_allowlist.py` GREEN
- **V-AG-6** CC-3 lock enforcement — runtime + AST forbid `_dispatch`/`_mutate`/`_internal_`/`_private_` prefix in adapters
- **V-AG-7** NO EP-19 `vertical_agent_register` — `test_no_ep19_method_in_registry.py` GREEN
- **V-AG-8** EP-6..EP-18 backlog stubs raise `NotImplementedError` when invoked semantically (not at registration)
- **D-T1** EP-3/EP-4 wrappers READ-ONLY delegation (Stories 6+7 frozen registries unchanged)
- **§7.5.4 NO EP-19 cement:** Vitalia treatment-agent recipe documented as APP-level composition pattern, NOT core EP
- **R23 cost-routing compliance:** T-5+T-6 Opus model documented in impl-logs (Stories 6+7 frozen registry wrappers); T-1..T-4 + T-7..T-18 Sonnet eligible (production_code=false per checkpoint)

## Commits aplicados

### Repo `alpacapurpura/luana-platform` (main, 18 commits range ae8cb96..3aeb795)

- T-1 ae8cb96 chore(workspace) register Story 8 luana-core-campaigns + luana-core-extension-sdk + apps/test-brand
- T-2 69c95af feat(luana-core-extension-sdk) skeleton + pyproject + README zero-dep contract layer
- T-3 6e01a7b feat(luana-core-extension-sdk) BrandContext frozen dataclass 9 fields (TDD GREEN 4 tests)
- T-4 ee0b15a feat(luana-core-extension-sdk) exceptions (3 types) + models (18 DataClasses) + protocols + TDD GREEN 14 tests
- T-5 5ece4cf feat(luana-core-extension-sdk) ★ R23 OPUS ★ ExtensionPointRegistry executable EP-1..EP-5 + CC-1..CC-5 runtime enforcement
- T-6 2e20def feat(luana-core-extension-sdk) ★ R23 OPUS ★ _adapters.py — EP-3+EP-4 read-only Stories 6+7 frozen registry wrappers
- T-7 665331a feat(luana-core-extension-sdk) EP-6..EP-18 backlog signature-only stubs raise NotImplementedError
- T-8 fbdc39c feat(@luana/extension-sdk) TS type mirror EP-6+EP-10+EP-18 (FE-mirror partial scope)
- T-9 9e3da61 feat(luana-core-campaigns) skeleton + pyproject + README v0.0.8-alpha
- T-10 1427017 feat(luana-core-campaigns) lift campaigns domain layer (12 src + 7 test files)
- T-11 8a422fd feat(luana-core-campaigns) lift campaigns infrastructure layer (29 files)
- T-12 ea48804 feat(luana-core-campaigns) lift campaigns application layer (21 files) + observability
- T-13 df722df feat(luana-core-campaigns) lift campaigns api + workers layers — 446 tests GREEN
- T-14 672215f feat(apps/test-brand) FastAPI lifespan + 18 register_all handlers (5 executable + 13 stubs)
- T-15 3df55df test(apps/test-brand) smoke pack 10 scenarios D1-D3 + C1-C5 + frozen ctx GREEN
- T-16 325209e docs(luana-platform) docs/extension-points.md §1-§5 + vertical-agent-recipe + per-vertical examples
- T-17 f6b97d6 test(arch-fitness) 12 NEW Story 8 arch fitness tests + Story 6 allowlist shrink + gitignore static/uploads
- T-18 3aeb795 chore(story-8) T-18 finalization — ruff lint+format 317 files + §3 hash update + DEFERRED-FILES + anti-duplication

### Repo AISALESHT (development)

- Multiple commits fa1f4b4c, e45de716, 3ce54fb1, 5c83fb8a, a14afe9e, f4a9f1a7, 6026e133, bc38cb01 — Story 8 ready package + 18 impl-logs + R3 SSoT update + anti-duplication inventory + checkpoint state transitions (parked → refining → refined → ready → developing → developed → reviewing → done)

## Validators outcome

- **26 validators total** per 04-validators.yaml
- **26/26 GREEN** at audit
- 0 waivers required
- 12 NEW arch fitness Story 8 GREEN: V-AG-1..V-AG-8 + 4 supplementary (BrandContext 9-field + namespace + no-EP-19 + no-unregister + registry surface + TS mirror + docs completeness + AISALESHT campaigns untouched + workspace alphabetical + no publish config + EP-3+EP-4 wrappers read-only + extension-sdk zero workspace deps)
- 12 NEW campaigns lift validators GREEN: 446 tests + import path rewrite verification + per-package coverage threshold preserved

## Downstream regression Stories 1-7

| Package | Tests GREEN | Status |
|---|---|---|
| luana-core-copilot | 1603 / 25 skipped | GREEN (Story 6 baseline preserved) |
| luana-core-sales-agent | 429/469 (40 PRE-EXISTING failures verified via `git checkout 147c61d` repro) | PRE-EXISTING — zero NEW failures |
| luana-core-brand-studio | 470 | GREEN |
| luana-core-offer-studio | 633 | GREEN |
| luana-core-observability | passes | GREEN |
| luana-core-shared | passes | GREEN |

Zero new regressions introduced by Story 8.

## Findings auditor

### Trivial PRE-EXISTING (Stories 6/7 carry-over — no Story 8 action required)

| ID | Cat | Origin | Action |
|---|---|---|---|
| PRE-1 | C4 | sales-agent 40 baseline failures (Story 4 luana-core-platform tech debt + T-7 templates_dir issue) | Documented Story 7 07-merge.md — addressed Story 9 or later cleanup |
| PRE-2 | C4 | sales-agent 1 collection error | Same Story 7 carry-over |
| PRE-3 | C5 | Aggregate workspace pytest conftest collision (V-F-x-2 type) | Pre-existing Story 4/5/6/7 — addressed Story 9 workspace cleanup |

### Strengths surfaced

1. **D-T1 byte-stable registry cement exemplary** — `_adapters.py` underscore-private pattern with AST-parse arch fitness forbidding `_dispatch`/`_mutate`/`_internal_`/`_private_` prefix. Stories 6+7 frozen registries golden snapshots GREEN post-Story-8 (read-only delegation discipline rigorously enforced).

2. **CC-1..CC-5 4-layer defense-in-depth** — runtime enforcement (lock + namespace + duplicate + immutable + mode flag) + AST arch fitness (12 NEW Story 8 tests) + integration smoke (apps/test-brand 10 scenarios) + documentation cement (docs/extension-points.md §1 verbatim).

3. **§7.5.4 NO EP-19 architectural discipline rigorous** — arch fitness `test_no_ep19_method_in_registry.py` enforces. Documentation cements pattern: vertical agents are brand APPs, NOT core EPs. Future Story 11.5+ Vitalia treatment-agent recipe documented as worked example.

4. **R26 hotfix-repro-mandatory exemplary** — auditor verified sales-agent 40 PRE-EXISTING failures via `git checkout 147c61d` repro (NOT introduced by Story 8). Diagnosis correction discipline prevents wrong-scope auto-fix waste.

5. **Cross-brand learning principle documented** — `docs/extension-points.md §5` cements "features graduate to core via /pm promotion path, never cross-namespace consumption" pattern (CC-4 namespace isolation enforces this architecturally).

## Capabilities promovidas

2 packages tracked at outcome level:
- `luana-core-campaigns` v0.0.8-alpha — Campaigns engine lifted intact (domain + infra + application + api + workers) + 446 tests GREEN
- `luana-core-extension-sdk` v0.0.8-alpha — Formal Extension SDK contract surface (18 EPs + 5 CC policies + BrandContext frozen 9-field + 3 exception types + `_adapters.py` Stories 6+7 frozen wrappers) + 92 tests GREEN + 12 NEW arch fitness GREEN

Plus 1 TS package mirror:
- `@luana/extension-sdk` v0.0.8-alpha — partial TS type mirror (EP-6 + EP-10 + EP-18 + BrandContext + 3 exceptions). FE-surface scope per architect §7.5.3.

Plus 1 smoke test pack:
- `apps/test-brand` v0.0.8-alpha — FastAPI lifespan smoke pack (18 register_all + 10 smoke scenarios GREEN).

Plus 1 documentation deliverable:
- `docs/extension-points.md` 1354 lines — §1 SDK overview + CC verbatim + §2 EP-1..EP-5 critical with per-vertical examples + §3 EP-6..EP-18 backlog signatures with per-vertical examples + §4 Vitalia treatment-agent recipe (NO EP-19 explicit) + §5 cross-brand learning principle.

Final outcome capabilities cumulative: **36** (5 Story 1 + 15 Story 2 + 6 Story 3 + 4 Story 4 + 2 Story 5 + 1 Story 6 + 1 Story 7 + 2 Story 8).

## DEFERRED files Story 8 (track DEFERRED-FILES.md luana-platform)

3 deferrals registered:
- **Story 9 (v0.1.0 publish):**
  - GH Packages publish pipeline (license proprietary + monorepo + real SemVer flip per outcome §7.1 + §7.5.2 D4=C)
  - semantic-release config
  - npm/PyPI publish workflows
- **Stories 11-13 (brand bootstraps):**
  - EP-6..EP-18 backlog implementations (signature-only Story 8, semantic deferred)
  - CF tunnel multi-domain dev setup per outcome §7.5.5
  - Vitalia + Comunify + Lupulo brand apps consume SDK via FastAPI lifespan
  - Vitalia treatment-agent worked recipe (Story 11.5+ actual agent code)
- **Allowlisted stubs (Stories 8+):**
  - AppointmentModel stub (scheduling territory — allowlisted for Story 8+ per outcome §7.3)
  - ProductModel stub (catalog territory — allowlisted for Story 8+)

## Cross-Story-9 handoff documented

- Outcome §7.1 scope ratified — license proprietary + monorepo + GH Packages publish pipeline deferred → Story 9 IS the implementation
- Outcome §7.5.2 D4=C — SDK versioning flip from strict alpha minor/patch → real SemVer enforcement at Story 9 publish
- Outcome §7.5.2 D7=B pre-auth — Stories 8+9 secuencial autonomous (cap §7.4 extended to 3 stories Tier 3)
- Story 9 checkpoint pre-ratified (state=parked, ratified_by_chris=true) per /pm session 4 Phase 0
- Halt criteria Story 9: GH Packages org-level config requires Chris token/billing setup → escalate

## Session 4 stats (Story 8 portion)

- Total spawns Story 8: 8 (1 /po Opus + 1 architect Opus + 5 builder-backend Sonnet batches + 1 builder-agentic Opus T-5+T-6 + 1 auditor-backend Opus)
- Builder pattern: Batch A T-1..T-4 Sonnet / Batch B T-5+T-6 Opus / Batch C T-7+T-8 Sonnet / Batch D T-9..T-13 Sonnet / Batch E T-14..T-16 Sonnet / Batch F T-17+T-18 Sonnet
- AISALESHT untouched verified post-merge (V-NF-1 cement 18 tickets + audit verified)
- R23 honored: T-5+T-6 Opus required + documented in impl-logs (Stories 6+7 frozen registry wrappers); T-1..T-4 + T-7..T-18 Sonnet eligible (production_code=false per checkpoint binding_decisions)
- Cumulative cost Session 4 Story 8: ~$2700-3000 Opus + Sonnet mixed (crossed $2500 soft check-in marker during build, continued autonomous per Chris pre-auth NO HARD CAP outcome §7.2)

## Próximo paso

- Outcome `luana-platform-migration` continúa state=developing
- **8/14 stories DONE** (Stories 1-8)
- Next story unblocked: `luana-v0-1-0-publish` (Story 9) — was blocked_by Story 8
- Session 4 continues secuencial autonomous per Chris mandate §7.5.2 D7=B
- Story 9 picks up: GH Packages publish pipeline + semantic-release + workflow `.releaserc` config + v0.1.0-alpha first publish
