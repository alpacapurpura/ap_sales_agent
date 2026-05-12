---
story_id: luana-v0-1-0-publish
arch_version: 1
architect_owner: claude-opus-4-7 (architect-orchestrator)
ratified_by_chris: true                          # ★ Pre-auth per outcome §7.5.2 D7=B + §7.1 scope ★
last_modified: 2026-05-12
links:
  spec: "01-spec.md"
  checkpoint: "checkpoint.md"
  outcome: "../../outcomes/luana-platform-migration.md"
  story_8_merge: "../../../archive/2026/stories/luana-campaigns-extension-sdk/07-merge.md"
  arch_be: "03-arch-be.md"
  validators: "04-validators.yaml"
  guidelines: "05-guidelines.md"
  tickets: "06-tickets.yaml"
---

# 03-arch — Story 9: Luana v0.1.0 Release Pipeline

> **Status:** READY · **Surface:** release engineering (cross-package, CI/CD, docs) · **Architect:** Claude Opus 4.7
> **Repo target:** `https://github.com/alpacapurpura/luana-platform.git` (private monorepo)
> **AISALESHT:** untouchable (V-NF cement cumulative 9 stories — diff scope ≤ Story 9 SSoT artifacts + outcome state)

## 0. Context summary

**Surface → builder → auditor mapping** (NO agentic surface; NO production_code; `R23 NOT triggered`):

| Surface | Owner | Builder | Auditor |
|---|---|---|---|
| Workspace version bumps (33 packages) | release | `dev-team` Sonnet | `auditor-backend` Opus |
| `.releaserc.json` + `.github/workflows/release.yml` | release | `dev-team` Sonnet | `auditor-backend` Opus |
| `CHANGELOG.md` + `docs/migration-from-nicolify.md` + `docs/api/` | docs | `dev-team` Sonnet | `auditor-backend` Opus |
| Smoke + downstream regression scripts | release | `dev-team` Sonnet | `auditor-backend` Opus |
| Arch fitness tests Story 9 (workspace versions + V-NF cement) | tests | `dev-team` Sonnet | `auditor-backend` Opus |

No agentic surface touched. Stories 6+7 frozen registries + Story 8 extension SDK = byte-stable invariant (V-AG-1..V-AG-2). NO Opus mandatory tickets.

**Spec resolution:**
- Publish target: **`v0.1.0`** (no `-alpha` suffix per 00-story "production-grade alpha" semantic — overrides checkpoint `publish_target: v0.1.0-alpha`).
- Pre-existing 40 sales-agent failures + 1 collection error: **DEFER to Story 10+ cleanup** (Story 9 = release infra, not test cleanup; documented in CHANGELOG.md "Known issues" + DEFERRED-FILES).

**Open question resolutions (architect Phase 0 cement, no Chris escalation):**

| # | Question | Architect decision | Rationale |
|---|---|---|---|
| 1 | Python API doc tool | **pdoc 14+** | spawn prompt suggests "simpler". pdoc = zero-config introspection; sphinx = full theme + sphinx.ext config (overkill). Output: HTML per module. |
| 2 | TS API doc tool | **typedoc 0.27+** | de facto standard. Output: HTML per package. |
| 3 | CHANGELOG format | **Keep-a-Changelog + cross-package sections** | semantic-release CAN auto-gen but Story 9 first release = manual emission (no prior Conventional Commits chain to derive from pre-`0.0.x-alpha`). v0.2.0+ auto-derived. |
| 4 | Release tool choice | **release-please (Google) — monorepo-native** | semantic-release-monorepo plugin has Python publishing gaps. release-please supports Python + TS multi-package, auto-PR pattern. **Fallback:** if release-please surfaces conflict, use changesets (TS-native) + custom Python publish script. |
| 5 | GitHub Pages | **NO deploy Story 9** — emit `docs/api/` artifacts only | Stories 14+ marketing scope. Reduces Story 9 attack surface. |
| 6 | Brand app stubs version | **Bump to `0.1.0`** for workspace coherence | mechanical bump, ~4 files. Future Stories 11-13 will re-evaluate per-brand. |
| 7 | First tag procedure | **Manual `git tag v0.1.0 && git push origin v0.1.0`** | release-please typically creates PR + tag from `feat:` commits. Pre-alpha history doesn't derive → manual override documented in `docs/RELEASES.md`. |
| 8 | Workflow build parallelization | **Single sequential job per language (build → publish)** with `pnpm -r` + `uv build --all` | 33 packages × ~10-20s build each = ~5-10min total. Below 6h GitHub Actions cap. Matrix split only if real measurement exceeds 30min. |

**Skills consulted:**
- `backend-expert` — release infra patterns, idempotent migrations parallel (no DB migrations here but pattern applies to docs gen scripts)
- `tessl__fastapi` — N/A (no FastAPI surface)
- `tessl__graceful-degradation` — applied to workflow failure modes (publish-python fails → release create skipped, fail-fast invariant Scenario 5)
- `copilot-expert` + `sales-agent-expert` — consulted for V-AG-1..V-AG-2 (Stories 6+7 byte-stable + Story 8 SDK byte-stable) — no surface touched

**Existing systems audit (NO NEW LAYER rule — anti-duplication.md):**

Story 9 is **first release pipeline** for luana-platform monorepo. Pre-flight grep:

