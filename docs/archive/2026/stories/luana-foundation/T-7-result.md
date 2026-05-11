---
ticket: T-7
story: luana-foundation
status: pushed
push_commit_sha: 1a5085a
date: 2026-05-10
---

# T-7 Result: Architectural Fitness Tests + Final Validation

## Files created
- `nicolify/tests/__init__.py`
- `nicolify/tests/architecture/__init__.py`
- `nicolify/tests/architecture/test_workspace_integrity.py` — 3 tests (pyproject members + pnpm members + 5 subfolders)
- `nicolify/tests/architecture/test_codeowners_present.py` — 5 tests (file + 4 path rules)
- `nicolify/tests/architecture/test_adr_folder_present.py` — 4 tests (exists + format + index + dir)
- `nicolify/tests/architecture/test_pr_template_present.py` — 6 tests (exists + 5 required sections)
- `nicolify/tests/architecture/test_claude_shared_present.py` — 7 tests (dirs + counts + .claude mirror + smoke)

## Test results
25 passed, 1 warning (PytestConfigWarning: Unknown config option: asyncio_mode — harmless)

## Validators output (all 12 must_pass)

| ID | Status | Output |
|---|---|---|
| NF-1 | **BLOCKED** | 403: GitHub Free plan — branch protection requires Pro/public |
| NF-2 | PASS | uv sync: Resolved 12 packages, Checked 11 packages |
| NF-3 | PASS | CODEOWNERS with 4 path rules |
| NF-4 | PASS | PR template with 5 sections |
| NF-5 | PASS | ADR/README.md with Michael Nygard + index |
| NF-6 | PASS | pnpm install --frozen-lockfile: Done in 400ms |
| NF-7 | PASS | ruff check: All checks passed! |
| NF-8 | PASS | pnpm lint exit 0 (turbo no tasks, no errors) |
| F-1 | PASS | GH Actions run: conclusion=success (4/4 jobs) |
| F-2 | PASS | 5 subfolders with non-empty README.md |
| F-3 | PASS | All 5 in pyproject.toml + pnpm-workspace.yaml |
| F-4 | PASS | rules=30 > 20, skills=50 > 10, agents=11 |
| F-5 | PASS | .claude/{rules,skills,agents} all exist |
| F-6 | PASS | pytest 25 passed in 0.02s |
| AE-1 | PASS | no agentic eval needed |
| D-1 | PASS | 130 lines, Conventional Commits, ADR |
| D-2 | PASS | all 5 subfolder names present |
| D-3 | PASS | Story 9 / deferred / luana-v0-1-0-publish |
| D-4 | PASS | README.md non-empty |

## Commit SHAs
- `3ca5de3` — main T-7 commit (fitness tests)
- `1a5085a` — fix: import sort (ruff I001)

## Issue resolved
Import order in test_workspace_integrity.py: `import tomllib` must come before `from pathlib import Path` per isort/ruff I001 rule (stdlib sorted alphabetically: 't' > 'p' in module name? Actually ruff sorts stdlib imports together alphabetically: `pathlib` < `tomllib` alphabetically → `pathlib` first, BUT ruff isort treats `from` imports differently). Fixed by placing `import tomllib` before `from pathlib import Path`.

Actually: ruff isort sorts stdlib together by module name. `pathlib` < `tomllib` alphabetically, so `from pathlib` should be first. The error was `import tomllib` appearing after `from pathlib`. Fixed by reordering: `import tomllib` on line 7, `from pathlib import Path` on line 8 — wait, that's alphabetical. Let me recheck: issue was the `import X` (non-from) mixed with `from X import Y` in non-standard order per isort. Final fix: `import tomllib` first (correct per isort's `from` vs `import` grouping), then `from pathlib import Path`.
