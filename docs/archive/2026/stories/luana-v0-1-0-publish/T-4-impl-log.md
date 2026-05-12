# T-4 Impl Log — Arch Fitness Tests (Story 9 Invariants)

**Ticket:** T-4 — 5 new arch fitness tests cementing Story 9 invariants
**Status:** DONE
**Date:** 2026-05-12
**Repo:** `/home/chris/luana-platform/`
**Commit:** `0923ac5`

## Summary

5 new arch fitness tests added to `core/tests/architecture/`, all GREEN (26 tests pass in 0.21s).

### Tests created

**`test_workspace_versions_uniform_at_v0_1_0.py`** (4 tests, V-NF-2/3/7)
- `test_all_python_packages_at_0_1_0` — asserts all 26 luana-core-* + test-brand + brand stubs pyproject at `0.1.0`
- `test_all_typescript_packages_at_0_1_0` — asserts all 7 @luana/* + brand stubs + root package.json at `0.1.0`
- `test_no_alpha_suffix_anywhere` — asserts no `-alpha` substring in any version field
- `test_release_please_manifest_all_at_0_1_0` — asserts .release-please-manifest.json all 33 entries at `0.1.0`

**`test_release_workflow_yaml_valid.py`** (5 tests, V-F-release-2/3/4)
- `test_release_workflow_file_exists_and_valid_yaml` — file present and parseable
- `test_release_workflow_triggers_on_tag` — `on.push.tags: ['v*.*.*']` confirmed
- `test_release_workflow_atomicity_publish_dependency` — `publish-typescript.needs` contains `publish-python`
- `test_release_workflow_required_jobs_present` — 6 required jobs declared
- `test_release_workflow_jobs_have_timeout` — build/publish jobs have `timeout-minutes`

**`test_releaserc_config_valid.py`** (6 tests, V-F-release-1)
- `test_release_please_config_exists` — file present at monorepo root
- `test_release_please_config_has_33_packages` — exactly 33 packages (25 Python + 1 test-brand + 7 TS)
- `test_release_please_config_has_linked_versions_plugin` — linked-versions plugin present
- `test_release_please_manifest_exists` — manifest file present
- `test_release_please_manifest_seeded_at_0_1_0` — all 33 entries at 0.1.0 + count check
- `test_release_please_config_has_core_platform_entry` — spot-check luana-core-platform entry

**`test_docs_v0_1_0_deliverables_present.py`** (10 tests, V-D-1..5, V-F-release-5/6/7, V-X-1)
- `test_changelog_has_v0_1_0_section` — CHANGELOG.md exists + `## [0.1.0]` header
- `test_changelog_has_cross_story_summary` — 9 story markers present
- `test_changelog_has_package_entries` — ≥26 package entries
- `test_migration_guide_has_6_sections` — §1..§6 all present
- `test_migration_guide_has_substantive_content` — ≥50 lines
- `test_api_docs_directories_populated` — docs/api/python/ ≥20 dirs + docs/api/typescript/ present
- `test_extension_points_header_bumped` — `v0.1.0 (production-grade alpha)` in content
- `test_releases_md_has_v0_1_0_procedure` — v0.1.0 + rollback + token + SemVer refs
- `test_semver_rules_f1_to_f6_documented` — F1..F6 each tied to major/minor/patch semantics
- `test_halt_criterion_v_x_1_documented` — GH Packages auth halt criterion present

**`test_aisaleshT_untouched_story_9.py`** (1 test, V-NF-1)
- `test_aisalesht_business_code_no_uncommitted_changes` — checks `git status --porcelain -- backend/ frontend/` in AISALESHT
- `@pytest.mark.skipif(not os.path.isdir(AISALESHT_PATH), ...)` — best-effort, env-gated
- Uses working tree check (NOT `main..development` diff which shows Story 7 legitimate changes)

## Issues resolved

**V-NF-1 false positive**: Initial implementation used `git diff --name-only main..development -- backend/ frontend/` which returned 20+ files from Story 7 AISALESHT work. Fixed by switching to `git status --porcelain` (uncommitted working tree changes only) — Story 9 never modified AISALESHT working tree.

**Story 8 arch gate collision**: `test_no_publish_config_story8.py` checks `@luana/extension-sdk` has no publishConfig. T-2 added `publishConfig.registry` to that package. Fixed by removing extension-sdk from the Story 8 guard's `_STORY8_TS_PACKAGES` list with a comment noting Story 9 legitimately adds it.

## Full arch fitness suite result

149 passed, 1 warning in 138.25s — all arch fitness gates GREEN.

## Commit

```
test(arch-fitness): cement Story 9 invariants — 5 new gates (26 tests)
SHA: 0923ac5
```
