# E2E Playwright GitHub Actions Workflow — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a dedicated GitHub Actions workflow for Playwright E2E tests, triggerable from Claude Code via `gh workflow run`, so regression testing runs in GitHub (not locally) before production deploys. Also update `/pase-produccion` skill to integrate it and save memory about local Playwright constraints.

**Architecture:** A standalone `e2e-tests.yml` workflow with `workflow_dispatch` trigger and suite-type input (smoke/regression/full). Reuses the exact same Docker Compose e2e infrastructure as `deploy-prod.yml` but without lint, pytest, tsc, security scan, or deploy jobs. Claude Code triggers it with `gh workflow run` and monitors with `gh run watch`.

**Tech Stack:** GitHub Actions, Docker Compose, Playwright, Clerk testing tokens

---

## File Structure

| File | Purpose |
|---|---|
| `.github/workflows/e2e-tests.yml` | New workflow — Playwright only, `workflow_dispatch` |
| `.claude/skills/pase-produccion/SKILL.md` | Update — add E2E GitHub step before push |
| `.claude/projects/-home-chris-AISALESHT/memory/feedback_playwright_local.md` | New — laptop can't run Playwright Docker |
| `.claude/projects/-home-chris-AISALESHT/memory/MEMORY.md` | Update — add pointer to new memory |

---

### Task 1: Create the E2E GitHub Actions Workflow

**Files:**
- Create: `.github/workflows/e2e-tests.yml`

- [ ] **Step 1: Write the workflow file**

```yaml
name: 🎭 E2E Playwright Tests

on:
  workflow_dispatch:
    inputs:
      suite:
        description: 'Test suite to run'
        required: true
        default: 'smoke'
        type: choice
        options:
          - smoke
          - regression
          - full
      branch:
        description: 'Branch to test (default: triggering branch)'
        required: false
        type: string

jobs:
  e2e:
    name: 🎭 Playwright (${{ inputs.suite }})
    runs-on: ubuntu-latest
    environment: ap_sales_agent
    timeout-minutes: 20

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          ref: ${{ inputs.branch || github.ref }}

      - name: Free disk space (~25 GB)
        uses: jlumbroso/free-disk-space@v1.3.1
        with:
          tool-cache: false
          android: true
          dotnet: true
          haskell: true
          large-packages: true
          docker-images: true
          swap-storage: false

      - uses: docker/setup-buildx-action@v3

      - name: Create .env for docker compose
        env:
          NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: ${{ secrets.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY }}
          NEXT_PUBLIC_API_URL: http://api_dev:8000
          NEXT_PUBLIC_APP_URL: http://localhost:3000
          INTERNAL_API_URL: http://api_dev:8000
          CLERK_SECRET_KEY: ${{ secrets.CLERK_SECRET_KEY }}
          E2E_CLERK_USER_EMAIL: ${{ secrets.E2E_CLERK_USER_EMAIL }}
          E2E_CLERK_USER_USERNAME: ${{ secrets.E2E_CLERK_USER_EMAIL }}
          E2E_CLERK_USER_PASSWORD: ${{ secrets.E2E_CLERK_USER_PASSWORD }}
          E2E_TENANT_ID: ${{ secrets.E2E_TENANT_ID }}
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: visionarias_test
          TRAEFIK_NETWORK: gateway
        run: |
          env | grep -E '^(NEXT_PUBLIC_|CLERK_|INTERNAL_|E2E_|POSTGRES_|TRAEFIK_|SHOPIFY_)' > .env
          echo "API_DOMAIN=localhost" >> .env
          echo "DASHBOARD_DOMAIN=http://localhost:3000" >> .env
          echo "CLOUDFLARE_TUNNEL_TOKEN=disabled" >> .env
          echo "SHOPIFY_API_KEY=disabled" >> .env
          echo "SHOPIFY_API_SECRET=disabled" >> .env
          echo "SHOPIFY_APP_URL=http://localhost:8000" >> .env
          echo "LOG_LEVEL=WARNING" >> .env
          echo "DOMAIN_NAME=localhost" >> .env
          echo "API_SECRET_KEY=e2e-test-secret-key-not-real" >> .env
          echo "WHATSAPP_API_TOKEN=disabled" >> .env
          echo "WHATSAPP_PHONE_NUMBER_ID=disabled" >> .env
          echo "WHATSAPP_VERIFY_TOKEN=disabled" >> .env
          echo "OPENAI_API_KEY=sk-disabled-for-e2e" >> .env
          echo "REDIS_URL=redis://redis:6379/0" >> .env
          echo "QDRANT_URL=http://qdrant:6333" >> .env
          echo "POSTGRES_HOST=postgres" >> .env
          echo "POSTGRES_PORT=5432" >> .env
          echo "API_URL=http://api_dev:8000" >> .env

      - name: Generate Clerk testing token
        env:
          CLERK_SECRET_KEY: ${{ secrets.CLERK_SECRET_KEY }}
        run: |
          TOKEN=$(curl -s -X POST "https://api.clerk.com/v1/testing_tokens" \
            -H "Authorization: Bearer $CLERK_SECRET_KEY" \
            | python3 -c "import sys,json;print(json.load(sys.stdin).get('token',''))")
          echo "CLERK_TESTING_TOKEN=$TOKEN" >> .env

      - name: Start services
        run: |
          docker network create gateway || true
          docker compose up -d --build postgres redis qdrant api_dev client_dashboard_dev
          echo "--- Disk usage after build ---"
          df -h / | tail -1
          echo "Waiting for Next.js to be healthy..."
          for i in $(seq 1 30); do
            if docker exec visionarias_client_dev wget -q --spider http://localhost:3000 2>/dev/null; then
              echo "Next.js ready after $((i*10))s"
              break
            fi
            sleep 10
          done

      - name: Run migrations
        run: docker exec visionarias_brain_dev bash -c "cd /app && alembic upgrade head"

      - name: Seed E2E tenant
        env:
          E2E_TENANT_ID: ${{ secrets.E2E_TENANT_ID }}
        run: |
          docker exec visionarias_postgres psql -U postgres -d visionarias_test -c "
            INSERT INTO tenants (id, name, slug, is_active, default_currency, timezone)
            VALUES ('$E2E_TENANT_ID', 'E2E Test Tenant', 'e2e-test', true, 'USD', 'UTC')
            ON CONFLICT (id) DO NOTHING;
          "

      - name: Resolve Playwright grep filter
        id: filter
        run: |
          case "${{ inputs.suite }}" in
            smoke)      echo "args=--grep @smoke --project=smoke" >> $GITHUB_OUTPUT ;;
            regression) echo "args=--project=regression" >> $GITHUB_OUTPUT ;;
            full)       echo "args=" >> $GITHUB_OUTPUT ;;
          esac

      - name: Run Playwright tests (${{ inputs.suite }})
        run: |
          docker compose --profile e2e run --rm e2e_runner \
            npx playwright test ${{ steps.filter.outputs.args }}

      - name: Cleanup
        if: always()
        run: docker compose --profile e2e down -v 2>/dev/null || true

      - name: Upload Playwright report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report-${{ inputs.suite }}
          path: |
            frontend/playwright-report/
            frontend/test-results/
          retention-days: 7
```