```bash
find /home/chris/luana-platform -name ".releaserc*" -o -name "release.yml" -o -name "release-please-config.json" 2>/dev/null
# → empty (no existing release tool — NEW layer required)

find /home/chris/luana-platform -name "CHANGELOG.md" 2>/dev/null
# → empty (NEW)

find /home/chris/luana-platform/docs -name "api" -type d 2>/dev/null
# → empty (NEW)

find /home/chris/luana-platform -name "migration*.md" 2>/dev/null
# → empty (NEW)
```

**Decision per system:**
- `.releaserc.json` / release.yml → **NEW** (no existing equivalent — Story 1 deferred per outcome §7.1)
- `CHANGELOG.md` → **NEW** (first release)
- `docs/migration-from-nicolify.md` → **NEW** (consumer migration guide first emission)
- `docs/api/` → **NEW** (auto-gen docs first emission)
- `docs/RELEASES.md` → **EXTEND** (existing Story 1 placeholder — append v0.1.0 procedure + rollback + token setup)
- `docs/extension-points.md` → **EXTEND** (Story 8 deliverable — bump header `v0.1.0 (alpha)` → `v0.1.0 (production-grade alpha)`)

Cross-module audit grep (no existing release/publish layer cross-codebase — confirmed NEW layer is sole option):

```bash
grep -rn "semantic-release\|release-please\|changesets" /home/chris/luana-platform/ 2>/dev/null
# → empty
grep -rn "uv publish\|twine\|npm publish" /home/chris/luana-platform/ 2>/dev/null
# → empty
```

Anti-duplication cleared: NO parallel layer being introduced. Single release pipeline at workspace root = canonical.

## 1. High-level architecture

```
luana-platform/                                            ← monorepo target (private)
├── .github/
│   └── workflows/
│       ├── ci.yml                                          ← Story 1 baseline (UNTOUCHED Story 9)
│       └── release.yml                                     ← ★ NEW Story 9 ★ (tag-triggered)
├── .releaserc.json                                         ← ★ NEW Story 9 ★ (release-please config)
│       OR release-please-config.json + .release-please-manifest.json
├── CHANGELOG.md                                            ← ★ NEW Story 9 ★ (Keep-a-Changelog cross-pkg)
├── core/
│   ├── pyproject.toml                                      ← bump 0.0.1-alpha → 0.1.0
│   ├── @luana/
│   │   ├── api-client/package.json                         ← bump 0.0.1-alpha → 0.1.0
│   │   ├── design-tokens/package.json                      ← bump 0.0.1-alpha → 0.1.0
│   │   ├── extension-sdk/package.json                      ← bump 0.0.8-alpha → 0.1.0
│   │   ├── format/package.json                             ← bump 0.0.1-alpha → 0.1.0
│   │   ├── hooks/package.json                              ← bump 0.0.1-alpha → 0.1.0
│   │   ├── schemas/package.json                            ← bump 0.0.1-alpha → 0.1.0
│   │   └── ui-kit/package.json                             ← bump 0.0.1-alpha → 0.1.0
│   └── luana-core-*/pyproject.toml (26 pkgs)               ← bump all to 0.1.0
├── apps/
│   └── test-brand/pyproject.toml                           ← bump 0.0.8-alpha → 0.1.0
├── nicolify|vitalia|comunify|lupulo/                       ← bump 0.0.1-alpha → 0.1.0 (coherence)
│   ├── pyproject.toml
│   └── package.json
├── pyproject.toml (workspace root)                         ← bump (no [project] → no-op OR cosmetic version annotation)
├── package.json (workspace root)                           ← bump 0.0.1-alpha → 0.1.0
├── docs/
│   ├── ARCHITECTURE.md                                     ← Story 1 (UNTOUCHED)
│   ├── CONTRIBUTING.md                                     ← Story 1 (UNTOUCHED)
│   ├── RELEASES.md                                         ← EXTEND (append v0.1.0 procedure + rollback + token setup + SemVer F1-F6)
│   ├── extension-points.md                                 ← EXTEND header stamp v0.1.0
│   ├── migration-from-nicolify.md                          ← ★ NEW Story 9 ★ (consumer guide)
│   ├── api/
│   │   ├── python/                                         ← ★ NEW ★ (pdoc HTML 26 packages)
│   │   └── typescript/                                     ← ★ NEW ★ (typedoc HTML 7 packages)
│   └── architecture/ (Story 1 ADRs UNTOUCHED)
├── scripts/
│   ├── generate_api_docs.sh                                ← ★ NEW Story 9 ★ (pdoc + typedoc runner)
│   └── publish_smoke_test.sh                               ← ★ NEW Story 9 ★ (post-publish consumer install)
└── tests/architecture/                                     ← ★ NEW Story 9 dir if first ★
    ├── test_workspace_versions_uniform_at_v0_1_0.py        ← V-NF-2/3 cement
    ├── test_release_workflow_yaml_valid.py                 ← V-F-release-2/3 cement
    ├── test_docs_v0_1_0_deliverables_present.py            ← V-D-1..V-D-5 cement
    └── test_aisaleshT_untouched_story_9.py                 ← V-NF-aisaleshT cement (best-effort)
```

## 2. Tech stack decisions

