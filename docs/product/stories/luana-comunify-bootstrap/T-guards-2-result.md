# T-guards-2 Result — community_safety_no_nsfw

**State**: tests-passing
**R23**: AGENTIC production_code=true → Opus 4.7
**Date**: 2026-05-14

## Validators

- ✅ **V-AE-3** (`smoke_nsfw_upload.py` — 5 NSFW images, 4+/5 blocked): unit-level cement at image vision scoring (block_pre_persist + IMAGE_FALLBACK_RESPONSE) + multi-attachment short-circuit + non-image skip. Integration smoke deferred to Story 13+.
- ✅ **V-AE-11**: audit_log severity=medium + tenant_id propagation + best-effort try/except.

## Test suite

```
.venv/bin/pytest tests/agentic_evals/guardrails/test_community_safety_no_nsfw.py -v
11/11 PASS
```

Suite covers: image NSFW above/below threshold + multiple attachments short-circuit + non-image skip + text NSFW above/below threshold + vision outage graceful + text outage graceful + audit_log failure best-effort + cross-tenant.

## Files

- `comunify/backend/src/modules/comunify/agentic/guardrails/community_safety_no_nsfw.py`
- `comunify/backend/tests/agentic_evals/guardrails/test_community_safety_no_nsfw.py`

## Quality gates

- ✅ pytest 11/11 PASS
- ✅ ruff check: clean
- ✅ ruff format: clean
- ✅ Step 0 anti-duplication: NEW surface
- ✅ Best-effort observability
- ✅ Tenant isolation
