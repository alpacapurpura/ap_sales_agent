---
story_id: luana-foundation
arch_version: 1
architect_owner: claude-opus-4-7 (drafted as /architect proxy)
ratified_by_chris: false                        # ★ awaiting Chris ratification ★
last_modified: 2026-05-09
---

# 03-arch — Luana Foundation

> **Status:** DRAFT — pending Chris ratification post 2026-05-11
> **Surface:** infra only (no BE/FE/agentic code)
> **Architect owner:** Claude Opus 4.7 (acting as /architect proxy)

## 1. High-level architecture

Story 1 entrega 5 capas físicas de infra:

```
GitHub Org luana-platform
├── luana-core (monorepo)              ← engine SSoT
│   ├── packages/python/                  uv workspaces
│   ├── packages/ts/                      pnpm + Turborepo workspaces
│   ├── .claude-shared/                   rules + skills + agents (lifted from AISALESHT)
│   ├── .github/workflows/                ci.yml + release.yml
│   ├── docs/                             ARCHITECTURE.md → ADR-001
│   └── pyproject.toml + package.json + turbo.json
├── nicolify (brand)                   ← canonical SaaS marketing
├── vitalia (brand)                    ← medical
├── comunify (brand)                   ← creator economy
└── lupulo-labs (brand)                ← gastronomy

GitHub Packages registry (private, org-scoped)
└── Publishes:
    ├── Python packages (luana-core-*)
    └── TypeScript packages (@luana/*)

GitHub Project v2 (cross-org)
└── Custom fields: Brand, State, Story
```

## 2. Tech stack decisions

| Layer | Choice | Rationale |
|---|---|---|
| Python package manager | **uv** (Astral) | 2026 standard, replaces poetry. Faster, native workspaces. |
| TS package manager | **pnpm** | Smaller node_modules, workspaces support, deterministic |
| Monorepo orchestrator | **Turborepo 2.3+** | Remote caching free for 1 org, native pnpm support, mature |
| Versioning | **semantic-release** | Auto-bump from Conventional Commits, generates CHANGELOG |
| Registry | **GitHub Packages** | Free with GH plan, supports both Python (PyPI-compat via OCI) and npm |
| CI | **GitHub Actions** | 2000min free private, native to GitHub ecosystem |
| Secret management | `${{ secrets.GITHUB_TOKEN }}` (built-in) for first iteration; later GitHub Environments for production secrets |
| Documentation | **markdown in `docs/`** initially; future: GitHub Pages for HTML docs |
| Cross-repo sync | **git subtree** (not submodule) | Simpler operationally, works without `--init` ceremony |

## 3. Repository topology

### 3.1 luana-core monorepo layout

```
luana-core/
├── packages/
│   ├── python/                              # uv workspace members
│   │   ├── luana-core-platform/             # Story 2 will populate
│   │   │   ├── pyproject.toml
│   │   │   └── src/luana_core_platform/__init__.py
│   │   ├── luana-core-iam/                  # Story 3
│   │   ├── luana-core-llm/                  # Story 2
│   │   ├── luana-core-events/               # Story 2
│   │   └── ...                              # 22+ packages total post-Story-9
│   └── ts/                                  # pnpm workspace members
│       ├── ui-kit/                          # Story 2 starter
│       ├── design-tokens/                   # Story 2
│       ├── format/                          # Story 2
│       ├── api-client/                      # Story 2
│       └── ...                              # 16+ packages total
├── .claude-shared/
│   ├── rules/                               # lifted from AISALESHT/.claude/rules/
│   ├── skills/                              # lifted from AISALESHT/.claude/skills/
│   └── agents/                              # lifted from AISALESHT/.claude/agents/
├── .github/
│   └── workflows/
│       ├── ci.yml                           # lint + test on PR + push
│       └── release.yml                      # semantic-release on main push
├── docs/
│   ├── ARCHITECTURE.md                      # links to ADR-001 in nicolify (or copy)
│   ├── CONTRIBUTING.md                      # Conventional Commits + PR flow
│   ├── RELEASES.md                          # semver + release process
│   └── extension-points.md                  # Story 8 will populate
├── scripts/
│   └── publish-all.sh                       # smoke helper
├── pyproject.toml                           # uv workspace root
├── package.json                             # pnpm workspace root
├── turbo.json                               # Turborepo task config
├── pnpm-workspace.yaml                      # pnpm workspace pattern
├── .releaserc.json                          # semantic-release config
├── .gitignore                               # copied from AISALESHT
├── .npmrc                                   # publishConfig: GH Packages
├── .python-version                          # 3.12
├── README.md                                # short — links to docs/
└── LICENSE                                  # proprietary placeholder (Chris ratifies)
```

### 3.2 Brand repo skeleton (template same for 4 brands)