| Layer | Choice | Rationale | Fallback |
|---|---|---|---|
| Release orchestrator | **release-please 16+** (Google) | Monorepo-native (Python + TS), PR-based pattern, no plugin compat issues vs semantic-release-monorepo | If conflict → changesets (TS-native) + custom Python publish bash script |
| Python publisher | **`uv publish`** (Astral 0.5+) | Native to monorepo uv workspace, supports `--publish-url` for GH Packages PyPI registry | twine (older but stable) |
| TS publisher | **`pnpm publish -r`** (recursive) | Native pnpm monorepo, `--publish-branch=main` + `--no-git-checks` for CI | npm publish (per-pkg loop) |
| Python API docs | **pdoc 14+** | Zero-config, HTML output, runs `pdoc ./src/luana_core_X --output-dir docs/api/python/luana-core-X` | sphinx-autoapi (heavier) |
| TS API docs | **typedoc 0.27+** | De facto, TS-native, HTML output, `typedoc --entryPointStrategy packages` for monorepo | api-extractor (Microsoft, heavier) |
| Changelog generator | **manual Keep-a-Changelog seed v0.1.0** + release-please auto-derive v0.2.0+ | First release has no Conv Commits chain → manual seed mandatory | git-cliff (Rust, but adds toolchain) |
| Workflow lint | **`actionlint`** (rhymeswithmonth/actionlint-action@v0.6) | De facto GH Actions YAML linter | `yamllint` (less specific) |
| YAML schema validation | **stdlib `yaml.safe_load` + json schema verify in Python arch test** | Avoid new dep | — |
| Conventional Commits enforcement | **commitlint pre-commit hook** + release-please conventional-commits parser | Cement SemVer F1-F6 from v0.1.0 onwards | manual review |

## 3. Workflow architecture (`.github/workflows/release.yml`)

```yaml
name: Release

on:
  push:
    tags: ['v*.*.*']

jobs:
  validate-tag:
    name: validate-tag
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.parse.outputs.version }}
    steps:
      - uses: actions/checkout@v4
      - id: parse
        run: |
          TAG="${GITHUB_REF#refs/tags/}"
          VERSION="${TAG#v}"
          # validate SemVer
          if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.-]+)?$ ]]; then
            echo "::error::Tag '$TAG' is not valid SemVer"
            exit 1
          fi
          echo "version=$VERSION" >> "$GITHUB_OUTPUT"

  build-python:
    needs: validate-tag
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with:
          python-version: "3.12"
      - run: uv sync --all-packages --frozen
      - name: Build all Python packages
        run: |
          for pkg in core/luana-core-* apps/test-brand; do
            if [ -f "$pkg/pyproject.toml" ]; then
              echo "Building $pkg"
              uv build --package $(basename "$pkg") --out-dir dist/
            fi
          done
      - uses: actions/upload-artifact@v4
        with:
          name: python-dist
          path: dist/
          retention-days: 7

  build-typescript:
    needs: validate-tag
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: "pnpm"
      - run: pnpm install --frozen-lockfile
      - run: pnpm -r --filter "./core/@luana/*" build
      - uses: actions/upload-artifact@v4
        with:
          name: typescript-dist
          path: core/@luana/*/dist/
          retention-days: 7

  publish-python:
    needs: [validate-tag, build-python, build-typescript]
    runs-on: ubuntu-latest
    timeout-minutes: 15
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - uses: actions/download-artifact@v4
        with:
          name: python-dist
          path: dist/
      - name: Publish to GitHub Packages
        env:
          UV_PUBLISH_TOKEN: ${{ secrets.GH_PACKAGES_TOKEN || secrets.GITHUB_TOKEN }}
          UV_PUBLISH_URL: https://pypi.pkg.github.com/alpacapurpura/
        run: |
          # Fail-fast: if no token, error explicitly with actionable hint
          if [ -z "$UV_PUBLISH_TOKEN" ]; then
            echo "::error::No GH Packages token. Set GH_PACKAGES_TOKEN secret OR ensure GITHUB_TOKEN has write:packages scope. See docs/RELEASES.md §Token-setup"
            exit 1
          fi
          # Publish each wheel/sdist atomically (per-package, fail-fast)
          for f in dist/*.tar.gz dist/*.whl; do
            echo "Publishing $f"
            uv publish "$f" || { echo "::error::Publish failed for $f. Verify GITHUB_TOKEN has write:packages scope OR set GH_PACKAGES_TOKEN secret per docs/RELEASES.md §Token-setup"; exit 1; }
          done

  publish-typescript:
    needs: [validate-tag, build-typescript, publish-python]
    runs-on: ubuntu-latest
    timeout-minutes: 10
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          registry-url: "https://npm.pkg.github.com/"
          scope: "@luana"
      - uses: actions/download-artifact@v4
        with:
          name: typescript-dist
          path: core/@luana/
      - run: pnpm install --frozen-lockfile
      - name: Publish @luana/* to GitHub Packages
        env:
          NODE_AUTH_TOKEN: ${{ secrets.GH_PACKAGES_TOKEN || secrets.GITHUB_TOKEN }}
        run: |
          pnpm -r --filter "./core/@luana/*" publish \
            --registry=https://npm.pkg.github.com/ \
            --no-git-checks \
            --access restricted

  create-github-release:
    needs: [validate-tag, publish-python, publish-typescript]
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Extract changelog section
        id: changelog
        run: |
          VERSION="${{ needs.validate-tag.outputs.version }}"
          # Extract section from CHANGELOG.md between '## [VERSION]' and next '## ['
          awk -v ver="$VERSION" '
            /^## \[/ {if (found) exit; if ($0 ~ "\\[" ver "\\]") found=1; next}
            found {print}
          ' CHANGELOG.md > release_notes.md
      - name: Create GitHub release
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          VERSION="${{ needs.validate-tag.outputs.version }}"
          gh release create "v${VERSION}" \
            --title "v${VERSION}" \
            --notes-file release_notes.md \
            --target main

  smoke-test-published:
    needs: [validate-tag, publish-python, publish-typescript]
    runs-on: ubuntu-latest
    timeout-minutes: 10
    if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/v')
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          registry-url: "https://npm.pkg.github.com/"
          scope: "@luana"
      - name: Run smoke test against published packages
        env:
          UV_PUBLISH_TOKEN: ${{ secrets.GH_PACKAGES_TOKEN || secrets.GITHUB_TOKEN }}
          NODE_AUTH_TOKEN: ${{ secrets.GH_PACKAGES_TOKEN || secrets.GITHUB_TOKEN }}
        run: bash scripts/publish_smoke_test.sh "${{ needs.validate-tag.outputs.version }}"
```

