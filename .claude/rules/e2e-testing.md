---
globs: "frontend/e2e/**/*.{ts,tsx}"
description: Stub — detalle en frontend-expert references
---

# E2E Testing

Cuándo: nueva UI feature, bug fix interaction, nav/auth flow change. NO: BE-only, styling-only, utils.

**Preflight obligatorio antes correr:**
```bash
cd /home/chris/AISALESHT && bash scripts/e2e-preflight.sh
```

Execution **NATIVE WSL** (NUNCA Docker — `make e2e*` crashea):
```bash
cd frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke
```

Detalle (Clerk auth setup, structure POMs, multi-tenant, mocks Growth Studio, smoke vs regression, troubleshooting FE 500) en `frontend-expert` skill → `references/e2e-testing.md`.

**Prohibido:** `make e2e`/`make e2e-smoke` (Docker, crashea). Spawn webServer dentro Playwright (siempre `E2E_BASE_URL`).
