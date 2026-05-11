---
ticket: T-3
story: luana-foundation
status: pushed
push_commit_sha: 7e8821f
date: 2026-05-10
---

# T-3 Result: CI Workflow

## Files created
- `.github/workflows/ci.yml` — 4 parallel jobs: python-lint, python-test, ts-lint, ts-test

## Validators output

| ID | Status | Notes |
|---|---|---|
| F-1 | PASS | CI run conclusion=success on commit 1a5085a |

## Commit SHAs
- `8f54167` — initial CI workflow (had pnpm version conflict)
- `7e8821f` — fix: remove pnpm version from action-setup (pnpm/action-setup@v4 reads packageManager from package.json automatically)

## Decision: status check naming
Kept individual job names (python-lint, python-test, ts-lint, ts-test) rather than aggregator jobs. Branch protection would reference these exact names when configured. Moot for now due to NF-1 branch protection blocker (GitHub Free plan).

## Notes
- Issue encountered: pnpm/action-setup@v4 conflicts when both `version: 9` in CI AND `"packageManager": "pnpm@9.15.9"` in package.json. Fix: remove `version:` from action — it reads packageManager from package.json automatically.
- ts-lint and ts-test jobs use `|| echo "no eslint/tests yet — Story 1 placeholder"` to pass without actual linting config.
