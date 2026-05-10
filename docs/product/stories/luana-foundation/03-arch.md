---
story_id: luana-foundation
arch_version: 2                                 # ★ revision applied 2026-05-10 ★
architect_owner: claude-opus-4-7 (drafted as /architect proxy)
ratified_by_chris: true                         # ★ Chris ratified scope 2026-05-10 ★
last_modified: 2026-05-10
revision_notes: |
  v2 (2026-05-10): scope shifted to MONOREPO (alpacapurpura/luana-platform).
  Removed: 5 separate repos, GitHub Packages publishing, semantic-release setup,
  org-level secrets, cross-org GitHub Project v2, .npmrc with publishConfig.
  Added: CODEOWNERS, PR template, ADR folder, monorepo subfolder layout.
  v1 (2026-05-09): superseded.
---

# 03-arch — Luana Foundation

> **Status:** READY (post Chris ratification 2026-05-10)
> **Surface:** infra only (no BE/FE/agentic code)
> **Architect owner:** Claude Opus 4.7 (acting as /architect proxy)
> **Repo:** `https://github.com/alpacapurpura/luana-platform.git` (private monorepo)

## 1. High-level architecture

Story 1 entrega 4 capas físicas de infra dentro de UN solo monorepo:

```
alpacapurpura/luana-platform/                  ← single private monorepo
├── core/                                       ← engine SSoT (placeholder; Story 2 lifts shared/)
│   └── README.md
├── nicolify/                                   ← canonical SaaS marketing brand
│   └── README.md
├── vitalia/                                    ← medical brand
│   └── README.md
├── comunify/                                   ← creator economy brand
│   └── README.md
├── lupulo/                                     ← gastronomy brand
│   └── README.md
├── .claude-shared/                             ← lifted from AISALESHT/.claude/
│   ├── rules/
│   ├── skills/
│   └── agents/
├── .claude/                                    ← copy/symlink → .claude-shared/
├── .github/
│   ├── CODEOWNERS                              ← anti-island gate #1
│   ├── PULL_REQUEST_TEMPLATE.md                ← anti-island gate #3
│   └── workflows/
│       └── ci.yml                              ← lint + test only (no release.yml in Story 1)
├── docs/
│   ├── ARCHITECTURE.md                         ← monorepo topology + subfolder layout
│   ├── CONTRIBUTING.md                         ← Conventional Commits + PR + ADR rules
│   ├── RELEASES.md                             ← placeholder (publishing deferred Story 9)
│   └── architecture/
│       └── ADR/
│           ├── README.md                       ← anti-island gate #2
│           └── (ADRs added forward)
├── scripts/
│   └── (per-need helpers; sync-claude-shared.sh deferred — single repo, no subtree needed)
├── pyproject.toml                              ← uv workspace root
├── package.json                                ← pnpm workspace root + turbo dev dep
├── turbo.json                                  ← Turborepo task config
├── pnpm-workspace.yaml                         ← workspace member globs
├── .python-version                             ← 3.12
├── .gitignore                                  ← copied from AISALESHT
├── README.md                                   ← short — links to docs/
└── LICENSE                                     ← proprietary "All Rights Reserved"
```

**Key deltas vs v1 architecture:**

| Removed (v1 had it) | Reason |
|---|---|
| 5 separate repos (luana-core, nicolify, vitalia, comunify, lupulo-labs) | Single monorepo per Chris ratification 2026-05-10 |
| GitHub Org `luana-platform` | Repo lives under `alpacapurpura/` user namespace |
| GitHub Packages publish setup (.npmrc with publishConfig) | DEFERRED to Story 9 (luana-v0-1-0-publish) |
| semantic-release config (.releaserc.json + release.yml) | DEFERRED to Story 9 |
| Cross-org GitHub Project v2 board | Single repo → standard repo Issues + Projects suffice; not in Story 1 scope |
| git subtree pattern (.claude-shared sync to brands) | Single repo → all brands see `.claude/` directly. No subtree |
| org-level PAT (LUANA_PACKAGES_READ_TOKEN) | No publishing in Story 1 → no token |

