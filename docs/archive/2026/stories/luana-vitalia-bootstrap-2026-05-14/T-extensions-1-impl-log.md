# T-extensions-1 — Implementation Log

**Ticket:** T-extensions-1 — extensions.py register_all EP-1..EP-18 entry point
**Story:** luana-vitalia-bootstrap (Story 11)
**Owner:** builder-agentic (Opus 4.7 — R23 production AGENTIC code, mandatory)
**Iteration:** 1/3
**Date:** 2026-05-14
**State:** developed

---

## Phase 0 — Anti-duplication GATE (Step 0)

Per `.claude/rules/anti-duplication.md` § 0, pre-write greps cross-codebase:

```bash
# 1. SDK contract surface
ls /home/chris/luana-platform/core/luana-core-extension-sdk/src/luana_core_extension_sdk/
# → __init__.py · _adapters.py · brand_context.py · exceptions.py · extension_points.py · models.py · protocols.py

# 2. Reference impl for register_all pattern
find /home/chris/luana-platform -name "extensions.py" -not -path "*/.venv/*"
# → /home/chris/luana-platform/apps/test-brand/src/test_brand/extensions.py  (Story 8 cement precedent)

# 3. ExtensionPointRegistry public API
grep -n "ExtensionPointRegistry\." /home/chris/luana-platform/core/luana-core-extension-sdk/src/luana_core_extension_sdk/extension_points.py
# → 18 register_* methods + 5 EP-1..EP-5 dispatch helpers + 13 EP-6..EP-18 NotImplementedError dispatch

# 4. Verify no existing vitalia/extensions.py mirror or stub
find /home/chris/luana-platform/vitalia -name "extensions.py"
# → (none — fresh creation)
```

**Verdict:** NO mirror risk. extensions.py is brand-side CONSUMER of the shared SDK,
not a shared/ abstraction. Pattern = test-brand precedent (apps/test-brand/src/test_brand/extensions.py).

**§0 Inventory row consulted:**
`luana-platform Extension SDK` → `core/luana-core-extension-sdk/src/luana_core_extension_sdk/extension_points.py::ExtensionPointRegistry` → consumed by ALL vertical brand packages.
This ticket adds the vitalia consumer (parallel to test-brand existing consumer).

---

## Skills Consulted

| Skill | Why invoked | Decision |
|---|---|---|
| `copilot-expert` (auto-loaded) | Touching agentic mounting (EP-4 copilot_workflow + EP-7 extractors + EP-14 KB packs) | Stop-first-read pattern honored. Anti-duplication §0 cardinal rule followed: SDK is canonical, no mirror. Module registry pattern preserved (workflow registration via EP-4, not direct module_registry edit). |
| `sales-agent-expert` (auto-loaded) | Touching sales-agent mounting (EP-3 tools + EP-13 guardrails) | §3 NO-TOUCH surfaces respected (Closer Studio, SmartBufferService untouched). Brand voice exception honored — output voice respects tenant via personality_profiles.system_instruction (SSoT), no voseo regulation needed in placeholder strings (description text is neutral metadata). |
| `tessl__langgraph` | EP-4 workflow registration | WorkflowDef.steps=() is a stub — actual StateGraph + reducers + checkpointer wiring deferred to T-workflow-1. Pattern is "register descriptor now, populate graph later". |
| `tessl__graceful-degradation` | Placeholder handlers must fail clearly when invoked | Rule 2 applied: every `_not_implemented_yet(point, owner_ticket)` placeholder raises `NotImplementedError` with explicit message + pointer to owning ticket. Caller knows EXACTLY where to look. No silent failures. |
| `tessl__pytest-api-testing` | 18 TDD tests on registry mounting | Used factory fixture pattern (`_make_fresh_registry()` helper) instead of session-scoped registries — function scope, no state leak between tests. Parametrize not applied here because each EP has distinct count assertion; individual test names give clearer pytest output. |
| `tessl__fastapi` | NOT touched | extensions.py is module-level Python, no FastAPI routes. Lifespan integration (where FastAPI calls register_all) is out-of-scope per ticket (lives in future BE composition root ticket — likely T-be-7 or main.py refactor). |
| `claude-api` | NOT touched | No Anthropic SDK / prompt cache changes in this ticket. Prompt slot architecture lands in T-prompts-1 (per ticket scope `out_of_scope`). |

