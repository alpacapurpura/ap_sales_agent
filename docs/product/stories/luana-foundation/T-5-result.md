---
ticket: T-5
story: luana-foundation
status: pushed
push_commit_sha: e106bde
date: 2026-05-10
---

# T-5 Result: 5 Workspace Subfolders

## Files created
For each of core, nicolify, vitalia, comunify, lupulo:
- `{sub}/README.md` — purpose + scope (5-12 lines)
- `{sub}/pyproject.toml` — minimal workspace member (hatchling, src layout)
- `{sub}/package.json` — @luana/{sub}, private
- `{sub}/src/__init__.py` — empty placeholder (required by hatchling)

## Validators output

| ID | Status | Notes |
|---|---|---|
| NF-2 | PASS | uv sync resolves and installs all 5 packages |
| NF-7 | PASS | ruff check passes on all 5 subfolders |
| F-2 | PASS | All 5 dirs exist with non-empty README.md |
| F-3 | PASS | All 5 members in pyproject.toml + pnpm-workspace.yaml |

## Commit SHA
e106bde — pushed to `main`

## Issue resolved
hatchling build backend requires a `packages = ["src"]` specification in `[tool.hatch.build.targets.wheel]` when no Python package directory matching the project name exists. Added `src/` layout with empty `__init__.py` to each subfolder. Also added `ruff` as dev dependency to root pyproject.toml (needed for NF-7 validator).
