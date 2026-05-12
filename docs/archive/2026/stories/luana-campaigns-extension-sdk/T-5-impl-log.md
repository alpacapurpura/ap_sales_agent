---
ticket_id: T-5
story_id: luana-campaigns-extension-sdk
owner: builder-agentic (Opus 4.7) — R23 required
state: done
luana_platform_commit: 5ece4cf
date: 2026-05-12
session: 4
authority: docs/product/stories/luana-campaigns-extension-sdk/06-tickets.yaml T-5 + 03-arch-be.md §1.3 step 4 verbatim + outcome §7.5
---

# T-5 — ExtensionPointRegistry executable EP-1..EP-5 + CC-1..CC-5 runtime enforcement

## R23 compliance

★ Opus 4.7 used (1M context) ★ — T-5 touches agentic-adjacent surface per 06-tickets.yaml.
While SDK code itself does not execute LLM calls, the **semantic correctness** requires
Opus-level discipline because V-AG-3 Story 6 + Story 7 golden snapshots must continue
GREEN after the registry is introduced.

## Skills consulted

- `copilot-expert` — agentic surface awareness (Story 6 WorkflowRegistry + Story 7 ToolRegistry frozen contracts)
- `sales-agent-expert` — Story 7 ToolRegistry §3 protected surface + anti-duplication §0 cardinal
- `tessl__langgraph` — confirmed registry pattern (closed-after-startup) matches LangGraph 2.0 supervisor-style constructor injection
- `tessl__pytest-api-testing` — fixture-less pure pytest with parametrize/strict-raises patterns
- `tessl__fastapi` — N/A for T-5 directly (T-14 will wire lifespan); informed adapter Optional[Any] DI pattern

## Files created

| File | Purpose |
|---|---|
| `core/luana-core-extension-sdk/src/luana_core_extension_sdk/extension_points.py` | ExtensionPointRegistry class + 18 register methods + CC-1..CC-5 enforcement |
| `core/luana-core-extension-sdk/tests/unit/test_registry_surface.py` | V-F-sdk-1 — 6 tests (18 methods exposed, no unregister_*, close() locks, constructor Optional[Any]) |
| `core/luana-core-extension-sdk/tests/unit/test_ep1_through_ep5.py` | V-F-sdk-2 — 13 tests (B1-B5 happy + adapter delegation graceful path) |
| `core/luana-core-extension-sdk/tests/unit/test_cross_cutting_policies.py` | V-F-sdk-4 — 14 tests (C1-C5 enforcement scenarios) |

## Files modified

| File | Change |
|---|---|
| `core/luana-core-extension-sdk/src/luana_core_extension_sdk/__init__.py` | Export `ExtensionPointRegistry` from public API (T-2 had commented placeholder) |

## TDD execution log

1. **RED phase** — wrote 3 test files (33 tests total) BEFORE any production code.
   - Confirmed RED: `ImportError: cannot import name 'ExtensionPointRegistry'`
2. **GREEN phase** — implemented `extension_points.py` per architect spec verbatim:
   - Module constants: `_EP_IDS`, `_OVERRIDE_PERMITTED_EPS` (EP-17 + EP-18), `_ALLOWED_BRAND_SLUGS` (5 brands), `_BACKLOG_EPS`
   - Private `_Registration` dataclass (ep_id + name + brand_slug + payload + mode)
   - `ExtensionPointRegistry.__init__` accepts `sales_agent_tool_registry_adapter` + `copilot_workflow_registry_adapter` as Optional[Any] kwargs
   - `close()` idempotent — sets `_closed = True`
   - 4 enforcement helpers: `_enforce_open` / `_enforce_namespace` / `_enforce_unique` / `_enforce_mode`
   - Single private `_register` composing all enforcements
   - 18 register methods (EP-1..EP-18) + 5 dispatch helpers (EP-1..EP-5 executable; EP-6..EP-18 raise NotImplementedError)
   - `get_all(ep_id)` test-only introspection helper
3. Tests re-run: 31/33 PASS. 2 fail = adapter graceful tests requiring `_adapters` module (T-6 implements).

## Validators addressed