---

## Cross-module Systems Audit (NO-NEW-LAYER)

```bash
# 1. Existing factories / abstractions in core/
grep -rn "ExtensionPointRegistry\|register_all\|BrandContext" /home/chris/luana-platform/core/luana-core-extension-sdk/

# 2. Cross-codebase patterns
grep -rn "def register_all" /home/chris/luana-platform/apps /home/chris/luana-platform/core
# → Found: apps/test-brand/src/test_brand/extensions.py::register_all(registry)  (Story 8 precedent)
```

**Verdict EXTEND > REPLACE > NEW priority applied:**
- The SDK already provides 18 `register_*` methods → EXTEND by writing brand-side `register_all(registry)` function that calls them. NO new infrastructure layer.
- test-brand precedent verified — same pattern, different brand-slug + content.

---

## Default-flip Detection (Step 0.5)

No `core/config.py` defaults touched. No feature flag flips in this ticket. Step 0.5 N/A.

---

## Design vs Implementation Reconciliation

**Spec drift candidate identified at read-time** (H4 halt trigger evaluation):

- `02-design-agentic.md § 18.3` and `03-arch.md § 4.1` show pseudo-code:
  `ExtensionPointRegistry.register_all(brand_slug="vitalia", config={dict})` as a classmethod.
- The actual SDK (Story 9 cement at `core/luana-core-extension-sdk/`) does NOT have such
  a classmethod. It has 18 individual `register_*` methods + per-brand `register_all(registry)`
  function in the brand consumer (test-brand precedent).
- Per **CC-5 inmutable**, the SDK cannot grow new public methods after Story 9 cement.

**Resolution:** NOT spec drift requiring escalation. The architectural pseudo-code shows
the **conceptual** single-entry-point semantics — preserved by the test-brand pattern
(one module-level `register_all(registry)` function). Same intent (single call mounts
the whole brand), same single-call interface, fully contract-compliant with Story 9
frozen SDK. I implemented the test-brand pattern verbatim with vitalia-specific content.

Decision documented in `extensions.py` module docstring §"NOTE on design vs implementation
reconciliation".

---

## TDD Cycle (RED → GREEN → REFACTOR)

### RED — Pre-implementation test failure

Wrote 18 tests in `tests/unit/test_extensions_register_all.py`. First test imports
`src.modules.vitalia.extensions.register_all` → `ModuleNotFoundError`:

```
$ pytest tests/unit/test_extensions_register_all.py
collected 18 items
tests/unit/test_extensions_register_all.py F
ModuleNotFoundError: No module named 'src.modules.vitalia.extensions'
1 failed in 0.13s
```

### GREEN — Implementation passes

Created `extensions.py` + 8 skeleton `__init__.py` files for `agentic/{tools,guardrails,prompts}/`
and `copilot/{extractors,workflows,kb}/` packages. Re-ran:

```
$ pytest tests/unit/test_extensions_register_all.py -v
collected 18 items
tests/unit/test_extensions_register_all.py .................. [100%]
==================== 18 passed in 0.11s ====================
```

18/18 PASS.

### REFACTOR — Lint + format pass

```
$ ruff check --fix vitalia/backend/src/modules/vitalia/extensions.py vitalia/backend/tests/unit/test_extensions_register_all.py
1 fixable (import sort) → fixed
$ ruff format vitalia/backend/src/modules/vitalia/extensions.py vitalia/backend/tests/unit/test_extensions_register_all.py
2 files reformatted
$ ruff check ...  # post-fix
All checks passed!
$ ruff format --check ...
2 files already formatted
$ pytest tests/unit/test_extensions_register_all.py
18 passed in 0.12s
```

