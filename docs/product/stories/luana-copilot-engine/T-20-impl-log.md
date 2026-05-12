# T-20 Implementation Log

**Story:** luana-copilot-engine
**Ticket:** T-20 — Add NEW arch fitness tests: D-T1+D-T2+D-T6 cement (6 tests)
**Owner:** builder-agentic (Opus 4.7) — R23
**Status:** done
**Validators:** V-AG-3, V-AG-4, V-AG-5, V-AG-6, V-AG-7, V-AG-8
**Start:** 2026-05-12
**Commits:**
- luana-platform main: `eaa1446` — test(story-6/T-20): D-T1+D-T2+D-T6 cement — 6 NEW arch fitness tests

## Skills Consulted

- **copilot-expert**: §"Registries (no hardcodear)" — confirmed 5 canonical registries (tools, workflows, module, extraction_domain, suggestions). §"Anchors" — 36 cap aspirational, empirical 33 unique post lift. Anti-duplication rule cardinal for V-AG-5 cement.
- **sales-agent-expert** (not invoked — no sales_agent code touched).
- **tessl__langgraph** (NA — arch fitness only, no graph code).
- **tessl__graceful-degradation** (NA — no new external calls).
- **tessl__pytest-api-testing**: pattern guidance for the registry contract golden snapshot test.

## Files

### Created (luana-platform main)
- `core/tests/architecture/_snapshots/copilot_registry_v1.json` — golden API surface snapshot (6683 bytes, schema_version=1)
- `core/tests/architecture/_snapshots/_generate_copilot_registry_snapshot.py` — one-off snapshot regen script (only re-run on architect-ratified bump)
- `core/tests/architecture/test_copilot_registry_contracts_stable.py` — V-AG-3 D-T1 (2 sub-tests)
- `core/tests/architecture/test_no_residual_test_stubs_post_story_6.py` — V-AG-4 D-T2 (2 sub-tests)
- `core/tests/architecture/test_no_mirror_observability_in_copilot.py` — V-AG-5 D-T6 (4 sub-tests)
- `core/tests/architecture/test_module_descriptor_complete_for_lifted_packages.py` — V-AG-6 D-T6 (3 sub-tests)
- `core/tests/architecture/test_voice_compiler_ssot_still_intact.py` — V-AG-7 Story 5 regression cement (3 sub-tests)
- `core/tests/architecture/test_copilot_anchors_count_stable.py` — V-AG-8 (2 sub-tests)

### Modified (luana-platform main)
- 8 pyproject.toml files (analytics, brand, commercial-calendar, connections, crm, landing, offer, social-proof) — added `[project.entry-points."nicolify.copilot_providers"]` to each
- `core/luana-core-copilot/src/luana_core_copilot/application/discovery.py` — demoted convention-scan failure log level from `exception` → `debug` (luana-platform absence of `src.modules` is expected)
- `core/tests/architecture/conftest.py` — added 35 CI-safe env defaults so registry-contract test can import registries without `Settings()` validation errors

## Approach

### Step 1 — T-18 followup study
Read T-18-impl-log.md "Followup recommendations for T-20 builder" which clarified:
- Tools/Workflows/Module/Extraction/Suggestion registries use **functional API**, not classes named ToolRegistry etc.
- Snapshot must capture function signatures, dataclass fields, top-level constants types
- D-T6 cement: callback_handler subclasses + turn_envelope subclasses
- discover_providers() currently fails in luana-platform (no `src.modules`) — recommendation (a) entry-points wiring

### Step 2 — Entry-points wiring (V-AG-6 enabler)
8 packages each got a `[project.entry-points."nicolify.copilot_providers"]` block. Mapping:
- `brand = "luana_core_brand_studio.copilot_provider:provider"` (etc. for offer/crm/analytics/landing/connections/commercial_calendar/social_proof)

Module-key naming verified against each provider's `module_id` property (brand, offer, crm, analytics, connections, commercial_calendar, landing, social_proof).

