---
story_id: luana-foundation
sequence_in_outcome: 1
po_version: 2                                   # ★ revision applied 2026-05-10 ★
po_owner: claude-opus-4-7 (drafted as /po proxy)
ratified_by_chris: true                         # ★ Chris ratified scope 2026-05-10 ★
spec_type: service                              # no UI — pure infra setup
last_modified: 2026-05-10
revision_notes: |
  v2 (2026-05-10): scope shifted to MONOREPO at alpacapurpura/luana-platform
  with subfolders core/ + nicolify/ + vitalia/ + comunify/ + lupulo/.
  GH Packages publishing DEFERRED to Story 9 (luana-v0-1-0-publish).
  Anti-island scaffolding (CODEOWNERS + PR template + ADR folder) added.
  License: proprietary (private repo, "All rights reserved").
  Claude subs: 1 sequential (was 5 parallel).
  v1 (2026-05-09): initial draft assuming 5 separate repos + GH Packages
  publishing in Story 1. Superseded.
---

# 01-spec — Luana Foundation

> **Status:** REFINED — Chris ratified scope 2026-05-10
> **Story type:** service (no UI deliverable)
> **Outcome:** luana-platform-migration (Story 1/14)
> **Repo target:** `https://github.com/alpacapurpura/luana-platform.git` (private monorepo, exists, empty)

## 1. Acceptance Criteria (Gherkin AI-resistant)

### Scenario 1: Monorepo cloned with branch protection + anti-island scaffolding

```gherkin
Feature: Monorepo bootstrap on alpacapurpura/luana-platform
  As Chris (founder solo, future collaborators TBD)
  I need the existing private monorepo seeded with branch protection,
  CODEOWNERS, PR template, and ADR folder
  So that the foundation enforces /pm SSoT discipline from commit #1

  Scenario: monorepo cloned locally with main branch protected
    Given Chris has authenticated `gh CLI` to alpacapurpura account
    And the empty repo `alpacapurpura/luana-platform` exists (private)
    When the foundation playbook is executed
    Then `~/luana-platform/` clone exists with default branch `main`
    And branch protection on `main` is enabled with:
      | required_pull_request_reviews.required_approving_review_count | 1 |
      | required_status_checks.contexts                                | ["lint", "test"] |
      | enforce_admins                                                  | false |
      | allow_force_pushes                                              | false |

  Validator: NF-1 + NF-2 (gh API checks).
```

### Scenario 2: Anti-island governance files seeded