---

## Acceptance Evidence

### A1 — register_all succeeds without exception

```
$ cd /home/chris/luana-platform/vitalia/backend && \
  /home/chris/luana-platform/.venv/bin/python -m pytest \
  tests/unit/test_extensions_register_all.py::test_register_all_succeeds -v
PASSED
```

All 18 tests in the file PASS — see GREEN block above. Verifications include:
- A1.1 `test_register_all_succeeds` — no exception on call
- A1.2 `test_register_all_populates_all_18_eps` — every EP-1..EP-18 has ≥1 record
- A1.3 `test_register_all_idempotent_on_fresh_registry` — two fresh registries get same shape
- A1.4 `test_all_registrations_use_vitalia_namespace` — CC-4 namespace enforced
- Per-EP count cement: EP-2=1, EP-3=4, EP-4=1, EP-5=1, EP-7=2, EP-8=3, EP-13=4, EP-14=3, EP-17=3
- Tool handlers callable, KB packs tenant_scope='brand', EP-17 mode='override' (CC-2)
- EP-1 dispatch returns None gracefully

### A2 — Docs extension_points.md completeness arch fitness GREEN

```
$ cd /home/chris/luana-platform && \
  .venv/bin/pytest core/tests/architecture/test_docs_extension_points_completeness.py -v
============================= 8 passed in 0.10s =============================
```

This arch test was authored in Story 8 to verify `docs/extension-points.md` has all
required sections (§1 CC-1..CC-5, §2 EP-1..EP-5 with vitalia/comunify/lupulo examples,
§3 EP-6..EP-18 backlog, §4 vertical-agent recipe + NO EP-19 literal, §5 cross-brand
learning principle). It is GREEN because docs/extension-points.md was already
populated by Story 8 with vitalia per-vertical examples baked in.

V-NF-13 PASS.

---

## Validators

- **V-NF-13** (Extension SDK docs completeness — vitalia register_all surface covered) — PASS

---

## Files Modified

### luana-platform side (production code)

```
vitalia/backend/src/modules/vitalia/extensions.py                   (CREATE — 348 lines incl. extensive scope docstring)
vitalia/backend/src/modules/vitalia/agentic/__init__.py             (CREATE empty package marker)
vitalia/backend/src/modules/vitalia/agentic/tools/__init__.py       (CREATE empty package marker)
vitalia/backend/src/modules/vitalia/agentic/guardrails/__init__.py  (CREATE empty package marker)
vitalia/backend/src/modules/vitalia/agentic/prompts/__init__.py     (CREATE empty package marker)
vitalia/backend/src/modules/vitalia/copilot/__init__.py             (CREATE empty package marker)
vitalia/backend/src/modules/vitalia/copilot/extractors/__init__.py  (CREATE empty package marker)
vitalia/backend/src/modules/vitalia/copilot/workflows/__init__.py   (CREATE empty package marker)
vitalia/backend/src/modules/vitalia/copilot/kb/__init__.py          (CREATE empty package marker)
```

### luana-platform side (tests)

```
vitalia/backend/tests/unit/test_extensions_register_all.py          (CREATE 18 tests, ~350 lines)
```

### AISALESHT side (docs)

```
docs/product/stories/luana-vitalia-bootstrap/T-extensions-1-impl-log.md  (this file)
docs/product/stories/luana-vitalia-bootstrap/T-extensions-1-result.md    (sibling)
docs/product/stories/luana-vitalia-bootstrap/checkpoint.md               (state update if applicable — handled by /pm)
```

### Files explicitly NOT touched (parallel-safety M8)

AISALESHT WIP:
- `buyer-persona-ai-flow-verified.png` (deletion in progress, not mine)
- `qa-extract-clean.png` (deletion in progress, not mine)
- `docs/etl/extraction-contract.md` (other-session WIP)
- `docs/product/BACKLOG-TLDR.md` (PM session WIP)
- `docs/product/stories/luana-vitalia-bootstrap/checkpoint.md` (PM-owned)

