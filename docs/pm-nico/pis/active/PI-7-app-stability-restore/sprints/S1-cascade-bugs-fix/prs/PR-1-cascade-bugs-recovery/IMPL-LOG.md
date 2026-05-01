# IMPL-LOG — PR-1-cascade-bugs-recovery (Bug #7)

> Builder: `nicolify-backend` (Sonnet 4.6)
> Date: 2026-05-01
> Scope: Bug #7 only (contract split § 0.5 — Bug #9 = PM ad-hoc)
> Surface: `backend/src/modules/brand/application/services/brand_data_adapter.py`

---

## Skills Consulted

- `backend-expert` — invoked Step 0 GATE mandatory. Loaded `runtime-quality-checklist.md` antes commit. Decision: fix at adapter layer (deepest without expanding blast radius), NOT at repository layer. Citation: SOP "Bugs (Outside-In)" — fix at deepest layer possible.
- `brand-expert` — invoked para PersonalityProfile schema + adapter pattern + DTO conversion. Decision: `PersonalityProfileDTO` ya existe en `brand/api/personality.py:45-63` con `ConfigDict(from_attributes=True)` — EXTEND, no crear nuevo. `model_validate(orm_instance)` es el canonical Pydantic v2 path para ORM→DTO. Citation: SOP "Quiero modificar voice / tone / personality" → `PersonalityProfile` layer.
- `tessl__fastapi` — invoked para Annotated dep patterns, response_model. Decision: no FastAPI routes touched en este PR — skill relevant para confirmar PII compliance pattern (response_model en api/personality.py ya tiene `PersonalityProfileDTO`).
- `tessl__pytest-api-testing` — invoked para fixture scoping + factory fixtures. Decision: unit tests con `MagicMock` + real ORM `PersonalityProfileModel` instance (NOT MagicMock — mascaría el bug). No DB connection needed.
- `tessl__graceful-degradation` — invoked. Decision: NOT applied this PR. Bug #7 es type mismatch, no transient failure. Recommendation deferred (backlog: wrap repo calls in try/except with empty `BrandKnowledgeDTO()` fallback). Citation: CONTRACT § 0.4 + § 15 research notes.

---

## Step 0 GATE — Anti-duplication grep (pre-write)

```bash
# Scan for PersonalityProfileDTO cross-codebase
find backend/src -name "*.py" | xargs grep -l "PersonalityProfileDTO"
# → Result: ONLY brand/api/personality.py
# Decision: EXTEND existing PersonalityProfileDTO (single file, no duplication)
# No new file created — pure EXTEND via import

# Scan for brand_data_adapter callers
find backend/src -name "*.py" | xargs grep -l "BrandDataAdapter|get_brand_knowledge"
# → Result: brand_data_adapter.py, shared/links/ports/brand.py,
#   sales_agent/knowledge_builder.py:71, copilot/suggestions/providers/brand.py:86,
#   copilot/suggestions/providers/copilot.py
# Decision: fix is at adapter layer → transparent to all callers (BrandKnowledgeDTO shape unchanged)
```

**EXTEND-vs-NEW decision: EXTEND existing `PersonalityProfileDTO` (import from brand/api/personality.py).**
No new file. No parallel layer. Anti-duplication rule satisfied.

---

## Bug #7 RCA

**Call chain:**
1. `sales_agent.knowledge_builder.build_identity` (line 71) → `brand_port.get_brand_knowledge(tenant_id)`
2. `BrandDataAdapter.get_brand_knowledge` (line 46) → `personality_profile.model_dump(mode="json")`
3. `personality_profile` = `PersonalityProfileModel` (SQLA ORM) — does NOT inherit Pydantic `BaseModel`
4. `AttributeError: 'PersonalityProfileModel' object has no attribute 'model_dump'`

**Root cause:** `PersonalityProfileRepository.get_active()` returns SQLA ORM model, not Pydantic DTO. The adapter assumed Pydantic.

**Fix:** Wrap ORM instance with `PersonalityProfileDTO.model_validate(orm_instance)` before calling `.model_dump(mode="json")`. Uses `ConfigDict(from_attributes=True)` (already set in DTO) — canonical Pydantic v2 path.

---

## TDD — RED → GREEN iterations