- [ ] **Step 2: Verify the file is valid YAML**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/e2e-tests.yml'))" && echo "VALID"`
Expected: `VALID`

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/e2e-tests.yml
git commit -m "ci(e2e): add dedicated Playwright workflow with workflow_dispatch

Standalone E2E workflow triggered via gh workflow run. Supports
smoke/regression/full suite selection. No lint/test/deploy — only
Playwright. Designed to run from Claude Code before production deploys."
```

---

### Task 2: Update `/pase-produccion` Skill

**Files:**
- Modify: `.claude/skills/pase-produccion/SKILL.md`

The key change: between Fase 2 (merge) and Fase 3 (local /test-all), insert a new phase that triggers the E2E workflow on GitHub and waits for it to pass. Also adjust Fase 3 to note that E2E smoke is now handled by GitHub (not locally).

- [ ] **Step 1: Add Fase 2.5 — E2E Regression on GitHub**

In `.claude/skills/pase-produccion/SKILL.md`, after the `## Fase 2` section (after line 69 `**NO pushear todavía.** Primero pasar las pruebas.`), insert:

```markdown
---

## Fase 2.5: E2E Regression en GitHub Actions

**Objetivo:** Correr la suite completa de Playwright en GitHub antes de pushear a main.
La laptop del usuario no soporta el contenedor Docker de Playwright, así que SIEMPRE
usar GitHub Actions para E2E.

### 2.5.1 Pushear development para que GitHub tenga el código actual
```bash
git checkout development
git push origin development
```

### 2.5.2 Disparar el workflow de E2E
```bash
gh workflow run "e2e-tests.yml" --ref development -f suite=regression
```

### 2.5.3 Monitorear el resultado
```bash
# Esperar ~5s para que el run se registre, luego:
sleep 5
RUN_ID=$(gh run list --workflow=e2e-tests.yml --limit 1 --json databaseId --jq '.[0].databaseId')
gh run watch $RUN_ID
```

### 2.5.4 Resultados posibles:

**SUCCESS:** Continuar con Fase 3 (verificación local lint+tests).

**FAILURE:**
1. Obtener logs: `gh run view $RUN_ID --log-failed`
2. Corregir en `development`, commitear, pushear
3. Re-disparar: `gh workflow run "e2e-tests.yml" --ref development -f suite=regression`
4. Máximo 3 intentos. Si falla 3 veces → reportar al usuario y pedir dirección.

**NOTA:** Si el usuario pide "pase rápido" o indica urgencia, se puede usar `suite=smoke`
en lugar de `regression` para acelerar.
```

- [ ] **Step 2: Adjust Fase 3 to exclude local E2E**

In `.claude/skills/pase-produccion/SKILL.md`, in the Fase 3 section, modify the list to note that E2E is handled by GitHub:

