---
story_id: luana-foundation
sequence_in_outcome: 1
po_version: 1
po_owner: claude-opus-4-7 (drafted as /po proxy)
ratified_by_chris: false                        # ★ awaiting Chris ratification ★
spec_type: service                              # no UI — pure infra setup
last_modified: 2026-05-09
---

# 01-spec — Luana Foundation

> **Status:** DRAFT — pending Chris ratification post 2026-05-11
> **Story type:** service (no UI deliverable)
> **Outcome:** luana-platform-migration (Story 1/14)

## 1. Acceptance Criteria (Gherkin AI-resistant)

### Scenario 1: GitHub Org + 5 repos exist

```gherkin
Feature: GitHub Organization bootstrap
  As Chris (founder)
  I need a GitHub Org with 5 private repos (1 core + 4 brands)
  So that Luana migration has its physical home

  Scenario: Org luana-platform exists with 5 expected repos
    Given Chris has authenticated `gh CLI` to his GitHub account
    When the Sunday playbook §3-§4 is executed
    Then the GitHub Org `luana-platform` exists
    And the org contains exactly 5 private repos with these names:
      | luana-core   |
      | nicolify     |
      | vitalia      |
      | comunify     |
      | lupulo-labs  |
    And each repo's default branch is `main`
    And each repo has branch protection enabled on `main` (PR mandatory, no direct push)

  Validator: `gh repo list luana-platform --json name,visibility,defaultBranchRef --limit 10` returns exactly 5 entries with visibility=PRIVATE and defaultBranchRef.name=main
```

### Scenario 2: luana-core monorepo skeleton functional

```gherkin
Feature: luana-core monorepo skeleton
  As Claude Code
  I need a working monorepo skeleton (uv + pnpm + turbo)
  So that subsequent stories can lift code into versioned packages

  Scenario: pyproject + package.json + turbo.json valid + lint runs
    Given `luana-core` repo is cloned locally
    And the skeleton from 05-cross-repo-tooling.md §5 has been applied
    When `uv sync --all-packages && pnpm install --frozen-lockfile` runs
    Then both succeed without errors
    When `uv run ruff check packages/python/ && pnpm lint` runs
    Then both pass with exit code 0

  Scenario: CI workflow green on first PR
    Given a stub commit pushed to a new branch
    When a PR is opened against `main`
    Then `.github/workflows/ci.yml` runs all 4 jobs (python-lint, python-test, ts-lint, ts-test)
    And all 4 jobs return success
```

### Scenario 3: GitHub Packages registry working end-to-end

```gherkin
Feature: GitHub Packages publish + install
  As a brand repo
  I need to install `luana-core-*` packages from GH Packages
  So that brands consume Luana versioned

  Scenario: stub package publishes successfully
    Given a stub package `luana-core-platform@0.0.1-alpha` exists in `packages/python/`
    When `uv publish` is invoked with `UV_PUBLISH_URL=https://npm.pkg.github.com` and valid `GITHUB_TOKEN`
    Then the package appears at `https://github.com/luana-platform/luana-core/packages`

  Scenario: stub brand installs the published package
    Given the stub package is published
    And a brand repo (any of vitalia/comunify/lupulo-labs/nicolify) has `.npmrc` configured per §11
    When `pip install luana-core-platform==0.0.1-alpha` runs in that brand
    Then the install succeeds
    And `python -c "import luana_core_platform; print(luana_core_platform.VERSION)"` outputs `0.0.1-alpha`
```

### Scenario 4: `.claude-shared/` subtree functional

```gherkin
Feature: Shared Claude rules across 5 repos via git subtree
  As any Claude Code session
  I need consistent .claude/rules + skills + agents across all 5 repos
  So that conventions don't drift

  Scenario: brand repo pulls .claude-shared from luana-core
    Given `luana-core` repo has `.claude-shared/{rules,skills,agents}/` populated from AISALESHT lift
    And brand repo (e.g. vitalia) has `git remote add luana-core` configured
    When `git subtree add --prefix=.claude --squash luana-core main` is executed in brand repo
    Then `.claude/rules/` contains all rules from luana-core .claude-shared/rules/
    And `.claude/skills/` contains all skills
    And `.claude/agents/` contains all agents

  Scenario: subtree update preserves brand-local edits
    Given a brand has the .claude subtree initially synced
    When luana-core .claude-shared/rules/new-rule.md is added and committed
    And `scripts/sync-claude-shared.sh` runs in brand repo
    Then brand repo's .claude/rules/new-rule.md exists
    And brand-local additions in .claude/local/ (if any) remain intact
