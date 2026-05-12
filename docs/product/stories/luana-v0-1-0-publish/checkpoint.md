---
story_id: luana-v0-1-0-publish
outcome: luana-platform-migration
state: developed
phase: STORY_DEVELOPED_AWAITING_AUDIT
last_artifact: T-5-impl-log.md
last_modified: 2026-05-12
next_action: "Build phase done (tests-passing). Awaiting orchestrator → auditor-backend (independent verdict). luana-platform commits on main. AISALESHT impl-logs committed to development."
ratified_by_chris: true                        # ★ Session 4 pre-auth — outcome §7.5.2 D7=B + §7.1 scope decisions ★
spawned_at: 2026-05-09
spawned_by: /pm
parallel_safe: false
sequence_in_outcome: 9
blocks: [luana-nicolify-migration]
blocked_by: [luana-campaigns-extension-sdk]
target_state: developed by 2026-05-13           # session 4 secuencial autonomous
estimated_complexity: low                       # lift-mode-equivalent — decisions §7.1 pre-ratified
estimated_tickets: 5                            # architect ratified: 5 tickets
surface: release engineering (cross-package — GH Packages publish pipeline)
production_code: false                          # pure CI/CD + release infra. R23 NOT triggered. Sonnet eligible.
owner_eligibility: [opus, sonnet]
session: 4
session_pre_auth: stories_8_plus_9_sequential_autonomous

binding_decisions:                              # outcome §7.1 + §7.5.2 D7 + architect §0 cement table
  license: proprietary                          # §7.1 ratified 2026-05-10
  gh_packages_strategy: introduce_publish_pipeline  # §7.1 ratified 2026-05-10 (Story 9 IS the implementation)
  repo_topology: monorepo                       # §7.1 ratified 2026-05-10
  versioning: real_semver_flip                  # §7.5.2 D4=C
  publish_target: v0.1.0                        # ★ spec resolution: NO -alpha suffix per 00-story production-grade alpha semantic ★
  release_tool: release-please                  # architect §0 #4 — monorepo Python+TS native
  python_api_docs: pdoc-14                      # architect §0 #1 — simpler than sphinx
  ts_api_docs: typedoc-0-27                     # architect §0 #2 — de facto
  changelog_format: keep-a-changelog            # architect §0 #3 — manual seed v0.1.0 + auto v0.2.0+
  github_pages_deploy: false                    # architect §0 #5 — emit artifacts, no Pages deploy Story 9
  brand_stubs_bump: yes                         # architect §0 #6 — workspace coherence
  first_tag_procedure: manual                   # architect §0 #7 — git tag v0.1.0 manual override
  pre_existing_failures_policy: defer_story_10  # architect §0 — 40 sales-agent pre-existing → Story 10+ cleanup

architect_cement:
  total_tickets: 5
  total_validators: 23
  opus_required_tickets: 0                      # All Sonnet eligible (production_code=false)
  sonnet_eligible_tickets: 5
  cardinal_invariants_count: 15                 # V-NF-* (6) + V-F-release-* (8) + V-AG-* (5) + V-D-* (5) + V-X (1) — overlap-deduplicated to 15 distinct cardinal cement items
  knowledge_cutoff_disclosure: |
    Opus 4.7 cutoff Jan 2026. release-please, pdoc, typedoc, uv all verified
    via canonical docs accessed 2026-05-12. No post-cutoff drift.

halt_criteria_session_4:                        # specific Story 9 halt risks
  - "GH Packages org-level config requires Chris token/billing setup (escalate, NOT autonomous)"
  - "release-please config conflicts pre-existing pyproject/package.json — fallback to changesets+custom Python script"
  - "Tests downstream R3 breakage post first publish (auto-fix cap 2 iter, then escalate)"
  - "uv.lock regen fails post-bump (try fallback --resolution=lowest then --resolution=highest)"
  - "Cumulative session 4 cost crosses $5000 → soft check-in"
---

## Bitácora

- 2026-05-09: spawned by /pm, state=parked (blocked_by Story 8)
- 2026-05-12: Session 4 pre-auth — outcome §7.5.2 D7=B + §7.1 scope decisions pre-ratified. Story 9 will pick up secuencial autonomous post Story 8 done.
- 2026-05-12: /po Opus drafted 01-spec.md (586 lines, 10 Gherkin scenarios, 15 out-of-scope, NFRs, edge cases, SemVer F1-F6 cement, 5 risks). State refined.
- 2026-05-12: architect-orchestrator Opus emitted ready package — 03-arch.md (778 lines, consolidated architecture) + 03-arch-be.md (271 lines, BE/CI detail) + 04-validators.yaml (290 lines, 23 validators) + 05-guidelines.md (335 lines, build patterns) + 06-tickets.yaml (690 lines, 5 tickets DAG). State refined → ready.

## Architect cement summary

**Phase 0 resolved open questions (NO Chris escalation):**

1. Python API docs: **pdoc 14+** (simpler vs sphinx)
2. TS API docs: **typedoc 0.27+** (de facto)
3. CHANGELOG format: **Keep-a-Changelog** (manual v0.1.0 seed + release-please auto v0.2.0+)
4. Release tool: **release-please 16+** (monorepo Python+TS native). Fallback: changesets+custom Python.
5. GitHub Pages: **NO Story 9 deploy** (emit artifacts only — Stories 14+ marketing scope)
6. Brand stubs version: **Bump to 0.1.0** (workspace coherence)
7. First-tag procedure: **Manual `git tag v0.1.0`** (release-please takes over v0.2.0+)
8. Build parallelization: **Single sequential job per language** (33 pkgs × ~10-20s = ~5-10min, well below 6h cap)

**Spec resolution:**
- Publish target: **`v0.1.0`** (NO `-alpha` suffix per 00-story.md "production-grade alpha" semantic). Overrides earlier checkpoint `publish_target: v0.1.0-alpha`.
- Pre-existing 40 sales-agent failures: **DEFER to Story 10+ cleanup** (Story 9 = release infra, not test cleanup).

**Cardinal invariants (15 cement items distributed across V-NF/V-F/V-AG/V-D/V-X):**
1. V-NF-1 AISALESHT untouched (V-NF-4 cumulative 9 stories)
2. V-NF-2/3 all 33 packages at 0.1.0 (26 Python + 7 TS)
3. V-NF-7 NO -alpha suffix retained
4. V-NF-4/5/6 test-brand + workspace roots + brand stubs coherence
5. V-F-release-1 release-please-config valid (33 packages enumerated)
6. V-F-release-2/3/4 release.yml YAML valid + tag-triggered + atomic
7. V-F-release-5 CHANGELOG.md with cross-Story summary
8. V-F-release-6 migration guide §1-§6
9. V-F-release-7 docs/api/ auto-gen present
10. V-F-release-8 lockfiles consistent
11. V-AG-1/2 apps/test-brand smoke + downstream regression zero NEW failures
12. V-AG-3/4 EP-3 ToolRegistry + EP-4 WorkflowRegistry byte-stable (Stories 6+7 frozen cement)
13. V-AG-5 5 critical EPs callable from registry
14. V-D-1..D-5 docs deliverables complete
15. V-X-1 GH Packages auth halt criterion documented

**No Opus mandatory tickets. R23 NOT triggered (production_code=false confirmed).** All 5 tickets Sonnet eligible. If Sonnet hits cap_reached → Opus rescue ONLY that ticket.
