# T-1 Impl Log — Cross-Package Version Bumps

**Ticket:** T-1 — Version bumps all 33 packages to 0.1.0 (no -alpha)
**Status:** DONE
**Date:** 2026-05-12
**Repo:** `/home/chris/luana-platform/`

## Summary

Bumped all 33 packages from pre-release (`0.0.1-alpha` / `0.1.0-alpha` / `0.1.0-alpha.1`) to `0.1.0`.

### Packages bumped

**26 Python pyproject.toml** (`core/luana-core-*/pyproject.toml` + `apps/test-brand/pyproject.toml`):
- Used `sed -i 's/^version = ".*"/version = "0.1.0"/' <path>` per package

**4 brand stub pyproject.toml** (`nicolify/`, `vitalia/`, `comunify/`, `lupulo/`):
- Same `sed` pattern

**Root `core/pyproject.toml`** — bumped to `0.1.0`

**7 TypeScript `@luana/*` package.json** (`core/@luana/{api-client,core,design-tokens,extension-sdk,format,hooks,schemas}/package.json`):
- `pnpm -r --filter '@luana/*' exec npm version 0.1.0 --no-git-tag-version`

**4 brand stub package.json** (`nicolify/`, `vitalia/`, `comunify/`, `lupulo/`):
- Used `python3 -c "import json; ..."` (jq not installed in environment)

**Root `package.json`** — bumped with `npm version 0.1.0 --no-git-tag-version`

### Issues resolved

1. **jq not available** — Used `python3 -c "import json, sys; ..."` for JSON file edits
2. **.tmp files staged** — Failed early jq attempts left `*.tmp` files; cleaned with `rm -f *.tmp` and `git rm --cached`
3. **`core/package.json` missed** — Alpha grep revealed 1 remaining; fixed with explicit python3 json update
4. **alpha grep verification** — Confirmed 0 alpha suffix remaining in all pyproject.toml + package.json files

## Validator coverage

- V-NF-2: all 26 Python + test-brand + brand stubs pyproject at 0.1.0 ✅
- V-NF-3: all 7 @luana/* + brand stubs + root package.json at 0.1.0 ✅
- V-NF-6: root package.json at 0.1.0 ✅
- V-NF-7: no -alpha suffix anywhere ✅

## Commit

Included in batch with T-2 release infra (same luana-platform commit series).
