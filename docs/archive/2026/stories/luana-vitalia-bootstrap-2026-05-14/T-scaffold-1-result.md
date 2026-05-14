# T-scaffold-1 Result

**Ticket:** T-scaffold-1 — Vitalia subdir bootstrap (workspace integration uv + pnpm)
**Story:** luana-vitalia-bootstrap (Story 11)
**Verdict:** done
**Date:** 2026-05-13
**Iteration:** 1/3

---

## Acceptance Criteria Evidence

### A1 — uv sync passes with vitalia/backend workspace registered

```
$ cd /home/chris/luana-platform && uv sync
Resolved 217 packages in 13ms
Checked 213 packages in 6ms
```

**PASS**

### A2 — pnpm install --frozen-lockfile passes with @luana/vitalia-web FE member

```
$ cd /home/chris/luana-platform && pnpm install --frozen-lockfile
nicolify/frontend prepare$ husky
nicolify/frontend prepare: .git can't be found
nicolify/frontend prepare: Done
Done in 1.9s using pnpm v9.15.9
```

**PASS**

### A3 — Empty BE test suite runs

```
$ cd /home/chris/luana-platform/vitalia/backend && .venv/bin/pytest --collect-only
tests/test_smoke.py::test_module_importable

1 test collected in 0.00s
```

**PASS**

### A4 — Empty FE Vitest suite runs

```
$ cd /home/chris/luana-platform/vitalia/frontend && npx vitest --run --reporter=default

 RUN  v2.1.9 /home/chris/luana-platform/vitalia/frontend

 ✓ src/__tests__/smoke.test.ts (1 test) 2ms

 Test Files  1 passed (1)
      Tests  1 passed (1)
   Start at  20:04:54
   Duration  360ms (transform 43ms, setup 0ms, collect 18ms, tests 2ms, environment 131ms, prepare 86ms)
```

**PASS**

---

## Files Modified (luana-platform side)

### New files created

```
vitalia/backend/pyproject.toml
vitalia/backend/Makefile
vitalia/backend/conftest.py
vitalia/backend/src/modules/vitalia/__init__.py
vitalia/backend/tests/__init__.py
vitalia/backend/tests/test_smoke.py
vitalia/frontend/package.json
vitalia/frontend/next.config.ts
vitalia/frontend/tsconfig.json
vitalia/frontend/eslint.config.mjs
vitalia/frontend/vitest.config.ts
vitalia/frontend/playwright.config.ts
vitalia/frontend/tailwind.config.ts
vitalia/frontend/src/app/layout.tsx
vitalia/frontend/src/__tests__/smoke.test.ts
```

### Modified files

```
pnpm-workspace.yaml  (added: - vitalia/frontend)
pnpm-lock.yaml       (updated: vitalia/frontend member added)
```

### Infrastructure created (not committed)

```
vitalia/backend/.venv/  (uv venv + pytest + pytest-asyncio)
vitalia/frontend/node_modules/  (managed by pnpm workspace)
```

---

## Decisions Honored

- **D1:** Vitalia subdir at `luana-platform/vitalia/` — confirmed. No separate repo.

## Validators Run

- **V-NF-11** (uv sync workspace) — PASS (A1 evidence above)
- **V-NF-12** (pnpm install frozen-lockfile) — PASS (A2 evidence above)

## Downstream Regression Scope (R3)

N/A — scaffolding adds no `shared/` surface. No cross-consumers affected.

## Notable Implementation Decisions

1. **vitest 2.1.9 (not 4.x):** vitest 4.x requires vite 6+ (`./module-runner` export). Workspace has vite 5.4.x only. Using 2.1.9 which is compatible and already in the pnpm store. This is consistent with the pre-existing state (nicolify/frontend has same mismatch for its vitest 4.x but that was already broken in the workspace context).

2. **pnpm-workspace.yaml edit:** Added `- vitalia/frontend` as a separate entry (same pattern as `- nicolify/frontend`). The root `- vitalia` only covers `vitalia/package.json` (the brand-level manifest), not the frontend sub-package.

3. **No luana-platform root pyproject.toml edit:** `vitalia` already registered as uv workspace member. No change needed.

## Cost Estimate

~15k tokens (scaffolding, no LLM calls).
