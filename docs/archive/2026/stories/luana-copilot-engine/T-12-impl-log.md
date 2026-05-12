---
story_id: luana-copilot-engine
ticket: T-12
phase: completed
last_modified: 2026-05-11
---

# T-12 impl-log — Lift copilot application/services + discovery + extraction_card_flow

## Surface

- **Source AISALESHT:** `backend/src/modules/copilot/application/services/` (10 files) + `application/discovery.py` + `application/extraction_card_flow.py`
- **Target luana-platform:** `core/luana-core-copilot/src/luana_core_copilot/application/`

## Steps executed

1. `cp -r` services dir (10 files + handlers/) + discovery.py + extraction_card_flow.py
2. Removed `__pycache__` artifacts
3. Applied §1.3 sed mapping verbatim on src + tests
4. Manually fixed string-literal `unittest.mock.patch` drift (continued from Batch 2/3 — process drift documented Batch 2)
5. Copied 5 AISALESHT tests where they existed: test_contextual_chunker, test_discovery, test_document_processor, test_limits_resolver, test_offer_psychology_service
6. Added new dep `langchain-text-splitters>=0.3` to pyproject.toml (T-12 surfaces use it)
7. Copied minimal env-var conftest (DAG-defer to T-15 but T-12 tests need env vars pre-import)
8. Verified `uv sync --all-packages` GREEN, ran isolated tests

## Results

- 25/27 tests PASS isolated (~92.6%)
- 2 tests deferred to downstream tickets (NOT failures intrinsic to T-12 lift integrity):
  - `test_discovery.py::test_picks_up_in_repo_providers` — discovery semantic depends on AISALESHT `src.modules.*` package layout; will work post-T-16 unlift OR requires discovery refactor for luana-platform paradigm (likely needs scope ticket — flagged for architect)
  - `test_offer_psychology_prompt_resolves_from_copilot_templates` — depends on `luana_core_platform.PromptLoader` default templates_dir hardcoded to `"src/modules/copilot/infrastructure/prompts/templates"` (Story 2 drift). Templates exist in luana_core_copilot but loader default wasn't updated during Story 2 lift.

## Process drifts (documented for /pm + architect)

### Drift 1: §1.3 missing string-literal `patch()` sed rule (recurrent — 4th time now)

Test files contain `patch("src.modules.copilot.X.Y.Z")` literal strings that the 5 sed rules don't catch. Pattern documented Batch 2 (T-7/T-8), Batch 3 (T-9/T-10/T-11), and now T-12. Solution: append `patch\("src\.modules\.copilot\.|patch\("src\.shared\.` sed rules to §1.3 canonical mapping.

### Drift 2: T-15 conftest DAG-defer requires earlier landing for env-var-dependent tests

The luana_core_platform `Settings` class enforces 11 mandatory env vars at module-load time. Tests can't proceed without these. Per the T-15 spec, conftest lift happens last, but practice shows tests across T-7..T-15 batches need env vars pre-import.

Mitigation: minimal env-var conftest copied from `core/luana-core-llm/tests/conftest.py` placed at T-12 time. T-15 will overwrite with full AISALESHT conftest verbatim.

### Drift 3: `_CONVENTION_PACKAGE = "src.modules"` discovery hardcode

`luana_core_copilot.application.discovery._CONVENTION_PACKAGE = "src.modules"` reflects AISALESHT package layout. In luana-platform paradigm, copilot providers live in separate workspace packages (`luana_core_brand_studio.copilot_provider`, etc. after T-16 unlift). Discovery semantics need refactor for luana-platform — likely T-16 territory or a new follow-up ticket.

**Decision:** Lift verbatim (preserve AISALESHT behavior). Surface as known issue for /architect ratification.

### Drift 4: `luana_core_platform.PromptLoader` default templates_dir wrong post-Story-2-lift

`PromptLoader.__init__(templates_dir="src/modules/copilot/infrastructure/prompts/templates")` is a Story 2 drift. Templates live at `core/luana-core-copilot/src/luana_core_copilot/infrastructure/prompts/templates/` in luana-platform. Either:
- (A) update default to walk parent packages or use a resolver
- (B) consumers (services) pass `templates_dir=` explicitly
- (C) accept the drift and treat as a future fix

**Decision:** Out-of-scope for T-12 (touches luana_core_platform). Flag for /architect.

## Commit

Stage:
```
git add core/luana-core-copilot/src/luana_core_copilot/application/services
git add core/luana-core-copilot/src/luana_core_copilot/application/discovery.py
git add core/luana-core-copilot/src/luana_core_copilot/application/extraction_card_flow.py
git add core/luana-core-copilot/tests/test_contextual_chunker.py
git add core/luana-core-copilot/tests/test_discovery.py
git add core/luana-core-copilot/tests/test_document_processor.py
git add core/luana-core-copilot/tests/test_limits_resolver.py
git add core/luana-core-copilot/tests/test_offer_psychology_service.py
git add core/luana-core-copilot/tests/conftest.py
git add core/luana-core-copilot/pyproject.toml
```

Conventional commit `feat(luana-core-copilot): lift application/services + discovery + extraction_card_flow (T-12)`.

## Next

T-13 — observability subfolder D-T6 subclass invariants (callback_handler, turn_envelope, persistence repos).