**Key invariants encoded:**
- **Fail-fast atomicity** (Scenario 5): publish-python depends on build-python AND build-typescript both green → no partial publish.
- **Atomic-ish per-language**: publish-typescript depends on publish-python success → if Python fails, TS never starts (no half-released registry state).
- **Smoke test gate** (Scenario 3): runs after publish; failure ≠ rollback (already published) but flags follow-up cleanup needed.
- **Tag validation** (V-F-release-3): SemVer regex enforced before any build.
- **Timeout per job**: each ≤ 20min, cumulative ≤ ~1.5h well below 6h GH Actions cap.

## 4. release-please config (`.releaserc.json` → actually `release-please-config.json`)

> Architect choice: release-please over semantic-release-monorepo. Story 9 first tag is **manual** (`git tag v0.1.0`); release-please takes over for v0.2.0+ via auto-PR pattern.

`release-please-config.json` (workspace root):

```json
{
  "$schema": "https://raw.githubusercontent.com/googleapis/release-please/main/schemas/config.json",
  "release-type": "python",
  "packages": {
    "core/luana-core-platform": {"release-type": "python", "package-name": "luana-core-platform"},
    "core/luana-core-llm": {"release-type": "python", "package-name": "luana-core-llm"},
    "core/luana-core-channels": {"release-type": "python", "package-name": "luana-core-channels"},
    "core/luana-core-idempotency": {"release-type": "python", "package-name": "luana-core-idempotency"},
    "core/luana-core-observability": {"release-type": "python", "package-name": "luana-core-observability"},
    "core/luana-core-events": {"release-type": "python", "package-name": "luana-core-events"},
    "core/luana-core-extraction": {"release-type": "python", "package-name": "luana-core-extraction"},
    "core/luana-core-compliance": {"release-type": "python", "package-name": "luana-core-compliance"},
    "core/luana-core-billing": {"release-type": "python", "package-name": "luana-core-billing"},
    "core/luana-core-iam": {"release-type": "python", "package-name": "luana-core-iam"},
    "core/luana-core-tenant-profile": {"release-type": "python", "package-name": "luana-core-tenant-profile"},
    "core/luana-core-tenant-domains": {"release-type": "python", "package-name": "luana-core-tenant-domains"},
    "core/luana-core-commercial-calendar": {"release-type": "python", "package-name": "luana-core-commercial-calendar"},
    "core/luana-core-social-proof": {"release-type": "python", "package-name": "luana-core-social-proof"},
    "core/luana-core-assets": {"release-type": "python", "package-name": "luana-core-assets"},
    "core/luana-core-crm": {"release-type": "python", "package-name": "luana-core-crm"},
    "core/luana-core-analytics-engine": {"release-type": "python", "package-name": "luana-core-analytics-engine"},
    "core/luana-core-landing": {"release-type": "python", "package-name": "luana-core-landing"},
    "core/luana-core-connections": {"release-type": "python", "package-name": "luana-core-connections"},
    "core/luana-core-brand-studio": {"release-type": "python", "package-name": "luana-core-brand-studio"},
    "core/luana-core-offer-studio": {"release-type": "python", "package-name": "luana-core-offer-studio"},
    "core/luana-core-copilot": {"release-type": "python", "package-name": "luana-core-copilot"},
    "core/luana-core-sales-agent": {"release-type": "python", "package-name": "luana-core-sales-agent"},
    "core/luana-core-campaigns": {"release-type": "python", "package-name": "luana-core-campaigns"},
    "core/luana-core-extension-sdk": {"release-type": "python", "package-name": "luana-core-extension-sdk"},
    "core/@luana/api-client": {"release-type": "node", "package-name": "@luana/api-client"},
    "core/@luana/design-tokens": {"release-type": "node", "package-name": "@luana/design-tokens"},
    "core/@luana/extension-sdk": {"release-type": "node", "package-name": "@luana/extension-sdk"},
    "core/@luana/format": {"release-type": "node", "package-name": "@luana/format"},
    "core/@luana/hooks": {"release-type": "node", "package-name": "@luana/hooks"},
    "core/@luana/schemas": {"release-type": "node", "package-name": "@luana/schemas"},
    "core/@luana/ui-kit": {"release-type": "node", "package-name": "@luana/ui-kit"}
  },
  "plugins": [
    {"type": "linked-versions", "name": "luana-platform", "components": ["luana-core-*", "@luana/*"]}
  ],
  "include-component-in-tag": false,
  "tag-separator": "-",
  "draft": false,
  "prerelease": false
}
```

`.release-please-manifest.json` (workspace root — seed at v0.1.0):

```json
{
  "core/luana-core-platform": "0.1.0",
  "core/luana-core-llm": "0.1.0",
  "core/luana-core-channels": "0.1.0",
  "_": "...all 33 packages at 0.1.0 (see workspace inventory §3.1+§3.2 of 01-spec.md)..."
}
```