### Iteration 1

**RED:** Appended `TestGetBrandKnowledgeHandlesORMPersonalityProfile` class to existing test file `test_brand_data_adapter_pr2.py`. Test instantiates real `PersonalityProfileModel` (NOT MagicMock — to ensure bug actually reproduces).

```
pytest tests/modules/brand/application/services/test_brand_data_adapter_pr2.py::TestGetBrandKnowledgeHandlesORMPersonalityProfile -v
FAILED: AttributeError: 'PersonalityProfileModel' object has no attribute 'model_dump'
```

**Fix applied:**
1. Added import `from src.modules.brand.api.personality import PersonalityProfileDTO` to top of adapter
2. Replaced single-line `personality_profile.model_dump(mode="json") if personality_profile else None` with:
   ```python
   personality_dict: dict[str, object] | None = None
   if personality_profile is not None:
       personality_dict = PersonalityProfileDTO.model_validate(
           personality_profile,
       ).model_dump(mode="json")
   ```
3. Passed `personality_profile=personality_dict` to `BrandKnowledgeDTO`

**GREEN:** All 6 tests pass.

---

## Quality gates — local native

| Gate | Result | Notes |
|---|---|---|
| `ruff check` | PASS | 0 errors |
| `ruff format --check` | PASS (after auto-format) | Test file reformatted by ruff |
| `mypy` (adapter file) | PASS | Fixed `dict` → `dict[str, object]` for mypy strict |
| `pytest tests/modules/brand/application/services/` | 6/6 PASS | All GREEN |
| `pytest tests/architecture/` | 805 PASS / 5 PRE-EXISTING FAILS | Pre-existing failures verified via git stash — NOT caused by this PR |

**Pre-existing arch failures (NOT caused by this PR):**
- `test_ddd_boundaries.py::test_no_new_cross_module_imports` (campaigns→sales_agent import)
- `test_sales_agent_anchors.py::test_all_sales_agent_anchors_are_registered`
- `test_sales_agent_system_prompt_order.py::test_cacheable_fragment_order_is_frozen`
- `test_sales_agent_system_prompt_order.py::test_full_order_is_cacheable_then_volatile`
- `test_folder_naming.py::test_all_python_files_snake_case` (copilot/_dependencies.py)

All confirmed by `git stash → run → git stash pop` — same failures without my changes.

**Pre-existing unit failure (NOT caused by this PR):**
- `tests/modules/brand/test_outbox_adapter_integration.py::TestBrandOutboxAdapterFlagOff::test_flag_off_is_default_for_brand_module`
  — confirms `USE_OUTBOX_PATTERN_BRAND=True` in local env (matches CONTEXT-BRIEF § 4 "Outbox cutover: ON").

---

## Cross-module reads

- READ-ONLY: `backend/src/modules/brand/api/personality.py` — consumed `PersonalityProfileDTO` (EXTEND, not copy)
- READ-ONLY: `backend/src/modules/brand/infrastructure/models/personality_model.py` — understood ORM shape for test fixture
- READ-ONLY: `backend/src/modules/sales_agent/application/services/knowledge_builder.py` — confirmed downstream shape `BrandKnowledgeDTO.personality_profile: dict | None` unchanged

---

## Files touched this session

| File | Action | Reason |
|---|---|---|
| `backend/src/modules/brand/application/services/brand_data_adapter.py` | MODIFIED | Bug #7 fix — import PersonalityProfileDTO + convert ORM via model_validate |
| `backend/tests/modules/brand/application/services/test_brand_data_adapter_pr2.py` | MODIFIED (append) | RED→GREEN regression tests for Bug #7 |
| `docs/pm-nico/pis/active/PI-7-app-stability-restore/sprints/S1-cascade-bugs-fix/prs/PR-1-cascade-bugs-recovery/IMPL-LOG.md` | CREATED | This file |

---

## Parallel session overlap (M7 check)

PI-4 S1 PR-1 modifies `buyer_persona.*` files — NO collision with `brand_data_adapter.py` or `personality_model.py`. Low collision risk confirmed.

---

## Gate-runner + Auditor

Gate-runner (Haiku) and auditor (Opus) to be auto-spawned per Phase 2 workflow.