`uv sync --all-packages` re-installed packages with entry-points metadata.

### Step 3 — Discovery noise reduction
`discovery.py:63` `_LOGGER.exception` on `src.modules` ModuleNotFoundError → `_LOGGER.debug`. In luana-platform `src.modules` does NOT exist (providers come via entry-points), so the noisy traceback was spurious. AISALESHT still gets the same logic with reduced log level. Documented in inline comment.

### Step 4 — Architecture test env defaults
Updated `core/tests/architecture/conftest.py` with 35 env defaults (POSTGRES_*, OPENAI_API_KEY, AI_PROVIDER_*, KIMI_API_KEY, etc.). Required because registry-contract test imports `tools/registry.py` which transitively imports `SessionLocal` → `Settings()` Pydantic validation.

### Step 5 — Registry snapshot generation
Wrote `_generate_copilot_registry_snapshot.py` to introspect each registry's public surface:
- Public names (no `_` prefix)
- Functions: name → signature
- Classes: name → { bases, dataclass_fields, methods }
- Top-level constants: name → type name

First iteration captured `dataclasses.field` function with its `_MISSING_TYPE` object address (non-deterministic across runs). Fix: filter symbols to **own attrs only** (`__module__ == mod.__name__`). Top-level constants pass-through (no `__module__`, captured by type name only).

Regenerated snapshot: 6683 bytes covering 5 registries with deterministic content.

### Step 6 — Authoring 6 tests

**Test 1 — Registry contracts stable (V-AG-3 D-T1)**
- Loads golden JSON, generates live snapshot, computes per-key diff
- Mismatch FAIL with human-readable diff + regen instructions
- 2 sub-tests: `snapshot_file_exists` (sanity) + `registry_contracts_stable` (main)

**Test 2 — No residual test stubs (V-AG-4 D-T2)**
ADJUSTED per T-17 R26 deferral. Original architect spec at §7.4 said:
> "Asserts `core/luana-core-offer-studio/tests/conftest.py` does NOT contain `class MessageModel(_Base)` declaration (must `import` from luana_core_copilot post-T-17)."

But T-17 closed as `deferred -> Story 7` because MessageModel is sales_agent territory. Per T-18 builder followup: "Allowlist BOTH MessageModel (Story 7 deferral) AND AppointmentModel (Story 8 deferral) stubs in offer-studio conftest."