luana-platform WIP (T-be-2 + other parallel sessions):
- `core/DEFERRED-FILES.md`
- `core/luana-core-platform/src/luana_core_platform/infrastructure/model_registry.py`
- `core/luana-core-platform/src/luana_core_platform/links/ports/calendar.py`
- `core/tests/architecture/test_docs_v0_1_0_deliverables_present.py`
- `core/tests/architecture/test_no_publish_config_story8.py`
- `core/tests/architecture/test_release_workflow_yaml_valid.py`
- `core/tests/architecture/test_releaserc_config_valid.py`
- `core/tests/architecture/test_story3_no_forward_module_imports.py`
- `core/tests/architecture/test_story4_no_forward_module_imports.py`
- `core/tests/architecture/test_story5_no_forward_module_imports.py`
- `core/tests/architecture/test_workspace_versions_uniform_at_v0_1_0.py`
- `pyproject.toml` (workspace config)

All other-session files VERIFIED INTACT post-stage (git status check before commit).

---

## Decisions Honored

- **D1** — Vitalia subdir at `luana-platform/vitalia/` (extensions.py lives in
  `vitalia/backend/src/modules/vitalia/`, no separate repo).
- **D5** — Slot 4 MEDICAL_SAFETY_RAILS reserved at architecture phase. Real prompt MD
  lands in T-prompts-1 (not registered via EP — slot is part of prompt layout SSoT
  in `02-design-agentic § 10`, registered via prompt compose pipeline not via EP).
  No SDK surface needed for prompts. Documented in module docstring.
- **D7** — compliance_level=hipaa_lite encoded in `KbPackDef.metadata.compliance_level`
  for all 3 EP-14 KB packs. Visible to downstream consumers.
- **D8** — voice_cloning_enabled=false reflected in brand.yaml. No SDK surface for
  voice cloning (sales-agent voice respects tenant via personality_profiles SSoT,
  not configured per-brand at SDK level). Mentioned in docstring for traceability.

---

## Anti-patterns Avoided (defensive checklist)

- ✅ NO new infrastructure layer — used SDK as-is, no parallel registry / factory.
- ✅ NO mirror of test-brand pattern — followed precedent verbatim with vitalia content.
- ✅ NO mutation of Story 9 cement (SDK code untouched — `core/luana-core-extension-sdk/` not edited).
- ✅ NO hardcoded model names / pricing / channel slugs — registry consumes SDK DataClass models.
- ✅ NO infinite loops or unbounded recursion (register_all is pure declarative).
- ✅ NO bare names — `_ns()` helper ensures every registration is `vitalia.*` prefixed (CC-4).
- ✅ NO silent failures — every placeholder handler raises NotImplementedError with explicit
  ticket pointer when invoked.
- ✅ NO unprotected external calls — there ARE no external calls in this ticket (pure
  in-memory registration). `tessl__graceful-degradation` applied to placeholder error
  messages so future invokers see clear remediation path.
- ✅ Spanish neutro / voseo concerns — N/A here; no user-facing strings. Labels in
  Spanish neutro tuteo (e.g. "Pendiente consentimiento", "Datos de la clínica",
  "Seguimientos") per `.claude/rules/spanish-text.md` (R2 LatAm neutro).
- ✅ Tenant isolation — N/A at registration time; tenant context arrives later via
  BrandContext at request time (CC-4 namespace already enforced).
- ✅ Best-effort observability — N/A; no observability writes here. Future ticket
  that wires lifespan will emit a trace event on register_all success/failure.

---

## Downstream Regression Scope (R3)

Per `.claude/rules/auditor-downstream-regression.md`, surface `vitalia/backend/src/modules/vitalia/extensions.py`
is a NEW path. NO downstream consumers yet — this is the BRAND consumer of the SDK,
not a shared surface. The SDK side (`core/luana-core-extension-sdk/`) is untouched.

