# T-13 Result

**Status:** GREEN
**Commit (luana-platform):** `18bea75`
**Date:** 2026-05-12

## Summary

Lifted sales_agent api/ (15 src files including api/dto/) + workers/ (7 src files) verbatim from AISALESHT to luana-platform with mechanical sed (§1.4). 6 §3-protected files sha256 captured POST-sed POST-ruff for T-18 V-AG-8 baseline.

## Validators addressed

| Validator | Status | Evidence |
|---|---|---|
| V-NF-2 | ✅ | Zero `from src.*` / `import src.*` leaks in 22 src files |
| V-F-closer-studio | ✅ | api/closer_studio.py + api/ws.py lifted hash-stable |
| V-F-followup | ✅ | workers/follow_up_engine.py lifted hash-stable |

## §3 Protected surfaces sha256 (V-AG-8 baseline)

```
api/closer_studio.py        : 8f31c50fdc851bd6432a31e049b4009c3155ca950bfac095d3d9cbb2ab8a992a
api/ws.py                   : d86ae9120cfaf5b02e5c502fdc818102a5cedb7fb2d39974b34fbb8b2828cdde
api/enrollments.py          : e147dea0d79fd321becb9d0358769f29a651c92167fc95166d7f4cbe11805a39
api/scheduler_webhooks.py   : 135d0df0be4d4ddb8858173d4c2cb0e2f6bc810cfd004b2b94b33e254e65ac86
api/payment_webhooks.py     : 0091c0aab63835e702e5fd6014c46f9fc34c39f5372170a30f61b41f9fc69cab
workers/follow_up_engine.py : 6d66c50347ec66a26aeae5be8903f3f7d2d9b142b9ffd35bcd41a3dbc2ba8a43
```

## Tests

- ✅ 29 tests passed (api routes + follow_up cadence/tuning constants + safety/signals)
- ⚠️ 8 failed = pre-existing tech debt (NOT introduced by T-13):
  - 5 follow_up Jinja TemplateNotFound (T-7 inherited templates_dir absolute path)
  - 3 payment_webhooks SQLA `LeadModel.messages` FK mismatch (Story 4 documented in T-12-result.md)

## Deferred test lifts (cross-package conftest dependency)

`test_enrollment_api.py + test_enrollment_tools.py + test_enrollment_service.py + test_enrollment_repository.py` import `from tests.modules.offer.conftest import create_product_model` — not lifted as shared helpers infrastructure. Tech debt for follow-up: extract create_product_model + TENANT_A/B constants into a shared importable helper module that lives outside test-only path.

## Cardinal invariants honored

- ★ AISALESHT UNTOUCHED (V-NF-4)
- ★ §3 6 files hash-stable POST sed+ruff (V-AG-8 baseline captured)
- ★ D-T3 hexagonal cement preserved (zero PersonalityCompiler imports)
- ★ D-T6 anti-mirror invariant: zero observability bases declared
- ★ NO logic refactor on §3 surfaces — pure import-path sed rewrites
- ★ FastAPI redirect_slashes=False invariant preserved (api/ uses APIRouter only; app-level setup lives in main.py — not lifted)
- ★ appointment_reminder_engine.py does NOT call compose_prompt — no D-T3 ripple from T-11