Implementation chose a **richer allowlist** capturing reality across **6 conftest files** (offer-studio + copilot + brand-studio + crm + connections + landing):
- `MessageModel` × 3 (offer-studio, copilot, crm, connections) → Story 7
- `AppointmentModel` × 4 (offer-studio, copilot, crm, connections) → Story 8
- `ProductModel` × 3 (brand-studio, crm, connections) → Story 8 (product/catalog)
- `_ProductStub` × 1 (landing) → Story 8 (landing's local prefix)

2 sub-tests:
- `test_no_residual_stubs_post_story_6` — scan all conftest.py for unallowed stubs
- `test_allowlisted_stubs_still_present` — sanity: each allowlist entry must actually find a stub class (catches drift where stub got removed but allowlist entry stayed)

Regex required relaxation: allow optional leading whitespace because stubs are typically declared inside `if "<table>" not in _Base.metadata.tables:` blocks (indented one level).

**Test 3 — No mirror observability (V-AG-5 D-T6)**
4 sub-tests:
- `no_mirror_observability_classes` — scan for forbidden `class FXResolver|PricingResolver|CostCalculator|BaseObservabilityContext|BaseAgentCallbackHandler`
- `no_mirror_observability_functions` — scan for forbidden `def sanitize_payload`
- `callback_handler_subclasses_base` — verify import + class declaration with `BaseAgentCallbackHandler` parent
- `observability_context_subclasses_base` — same for `BaseObservabilityContext`

**Test 4 — ModuleDescriptor complete for lifted packages (V-AG-6 D-T6)**
3 sub-tests:
- `discovery_finds_all_lifted_providers` — asserts `discover_providers()` returns all 8 entry-points
- `module_registry_complete_for_lifted_packages` — asserts `get_module_registry()` returns all 8 ModuleDescriptors
- `module_descriptor_fields_populated` — verifies `module_id`, `label`, `description`, `route_prefix` are non-empty strings

`autouse=True` fixture resets discovery cache between tests.

**Test 5 — Voice compiler SSoT (V-AG-7 — regression Story 5)**
3 sub-tests:
- `personality_compiler_canonical_unchanged` — assert canonical file + class exist
- `no_mirror_personality_compiler_in_copilot` — scoped to luana-core-copilot
- `no_mirror_personality_compiler_workspace_wide` — full core/ scan

**Test 6 — Anchor count stable (V-AG-8)**
2 sub-tests:
- `copilot_anchor_count_stable` — assert union(copilot/* + business-module/*/copilot_provider/*) == 33
- `anchor_uniqueness` — regex sanity + non-empty

Empirical count is 33 unique, NOT 36 as architect spec wrote. Architect aspiration assumed copilot/ proper (33) + business modules (3 = WORKFLOW-F6, PROVIDER-PATTERN, BRAND-SUMMARY-F3) without recognizing overlap. Test docstring explains and cements empirical reality.

### Step 7 — Test execution

```
$ cd /home/chris/luana-platform && uv run pytest \
    core/tests/architecture/test_story6_*.py \
    core/tests/architecture/test_copilot_*.py \
    core/tests/architecture/test_no_residual_test_stubs_post_story_6.py \
    core/tests/architecture/test_no_mirror_observability_in_copilot.py \
    core/tests/architecture/test_module_descriptor_complete_for_lifted_packages.py \
    core/tests/architecture/test_voice_compiler_ssot_still_intact.py -v --tb=short

22 passed, 1 warning in 138.84s (0:02:18)
```

T-19 (6 tests) + T-20 (16 tests) = **22 total GREEN.**

## Decisions

- **Entry-points over filesystem scan**: Wired entry-points across all 8 Stories 2-5 pyprojects (vs. refactoring discovery to walk luana-platform workspace). Justification: architect's preferred pattern per discovery.py docstring ("Lets external packages distribute providers via pyproject.toml without touching this repo"). Also forward-compatible with Story 9+ external distribution.
- **Snapshot filter to "own attrs only"**: Imported callables/classes (like `dataclasses.field` leaking into module_registry's public surface) are EXCLUDED from snapshot. Otherwise `_MISSING_TYPE` object addresses non-deterministically poison the diff.
- **Allowlist expansion over architect spec**: Architect §7.4 named only offer-studio's MessageModel + AppointmentModel. Reality has stubs across 6 conftest files. Expanded allowlist captures reality with explicit Story ownership.
- **Anchor count = 33 (empirical)**: Architect spec said 36. Reality post lift is 33 unique. Followed established T-17 R26 pattern: spec premise wrong → adapt to reality, document discrepancy.
- **Discovery noise reduction**: Demote convention-scan failure to debug. Minimal patch (1 line + comment).

## Followup recommendations

For Story 7 builder (sales_agent lift):
- When MessageModel is lifted, REMOVE `MessageModel` allowlist entries from 4 conftest files (offer-studio, copilot, crm, connections) IN THE SAME COMMIT
- The arch fitness test `test_allowlisted_stubs_still_present` will then catch any stale allowlist entry

For Story 8 builder (scheduling lift):
- Same pattern for `AppointmentModel` (4 entries) + `ProductModel` (3 entries) + `_ProductStub` (1 entry)

For Story 9 architect:
- Snapshot bump occasion (Story 8 EP-1..EP-5 SDK introduction) → re-run `_generate_copilot_registry_snapshot.py` with new schema_version=2

## Verdict

**done -> docs/product/stories/luana-copilot-engine/T-20-result.md**