**Linked versions** plugin ensures all 33 packages bump together (single `v0.1.0` tag, not per-pkg tags). Reflects monorepo coherence.

## 5. Version bump strategy

Two viable mechanical approaches:

**Option A — bash sed loop (selected — simpler):**

```bash
# Python: sed inline replace
for pyproject in core/pyproject.toml core/luana-core-*/pyproject.toml apps/test-brand/pyproject.toml \
                 nicolify/pyproject.toml vitalia/pyproject.toml comunify/pyproject.toml lupulo/pyproject.toml; do
  sed -i 's/^version = "0\.0\.[0-9]*-alpha"$/version = "0.1.0"/' "$pyproject"
done

# TS: pnpm version (idempotent, also updates internal workspace refs)
pnpm -r --filter "./core/@luana/*" exec npm version 0.1.0 --no-git-tag-version
# Manual edit for brand stubs (not part of pnpm filter):
for pkgjson in nicolify/package.json vitalia/package.json comunify/package.json lupulo/package.json package.json; do
  sed -i 's/"version": "0\.0\.[0-9]*-alpha"/"version": "0.1.0"/' "$pkgjson"
done

# Regen lockfiles
uv lock --upgrade
pnpm install --lockfile-only
```

**Option B — release-please bootstrap PR (deferred to v0.2.0+):** release-please runs in CI on `main` merge → creates PR with version bumps. Story 9 first release: manual sed (Option A) because no Conv Commits chain to derive from.

**Cross-package internal deps audit (Risk 7):** all current internal refs use `{ workspace = true }` (Python) or `workspace:*` (TS) per Story 1-8 lift mode. NO hardcoded `0.0.x-alpha` pins → grep confirms (architect verified). Lift mode discipline pays off.

## 6. Smoke test script (`scripts/publish_smoke_test.sh`)

```bash
#!/bin/bash
set -euo pipefail

VERSION="${1:-0.1.0}"
SMOKE_DIR=$(mktemp -d -t luana-smoke-XXXXXX)

cleanup() { rm -rf "$SMOKE_DIR"; }
trap cleanup EXIT

echo "Smoke test against published v${VERSION} in ${SMOKE_DIR}"

# Python smoke
cd "$SMOKE_DIR"
cat > pyproject.toml <<EOF_PY
[project]
name = "smoke-test"
version = "0.0.0"
requires-python = ">=3.12"
dependencies = [
    "luana-core-platform==${VERSION}",
    "luana-core-extension-sdk==${VERSION}",
]

[[tool.uv.index]]
name = "github"
url = "https://pypi.pkg.github.com/alpacapurpura/simple/"
default = false
EOF_PY

# Auth env
echo "machine pypi.pkg.github.com login alpacapurpura password ${UV_PUBLISH_TOKEN}" > ~/.netrc
chmod 600 ~/.netrc

uv sync
uv run python -c "from luana_core_platform import __version__; assert __version__ == '${VERSION}', f'got {__version__}'; print('luana-core-platform==${VERSION} installed OK')"
uv run python -c "from luana_core_extension_sdk import ExtensionPointRegistry, BrandContext; r = ExtensionPointRegistry(); print('luana-core-extension-sdk==${VERSION} installed OK')"

# TS smoke
mkdir ts-smoke && cd ts-smoke
cat > .npmrc <<EOF_NPM
@luana:registry=https://npm.pkg.github.com/
//npm.pkg.github.com/:_authToken=${NODE_AUTH_TOKEN}
EOF_NPM
cat > package.json <<EOF_PKG
{"name": "smoke", "version": "0.0.0", "dependencies": {"@luana/extension-sdk": "${VERSION}"}}
EOF_PKG
npm install
node -e "const sdk = require('@luana/extension-sdk'); if (Object.keys(sdk).length === 0) { console.error('SDK empty'); process.exit(1); } console.log('@luana/extension-sdk@${VERSION} installed OK')"

echo "=== SMOKE TEST GREEN — v${VERSION} consumable from published registry ==="
```

## 7. CHANGELOG.md seed (Keep-a-Changelog)

