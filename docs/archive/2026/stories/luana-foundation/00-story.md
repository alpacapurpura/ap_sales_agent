# Story 1 — Luana Foundation

> **Outcome:** luana-platform-migration · **Sequence:** 1/14 · **State:** refining

## Why

Antes de cualquier code lift, necesitamos infraestructura de repos, packages, CI, y `.claude-shared/` subtree funcionando. Sin esto Story 2 (lift `shared/`) no tiene dónde publicar packages ni cómo consumir.

## What

Crear infraestructura repo + tooling cross-repo:

1. GitHub Org `luana-platform` (Chris manual)
2. 5 repos vacíos: `luana-core`, `nicolify`, `vitalia`, `comunify`, `lupulo-labs`
3. `luana-core` repo skeleton:
   - Monorepo: uv workspaces (Python) + pnpm workspaces + Turborepo (TS)
   - `pyproject.toml` workspace root
   - `package.json` workspace root
   - `turbo.json` build orchestration
   - `.github/workflows/`: lint + test + build + publish-on-tag
   - `semantic-release` config (Conventional Commits → semver bump auto)
   - GitHub Packages publish setup (Python via Twine to GH Packages, TS via npm publish to GH)
   - README + LICENSE (proprietary placeholder)
4. `.claude-shared/` subtree pattern:
   - `luana-core/.claude-shared/rules/` (lift from `nicolify/.claude/rules/`)
   - `luana-core/.claude-shared/skills/` (lift from `nicolify/.claude/skills/`)
   - Subtree pull instructions in each brand README
5. Brand repo skeletons (4):
   - `apps/api/` placeholder
   - `apps/web/` placeholder
   - `vertical-{niche}/` placeholder
   - `brand.config.{ts,py}` template
   - `deployments/` placeholder K8s manifests
   - `.claude/` subtree pull from luana-core
6. GitHub Project v2 cross-org "Luana Roadmap" board
7. CI baseline en cada brand repo (lint + test + build, sin publish)
8. Documentation: `luana-core/docs/CONTRIBUTING.md`, `luana-core/docs/RELEASES.md`, `luana-core/docs/ARCHITECTURE.md` (link to ADR-001)

## Acceptance criteria

- [ ] 5 repos exist and are accessible to Chris
- [ ] `luana-core` CI runs lint + test on every PR (initial green even without code)
- [ ] `luana-core` can publish a `0.0.1-alpha` package to GH Packages successfully (smoke test)
- [ ] Each brand repo can install `luana-core` package from GH Packages (auth via `GITHUB_TOKEN`)
- [ ] `.claude-shared/` subtree pull works in at least 1 brand repo (smoke test)
- [ ] GitHub Project v2 board created with brand-tagged columns
- [ ] `docs/CONTRIBUTING.md` documents PR flow + commit conventions
- [ ] `docs/RELEASES.md` documents semver policy + release process
- [ ] All 5 repos have `main` branch protected (PR mandatory, no direct push)
- [ ] All 5 repos have `development` branch deleted (single-repo legacy)

## Out of scope

- Lift any code from AISALESHT (Story 2+)
- Configure deployment to actual K8s clusters (Story 11-13)
- Define extension points formal (Story 8)

## Decisions cementadas (from ADR-001)

- Trunk-based `main` only + PR mandatory
- GitHub Packages private registry (free with org)
- semantic-release for auto-versioning
- `.claude-shared/` via git subtree (not submodule)

## Dependencies

- **Blocks:** luana-shared-lift (Story 2)
- **Blocked by:** ADR-001 ratificado + Chris crea GitHub Org + 4 Claude Code subs compradas

## Estimated effort

8-12 atomic tickets, ~3-5 días tool-time. Mostly mechanical setup. Sonnet/opencode acceptable owner.

## Risks

| Risk | Mitigation |
|---|---|
| GitHub Packages auth flow surprises | Story 1 incluye smoke test publish + install end-to-end |
| Subtree pull command UX raro | Script wrapper en `scripts/sync-claude-shared.sh` per brand |
| CI billing surprise (Actions paid tier) | Free 2000 min/mo, smoke test only Sem 1, scale Sem 4+ |