```gherkin
Feature: CODEOWNERS + PR template + ADR folder enforce /pm SSoT discipline
  As Chris (preparing for future collaborators)
  I need governance scaffolding present from day one
  So that when collaborators onboard, gates are already cement

  Scenario: CODEOWNERS file present with critical-path owners
    Given monorepo cloned
    When inspecting `.github/CODEOWNERS`
    Then file exists
    And the file contains rules for:
      | * (default fallback)                       | @alpacapurpura |
      | core/copilot/**                            | @alpacapurpura |
      | core/sales-agent/**                        | @alpacapurpura |
      | core/shared/**                             | @alpacapurpura |
      | docs/architecture/ADR/**                   | @alpacapurpura |

  Scenario: PR template present
    Given monorepo cloned
    When inspecting `.github/PULL_REQUEST_TEMPLATE.md`
    Then file exists with sections:
      | ## Qué cambia                              |
      | ## Por qué                                 |
      | ## Módulos tocados                         |
      | ## ADR ref (si toca core/)                 |
      | ## Outcome / story ref                     |

  Scenario: ADR folder seeded
    Given monorepo cloned
    When inspecting `docs/architecture/ADR/`
    Then directory exists
    And `docs/architecture/ADR/README.md` exists explaining ADR template
    And README states ADR is mandatory for any change touching `core/**`

  Validator: NF-3 + NF-4 + NF-5.
```

### Scenario 3: Monorepo skeleton (uv + pnpm + turborepo) functional

```gherkin
Feature: Workspace tooling boots without errors
  As Claude Code
  I need uv workspace + pnpm workspace + turbo orchestration to install
  So that subsequent stories can lift code into workspace-internal packages

  Scenario: pyproject + package.json + turbo.json + workspaces resolve
    Given the monorepo skeleton from Story 1 has been applied
    When `uv sync --all-packages` runs at repo root
    Then exit code is 0
    When `pnpm install --frozen-lockfile` runs at repo root
    Then exit code is 0

  Scenario: lint passes on empty workspaces
    Given the skeleton committed
    When `uv run ruff check core/ nicolify/ vitalia/ comunify/ lupulo/` runs
    Then exit code is 0
    When `pnpm lint` runs
    Then exit code is 0

  Validator: NF-6 + NF-7 + NF-8 + NF-9.
```

### Scenario 4: CI workflow green on first PR

```gherkin
Feature: GitHub Actions CI runs lint + test on every PR
  As Chris (and future collaborators)
  I need CI gating PRs into main
  So that branch protection's required_status_checks have something to enforce

  Scenario: CI workflow boots and goes green on smoke commit
    Given `.github/workflows/ci.yml` has been committed with 4 jobs:
      | python-lint  |
      | python-test  |
      | ts-lint      |
      | ts-test      |
    When a PR is opened against `main` with a no-op commit
    Then all 4 jobs run
    And all 4 jobs return success

  Validator: F-1 (gh run list verification).
```

### Scenario 5: Subfolders bootstrapped for 5 brands

```gherkin
Feature: Brand subfolders exist as workspace members
  As Story 2-9 (lift)
  I need predictable subfolder structure
  So that code lifts have predictable destinations

  Scenario: 5 brand subfolders exist with placeholder structure
    Given the monorepo skeleton applied
    When inspecting repo root
    Then directory `core/` exists with `core/README.md`
    And directory `nicolify/` exists with `nicolify/README.md`
    And directory `vitalia/` exists with `vitalia/README.md`
    And directory `comunify/` exists with `comunify/README.md`
    And directory `lupulo/` exists with `lupulo/README.md`
    And each subfolder is registered as workspace member in pyproject.toml + pnpm-workspace.yaml

  Validator: F-2 + F-3.
```

### Scenario 6: `.claude-shared/` lifted from AISALESHT

```gherkin
Feature: Claude rules + skills + agents shared across workspace via single source
  As any Claude Code session in this monorepo
  I need consistent .claude/ rules + skills + agents
  So that conventions apply uniformly

  Scenario: .claude-shared directory populated from AISALESHT
    Given the AISALESHT lift step has run (cp -r)
    When inspecting `.claude-shared/` at repo root
    Then directory `.claude-shared/rules/` exists with > 20 rule files
    And directory `.claude-shared/skills/` exists with > 10 skills
    And directory `.claude-shared/agents/` exists
    And directory `.claude/` symlink (or copy) exists pointing to `.claude-shared/`

  Validator: F-4 + F-5.
```

### Scenario 7: Documentation seeded

```gherkin
Feature: Foundational docs exist
  Scenario: CONTRIBUTING.md + ARCHITECTURE.md + ADR README + RELEASES.md placeholder
    Given monorepo cloned
    When inspecting `docs/`
    Then `docs/CONTRIBUTING.md` exists describing Conventional Commits + PR flow + ADR rules
    And `docs/ARCHITECTURE.md` exists describing monorepo topology + subfolder layout
    And `docs/architecture/ADR/README.md` exists explaining ADR template
    And `docs/RELEASES.md` placeholder exists noting "publishing pipeline deferred to Story 9 (luana-v0-1-0-publish)"

  Validator: D-1 + D-2 + D-3 + D-4.
```

### Scenario 8: Architectural fitness tests bootstrap

```gherkin
Feature: Fitness tests prevent drift from foundation invariants
  As future stories
  I need failing tests when an invariant breaks
  So that drift surfaces immediately

  Scenario: fitness tests pass on clean foundation
    Given foundation T-1..T-6 complete
    When `cd nicolify && pytest tests/architecture/ -x -q` runs
    Then all bootstrap tests pass:
      | test_workspace_integrity         | uv + pnpm members resolve to actual dirs |
      | test_codeowners_present          | .github/CODEOWNERS exists with required rules |
      | test_adr_folder_present          | docs/architecture/ADR/README.md exists |
      | test_claude_shared_present       | .claude-shared/{rules,skills,agents}/ non-empty |
      | test_pr_template_present         | .github/PULL_REQUEST_TEMPLATE.md exists with required sections |

  Note: tests live initially in `nicolify/tests/architecture/` since
  nicolify is the canonical Python workspace. Cross-workspace fitness
  evolves in Story 2+.

  Validator: F-6.
```

## 2. Out of scope

- Code lift from AISALESHT (Story 2 — `luana-shared-lift`)
- GitHub Packages publishing pipeline (Story 9 — `luana-v0-1-0-publish`)
- semantic-release configuration (Story 9)
- Deploy K8s clusters (Stories 11-13)
- Define formal extension points (Story 8)
- Migrate Nicolify imports to package paths (Story 10)
- Multi-repo refactor (deferred until Chris contracts per-brand teams)
- Cross-org GitHub Project v2 board (single-repo monorepo → standard repo Projects suffice)

## 3. User flows (post-foundation)

Foundation enables these workflows:

1. **Story 2 lift starts:** `luana-shared-lift` lifts `shared/` to `core/shared/` (workspace-internal package). No GH Packages required — uv workspace + pnpm workspace handle internal deps.
2. **Single-repo PM:** GitHub repo Issues + Projects (built-in to repo) tracks 14 stories. Cross-org Projects v2 deferred (single repo doesn't need it).
3. **Conventional commits:** every merge to `main` follows format. Auto-versioning + publish DEFERRED until Story 9.
4. **Anti-island gates active from day 1:** CODEOWNERS + PR template + ADR folder ready when first collaborator onboards.

## 4. Out-of-scope explicit clarifications

- We do NOT migrate AISALESHT git history into the monorepo in this story (Story 10)
- We do NOT delete AISALESHT repo (it becomes `nicolify/` content post Story 10)
- We do NOT configure deployment K8s manifests beyond placeholder folders
- We do NOT create real Clerk apps for the 4 brands (Stories 11-13)
- We do NOT publish any package (Story 9) — workspace dependencies via uv `tool.uv.sources` + pnpm `workspace:*` protocol
- We do NOT install semantic-release (Story 9)
- We do NOT create `.npmrc` with publishConfig (Story 9)

## 5. Dependencies + blockers

- **Blocks:** Story 2 (luana-shared-lift) — without monorepo skeleton, no place to lift code
- **Blocked by:** Chris manual actions completed pre-Story-1:
  - ✅ Repo `alpacapurpura/luana-platform` created (private, empty) — DONE 2026-05-10
  - ✅ ADR-001 ratified — DONE 2026-05-10
  - ✅ Scope decisions ratified (monorepo + proprietary + defer publishing) — DONE 2026-05-10

## 6. Success metrics

- Monorepo cloned at `~/luana-platform/` with `main` branch protected
- CODEOWNERS + PR template + ADR folder seeded
- 5 subfolders (core/ + nicolify/ + vitalia/ + comunify/ + lupulo/) registered as workspace members
- `uv sync --all-packages` and `pnpm install` both green
- CI workflow green on at least 1 PR
- `.claude-shared/` populated with > 20 rules + > 10 skills

## 7. Estimated complexity

| Aspect | Estimate |
|---|---|
| Tickets | 7 atomic |
| Tool-time | 2-3 días Sonnet (mechanical, scope reduced vs v1) |
| Risk level | Low (no GH Packages auth surprises, single repo simpler) |
| Surface | Infra only (no business logic) |
| Owner eligibility | sonnet, opus (R23 N/A — pure infra setup) |

## 8. Glossary

- **Monorepo:** single git repo containing multiple workspace members (`core/` + 4 brands). Subfolders act as packages.
- **uv workspace:** Python package manager workspace (`tool.uv.workspace.members`). Internal deps via `tool.uv.sources` (no publish needed).
- **pnpm workspace:** TypeScript package manager workspace (`pnpm-workspace.yaml`). Internal deps via `workspace:*` protocol.
- **Turborepo:** build orchestrator for TypeScript monorepos with task pipeline + caching.
- **CODEOWNERS:** GitHub-native file declaring path-based reviewers for PRs.
- **ADR (Architecture Decision Record):** lightweight markdown doc capturing architectural decisions + rationale + alternatives + consequences.
- **Conventional Commits:** spec for commit messages: `<type>(<scope>): <description>` where types are `feat|fix|docs|chore|refactor|test|perf|ci|build`.

## 9. Ratification status

Chris ratified scope 2026-05-10 (verbal):
1. ✅ Monorepo at `alpacapurpura/luana-platform` (NOT 5 separate repos)
2. ✅ Proprietary license (private repo, "All rights reserved")
3. ✅ GH Packages publishing DEFERRED to Story 9
4. ✅ Branch protection: review_count=1 from day 1 (was 0 in v1 draft)
5. ✅ Anti-island scaffolding mandatory (CODEOWNERS + PR template + ADR folder)
6. ✅ Conventional Commits enforcement: pre-commit hook deferred to Story 1 final ticket if scope allows; otherwise backlog

## 10. Open guidelines questions for /architect (post Chris ratification)

None blocking. Technical decisions delegated to /architect:
- Single `pyproject.toml` workspace root vs hybrid (workspace root + per-brand pyproject)? Recommendation: workspace root + per-subfolder pyproject for `nicolify/` and `core/` (Python-heavy), placeholder for others.
- pnpm-workspace.yaml glob pattern? Recommendation: `packages: [core/*, nicolify, vitalia, comunify, lupulo]`.
- `.claude/` symlink vs copy? Recommendation: directory copy (Windows-compat for future Chris machines).