```markdown
# Changelog

All notable changes to the Luana Platform are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [SemVer](https://semver.org/spec/v2.0.0.html) per `docs/RELEASES.md` §SemVer.

## [0.1.0] — 2026-05-XX

> **First production-grade alpha release** — Stories 1-9 of outcome `luana-platform-migration`.
> Proprietary license · GitHub Packages private registry · Cross-package SemVer cement.

### Release Engineering (Story 9)
- Introduce GitHub Packages publish pipeline (Python + TypeScript)
- Add `.github/workflows/release.yml` tag-triggered automation
- Add `release-please-config.json` for v0.2.0+ auto-derivation
- Add `docs/migration-from-nicolify.md` consumer migration guide
- Add `docs/api/` auto-gen API reference (pdoc + typedoc)
- Cement SemVer F1-F6 discipline (see `docs/RELEASES.md` §SemVer)

### Foundations (Story 1 — luana-foundation)
- Bootstrap monorepo `alpacapurpura/luana-platform` (private, proprietary)
- CODEOWNERS + PR template + ADR folder + branch protection
- uv + pnpm + Turborepo workspace skeleton
- `.claude-shared/` lifted from AISALESHT
- CI baseline (`.github/workflows/ci.yml`)

### Shared lift (Story 2)
- `luana-core-platform` — core platform abstractions
- `luana-core-llm` — LLM provider routing + LiteLLM proxy
- `luana-core-channels` — multi-channel format dispatcher
- `luana-core-idempotency` — idempotency keys + Redis sliding window
- `luana-core-observability` — `BaseAgentCallbackHandler` + `BaseObservabilityContext` + cost recorder
- `luana-core-events` — domain events + outbox pattern
- `luana-core-extraction` — wave-based LLM extraction orchestrator
- `luana-core-compliance` — compliance gates
- `luana-core-billing` — `BudgetGuard` + `OutboundRateLimiter` + plan config

### IAM + Tenancy + Content (Story 3)
- `luana-core-iam` — Clerk integration + tenant scoping
- `luana-core-tenant-profile` — business types + tenant profile (post-2026-04-20 SSoT)
- `luana-core-tenant-domains` — domain management
- `luana-core-commercial-calendar` — commercial calendar engine
- `luana-core-social-proof` — testimonials + placements M:N
- `luana-core-assets` — asset management

### CRM + Analytics + Landing + Connections (Story 4)
- `luana-core-crm` — lifecycle + deals
- `luana-core-analytics-engine` — ETL contract + stage services + Bowtie funnel
- `luana-core-landing` — landing template engine
- `luana-core-connections` — channel connection providers

### Brand + Offer Studios (Story 5)
- `luana-core-brand-studio` — brand identity + PersonalityProfile v2 compiler + buyer personas
- `luana-core-offer-studio` — 7 catalogs DAG + 84 presets + field-contract platform

### Copilot Engine (Story 6)
- `luana-core-copilot` — LangGraph 2.0 + deepagents harness + 11 phases (F0-F11) + observability
- 5 registries frozen (Tool + Workflow + Extractor + Module + Suggestion)

### Sales Agent Engine (Story 7)
- `luana-core-sales-agent` — StateGraph + specialists + Closer Studio + BrandVoicePort

### Campaigns + Extension SDK (Story 8)
- `luana-core-campaigns` — drip campaigns + workers
- `luana-core-extension-sdk` — 18 EPs + 5 CC policies + BrandContext frozen 9-field
- `@luana/extension-sdk` — TS type mirror (EP-6 + EP-10 + EP-18)
- `apps/test-brand` smoke pack (10 scenarios GREEN)
- `docs/extension-points.md` 1354-line spec

### TypeScript packages
- `@luana/api-client`, `@luana/design-tokens`, `@luana/format`, `@luana/hooks`, `@luana/schemas`, `@luana/ui-kit` — all bumped to v0.1.0 (Stories 2+5 lift)

### Known issues
- `luana-core-sales-agent` ships with 40 pre-existing test failures + 1 collection error (Story 7 carry-over per 07-merge.md PRE-1/PRE-2/PRE-3). Trivial test fixture issues. Scheduled for Story 10+ cleanup.
- Integration smoke test against published packages requires `EVAL_SMOKE_PUBLISH=1` env gate (default off in local dev).

### Migration from Nicolify
See `docs/migration-from-nicolify.md` for consumer guide. Story 10 (`luana-nicolify-migration`) executes the migration.

[0.1.0]: https://github.com/alpacapurpura/luana-platform/releases/tag/v0.1.0
```

## 8. Migration guide (`docs/migration-from-nicolify.md`) — section outline

```markdown
# Migration from Nicolify (AISALESHT) to Luana Platform v0.1.0

## §1 Audience
Nicolify maintainers (Chris team) + future brand consumers (Vitalia, Comunify, Lupulo bootstrap teams).

## §2 Pre-migration checklist
- Python ≥ 3.12 (verify `python --version`)
- Node ≥ 22 (verify `node --version`)
- pnpm ≥ 9 (verify `pnpm --version`)
- uv installed (Astral, verify `uv --version`)
- `~/.netrc` or `pip config` configured for `https://pypi.pkg.github.com/alpacapurpura/`
- `~/.npmrc` configured for `@luana:registry=https://npm.pkg.github.com/`
- `GH_PACKAGES_TOKEN` env var with `read:packages` scope (or `GITHUB_TOKEN` from `gh auth login`)

## §3 Import migration mapping
| Old (AISALESHT) | New (Luana) |
|---|---|
| `from src.shared.agent_observability.X` | `from luana_core_observability.X` |
| `from src.shared.events.X` | `from luana_core_events.X` |
| `from src.shared.billing.X` | `from luana_core_billing.X` |
| `from src.modules.copilot.X` | `from luana_core_copilot.X` |
| `from src.modules.sales_agent.X` | `from luana_core_sales_agent.X` |
| `from src.modules.brand.X` | `from luana_core_brand_studio.X` |
| `from src.modules.offer.X` | `from luana_core_offer_studio.X` |
| ...26 packages total — see `core/README.md` per-package mapping... |
| TS `from '@/components/...'` | `from '@luana/ui-kit/...'` |
| TS `from '@/lib/api-client'` | `from '@luana/api-client'` |
| TS `from '@/lib/format'` | `from '@luana/format'` |

## §4 Dependency installation
- Python: `uv add luana-core-platform==0.1.0` (or `pip install`)
- TS: `pnpm add @luana/extension-sdk@0.1.0`
- Required auth: see §2 pre-migration checklist
- Full inventory: see `docs/api/python/` + `docs/api/typescript/` for package surface

## §5 Extension SDK consumer pattern
See `docs/extension-points.md` for full spec. Quickstart:
```python
from fastapi import FastAPI
from luana_core_extension_sdk import ExtensionPointRegistry, BrandContext

registry = ExtensionPointRegistry()
# ... register handlers per docs/extension-points.md §2 ...
registry.lock()  # immutable post-startup per CC-5
app = FastAPI(lifespan=lambda app: registry_lifespan(registry, app))
```