```
{brand}/                                     # vitalia | comunify | lupulo-labs | nicolify (post-rename)
├── apps/
│   ├── api/                                 # FastAPI app (Story 10/11/12/13 populates)
│   │   ├── main.py
│   │   ├── pyproject.toml
│   │   └── src/{brand}_api/
│   └── web/                                 # Next.js app
│       ├── app/                             # App Router
│       ├── package.json
│       └── ...
├── vertical-{niche}/                        # vertical-medical | -creator-economy | -gastronomy | -saas-marketing
│   ├── tools/                               # sales_agent tool extensions
│   ├── extractors/                          # copilot extractors
│   ├── workflows/                           # copilot workflows
│   ├── kb/                                  # knowledge base packs
│   └── guardrails/
├── deployments/
│   └── k8s/                                 # placeholder manifests
├── .claude/                                 # subtree from luana-core/.claude-shared
├── .github/
│   └── workflows/
│       ├── ci.yml                           # brand-specific CI
│       └── deploy.yml                       # brand-specific deploy (Stories 11-13)
├── scripts/
│   └── sync-claude-shared.sh                # subtree pull helper
├── brand.config.ts
├── brand.config.py
├── pyproject.toml                           # brand workspace
├── package.json                             # brand workspace
└── README.md
```

## 4. CI workflow design

### 4.1 luana-core ci.yml — 4 parallel jobs

```yaml
name: CI
on:
  pull_request: { branches: [main] }
  push: { branches: [main] }

jobs:
  python-lint:                                # ruff check + format-check
  python-test:                                # pytest packages/python/
  ts-lint:                                    # eslint + tsc --noEmit
  ts-test:                                    # vitest packages/ts/
```

Reference impl: `05-cross-repo-tooling.md` §6.

### 4.2 luana-core release.yml — semantic-release on main push

Triggered on push to main. Steps:
1. Checkout with full history (`fetch-depth: 0`)
2. Build all packages (`pnpm build && uv build --all-packages`)
3. Publish Python packages to GH Packages (uv publish with `UV_PUBLISH_URL=https://npm.pkg.github.com`)
4. Run semantic-release for TS packages (publishes via npm to GH Packages)
5. Create GitHub Release with auto-generated changelog
6. Update CHANGELOG.md in main

### 4.3 Brand repo ci.yml — minimal initial

Each brand starts with stub jobs (no actual tests until Stories 10-13 populate code):
- `lint` (placeholder if no code, exit 0)
- `test` (placeholder if no code, exit 0)
- These are required for branch protection but tolerant initially

Once Story 10 populates Nicolify code, this expands.

## 5. GitHub Packages auth model

### 5.1 Publishing (luana-core CI)

Built-in `${{ secrets.GITHUB_TOKEN }}` has `write:packages` scope automatically when `permissions: { packages: write }` is set in workflow.

### 5.2 Consuming (brand repos)

Each brand repo's `.npmrc`:
```
@luana:registry=https://npm.pkg.github.com
//npm.pkg.github.com/:_authToken=${GITHUB_TOKEN}
```

For local dev, Chris exports `GITHUB_TOKEN` env var with `read:packages` scope (PAT created at github.com/settings/tokens).

For brand CI, `${{ secrets.GITHUB_TOKEN }}` is sufficient when workflow has `permissions: { packages: read }`.

### 5.3 Token management

Per-repo: built-in `GITHUB_TOKEN` (auto, no manual setup).
Cross-repo (brand reading luana-core packages): a single org-level PAT stored as org secret `LUANA_PACKAGES_READ_TOKEN`, propagated to all 5 repos via `gh secret set --org`.

## 6. `.claude-shared/` subtree pattern

### 6.1 Initial lift (luana-core side)

```bash
cd luana-core
mkdir -p .claude-shared
cp -r /home/chris/AISALESHT/.claude/rules .claude-shared/
cp -r /home/chris/AISALESHT/.claude/skills .claude-shared/
cp -r /home/chris/AISALESHT/.claude/agents .claude-shared/
git add .claude-shared/
git commit -m "chore: lift .claude-shared from AISALESHT"
git push origin main
```

### 6.2 Brand subtree add (one-time per brand)

```bash
cd {brand}
git remote add luana-core git@github.com:luana-platform/luana-core.git
git fetch luana-core
git subtree add --prefix=.claude --squash luana-core main
git push origin main
```

The brand's `.claude/` directory now mirrors `luana-core/.claude-shared/` content (squashed = single commit history).

### 6.3 Sync updates (brand pulls from luana-core)

Helper script `{brand}/scripts/sync-claude-shared.sh`:
```bash
#!/bin/bash
set -e
git fetch luana-core
git subtree pull --prefix=.claude --squash luana-core main \
  -m "chore: sync .claude-shared from luana-core"
git push origin main
```

### 6.4 Brand-local extensions