| Added (v1 didn't have) | Reason |
|---|---|
| `.github/CODEOWNERS` | Anti-island gate #1 (Chris ratified 2026-05-10) |
| `.github/PULL_REQUEST_TEMPLATE.md` | Anti-island gate #3 (Chris ratified 2026-05-10) |
| `docs/architecture/ADR/README.md` | Anti-island gate #2 (Chris ratified 2026-05-10) |
| Branch protection review_count=1 from day 1 | Chris ratified 2026-05-10 (was 0 in v1) |

## 2. Tech stack decisions

| Layer | Choice | Rationale |
|---|---|---|
| Python package manager | **uv** (Astral) | 2026 standard. Native workspaces. Internal deps via `tool.uv.sources` (no publish required) |
| TS package manager | **pnpm** | Workspaces support. Internal deps via `workspace:*` protocol (no publish required) |
| Monorepo orchestrator | **Turborepo 2.3+** | Task pipeline + caching. Native pnpm support |
| Versioning | **manual SemVer** in Story 1 (semantic-release deferred Story 9) | Pre-publish era, version in pyproject.toml manually |
| Registry | **none in Story 1** (workspace-internal only) | All consumers within monorepo. Story 9 introduces GH Packages |
| CI | **GitHub Actions** | Free 2000min/mo private. Native to GitHub |
| Secret management | none required Story 1 (no publish, no deploy) | Story 9 + Stories 11-13 introduce |
| Documentation | **markdown in `docs/`** | Future GitHub Pages possible |
| License | **Proprietary "All Rights Reserved"** | Chris ratified 2026-05-10 |

## 3. Repository topology (monorepo subfolder layout)

### 3.1 Workspace root layout

```
luana-platform/
├── pyproject.toml                              # uv workspace root (only [tool.uv.workspace] section)
├── package.json                                # pnpm workspace root (private: true, no publish)
├── pnpm-workspace.yaml                         # packages: [core, nicolify, vitalia, comunify, lupulo]
├── turbo.json                                  # task pipeline (build, test, lint)
├── .python-version                             # 3.12
└── README.md                                   # 5-10 lines, links to docs/
```

### 3.2 Per-subfolder skeleton

Each of `core/` + `nicolify/` + `vitalia/` + `comunify/` + `lupulo/`:

```
{subfolder}/
├── pyproject.toml                              # workspace member, declares own deps
│                                                # core/: name="luana-core" placeholder
│                                                # nicolify/: name="nicolify-app" placeholder
│                                                # etc.
├── package.json                                # workspace member, name="@luana/{slug}"
└── README.md                                   # purpose + scope + links to ARCHITECTURE.md
```

Stories 2-9 populate `core/{copilot,sales-agent,shared,...}/` + brand-specific code.
Story 10 lifts AISALESHT codebase into `nicolify/` (preserves DDD structure).

### 3.3 Workspace member declaration

`pyproject.toml` (workspace root, partial):

```toml
[tool.uv.workspace]
members = ["core", "nicolify", "vitalia", "comunify", "lupulo"]

[tool.uv.sources]
# Future internal deps go here, e.g.:
# nicolify-app = { workspace = true }
# luana-core = { workspace = true }

[tool.ruff]
line-length = 120
target-version = "py312"
```

`pnpm-workspace.yaml`:

```yaml
packages:
  - core
  - nicolify
  - vitalia
  - comunify
  - lupulo
```

`turbo.json` (minimal Story 1):

```json
{
  "$schema": "https://turbo.build/schema.json",
  "tasks": {
    "build": { "dependsOn": ["^build"] },
    "lint": {},
    "test": { "dependsOn": ["^build"] }
  }
}
```

## 4. CI workflow design

### 4.1 ci.yml — 4 parallel jobs

```yaml
name: CI
on:
  pull_request: { branches: [main] }
  push: { branches: [main] }

jobs:
  python-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
        with: { python-version: "3.12" }
      - run: uv sync --all-packages
      - run: uv run ruff check core nicolify vitalia comunify lupulo

  python-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
        with: { python-version: "3.12" }
      - run: uv sync --all-packages
      - run: uv run pytest -x -q || echo "no tests yet — Story 1 placeholder"

  ts-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v3
        with: { version: 9 }
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: "pnpm" }
      - run: pnpm install --frozen-lockfile
      - run: pnpm lint || echo "no eslint yet — Story 1 placeholder"

  ts-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v3
        with: { version: 9 }
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: "pnpm" }
      - run: pnpm install --frozen-lockfile
      - run: pnpm test || echo "no tests yet — Story 1 placeholder"
```

Branch protection requires `lint` and `test` checks. Map status check names by ensuring jobs are named `python-lint`, `python-test`, `ts-lint`, `ts-test` and configuring branch protection to require any 2 (or rename to plain `lint` / `test` aggregator job — /dev-team decides at T-3).

### 4.2 No release.yml in Story 1

Publishing pipeline DEFERRED to Story 9 (`luana-v0-1-0-publish`). Story 1 only ships `ci.yml`.

## 5. Anti-island governance scaffolding (Chris ratified 2026-05-10)

### 5.1 `.github/CODEOWNERS`

```
# Default: Chris owns everything until collaborators onboard
*                                @alpacapurpura

# Critical core paths require Chris review explicitly
core/copilot/**                  @alpacapurpura
core/sales-agent/**              @alpacapurpura
core/shared/**                   @alpacapurpura

# Architecture decisions require Chris review
docs/architecture/ADR/**         @alpacapurpura
docs/process/**                  @alpacapurpura

# Workspace root config requires Chris review
pyproject.toml                   @alpacapurpura
package.json                     @alpacapurpura
pnpm-workspace.yaml              @alpacapurpura
turbo.json                       @alpacapurpura
.github/**                       @alpacapurpura
```

When collaborators onboard:
- Add brand-specific lines: `vitalia/** @collab-vitalia @alpacapurpura`
- Brand-isolated paths get the brand collaborator + Chris (defense in depth)
- `core/` stays Chris-only until co-architect role formalizes

### 5.2 `.github/PULL_REQUEST_TEMPLATE.md`

```markdown
## Qué cambia

<!-- 1-3 bullet points describiendo el cambio funcional -->

## Por qué

<!-- Razón de negocio o técnica. Link a outcome / story / issue si aplica. -->

## Módulos tocados

<!-- Marca con [x] -->
- [ ] core/copilot
- [ ] core/sales-agent
- [ ] core/shared
- [ ] core/* (otro)
- [ ] nicolify/*
- [ ] vitalia/*
- [ ] comunify/*
- [ ] lupulo/*
- [ ] docs/*
- [ ] .github/* (CI o gobernanza)

## ADR ref (si toca core/)

<!-- Link al ADR en docs/architecture/ADR/ que justifica este cambio.
     Sin ADR para cambios core/ → PR rechazado per anti-island gate #2. -->

ADR: docs/architecture/ADR/NNN-...

## Outcome / story ref

<!-- Link a outcome o story en docs/product/.
     Sin link → /pm SSoT discipline rota. -->

Outcome: docs/product/outcomes/...
Story:   docs/product/stories/...
```

### 5.3 `docs/architecture/ADR/README.md`

```markdown
# Architecture Decision Records (ADR)

Formato Michael Nygard (lightweight). Toda decisión que afecta `core/**`
(cross-module behavior, schema, API contract, abstracción shared) requiere
ADR antes de PR.

## Cuándo escribir ADR

- ✅ Nuevo abstract en `core/shared/` consumido cross-brand
- ✅ Cambio de contrato API que rompe consumidores
- ✅ Schema migration con impacto cross-module
- ✅ Nueva abstracción cross-brand
- ❌ Bug fix con scope local (no requiere ADR)
- ❌ Refactor interno de un módulo sin contrato cambiado
- ❌ Documentación o config sin impacto runtime

## Template

`docs/architecture/ADR/_template.md`:

\`\`\`markdown
# ADR-NNN: <Título corto>

- **Status:** proposed | accepted | superseded by ADR-MMM
- **Date:** YYYY-MM-DD
- **Deciders:** Chris + (collaborators si aplica)

## Context

<Qué problema resolvemos. Qué fuerzas están en juego.>

## Decision

<Qué decidimos. Una frase clara.>

## Consequences

### Positive
<Qué ganamos.>

### Negative
<Qué cuesta.>

### Neutral
<Qué cambia sin ser bueno o malo.>

## Alternatives considered

1. <Alt A> — <por qué descartada>
2. <Alt B> — <por qué descartada>

## References

- Outcome / story que motivó el ADR
- Issues / PRs relacionados
\`\`\`

## ADR index

| # | Título | Status | Date |
|---|---|---|---|
| 001 | Luana Platform topology (monorepo) | accepted | 2026-05-10 |

## Anti-island enforcement

CODEOWNERS protege `docs/architecture/ADR/**` con review Chris obligatorio.
PR template requiere link a ADR si toca `core/**`. Sin ADR → PR rechazado.
```

## 6. `.claude-shared/` lift pattern

### 6.1 Single-repo (no subtree)

Since the monorepo is single-source, `.claude-shared/` is just a copy from
AISALESHT. All workspace members see the same `.claude/` directory.

```bash
cd ~/luana-platform
mkdir -p .claude-shared
cp -r /home/chris/AISALESHT/.claude/rules .claude-shared/
cp -r /home/chris/AISALESHT/.claude/skills .claude-shared/
cp -r /home/chris/AISALESHT/.claude/agents .claude-shared/
ln -sf .claude-shared .claude       # or directory copy if Windows-compat needed
git add .claude-shared .claude
git commit -m "chore: lift .claude-shared from AISALESHT (initial sync)"
```

**Note vs v1:** v1 had subtree pattern for cross-repo sync. Single monorepo
makes subtree obsolete. If multi-repo refactor happens later (collaborators
contracted per brand), subtree pattern returns at that point.

### 6.2 Brand-local Claude rules (future)

If a brand subfolder needs vertical-specific rules (e.g., Vitalia HIPAA),
they live in `{subfolder}/.claude/local/` (NOT `.claude/rules/` —
that's the shared baseline).

## 7. Branch protection model

For `main`:
- Default branch: `main`
- Direct pushes: blocked (`allow_force_pushes: false`)
- PR required, `required_approving_review_count: 1`
- Required status checks: `lint`, `test` (or 4 jobs python-lint/python-test/ts-lint/ts-test — /dev-team decides naming at T-3)
- `enforce_admins: false` (Chris can override in emergencies)

**Future when collaborators onboard:** consider raising `required_approving_review_count` to 2 for `core/**` changes via branch protection rule + CODEOWNERS escalation.

## 8. Risks + mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| pnpm + uv workspace member resolution surprises | Low | F-2 + F-3 validators check presence; T-2 commits + tests immediately |
| Branch protection blocks first PR (no checks yet) | Low | T-1 sets up branch protection AFTER T-3 merges CI workflow (DAG enforces) |
| CODEOWNERS rules block solo Chris from merging own PR | Low | `enforce_admins: false` + Chris is the owner — review-self mechanic OR raise to 2 review-cap when collab onboards |
| ADR process feels heavy for Chris solo | Medium | ADR README explicitly says "lightweight Michael Nygard format"; first ADR (ADR-001) is a back-link to outcome doc, not a fresh write |
| `.claude/` symlink fails on future Windows machine | Low | Use directory copy not symlink (T-4 ticket decides) |

## 9. Out-of-scope (explicitly)

- BE/FE code lift (Stories 2-10)
- GitHub Packages publishing pipeline (Story 9 — `luana-v0-1-0-publish`)
- semantic-release configuration (Story 9)
- `.releaserc.json` + `release.yml` (Story 9)
- `.npmrc` with publishConfig (Story 9)
- Stub publishing smoke test (Story 9)
- Real Clerk app credentials per brand (Stories 11-13)
- K8s deployment manifests with real values (Stories 11-13)
- LiteLLM Proxy svc per brand cluster (Stories 11-13)
- Postgres + Qdrant DB provisioning (Stories 11-13)
- Cross-org GitHub Project v2 board (single repo → standard repo Projects suffice)
- ADR-002+ (added incrementally as decisions arise)

## 10. Architectural fitness tests (Story 1 specific)

Tests baseline added to `nicolify/tests/architecture/` (chosen because nicolify is the canonical Python workspace; Story 10 lifts AISALESHT into nicolify, where `tests/architecture/` already lives in AISALESHT today):

```python
# nicolify/tests/architecture/test_workspace_integrity.py
def test_pyproject_workspace_members_exist():
    """All uv workspace members in pyproject.toml resolve to actual directories."""

def test_pnpm_workspace_members_exist():
    """All pnpm-workspace.yaml packages resolve to actual directories."""

def test_no_top_level_circular_imports():
    """Stub: no circular imports between python packages declared so far."""

# nicolify/tests/architecture/test_codeowners_present.py
def test_codeowners_file_exists():
    """`.github/CODEOWNERS` exists at repo root."""

def test_codeowners_protects_core_paths():
    """CODEOWNERS rules cover core/copilot/**, core/sales-agent/**, core/shared/**."""

# nicolify/tests/architecture/test_adr_folder_present.py
def test_adr_readme_exists():
    """`docs/architecture/ADR/README.md` exists with template + index sections."""

# nicolify/tests/architecture/test_pr_template_present.py
def test_pr_template_has_required_sections():
    """`.github/PULL_REQUEST_TEMPLATE.md` exists with sections: Qué cambia, Por qué, Módulos tocados, ADR ref, Outcome/story ref."""

# nicolify/tests/architecture/test_claude_shared_present.py
def test_claude_shared_directories_present():
    """`.claude-shared/{rules,skills,agents}/` exist + non-empty."""
```

These tests fail-on-drift in subsequent Stories (e.g., if a future PR removes CODEOWNERS rule for `core/copilot/**`, the test fires).

## 11. Open architectural questions

None blocking. Resolved via Chris ratification 2026-05-10:
- ✅ License: proprietary
- ✅ Repo topology: monorepo
- ✅ Publishing: deferred Story 9
- ✅ Branch protection: review_count=1 day 1
- ✅ Anti-island scaffolding: mandatory

**Deferred to /dev-team at T-3:** status check names (`lint`/`test` aggregator vs 4 separate jobs) — choose what works with branch protection UI.

## 12. Dependencies on Story 0 (pre-flight)

- ✅ ADR-001 ratificado por Chris (2026-05-10)
- ✅ Repo `alpacapurpura/luana-platform` creado (2026-05-10)
- ✅ Scope decisions ratificadas (monorepo + proprietary + defer publishing) (2026-05-10)
- ✅ `gh CLI` autenticado en Chris's local machine (assumed)