## §6 Troubleshooting
| Error | Remediation |
|---|---|
| `403 Forbidden` on pip install | Verify `~/.netrc` has token with `read:packages`. Regen via `gh auth login --scopes read:packages,write:packages` |
| `Cannot find module '@luana/X'` | Verify `~/.npmrc` has `@luana:registry=https://npm.pkg.github.com/` + `//npm.pkg.github.com/:_authToken=...` |
| `version mismatch` | Pin all `luana-core-*` packages to same version (e.g., `==0.1.0`). Cross-pkg deps strict-pin |
| `namespace not registered` | Set `LUANA_BRAND_SLUG=nicolify` env var. Required by Extension SDK §CC-4 |
```

## 9. Test surfaces (TDD-mandatory)

Story 9 = pure infra. Tests are arch fitness + workflow YAML validation + smoke scripts. RED→GREEN per layer:

### Arch fitness (`tests/architecture/` — new dir if first)

1. **`test_workspace_versions_uniform_at_v0_1_0.py`** (V-NF-2/3/4/5)
   - Walks `core/luana-core-*/pyproject.toml` + `core/@luana/*/package.json` + `apps/test-brand/pyproject.toml` + brand stubs
   - asserts `version == "0.1.0"` for each
   - asserts no `-alpha` substring in any version field

2. **`test_release_workflow_yaml_valid.py`** (V-F-release-2/3)
   - Parses `.github/workflows/release.yml` with PyYAML
   - asserts top-level `on.push.tags` contains `'v*.*.*'`
   - asserts jobs `validate-tag`, `build-python`, `build-typescript`, `publish-python`, `publish-typescript`, `create-github-release`, `smoke-test-published` all present
   - asserts `publish-typescript` depends_on `publish-python` (atomicity)

3. **`test_releaserc_config_valid.py`** (V-F-release-1)
   - Parses `release-please-config.json` as JSON
   - asserts 33 entries in `packages` (26 Python + 7 TS)
   - asserts `.release-please-manifest.json` matches version `0.1.0` across all packages

4. **`test_docs_v0_1_0_deliverables_present.py`** (V-D-1..V-D-5)
   - asserts `CHANGELOG.md` exists + contains `## [0.1.0]`
   - asserts `docs/migration-from-nicolify.md` exists + has §1..§6 headers
   - asserts `docs/api/python/` + `docs/api/typescript/` dirs exist + non-empty
   - asserts `docs/RELEASES.md` updated (contains "v0.1.0" + "SemVer F1-F6")
   - asserts `docs/extension-points.md` header bumped (regex `v0.1.0.*production-grade alpha`)

5. **`test_aisaleshT_untouched_story_9.py`** (V-NF-AISALESHT — best-effort)
   - Best-effort guard: emits warning if env `AISALESHT_PATH` is set; otherwise skips
   - When set: `git -C $AISALESHT_PATH diff --name-only main..development -- backend/ frontend/` → asserts empty

### Validators (executable shell — see `04-validators.yaml`)

Same 26+ validators per `01-spec.md` §12 preview, fleshed out in `04-validators.yaml`.

### Smoke tests

- `scripts/publish_smoke_test.sh ${VERSION}` — runs against published packages (env-gated)
- `apps/test-brand/tests/` re-run with `STORY_9_PUBLISH_REGRESSION=1` (Scenario 4)

## 10. Validators preview (full list — 04-validators.yaml emits)

20 validators across 4 categories. See `04-validators.yaml`.

| Category | Count | Examples |
|---|---|---|
| `non_functional` | 6 | V-NF-1 AISALESHT untouched, V-NF-2 all Python pkgs at 0.1.0, V-NF-3 no -alpha retained, V-NF-4 test-brand bumped, V-NF-5 root coherence, V-NF-6 brand stubs bumped |
| `functional` | 8 | V-F-release-1..8 (releaserc + workflow yaml + tag trigger + CHANGELOG + migration guide + api/ + dry-run + lockfile regen) |
| `agentic_integration` | 4 | V-AG-1 test-brand smoke vs published, V-AG-2 downstream regression Stories 1-8, V-AG-3 EP-3 ToolRegistry golden, V-AG-4 EP-4 WorkflowRegistry golden, V-AG-5 5 critical EPs callable from registry |
| `documentation` | 5 | V-D-1..V-D-5 |

Plus halt criterion validators:
- **V-X-1** GH Packages auth halt criterion documented (Scenario 5)

Total: ~22 validators, all must_pass.

## 11. SemVer cement (F1-F6 documented in `docs/RELEASES.md`)

Per 01-spec.md §11. Architect ratifies:
- F1 major: EP signature change → `feat!:` + `BREAKING CHANGE:` footer
- F2 minor: New EP added OR additive BrandContext field
- F3 patch: Bug fix without API change
- F4 minor: BrandContext optional field with default
- F5 major: BrandContext field removal
- F6 special: Default flag flip side-effect — major + audit body required

Enforcement layers:
- release-please conventional-commits parser
- Pre-commit hook commitlint (Story 10+ may add — Story 9 doc-only)
- Auditor C4 manual review
- `docs/RELEASES.md` cements rules verbatim

## 12. Cross-cutting concerns

- **Tenant isolation:** N/A (no DB queries Story 9 — pure infra)
- **Currency:** N/A
- **Master data:** N/A
- **Spanish neutro LatAm:** migration-from-nicolify.md user-facing español neutro tuteo. CHANGELOG.md acepta inglés técnico (es para devs). README + docs/RELEASES.md inglés OK
- **PII:** N/A (no API endpoints Story 9)
- **Native-first dev:** workflow runs on `ubuntu-latest`. Local lint native (uv run ruff, pnpm lint). NEVER docker exec
- **License surface:** all docs + CHANGELOG + workflow YAML carry implicit proprietary (root LICENSE applies)
- **Workflow secret handling:** `GH_PACKAGES_TOKEN` preferred (separate scope) → falls back to `GITHUB_TOKEN` (workflow-scoped, default action). Document both setup paths in `docs/RELEASES.md`

## 13. Architecture fitness impact

| Test file | Status | Allowlist note |
|---|---|---|
| `test_workspace_versions_uniform_at_v0_1_0.py` | NEW | Cement rule — versions monolithic |
| `test_release_workflow_yaml_valid.py` | NEW | Cement rule — release workflow structural invariants |
| `test_releaserc_config_valid.py` | NEW | Cement rule — 33-package manifest |
| `test_docs_v0_1_0_deliverables_present.py` | NEW | Cement rule — 5 docs deliverables |
| Story 8 12 NEW arch fitness | UNCHANGED | Must remain GREEN post-Story-9 (V-AG-2) |
| Stories 6+7 frozen registry goldens | UNCHANGED | V-AG-1 cement byte-stable |

Allowlists shrink only — no new exemptions Story 9.

## 14. capability YAML + modules updates required (post-merge)

Post-merge `/pm` operations:
- `docs/product/capabilities/luana-core/release-engineering.yaml` — **NEW capability** bootstrapped at status=in-development (state=done post-merge)
- `docs/product/capabilities/luana-core/multi-brand-platform.yaml` — UPDATE: cumulative stories list includes Story 9
- `docs/product/outcomes/luana-platform-migration.md` — UPDATE `stories_done` list to include Story 9 + capabilities count from 36 → 37+
- BACKLOG.{yaml,md} auto-regen via pre-commit hook (R33)

## 15. Research notes (date-aware)

| Source | URL | Accessed | Key takeaway |
|---|---|---|---|
| release-please monorepo support | `https://github.com/googleapis/release-please/blob/main/docs/manifest-releaser.md` | 2026-05-12 | Python + Node multi-pkg with linked-versions plugin. Strongly preferred over semantic-release-monorepo for Python support. |
| GitHub Packages PyPI registry | `https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-python-registry` | 2026-05-12 | `https://pypi.pkg.github.com/{org}/` is the canonical URL pattern. uv publish supports `--publish-url`. |
| GitHub Packages npm registry | `https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-npm-registry` | 2026-05-12 | `npm.pkg.github.com` + `@scope` mapping in `.npmrc`. pnpm `--access restricted` for private. |
| uv build/publish CLI | `https://docs.astral.sh/uv/reference/cli/#uv-publish` | 2026-05-12 | Astral docs — `uv publish dist/*.whl` with `UV_PUBLISH_TOKEN` env or `--token`. |
| pdoc 14 | `https://pdoc.dev/docs/pdoc.html` | 2026-05-12 | Zero-config HTML generator. `pdoc ./src/module --output-dir ./docs` |
| typedoc 0.27 | `https://typedoc.org/guides/options/` | 2026-05-12 | Monorepo via `--entryPointStrategy packages` flag. |
| actionlint | `https://github.com/rhysd/actionlint` | 2026-05-12 | De facto YAML schema validation for GH Actions. |
| Keep a Changelog 1.1.0 | `https://keepachangelog.com/en/1.1.0/` | 2026-05-12 | Format spec — `## [VERSION]` headers required. |
| SemVer 2.0.0 | `https://semver.org/spec/v2.0.0.html` | 2026-05-12 | Major.Minor.Patch contract. |

Knowledge cutoff disclosure: Opus 4.7 cutoff Jan 2026. All tools researched today via canonical docs (URLs above). No post-cutoff drift detected in 4 months — release-please, pdoc, typedoc, uv all stable.

## 16. Open questions for PM

None. All Phase 0 questions resolved per §0 cement table. Story 9 is mechanical lift-mode-equivalent — outcome §7.1 + §7.5 binding decisions cover all surface decisions.

## 17. Halt criteria (architect surfaces)

| # | Trigger | Action |
|---|---|---|
| 1 | GH Packages auth missing (Scenario 5) — `GITHUB_TOKEN` lacks `write:packages` AND no `GH_PACKAGES_TOKEN` secret | HALT — escalate Chris for token setup. NOT autonomous resolvable |
| 2 | release-please config conflict with monorepo layout (Scenario 6 conflict path) | Builder switches to fallback: changesets (TS) + custom Python bash publish loop. Document in `docs/RELEASES.md` |
| 3 | uv.lock regen fails post-bump (uv dep conflict) | Builder runs `uv lock --upgrade --resolution=lowest` as fallback. If still fails → HALT |
| 4 | Cumulative session 4 cost crosses $5000 | Soft check-in (Claude reports, continues autonomous per outcome §7.2 NO HARD CAP) |
| 5 | Workflow build time > 30min (exceeds reasonable) | Split build-python into matrix per directory (10 pkgs each, 3 parallel jobs) — architect did NOT need to design upfront |

Story 9 happy path estimated 5-6 tickets, ~$1000-2000 Sonnet, ~3-5h tool-time.
