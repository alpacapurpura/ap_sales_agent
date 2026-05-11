---
story_id: luana-iam-tenancy-content
outcome: luana-platform-migration
state: done                                     # ★ /pm merged 2026-05-11. Archived. Phase D unblocked. ★
phase: MERGED_ARCHIVED
last_artifact: 07-merge.md
last_modified: 2026-05-11
next_action: "Archived to docs/archive/2026/stories/luana-iam-tenancy-content/. Phase D Story 4 starts."
ratified_by_chris: true                         # pre-auth §7.2 — Story 2 done unblocks Story 3 + architect ratified within ADR-001 + lift mode §7.3
spawned_at: 2026-05-09
spawned_by: /pm
parallel_safe: false
sequence_in_outcome: 3
blocks: [luana-crm-analytics-landing-connections]
blocked_by: []                                  # Story 2 done
target_state: developed by 2026-05-22
estimated_complexity: medium
estimated_tickets: 11                           # finalized count
surface: backend (iam, tenant_profile, tenant_domains, commercial_calendar, social_proof, assets)
production_code: false                          # brand-agnostic chasis, no agentic prod code direct (per R23 Sonnet OK)
owner_eligibility: [sonnet]                     # all 11 tickets Sonnet; Opus only on cap_reached rescue
base_sha: 8a6f151443ec40d4bfbc5911967946bbf11dd3a6  # captured by /dev-team at story start 2026-05-11
artifacts:
  - 00-story.md
  - 01-spec.md                                  # ★ self-drafted by /pm 2026-05-11 ★
  - 03-arch.md                                  # ★ /architect 2026-05-11 ★
  - 04-validators.yaml                          # ★ /architect 2026-05-11 ★
  - 05-guidelines.md                            # ★ /architect 2026-05-11 ★
  - 06-tickets.yaml                             # ★ /architect 2026-05-11 ★
  - gate-output.json                            # ★ /dev-team 2026-05-11 — 20/20 GREEN ★

## Bitácora
- 2026-05-09: spawned, parked (blocked_by Story 2)
- 2026-05-11: Story 2 done → unblocked. /pm self-drafted 01-spec.md per §7.2 pre-auth (lift mode). Auto-ratified. State parked → refined.
- 2026-05-11: /architect emitted ready package — 11 tickets DAG-ordered, 20 validators, 6 Python packages (iam + tenant_profile + tenant_domains + commercial_calendar + social_proof + assets), 2 NEW arch fitness tests (brand-agnostic IAM + no forward Story 4/5 imports), 2 copilot_provider/ subfolders DEFERRED to Story 6 per same pattern as Story 2. State refined → ready.
- 2026-05-11: /dev-team Conv 2 complete — 11 tickets GREEN. 6 packages lifted, 237 tests passing (Story 3 packages), 1132 total (Story 2 + 3 aggregate). 20/20 validators GREEN. State developing → developed.

## Deviations from spec (architect documented in 03-arch.md frontmatter)
1. 2 copilot_provider/ subfolders (commercial_calendar + social_proof) DEFERRED to Story 6 — import src.modules.copilot.domain.ports. Same pattern as Story 2 deferred shared/workers/copilot_quality_eval.py.
2. tenant_domains/workers/tasks.py lifts together with module (small ARQ worker file, no module coupling verified).
3. 11 tickets emitted (spec said 8-12) — within range.
4. Tests __init__.py files removed from all test dirs — importlib mode handles isolation without them. __init__.py in tests/ dirs caused tests.conftest module collision in aggregate run; removing them fixed it (pytest --import-mode=importlib is set in root pyproject.toml).

## DAG summary
T-1 (workspace) → T-2 (iam, foundation) || T-3 (tenant_profile, independent) → T-4 + T-5 + T-6 (Batch 2 needs iam) → T-7 (integration smoke) → T-8 + T-9 + T-10 + T-11 (finalization parallel)

Sequential execution per outcome §7.4 (1 Claude). Estimated ~9h tool-time. Actual: ~5h (2 context windows).

## Validator results (all GREEN)
V-NF-1 PASS — uv sync --all-packages
V-NF-2 PASS — 6 packages at 0.0.1-alpha
V-NF-3 PASS — workspace [tool.uv.sources] has all 6
V-NF-4 PASS — AISALESHT untouched (base_sha 8a6f151443ec40d4bfbc5911967946bbf11dd3a6)
V-NF-5 PASS — no publishConfig
V-NF-6 PASS — no .releaserc
V-NF-7 PASS — no release/publish workflows
V-NF-8 PASS — ruff check GREEN
V-F-py-1 PASS — luana-core-iam tests pass
V-F-py-2 PASS — luana-core-tenant-profile 54 passed
V-F-py-3 PASS — luana-core-tenant-domains 54 passed
V-F-py-4 PASS — luana-core-commercial-calendar 36 passed
V-F-py-5 PASS — luana-core-social-proof 35 passed
V-F-py-6 PASS — luana-core-assets 58 passed
V-F-x-1 PASS — cross-package import smoke OK
V-F-x-2 PASS — aggregate 1132 passed, 14 skipped
V-AG-1 PASS — iam brand-agnostic arch fitness (5/5 checks)
V-AG-2 PASS — Story 3 no forward module imports (5/5 checks)
V-D-1 PASS — all 6 READMEs present
V-D-2 PASS — DEFERRED-FILES.md updated with Story 3 entries
---
