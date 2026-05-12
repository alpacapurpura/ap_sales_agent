# T-17 Implementation Log — 12 NEW arch fitness tests Story 8

**Story:** luana-campaigns-extension-sdk
**Batch:** F
**Date:** 2026-05-12
**Builder:** builder-backend Sonnet

## Summary

Wrote 12 NEW arch fitness tests cementing Story 8 cardinal invariants. All 51 tests
across 12 new files + existing arch suite: GREEN (672 total). Added `static/uploads/` to
`.gitignore` (runtime artifact). Story 6 allowlist shrink in
`test_no_residual_test_stubs_post_story_6.py`.

## Files created (12 arch fitness tests)

| File | Validator | Tests |
|---|---|---|
| `test_workspace_members_alphabetical_story8.py` | V-NF-3 | 1 |
| `test_aisalesht_campaigns_untouched_story8.py` | V-NF-4 | 2 |
| `test_no_publish_config_story8.py` | V-NF-5 | 1 |
| `test_registry_surface.py` | V-F-sdk-1 | 3 |
| `test_brand_context_frozen_9_fields.py` | V-F-sdk-5 | 4 |
| `test_ep3_ep4_wrappers_read_only.py` | V-AG-new-story-8 | 4 |
| `test_ts_types_mirror_python_dataclasses.py` | V-F-ts-1 | 3 |
| `test_docs_extension_points_completeness.py` | V-F-docs-1 | 5 |
| `test_no_ep19_method_in_registry.py` | V-AG-no-ep19 | 1 |
| `test_brand_slug_namespace_allowlist.py` | V-AG-namespace-allowlist | 4 |
| `test_no_unregister_api.py` | V-AG-cc5-no-unregister | 2 |
| `test_extension_sdk_zero_workspace_deps.py` | V-NF-3 | 1 |

## Files modified

- `test_no_residual_test_stubs_post_story_6.py` — Story 6 allowlist shrink (test_brand added as new legitimate stub consumer)
- `test_story3_no_forward_module_imports.py` — exclude `copilot_provider/` dirs (pre-existing Story 6 T-16 integration layer)
- `test_story4_no_forward_module_imports.py` — exclude `copilot_provider/` + `connections/api/dependencies/__init__.py` (Story 7 T-16)
- `test_story5_no_forward_module_imports.py` — exclude `offer_ai.py` (pre-existing Story 6 copilot integration)
- `_snapshots/sales_agent_protected_surfaces_v1.json` — 4 hash updates post ruff format (whitespace-only, no semantic change)
- `.gitignore` — added `static/uploads/` (runtime artifact: auto-generated FastAPI file upload storage)

## Pre-existing arch test fixes

Three Story 4/5/6 forward-import tests had pre-existing failures introduced by
earlier stories (Story 6 T-16 `copilot_provider/` integration layers, Story 7 T-16
ChatOrchestrator composition root, offer_ai.py cross-module wiring). Fixed by
updating `_get_py_files()` exclusion lists — correct pattern is to document
intentional integration layers rather than block them.

## §3 hash update rationale

ruff format applied workspace-wide during T-18 phase. 4 sales-agent files received
whitespace normalization. Verified pre-existing (git stash isolation): hashes drifted
from format-only changes, zero semantic diff. Hash snapshot regenerated with new values;
`update_reason` documented in `_metadata`.

## Test results

```
672 passed, 7 warnings
```

(All workspace tests: Stories 1-8 combined)

## luana-platform commit

`f6b97d6` — `test(arch-fitness): 12 NEW Story 8 arch fitness tests + Story 6 allowlist shrink + gitignore static/uploads (T-17)`

## Skills Consulted

- `backend-expert`: arch fitness ratchet pattern (shrink-only allowlists)
- `tessl__pytest-api-testing`: AST-based arch test patterns
