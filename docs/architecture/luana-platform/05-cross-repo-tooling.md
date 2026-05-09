<!-- voseo-allowed: internal devops playbook + commands reference, Chris-targeted, not user-facing UI -->

# 05 — Cross-Repo Tooling + Sunday Playbook

> **Status:** Draft v0.1 — 2026-05-09
> **Purpose:** comandos exactos copy-paste para bootstrap GitHub Org + 5 repos + CI baseline + `.claude-shared/` subtree. Sunday playbook embebido §6.

## 1. Pre-requisitos

Antes de ejecutar comandos:

```bash
# Verificar gh CLI logueado a tu cuenta GitHub
gh auth status

# Si no:
gh auth login   # interactivo, elegí HTTPS + browser auth

# Verificar git config
git config --global user.name        # debe estar
git config --global user.email       # alpacapurpura@... o tu email GitHub

# Verificar permisos org creation (necesitás cuenta GitHub Pro $4/user/mo o gratis si solo tu)
gh api /user | jq .plan
```

## 2. Crear GitHub Org

```bash
# Org creation NO se puede vía gh CLI — requiere browser
# Andá a:
open "https://github.com/account/organizations/new"

# Datos:
# Org name: luana-platform
# Plan: Free (cambias a Team $4/user/mo después si necesitás más Actions minutes)
# Email: alpacapurpura@... (tuyo)
```

## 3. Crear 5 repos privados

```bash
ORG="luana-platform"

# Crear los 5 repos (gh CLI funciona post org creada)
gh repo create $ORG/luana-core --private --description "Luana Core — shared SSoT for multi-brand vertical SaaS"
gh repo create $ORG/nicolify --private --description "Nicolify — SaaS marketing/sales (canonical horizontal brand)"
gh repo create $ORG/vitalia --private --description "Vitalia — medical/dental/wellness clinics vertical"
gh repo create $ORG/comunify --private --description "Comunify — creator/expert economy vertical"
gh repo create $ORG/lupulo-labs --private --description "Lupulo Labs — gastronomy agentic vertical"

# Verificar:
gh repo list $ORG
```

## 4. Branch protection (post-clone)

```bash
ORG="luana-platform"

for REPO in luana-core nicolify vitalia comunify lupulo-labs; do
  gh api -X PUT \
    "repos/$ORG/$REPO/branches/main/protection" \
    -f required_status_checks='{"strict":true,"contexts":["lint","test"]}' \
    -f enforce_admins=false \
    -f required_pull_request_reviews='{"required_approving_review_count":0}' \
    -f restrictions=null
  echo "Protected: $ORG/$REPO main"
done
```

> Nota: `required_approving_review_count:0` = solo vos owner, no necesitás review humana extra. Cambiá a `1` cuando contrates devs.

## 5. `luana-core` repo skeleton

```bash
mkdir -p ~/luana-platform && cd ~/luana-platform
gh repo clone luana-platform/luana-core
cd luana-core

# Estructura monorepo
mkdir -p packages/{python,ts}
mkdir -p .claude-shared/{rules,skills,agents}
mkdir -p .github/workflows
mkdir -p docs/{architecture,product,api}
mkdir -p scripts
```

**`pyproject.toml` workspace root:**

```toml
[tool.uv.workspace]
members = ["packages/python/*"]

[project]
name = "luana-core-workspace"
version = "0.0.0"
description = "Luana Core — Python workspace root"
requires-python = ">=3.12"

[tool.ruff]
line-length = 120
target-version = "py312"

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

**`package.json` workspace root:**

```json
{
  "name": "@luana/workspace",
  "private": true,
  "version": "0.0.0",
  "workspaces": ["packages/ts/*"],
  "scripts": {
    "build": "turbo build",
    "test": "turbo test",
    "lint": "turbo lint",
    "publish-packages": "turbo publish"
  },
  "devDependencies": {
    "turbo": "^2.3.0",
    "typescript": "^5.7.0"
  },
  "packageManager": "pnpm@9.15.0"
}
```

**`turbo.json`:**

```json
{
  "$schema": "https://turbo.build/schema.json",
  "tasks": {
    "build": { "dependsOn": ["^build"], "outputs": ["dist/**"] },
    "test": { "dependsOn": ["build"] },
    "lint": {},
    "publish": { "dependsOn": ["build", "test"] }
  }
}
```

**`.gitignore`** (paste from current AISALESHT — already battle-tested):

```bash
cd ~/luana-platform/luana-core
cp /home/chris/AISALESHT/.gitignore .
```

## 6. CI workflow baseline

**`.github/workflows/ci.yml`:**

```yaml
name: CI
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  python-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --all-packages
      - run: uv run ruff check packages/python/
      - run: uv run ruff format --check packages/python/

  python-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --all-packages
      - run: uv run pytest packages/python/ -v --tb=short

  ts-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: pnpm }
      - run: pnpm install --frozen-lockfile
      - run: pnpm lint

  ts-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: pnpm }
      - run: pnpm install --frozen-lockfile
      - run: pnpm test
