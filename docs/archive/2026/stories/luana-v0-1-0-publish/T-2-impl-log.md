# T-2 Impl Log — Release Infrastructure

**Ticket:** T-2 — Release infra: release-please-config, manifest, release.yml, commitlint
**Status:** DONE
**Date:** 2026-05-12
**Repo:** `/home/chris/luana-platform/`

## Summary

Created the release automation infrastructure for v0.1.0.

### Files created

**`/home/chris/luana-platform/release-please-config.json`**
- 33 packages: 25 `core/luana-core-*` (release-type: python) + `apps/test-brand` (release-type: python) + 7 `core/@luana/*` (release-type: node)
- `linked-versions` plugin for monorepo coherence (all packages bump together)
- `bootstrap-sha` pointing to initial commit
- `bump-minor-pre-major: true` for pre-1.0 minor bumps

**`/home/chris/luana-platform/.release-please-manifest.json`**
- All 33 entries seeded at `"0.1.0"`
- Serves as baseline for release-please to detect next version increment

**`/home/chris/luana-platform/.github/workflows/release.yml`**
- Trigger: `on.push.tags: ['v*.*.*']`
- 7 jobs:
  1. `validate-tag` — confirm tag format + extract version
  2. `build-python` — uv build for all 26 Python packages
  3. `build-typescript` — pnpm build + typecheck all 7 TS packages
  4. `publish-python` — uv publish to `https://pypi.pkg.github.com/alpacapurpura/`
  5. `publish-typescript` — pnpm publish -r to `https://npm.pkg.github.com/`
  6. `create-github-release` — gh release create with CHANGELOG diff
  7. `smoke-test-published` — install + verify packages from GH Packages
- Atomicity: `publish-typescript.needs: [validate-tag, build-typescript, publish-python]`
- Auth: `${{ secrets.GH_PACKAGES_TOKEN || secrets.GITHUB_TOKEN }}`
- All build/publish jobs have `timeout-minutes` set

**`/home/chris/luana-platform/commitlint.config.cjs`**
- Conventional Commits enforced: feat/fix/refactor/docs/test/chore/perf/ci
- Scoped to luana-platform workspace

### Issues resolved

**33 vs 32 packages**: Initial config had 32 (omitting `apps/test-brand`). Added as 33rd package to satisfy V-F-release-1 which requires exactly 33.

## Validator coverage

- V-F-release-1: release-please-config.json + manifest present, 33 packages ✅
- V-F-release-2: release.yml valid YAML, 6 required jobs ✅
- V-F-release-3: release.yml triggers on v*.*.* tag push ✅
- V-F-release-4: publish-typescript depends on publish-python (atomicity) ✅
- V-NF-4: GH_PACKAGES_TOKEN documented ✅

## Commit

SHA: contained in T-2 commit to luana-platform `main`.
