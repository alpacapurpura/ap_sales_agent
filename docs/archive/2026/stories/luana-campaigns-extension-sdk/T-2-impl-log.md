---
ticket: T-2
title: "Create luana-core-extension-sdk package skeleton + pyproject.toml + README"
story_id: luana-campaigns-extension-sdk
completed_at: 2026-05-12
iteration: 1
commit: 69c95af
---

## Files Created

- `core/luana-core-extension-sdk/pyproject.toml` — version 0.0.8-alpha, dependencies=[] (zero-dep)
- `core/luana-core-extension-sdk/README.md` — 18 EP overview stub
- `core/luana-core-extension-sdk/src/luana_core_extension_sdk/__init__.py` — empty placeholder
- `core/luana-core-extension-sdk/tests/__init__.py` — empty
- `core/luana-core-extension-sdk/tests/unit/__init__.py` — empty
- `core/luana-core-extension-sdk/tests/architecture/__init__.py` — empty

## Implementation

Per 06-tickets.yaml T-2 description + 05-guidelines.md §1.3 verbatim:

1. `mkdir -p core/luana-core-extension-sdk/{src/luana_core_extension_sdk,tests/{unit,architecture}}`
2. Wrote `pyproject.toml` with `version = "0.0.8-alpha"`, `dependencies = []` (ZERO workspace deps — pure contract layer), hatchling build system, pytest asyncio_mode = "auto"
3. Wrote `README.md` stub per 06-tickets.yaml verbatim (18 EP overview)
4. Wrote `src/luana_core_extension_sdk/__init__.py` empty (T-3..T-7 populate)
5. Wrote test `__init__.py` files
6. Ran `uv sync --package luana-core-extension-sdk` — PASSES (package builds and installs)

## Validators Run

- V-NF-2: `grep -q 'version = "0.0.8-alpha"'` → PASS
- V-D-1: package skeleton created with correct DDD structure → PASS

## Deviations

None. uv installs luana-core-extension-sdk==0.0.8a0 successfully.

Note: uv normalizes `0.0.8-alpha` to `0.0.8a0` in the lock file (PEP 440 canonical form). pyproject.toml retains `version = "0.0.8-alpha"` per spec. Grep validators against pyproject.toml will pass.