```

**`.github/workflows/release.yml`** (semantic-release on tag):

```yaml
name: Release
on:
  push:
    branches: [main]

permissions:
  contents: write
  packages: write
  issues: write
  pull-requests: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: astral-sh/setup-uv@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: pnpm }
      - run: pnpm install --frozen-lockfile
      - run: uv sync --all-packages

      - name: Build all
        run: pnpm build && uv build --all-packages

      - name: Publish Python packages to GitHub Packages
        env:
          UV_PUBLISH_URL: https://npm.pkg.github.com
          UV_PUBLISH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          for pkg in packages/python/*/dist/*.whl; do
            uv publish "$pkg" || true
          done

      - name: Publish TS packages via semantic-release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          NPM_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: pnpm exec semantic-release
```

**`.releaserc.json`** (semantic-release config):

```json
{
  "branches": ["main"],
  "plugins": [
    "@semantic-release/commit-analyzer",
    "@semantic-release/release-notes-generator",
    "@semantic-release/changelog",
    ["@semantic-release/npm", { "npmPublish": false }],
    "@semantic-release/github",
    ["@semantic-release/git", { "assets": ["CHANGELOG.md", "package.json"] }]
  ]
}
```

## 7. `.claude-shared/` lift desde Nicolify

```bash
cd ~/luana-platform/luana-core/.claude-shared

# Copiar rules existentes (Nicolify)
cp -r /home/chris/AISALESHT/.claude/rules ./
cp -r /home/chris/AISALESHT/.claude/skills ./
cp -r /home/chris/AISALESHT/.claude/agents ./

# Verificar
ls rules/ skills/ agents/

# Commit inicial
cd ~/luana-platform/luana-core
git add .claude-shared/
git commit -m "chore: lift .claude-shared from Nicolify"
git push origin main
```

## 8. Brand repo skeleton template

Para CADA brand (vitalia, comunify, lupulo-labs, nicolify):

```bash
ORG="luana-platform"
BRAND="vitalia"   # cambiar por cada uno

cd ~/luana-platform
gh repo clone $ORG/$BRAND
cd $BRAND

mkdir -p apps/{api,web}
mkdir -p vertical-{niche}/  # niche varies: medical, creator-economy, gastronomy, saas-marketing
mkdir -p deployments/k8s
mkdir -p .github/workflows

# Subtree pull .claude-shared desde luana-core
git remote add luana-core git@github.com:luana-platform/luana-core.git
git fetch luana-core
git subtree add --prefix=.claude --squash luana-core main

# .claude ahora contiene rules + skills + agents desde luana-core
ls .claude/

# Commit + push
git add .
git commit -m "chore: bootstrap brand skeleton + .claude subtree"
git push origin main
```

**`brand.config.ts` template:**

```typescript
// {brand}/brand.config.ts
import type { BrandConfig } from '@luana/extension-sdk';

export const brandConfig: BrandConfig = {
  name: 'Vitalia',                              // cambiar
  slug: 'vitalia',                              // cambiar
  domain: 'vitalia.health',                     // cambiar
  themeTokens: {
    primary: '#0066CC',                         // cambiar — Vitalia blue clinical
    accent: '#00A86B',                          // cambiar
    fontFamily: 'Inter',
  },
  features: {
    voiceCloning: false,                        // per ADR-001 §2.4
    realTimeSync: false,
  },
  brandStudio: {
    enabledSections: ['identity', 'contact', 'team', 'testimonials'],
    fieldOverrides: {
      voice_archetype: { required: false },
    },
  },
  offerStudio: { presetPack: 'medical_services_v1' },
  scheduling: { bookingPolicy: 'vitalia_prepaid_required' },
  planTiers: {
    solo_doctor: { price: 49, currency: 'USD', features: [] },
    clinic: { price: 199, currency: 'USD', features: [] },
    multi_site: { price: 599, currency: 'USD', features: [] },
  },
  clerkApp: {
    publishableKeyEnv: 'VITALIA_CLERK_PUBLISHABLE_KEY',
    secretKeyEnv: 'VITALIA_CLERK_SECRET_KEY',
  },
  sidebarRoutes: [
    { path: '/treatments', label: 'Tratamientos', verticalOnly: true },
  ],
};
```

## 9. GitHub Project v2 cross-org

```bash
# Crear project en org luana-platform
gh project create --owner luana-platform --title "Luana Roadmap"

# Anotar el project number que devuelve (e.g. #1)
PROJECT_NUM=1

# Habilitar campos custom: Brand, Story, State
gh project field-create $PROJECT_NUM --owner luana-platform --name "Brand" --data-type SINGLE_SELECT --single-select-options "luana-core,nicolify,vitalia,comunify,lupulo-labs"
gh project field-create $PROJECT_NUM --owner luana-platform --name "State" --data-type SINGLE_SELECT --single-select-options "refining,refined,ready,developing,developed,reviewing,done,parked,dropped"
gh project field-create $PROJECT_NUM --owner luana-platform --name "Story" --data-type TEXT
```

## 10. Subtree update cycle (post-bootstrap)

Cuando actualices `.claude-shared/` en luana-core, brands hacen pull:

```bash
# En cualquier brand repo
cd ~/luana-platform/vitalia
git fetch luana-core
git subtree pull --prefix=.claude --squash luana-core main
git push origin main

# Crear script helper en cada brand: scripts/sync-claude-shared.sh
cat > scripts/sync-claude-shared.sh <<'EOF'
#!/bin/bash
set -e
git fetch luana-core
git subtree pull --prefix=.claude --squash luana-core main -m "chore: sync .claude-shared from luana-core"
git push origin main
echo "✓ .claude-shared synced from luana-core"
EOF
chmod +x scripts/sync-claude-shared.sh
```

## 11. GitHub Packages auth (consumer side)

Para que `nicolify` o cualquier brand pueda `pip install luana-core-*`:

**`.npmrc`** (en cada brand repo):
```
@luana:registry=https://npm.pkg.github.com
//npm.pkg.github.com/:_authToken=${GITHUB_TOKEN}
```

**`pip.conf`** (en cada brand repo, `pip.conf` o env):
```
[global]
extra-index-url = https://__token__:${GITHUB_TOKEN}@maven.pkg.github.com/luana-platform/_/simple/
```

> Token: usar `GITHUB_TOKEN` con scope `read:packages`. En CI usar built-in `${{ secrets.GITHUB_TOKEN }}`.

## 12. Sem 1 verification smoke test

Post-setup, verificar que todo funciona:

```bash
# 1. Crear stub Python package en luana-core
cd ~/luana-platform/luana-core
mkdir -p packages/python/luana-core-platform/src/luana_core_platform
echo "VERSION = '0.0.1-alpha'" > packages/python/luana-core-platform/src/luana_core_platform/__init__.py

cat > packages/python/luana-core-platform/pyproject.toml <<'EOF'
[project]
name = "luana-core-platform"
version = "0.0.1-alpha"
description = "Luana Core — Platform foundation"
requires-python = ">=3.12"
EOF

# 2. Build + publish
uv build packages/python/luana-core-platform/

# 3. Manual publish smoke (replace token)
# uv publish packages/python/luana-core-platform/dist/*.whl

# 4. Consume en stub brand repo
cd ~/luana-platform/vitalia
echo "luana-core-platform==0.0.1-alpha" > apps/api/requirements.txt
# pip install -r apps/api/requirements.txt   # debe traer desde GH Packages
```

## 13. ★ Sunday Playbook ★

Sunday 5pm-8pm playbook step-by-step. Cada step ~5-15min. Total ~2-3h.

### Step 0 — Prep (5min)

```bash
# Verificar gh CLI auth + git config
gh auth status && git config --global --list | grep user
```

### Step 1 — Ratificar ADR-001 (10min lectura)

```bash
# Leer
cat /home/chris/AISALESHT/docs/architecture/luana-platform/adr/ADR-001-luana-platform.md

# Si OK, firmar:
# Editar archivo línea 6: status: PROPOSED → status: ACCEPTED
# Editar línea ~250 (sección 7): firma + fecha
# Commit
cd /home/chris/AISALESHT
git add docs/architecture/luana-platform/adr/ADR-001-luana-platform.md
git commit -m "chore(luana): ratify ADR-001 multi-brand vertical SaaS"
git push origin development
```

### Step 2 — Leer REVIEW Story E (10min)

```bash
cat /home/chris/AISALESHT/docs/product/stories/sales-agent-voice-fidelity-grader-runtime/REVIEW-agentic.md

# Verdict PASS confirmado en notif previa
# Trigger /auditor Conv 3 (FRESH conversation Claude Code):
# Comando: /auditor sales-agent-voice-fidelity-grader-runtime
```

### Step 3 — Crear GitHub Org (5min, browser)

```bash
open "https://github.com/account/organizations/new"
# Org name: luana-platform
# Plan: Free
```

### Step 4 — Crear 5 repos (5min)

```bash
# Copy-paste de §3 arriba
ORG="luana-platform"
gh repo create $ORG/luana-core --private --description "Luana Core SSoT"
gh repo create $ORG/nicolify --private
gh repo create $ORG/vitalia --private
gh repo create $ORG/comunify --private
gh repo create $ORG/lupulo-labs --private
gh repo list $ORG
```

### Step 5 — Comprar 4 Claude Code Max subs (10min, browser)

```bash
open "https://claude.ai/settings/billing"
# 4 subs adicionales × $200 = $800/mo total
# Setup 5 perfiles distintos: cada uno en distinto navegador profile o usar /switch
```

### Step 6 — Bootstrap luana-core skeleton (30min)

Copy-paste §5 + §6 + §7 arriba. Resultado: luana-core repo con:
- pyproject.toml + package.json + turbo.json
- .github/workflows/ci.yml + release.yml
- .claude-shared/ con rules + skills + agents lifted

```bash
cd ~/luana-platform/luana-core
# Después de seguir §5-§7
git add .
git commit -m "feat: bootstrap luana-core skeleton + lift .claude-shared"
git push origin main
```

### Step 7 — Bootstrap 4 brand skeletons (40min, ~10min cada uno)

Copy-paste §8 × 4 brands. Cada brand:
- apps/{api,web}/ placeholder
- vertical-{niche}/ placeholder
- .claude/ subtree desde luana-core

### Step 8 — Smoke test (15min)

```bash
# §12 publish stub package + install en stub brand
# Verifica que la cadena GitHub Packages funciona
```

### Step 9 — GitHub Project v2 (10min)

§9 arriba. Crear board "Luana Roadmap" con custom fields.

### Step 10 — Trigger /pm bootstrap outcome (10min, fresh Claude conv)

En NUEVA conversación Claude Code (luana-core repo):

```
/pm bootstrap outcome luana-platform-migration
```

PM lee `docs/product/outcomes/luana-platform-migration.md` (ya existe en AISALESHT, vos copiás manual a luana-core post-Story-11) + `docs/product/stories/luana-foundation/`.

### Step 11 — Trigger /po Story 1 (20min, fresh Claude conv)

```
/po luana-foundation
```

PO lee `00-story.md` + escribe `01-spec.md` con Gherkin AI-resistant. Ratificás. State refining → refined.

### Step 12 — Trigger /architect Story 1 (30min, fresh Claude conv)

```
/architect luana-foundation
```

Architect produce `03-arch.md` + `04-validators.yaml` + `05-guidelines.md` + `06-tickets.yaml` = ready package. State refined → ready.

### Step 13 — Cierre Sunday

```bash
git status
# Tu working tree debe estar clean post-commits
```

### Lunes 2026-05-12 8am — arranca Sem 1

```
# Fresh Claude Code en luana-core repo:
/dev-team luana-foundation
```

Dev-team toma `06-tickets.yaml` ticket-por-ticket. Itera contra validators. Sem 1 corriendo.

## 14. Quick reference cheatsheet

```bash
# Ver state outcome
cat docs/product/outcomes/luana-platform-migration.md | head -20

# Ver state Story 1
cat docs/product/stories/luana-foundation/checkpoint.md | head -20

# Sync .claude-shared en cualquier brand
./scripts/sync-claude-shared.sh

# Bump versión luana-core (semantic-release auto vía conventional commit)
git commit -m "feat(core-llm): add new provider adapter"
# → minor bump on next merge to main
git commit -m "fix(core-iam): resolve JWT expiry edge case"
# → patch bump
git commit -m "feat(core-brand-studio)!: rename PersonalityProfile → BrandPersona

BREAKING CHANGE: ..."
# → major bump
```

## 15. Troubleshooting

| Problema | Fix |
|---|---|
| `gh repo create` falla "name already exists" | Org no permite duplicate names; elegí otro o borrá repo previo |
| GitHub Packages publish 401 | Token sin scope `write:packages`; regenerar con scope correcto |
| Subtree pull conflict | Resolver conflict + commit; subtree no es magic |
| CI Actions minutes exhausted | Free tier 2000min/mo private repos; upgrade a Team plan o limitar matrix |
| `.claude-shared/` desincronizado | Ejecutar `scripts/sync-claude-shared.sh` en brand afectado |
| `pnpm install` fails missing @luana | `.npmrc` mal configurado, verificá `_authToken` |

---

**Doc complete.** Sunday playbook §13 = ruta crítica para arrancar Sem 1 lunes 2026-05-12.
