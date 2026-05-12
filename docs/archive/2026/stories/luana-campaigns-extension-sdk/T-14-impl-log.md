# T-14 Implementation Log — apps/test-brand FastAPI app + lifespan + register_all

**Story:** luana-campaigns-extension-sdk
**Batch:** E
**Date:** 2026-05-12
**Builder:** builder-backend Sonnet

## Summary

Created `apps/test-brand` package with FastAPI lifespan event + 18-handler `register_all()`
(5 executable EP-1..EP-5 + 13 stubs EP-6..EP-18). All names use `test-brand.` namespace
prefix (CC-4). `uv sync --package test-brand` succeeded.

## Files created

- `apps/test-brand/pyproject.toml` — deps: fastapi + luana-core-extension-sdk
- `apps/test-brand/README.md` — stub: "SDK smoke validation, NOT deployable product"
- `apps/test-brand/src/test_brand/__init__.py` — empty
- `apps/test-brand/src/test_brand/main.py` — FastAPI app with `redirect_slashes=False` + lifespan
- `apps/test-brand/src/test_brand/extensions.py` — `register_all(registry)` with 18 handlers
- `apps/test-brand/tests/__init__.py` — empty

## Key implementation notes

### main.py lifespan pattern

```python
@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    registry = ExtensionPointRegistry()
    register_all(registry)
    registry.close()  # CC-3 startup-only lock
    yield
```

`FastAPI(redirect_slashes=False, lifespan=_lifespan)` per CLAUDE.md mandate.

### extensions.py register_all

- **EP-1 field_override:** `test-brand.layout_override` handler returning `FieldOverride(field="layout", value="test")`
- **EP-2 offer_preset_pack_register:** `test-brand.starter_pack` PresetPack
- **EP-3 sales_agent_tool_register:** `test-brand.greet` ToolDef (adapter=None → graceful NotImplementedError)
- **EP-4 copilot_workflow_register:** `test-brand.onboarding` WorkflowDef (adapter=None → graceful)
- **EP-5 scheduling_booking_policy_register:** `test-brand.default_policy` BookingPolicy
- **EP-6..EP-18:** stubs — DataClasses populated, registration succeeds, dispatch raises NotImplementedError

## Invariants confirmed

- **V-NF-1:** zero AISALESHT touch
- **CC-4 namespace:** all 18 names prefixed `test-brand.`
- **CC-3:** `registry.close()` called post-register in lifespan

## luana-platform commit

`672215f` — `feat(apps/test-brand): FastAPI lifespan + 18 register_all handlers (5 executable + 13 stubs)`

## Skills Consulted

- `backend-expert`: FastAPI lifespan pattern, redirect_slashes=False
- `tessl__fastapi`: asynccontextmanager lifespan, startup-only registration