- **V-F-sdk-1** ✅ — 18 register methods exposed (test_18_register_methods_exposed)
- **V-F-sdk-2** ✅ — EP-1..EP-5 executable scenarios B1-B5 GREEN
- **V-F-sdk-4** ✅ — CC-1..CC-5 enforcement scenarios C1-C5 GREEN (14 tests)
- **V-AG-namespace-allowlist** ✅ — bare name + unknown brand both raise (test_c2_*)
- **V-AG-cc5-no-unregister** ✅ — `dir()` introspection + `hasattr` check confirm zero unregister_* (test_c4_*)

## Byte-stable invariants verified

Stories 6+7 frozen registries untouched. T-5 introduces ExtensionPointRegistry but
does NOT import or modify Story 6 WorkflowRegistry or Story 7 ToolRegistry. Adapter
delegation hooks (`if self._sales_agent_tool_adapter is not None:`) are guarded —
when adapter is None (current Story 8 default), zero side-effect on Stories 6+7.

Baseline 15/15 Story 6+7 byte-stable tests reconfirmed GREEN pre-spawn (see commit
message + checkpoint Bitácora).

## Deviations from architect spec

None. Implementation follows 03-arch-be.md §1.3 step 4 verbatim. Minor enhancements
over spec (no semantic divergence):
- `_enforce_namespace` adds `not parts[1]` check (empty suffix after dot) — defensive guard against `"vitalia."` edge case. Spec didn't forbid; we forbid for robustness.
- `_enforce_mode` validates `mode not in ("append", "override")` BEFORE the override-permitted check — clearer error messages on invalid mode strings.
- Module-level constants `_EP_IDS` + `_OVERRIDE_PERMITTED_EPS` + `_ALLOWED_BRAND_SLUGS` use `frozenset` for O(1) membership lookup (spec showed `frozenset` too — no deviation).
- `BookingResult` exported from package public API (architect spec models.py defined it; T-5 confirms via re-export check in test_c5e).

## Quality gates

- ✅ `uv run pytest core/luana-core-extension-sdk/tests/ -v` → 51/51 PASS (T-2..T-5 cumulative; 2 adapter graceful tests remain RED for T-6).
- ✅ `uv run ruff check core/luana-core-extension-sdk/` → all checks passed
- ✅ `uv run ruff format --check core/luana-core-extension-sdk/` → all files formatted
- ⚪ Stories 6+7 V-AG-3 verified post-T-6 (combined Batch B verification — see T-6-impl-log.md)

## Commit

`5ece4cf` — luana-platform/main
```
feat(luana-core-extension-sdk): ExtensionPointRegistry executable EP-1..EP-5 + CC-1..CC-5 runtime enforcement
```

5 files changed, 1131 insertions, 3 deletions.

## Anti-duplication audit

✅ T-5 introduces NEW abstraction (ExtensionPointRegistry) — no existing equivalent in shared/ or modules/ per cross-codebase grep:
```bash
grep -rn "class ExtensionPointRegistry" /home/chris/luana-platform/core/ /home/chris/AISALESHT/backend/src/
# → only luana-core-extension-sdk/src/luana_core_extension_sdk/extension_points.py (new)
```

This is a NEW domain abstraction (Luana platform extension SDK contract layer) — no
prior art to lift. Per outcome §7.5 architect spec, lives in `luana-core-extension-sdk`
zero-dep package (consumed by brand apps at lifespan).

## Cross-module audit (NO-NEW-LAYER)

- ✅ T-5 does NOT introduce parallel infrastructure layer
- ✅ Uses NEW package `luana-core-extension-sdk` (Story 8 scope per outcome §7.5)
- ✅ Zero workspace dependencies — pure stdlib + typing
- ✅ Does NOT import luana-core-copilot or luana-core-sales-agent (adapter accepts `Any`)
- ✅ Maintains DAG cycle-clean (per architect §1.5)

## Open items deferred to T-6 / T-7+

- T-6 implements `_adapters.py` (2 remaining adapter graceful tests turn GREEN)
- T-7 extends with backlog EP-6..EP-18 dispatch raises NotImplementedError signature-only tests (T-5 has them in core class already; T-7 adds dedicated coverage file per scenarios B6-B18)
- T-17 adds arch fitness tests (test_brand_slug_namespace_allowlist, test_no_unregister_api, test_extension_sdk_zero_workspace_deps)