Anti-default-flip: NO flags flipped. No downstream regression scope mandatory.

Pre-commit freshness gate (Section 4): the new files live under `vitalia/backend/`,
NOT `backend/src/shared/`. Freshness gate does not apply.

---

## Cost Estimate

- Read SSoT (06-tickets.yaml + 03-arch.md + 03-arch-agentic.md + 02-design-agentic.md + brand.yaml + SDK source + test-brand reference): ~30k context tokens
- Implementation (extensions.py + 8 skeleton inits + 18 tests): ~12k tokens
- Lint + format + test cycles: ~2k tokens
- Impl-log + result: ~6k tokens

Total: ~50k tokens. Opus 4.7 input ~$0.75 / output ~$1.10 (rough estimate, R23 justified).

---

## Notable Implementation Decisions

1. **Pattern Option C (skeleton modules) selected over A (NotImplementedError raise everywhere) or B (deferred None handlers)** —
   clean scaffolding lets later tickets DROP files into the right package without
   re-jiggering registry. Empty packages enable clean Python imports (no
   side-effect imports at register_all time). Placeholder handlers in extensions.py
   raise NotImplementedError when invoked (clearer for debugging than silent None).

2. **EP-13 guardrails registered with mode='append' (default)** despite the fact that
   later T-guards-* tickets need to "replace" the placeholders — they will replace
   by direct file edit of extensions.py (not re-register via SDK) since CC-2 forbids
   override on EP-13. This is the documented pattern per `extensions.py` docstring.

3. **EP-17 + EP-18 use mode='override'** intentionally — Vitalia REPLACES core defaults
   (medical-vertical pricing + wizard step), which is exactly the CC-2 use case for
   override permitted EPs. Test verifies `rec.mode == "override"` for EP-17.

4. **EP-4 WorkflowDef.steps=()** is intentional placeholder. T-workflow-1 lands the
   real LangGraph StateGraph. Trigger event `vitalia.treatment.started` is encoded
   here so analytics/CRM/campaign consumers see consistent event name from day one.

5. **EP-14 tenant_scope='brand'** for all 3 KB packs — medical reference content
   (procedures, ethics, safety) is CROSS-TENANT shareable (D7 hipaa_lite OK because
   no PHI lives in these KB packs). Per-tenant clinic-specific KB content would
   use tenant_scope='tenant' (not registered in Story 11).

6. **Loop iteration for EP-8 channel adapters + EP-13 guardrails + EP-14 KB packs** —
   DRY pattern. Each iteration registers 3-4 similar entries. Trade-off: slightly less
   verbose at the cost of slightly more abstract reading. Lint passes; readability
   acceptable given the surrounding rich docstring.

7. **Did NOT modify** test_smoke.py — pre-existing failing test from T-scaffold-1 is
   out of scope for this ticket. M8 rule: leave parallel-session files intact.

---

## Coverage Snapshot

Test count: 18 NEW unit tests in `tests/unit/test_extensions_register_all.py`.
Per-EP coverage: 18 EPs × ≥1 assertion = ≥18 invariants verified.
Production code: 348 lines extensions.py (incl. ~150 lines docstring + 200 lines registration
logic). Line coverage of register_all: every register_* call exercised by the
"populates_all_18_eps" test.

---

## Next Steps

This ticket UNBLOCKS:
- T-tools-1..4 (real tool handlers replace EP-3 placeholders)
- T-extractors-1,2 (real extractor instantiation feeds EP-7)
- T-kb-1..3 (real Qdrant ingestion populates EP-14 collections)
- T-workflow-1 (LangGraph StateGraph fills EP-4 steps)
- T-prompts-1 (Slot 4 MEDICAL_SAFETY_RAILS prompt MD lands; not via EP)

Each ticket above will edit extensions.py in-place to replace placeholder handlers
with real callables. Test file `test_extensions_register_all.py` will gain new
test functions per ticket that verify the real handler behavior on invocation
(currently we only verify registration shape; later we verify execution).