Change lines 78-82 from:
```markdown
1. Backend lint (ruff)
2. Backend tests + coverage (pytest)
3. Frontend types (tsc)
4. Frontend lint (ESLint)
5. Frontend tests + coverage (vitest)
6. E2E Smoke (Playwright)
7. Migration verification (fresh DB)
```

To:
```markdown
1. Backend lint (ruff)
2. Backend tests + coverage (pytest)
3. Frontend types (tsc)
4. Frontend lint (ESLint)
5. Frontend tests + coverage (vitest)
6. ~~E2E Smoke (Playwright)~~ — handled by Fase 2.5 on GitHub Actions
7. Migration verification (fresh DB)
```

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/pase-produccion/SKILL.md
git commit -m "chore(skills): integrate GitHub E2E into pase-produccion pipeline

Add Fase 2.5: trigger e2e-tests.yml on GitHub before local verification.
Remove local E2E from Fase 3 — laptop can't run Playwright Docker."
```

---

### Task 3: Save Feedback Memory

**Files:**
- Create: `/home/chris/.claude/projects/-home-chris-AISALESHT/memory/feedback_playwright_local.md`
- Modify: `/home/chris/.claude/projects/-home-chris-AISALESHT/memory/MEMORY.md`

- [ ] **Step 1: Write the feedback memory file**

Create `/home/chris/.claude/projects/-home-chris-AISALESHT/memory/feedback_playwright_local.md`:

```markdown
---
name: Playwright runs on GitHub, not local
description: User's laptop crashes running Playwright Docker container. Always use GitHub Actions for E2E tests. Native Playwright (no Docker) only for single-test visual checks.
type: feedback
---

NEVER run Playwright via Docker locally (`make e2e-smoke`, `make e2e`). The user's laptop crashes due to insufficient resources (the e2e_runner container requires 2GB RAM + 2 CPUs + 2GB shm).

**Why:** User's WSL environment doesn't have enough resources for the Playwright Docker container. Multiple crashes confirmed.

**How to apply:**
- For E2E regression before production: trigger `gh workflow run e2e-tests.yml --ref development -f suite=regression` and monitor with `gh run watch`
- For quick functional checks: use native Playwright in WSL (`cd frontend && npx playwright test --grep "specific test" --project=smoke`) — lighter than Docker but still resource-intensive, use sparingly
- For visual verification (screenshots): native Playwright with single test + screenshot, then read the image file
- NEVER suggest `make e2e-smoke` or `make e2e` — it will crash the machine
- The `/pase-produccion` skill has Fase 2.5 that handles this automatically
```

- [ ] **Step 2: Update MEMORY.md index**

Add a pointer in the Feedback section of `/home/chris/.claude/projects/-home-chris-AISALESHT/memory/MEMORY.md`:

```markdown
- [feedback_playwright_local.md](feedback_playwright_local.md) - NEVER run Playwright Docker locally (laptop crashes). Use GitHub Actions workflow `e2e-tests.yml` for all E2E. Native Playwright only for single visual checks.
```

- [ ] **Step 3: No commit needed** (memory files are outside the repo)

---

### Task 4: Push & Verify Workflow Registration

- [ ] **Step 1: Push development to register the workflow with GitHub**

```bash
git push origin development
```

- [ ] **Step 2: Verify the workflow is visible**

```bash
gh workflow list | grep -i e2e
```

Expected output includes: `🎭 E2E Playwright Tests` with status `active`

- [ ] **Step 3: Do a dry-run trigger (smoke, fast)**

```bash
gh workflow run "e2e-tests.yml" --ref development -f suite=smoke
sleep 5
RUN_ID=$(gh run list --workflow=e2e-tests.yml --limit 1 --json databaseId --jq '.[0].databaseId')
echo "Triggered run: $RUN_ID"
gh run watch $RUN_ID
```

Expected: The workflow starts, runs smoke tests, completes (pass or fail — we're verifying infrastructure, not test correctness).

- [ ] **Step 4: Download report artifact (if needed)**

```bash
gh run download $RUN_ID --name playwright-report-smoke --dir /tmp/playwright-report
```

---

## Summary of Changes

| What | Where | Why |
|---|---|---|
| New workflow `e2e-tests.yml` | `.github/workflows/` | Dedicated E2E runner, no lint/deploy overhead, `workflow_dispatch` for on-demand |
| Updated pase-produccion skill | `.claude/skills/pase-produccion/` | Fase 2.5 triggers E2E on GitHub before local verification |
| New feedback memory | `memory/feedback_playwright_local.md` | Prevents future Claude sessions from attempting local Playwright Docker |

## Estimated GitHub Actions Usage

| Suite | Estimated Time | When to Use |
|---|---|---|
| `smoke` | ~8-10 min | Quick pre-merge check |
| `regression` | ~12-15 min | Before production deploy |
| `full` | ~15-20 min | Major releases, post-refactor |

At ~10 min per run, 2-3 runs/day = ~600-900 min/month — well within Free tier (2,000 min).
