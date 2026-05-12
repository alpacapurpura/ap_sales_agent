# T-19 Implementation Log

**Story:** luana-copilot-engine
**Ticket:** T-19 — Add NEW arch fitness tests: brand-agnostic engine + no-forward-imports (Story 6)
**Owner:** builder-agentic (Opus 4.7) — R23
**Status:** done
**Validators:** V-AG-1, V-AG-2
**Start:** 2026-05-12
**Commits:**
- luana-platform main: `9a7a0df` — test(story-6/T-19): brand-agnostic + no-forward-module-imports arch fitness

## Skills Consulted

- **copilot-expert** (mandatory per scope): no production logic changed in luana-core-copilot; arch fitness gate enforces brand-agnostic invariant (Stories 4+5 established pattern). One bonus deferral exemption applied to lazy import (Story 8 deferral path).
- **tessl__langgraph** (NA — no graph code touched).

## Files

### Created (luana-platform main)
- `core/tests/architecture/test_story6_brand_agnostic_engine.py` — 4 sub-tests (no brand conditional, no brand slug equality, no Clerk app IDs, no hardcoded secrets). PKGS = `[("luana-core-copilot", "luana_core_copilot")]`.
- `core/tests/architecture/test_story6_no_forward_module_imports.py` — 2 sub-tests (no forward module imports, no AISALESHT src.modules.* paths). Forward modules: `luana_core_{sales_agent, campaigns, advertising, scheduling, social_media}`.

### Modified (luana-platform main)
- `core/luana-core-copilot/src/luana_core_copilot/application/tools/offer_section_tools.py` line 147 — added `# type: ignore[import-not-found]` deferral exemption to lazy `from luana_core_scheduling...` import inside `_event_types()` helper. Function is reachable only when offer-studio sections include event-type-driven flows; scheduling lifts in Story 8.

## Approach

### Step 1 — Template study
Read existing Stories 4+5 arch fitness tests:
- `core/tests/architecture/test_story5_brand_agnostic_engines.py` — 3 sub-tests pattern (no brand conditional, no Clerk IDs, no brand slug in logic)
- `core/tests/architecture/test_story5_no_forward_module_imports.py` — 2 sub-tests pattern (forward modules, AISALESHT src paths)

Adapted Story 5 templates per 06-tickets.yaml T-19 spec which expanded the forbidden patterns list to include:
- `r"if\s+brand\s*=="`
- `r"if\s+tenant\.brand\s*=="`
- `r"if\s+self\.brand\s*=="`
- `r'brand\s*==\s*["\'](nicolify|vitalia|comunify|lupulo)["\']'`
- `r'(API_KEY|SECRET|TOKEN)\s*=\s*["\'](?!os\.|settings\.|env|getenv).{8,}["\']'`

### Step 2 — Brand-agnostic test design
Split into 4 sub-tests for clear failure mode signaling:
1. `test_no_brand_conditional` — covers the 3 conditional patterns
2. `test_no_brand_slug_equality_literal` — covers literal brand-slug `==` comparisons
3. `test_no_hardcoded_clerk_app_ids` — Clerk identifier sniff
4. `test_no_hardcoded_secrets` — API key/token/secret literal assignment

Comment-line skip applied uniformly (`stripped.startswith("#")`).

### Step 3 — No-forward test design
Mirror Story 5's pattern. STORY6 forward modules excludes copilot itself (we ARE Story 6) and excludes Stories 2-5 packages (Stories 6 may legitimately depend on them — observability, brand-studio, offer-studio, etc.). Honors documented deferral exemption regex (`# Story N deferred` | `# type: ignore[import-not-found]`).

### Step 4 — RED then GREEN
First run produced ONE legitimate violation:
```
luana-core-copilot/application/tools/offer_section_tools.py:147:
  from luana_core_scheduling.application.services.event_type_service import (
```

This is a **lazy import inside `_event_types()` function**, called only when offer-studio sections (form-runtime) need to enumerate event types. luana-core-scheduling will lift in Story 8 per outcome §7.4. Two options:
1. Hardcode allowlist in test (path:line allowlist)
2. Apply documented deferral exemption pattern

Chose option 2 (cleaner, follows established Story 4/5 deferral comment convention). Applied `# type: ignore[import-not-found]` inline comment with a docstring note about Story 8 deferral.

Re-ran: 6/6 GREEN.

## Test execution

```bash
$ cd /home/chris/luana-platform && uv run pytest \
    core/tests/architecture/test_story6_brand_agnostic_engine.py \
    core/tests/architecture/test_story6_no_forward_module_imports.py -v --tb=short

core/tests/architecture/test_story6_brand_agnostic_engine.py::test_no_brand_conditional PASSED
core/tests/architecture/test_story6_brand_agnostic_engine.py::test_no_brand_slug_equality_literal PASSED
core/tests/architecture/test_story6_brand_agnostic_engine.py::test_no_hardcoded_clerk_app_ids PASSED
core/tests/architecture/test_story6_brand_agnostic_engine.py::test_no_hardcoded_secrets PASSED
core/tests/architecture/test_story6_no_forward_module_imports.py::test_no_forward_module_imports PASSED
core/tests/architecture/test_story6_no_forward_module_imports.py::test_no_aisalesht_src_imports PASSED

============================== 6 passed in 0.21s ===============================
```

## Decisions

- **Deferral exemption over allowlist**: Established Story 4/5 pattern uses comment-based deferral exemption (`# Story N deferred` | `# type: ignore[import-not-found]`). Hardcoded path:line allowlists drift over time. Comment-based exemption is self-documenting and travels with the code.
- **4 sub-tests over 1 mega-test**: Single test would conflate distinct failure modes (brand conditional vs. Clerk ID vs. secret). Sub-tests give precise audit signal.
- **PKGS list as tuples**: Future-proof signature for adding multiple Story 6 packages (none planned, but matches outcome §7.4 forward thinking).

## Verdict

**done -> docs/product/stories/luana-copilot-engine/T-19-result.md**
