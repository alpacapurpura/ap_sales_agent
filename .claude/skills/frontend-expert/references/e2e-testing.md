---
globs: "frontend/e2e/**/*.{ts,tsx}"
description: DEPRECATED — see playwright-expert skill (SSoT moved 2026-05-04)
---

# E2E Testing (DEPRECATED)

**This file is now a stub.** The full E2E testing SSoT moved to its own dedicated skill on 2026-05-04 because:
- E2E knowledge had outgrown a single reference file
- Adding more smoke tests required deeper Clerk auth + POM + mocks + CI guidance
- Skill triggering is more reliable than reference loading from `frontend-expert`

## Where to look now

Invoke the **`playwright-expert`** skill. It auto-loads on any of:
- "smoke test", "e2e", "playwright", "tests E2E", "agreguemos un smoke", "el smoke falla"
- File touches in `frontend/e2e/**`, `playwright.config.ts`, `.github/workflows/e2e-tests.yml`
- Errors like "Bot traffic detected", "Clerk Frontend API URL is required", auth expired

## Skill structure

```
.claude/skills/playwright-expert/
├── SKILL.md                              ← entrypoint, decision tree, daily commands
└── references/
    ├── architecture.md                   ← projects, fixtures, env flow, freshness gate
    ├── clerk-auth-deep-dive.md           ← testing token, cf_bm, retry, sanity check, multi-worker
    ├── adding-smoke-test.md              ← step-by-step recipe (the most common task)
    ├── pom-patterns.md                   ← locator priority, POM anatomy, common recipes
    ├── fixtures-and-mocks.md             ← auth.fixture, page.route, growth-studio mocks, SSE
    ├── ci-and-flaky-tests.md             ← CI workflow, sharding, trace viewer, flake hunting
    └── anti-patterns.md                  ← every mistake we've made, with WHY and FIX
```

## Quick reference (kept here for cross-link compatibility)

```bash
bash /home/chris/AISALESHT/scripts/e2e-preflight.sh    # always first
cd frontend && npm run test:e2e:smoke                  # happy path
cd frontend && npm run test:e2e:fresh                  # auth roto / "siempre falla"
cd frontend && npm run test:e2e:auth                   # solo regenerar storageState
```

NEVER `make e2e*` (Docker, crashea WSL2). Always native.

For everything else → `playwright-expert` skill.
