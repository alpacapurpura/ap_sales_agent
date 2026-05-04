---
globs: "frontend/e2e/**/*.{ts,tsx}"
description: Stub — full E2E SSoT lives in playwright-expert skill
---

# E2E Testing

**SSoT skill: `playwright-expert`** (auto-loads on any e2e/playwright/smoke trigger). Carga el skill ANTES de tocar `frontend/e2e/**` o `playwright.config.ts` o `.github/workflows/e2e-tests.yml`.

Cuándo: nueva UI feature, bug fix interaction, nav/auth flow change. NO: BE-only, styling-only, utils.

**Preflight obligatorio antes correr:**
```bash
cd /home/chris/AISALESHT && bash scripts/e2e-preflight.sh
```

**Execution NATIVE WSL** (NUNCA Docker — `make e2e*` crashea WSL2 OOM):
```bash
cd frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke
# o más fácil:
cd frontend && npm run test:e2e:smoke
# auth roto / siempre falla:
cd frontend && npm run test:e2e:fresh
```

Detalle (Clerk auth lifecycle deep-dive, freshness gate, retry+sanity, POMs, fixtures+mocks, CI+flaky debugging, anti-patterns) en `playwright-expert` skill → `references/{architecture,clerk-auth-deep-dive,adding-smoke-test,pom-patterns,fixtures-and-mocks,ci-and-flaky-tests,anti-patterns}.md`.

**Prohibido:** `make e2e`/`make e2e-smoke` (Docker, crashea). Spawn webServer dentro Playwright (siempre `E2E_BASE_URL`). Importar `test` de `@playwright/test` directo en specs autenticados (usar `auth.fixture`). Locators CSS/XPath. `test.skip` permanente. Editar `playwright/.clerk/user.json` manualmente.