If a brand needs vertical-specific Claude rules (e.g., Vitalia HIPAA guidelines), they live in `{brand}/.claude/local/` (NOT `.claude/rules/` — that's subtree-managed).

## 7. semantic-release configuration

### 7.1 Conventional Commits → version bump

| Commit prefix | Bump type |
|---|---|
| `feat(scope): ...` | minor |
| `feat(scope)!: ...` or body has `BREAKING CHANGE:` | major |
| `fix(scope): ...` | patch |
| `docs|chore|refactor|test|perf|ci|build|style: ...` | no bump |

### 7.2 Multi-package release (monorepo)

semantic-release runs once per main push. For per-package versioning, use `semantic-release-monorepo` plugin OR commit scope to package name (e.g., `feat(core-llm): ...` → bumps only `luana-core-llm`).

**Decision:** Use commit scope = package name. Package versions independent. Single CHANGELOG.md aggregates all.

### 7.3 Pre-release tags

Initial publishes use `0.0.x-alpha` (manually set in pyproject + package.json). semantic-release takes over post-Story-9 promote to `0.1.0`.

## 8. Branch protection model

For all 5 repos:
- Default branch: `main`
- Direct pushes: blocked
- PR required, but `required_approving_review_count: 0` (Chris solo)
- Required status checks: `lint`, `test` (must pass before merge)
- `enforce_admins: false` (Chris can override in emergencies)

Future change: `required_approving_review_count: 1` cuando contrate devs.

## 9. GitHub Project v2 schema

Project name: **Luana Roadmap**
Owner: org `luana-platform`

Custom fields:
| Field | Type | Options |
|---|---|---|
| Brand | SINGLE_SELECT | luana-core, nicolify, vitalia, comunify, lupulo-labs |
| State | SINGLE_SELECT | refining, refined, ready, developing, developed, reviewing, done, parked, dropped |
| Story | TEXT | story slug (e.g., `luana-foundation`) |
| Estimated Sprint | NUMBER | sprint number 1-8 |

Views:
- **Roadmap** — group by Sprint, color by State
- **By Brand** — group by Brand, sort by Story
- **Active** — filter State in [refining, refined, ready, developing, reviewing]

## 10. Risks + mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| GH Packages publish auth flow surprises | Medium | Story 1 includes smoke test publish + install end-to-end (Scenario 3) |
| Subtree merge conflicts when Chris edits brand `.claude/` directly | Medium | Documentation: brand-local rules go in `.claude/local/`, not `.claude/rules/` |
| GitHub Actions free 2000min/mo exhausted | Low | Smoke tests only Sem 1-3; scale to Team plan when needed |
| Conventional Commits enforcement drift | Low | Add pre-commit hook in luana-core (Sem 1 ticket if Chris ratifies Q4) |
| `gh repo create` permission issues if Chris's account doesn't have org access | Low | Story 1 step 0 verifies `gh api /user` shows correct plan |

## 11. Out-of-scope (explicitly)

- BE/FE code lift (Stories 2-10)
- Real Clerk app credentials per brand (Stories 11-13)
- K8s deployment manifests with real values (Stories 11-13)
- LiteLLM Proxy svc per brand cluster (Stories 11-13)
- Postgres + Qdrant DB provisioning (Stories 11-13)
- ADR-002 multi-Clerk arquitectura deeper (would be follow-up ADR if needed)

## 12. Architectural fitness tests (Story 1 specific)

Tests baseline added to `luana-core/tests/architecture/`:

```python
# test_workspace_integrity.py
def test_pyproject_workspace_members_exist():
    """All uv workspace members in pyproject.toml resolve to actual directories."""
def test_package_json_workspaces_exist():
    """All pnpm workspace members resolve."""
def test_no_top_level_circular_imports():
    """Stub: no circular imports between python packages declared so far."""
def test_claude_shared_present():
    """`.claude-shared/{rules,skills,agents}/` directories exist + non-empty."""
def test_ci_workflow_present():
    """`.github/workflows/ci.yml` exists with required jobs."""
```

These tests fail-on-drift in subsequent Stories (e.g., if Story 2 adds package without registering in workspace, test fires).

## 13. Open architectural questions (for Chris ratification)

1. **License model.** Recomendación: proprietary "All Rights Reserved" durante v0.x. Re-evaluar Sem 9+ si business decide source-available.
2. **`semantic-release-monorepo` vs commit scope = package name.** Recomendación: commit scope. Más explícito.
3. **Conventional Commits pre-commit hook.** Recomendación: SÍ, evita drift histórico. Implementar en Story 1 ticket.
4. **PAT scope para `LUANA_PACKAGES_READ_TOKEN` org secret.** Recomendación: minimal `read:packages` only.
5. **Turborepo remote caching.** Free tier OK arranque. Considerar Vercel Remote Cache integration Sem 4+ si CI lento.
6. **Python version pin.** 3.12 cement (matches AISALESHT actual). Future bump to 3.13 = cross-repo coordination.

## 14. Dependencies on Story 0 (pre-flight)

- ADR-001 ratificado por Chris
- GitHub Org `luana-platform` creado (Chris manual)
- Chris compró 4 Claude Code Max subs adicionales (5 totales)
- (Optional) `gh CLI` autenticado en Chris's local machine