```

### Scenario 5: GitHub Project v2 cross-org board

```gherkin
Feature: Cross-org roadmap visibility
  As Chris
  I need a unified board across 5 repos
  So that I see the migration roadmap holistically

  Scenario: project Luana Roadmap exists with custom fields
    Given GitHub Project v2 has been created via `gh project create`
    Then a project named "Luana Roadmap" exists at org luana-platform
    And the project has custom fields:
      | Brand | SINGLE_SELECT (luana-core, nicolify, vitalia, comunify, lupulo-labs) |
      | State | SINGLE_SELECT (refining, refined, ready, developing, developed, reviewing, done, parked, dropped) |
      | Story | TEXT |
```

### Scenario 6: Documentation seeded

```gherkin
Feature: Foundational docs in luana-core
  Scenario: docs/CONTRIBUTING.md + RELEASES.md + ARCHITECTURE.md exist
    Given `luana-core` repo is cloned
    When inspecting `docs/`
    Then file `docs/CONTRIBUTING.md` exists describing Conventional Commits + PR flow
    And file `docs/RELEASES.md` exists describing semver policy + semantic-release config
    And file `docs/ARCHITECTURE.md` exists linking to ADR-001
```

## 2. Out of scope

- Code lift from AISALESHT (Story 2)
- Deploy K8s clusters (Stories 11-13)
- Define formal extension points (Story 8)
- Migrate Nicolify imports (Story 10)

## 3. User flows (post-foundation)

Foundation enables these workflows:

1. **Story 2 lift starts:** `luana-shared-lift` can begin lifting `shared/` to packages because monorepo + CI + GH Packages publish pipeline exists
2. **Cross-repo PM:** GitHub Project v2 board shows all 14 stories' state across repos
3. **Subtree sync:** `.claude-shared/` rules updates flow `luana-core → 4 brands` via `scripts/sync-claude-shared.sh`
4. **Conventional commits + semantic-release:** every merge to `main` in luana-core auto-bumps semver + publishes packages

## 4. Out-of-scope explicit clarifications

- We do NOT migrate AISALESHT git history into luana-core in this story (Story 10)
- We do NOT delete AISALESHT repo (it becomes nicolify post Story 10)
- We do NOT configure deployment K8s manifests beyond placeholder folders
- We do NOT create real Clerk apps for the 4 brands (Stories 11-13)

## 5. Dependencies + blockers

- **Blocks:** Story 2 (luana-shared-lift) — without foundation, no place to lift code
- **Blocked by:** Chris manual actions (GitHub Org creation, 4 Claude subs purchase, ADR-001 ratification)

## 6. Success metrics

- 5 repos exist + accessible via `gh repo list luana-platform`
- 1 stub package successfully published + installed end-to-end
- 1 brand repo successfully subtree-pulled `.claude-shared/`
- CI workflow green on at least 1 PR in luana-core
- GitHub Project v2 board operational

## 7. Estimated complexity

| Aspect | Estimate |
|---|---|
| Tickets | 8-12 atomic |
| Tool-time | 3-5 días Sonnet/opencode (mechanical) |
| Risk level | Low (standard infra setup, no novel tech) |
| Surface | Infra only (no business logic) |
| Owner eligibility | opencode, sonnet, opus (R23 N/A) |

## 8. Glossary

- **Subtree:** git mechanism to embed an external repo's content as a subdirectory, with sync via pull/push (alternative to submodule, simpler operationally)
- **GitHub Packages:** GitHub's private package registry, supports npm + pip + maven + nuget + container; free with GitHub plan for private repos
- **semantic-release:** tool that automates versioning + changelog from Conventional Commits
- **Conventional Commits:** spec for commit messages: `<type>(<scope>): <description>` where types are `feat|fix|docs|chore|refactor|test|perf|ci|build`
- **Turborepo:** build orchestrator for TypeScript monorepos with remote caching
- **uv:** modern Python package manager replacing pip+poetry, supports workspaces

## 9. Pre-ratification questions for Chris

When you ratify Sunday, confirm or adjust:

1. **License placeholder:** ¿"All Rights Reserved" proprietary o algo MIT-flavored para Luana? (Mi recomendación: proprietary durante v0.x, considerar source-available post v1.0)
2. **GitHub Packages free tier suficiente?** Free = unlimited storage + unlimited bandwidth para private packages. Confirmá que tu plan GitHub permite.
3. **Branch protection: review count = 0** durante solo-tu, cambiar a `1` cuando contrates devs. ¿OK?
4. **Conventional Commits enforcement:** ¿pre-commit hook que bloquea commits sin formato? (Recomendado, evita drift)
5. **GitHub Actions minutes:** Free 2000min/mo private. Probable suficiente Sem 1-3, escalar Team plan ($4/user/mo) si excede.

Si alguno disent → comentar en el spec ratification, ajustamos.
