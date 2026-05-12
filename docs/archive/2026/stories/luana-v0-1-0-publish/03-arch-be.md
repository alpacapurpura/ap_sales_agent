---
story_id: luana-v0-1-0-publish
arch_version: 1
sub_arch: backend (release engineering — no business code)
architect_owner: claude-opus-4-7
ratified_by_chris: true
last_modified: 2026-05-12
note: |
  Story 9 has NO traditional BE surface (no DB models, no API endpoints,
  no domain entities, no services). This sub-arch documents CI/CD pipeline
  technical detail. Maintained for parity with prior stories' 03-arch-{be,fe,agentic}.md pattern.
---

# 03-arch-be — Story 9: Backend release engineering detail

> **Scope:** CI/CD pipeline + Python publish mechanics + workspace version bump + Python smoke test
> **No FE arch:** TS surfaces handled inline in 03-arch.md §3-§6 (release.yml + pnpm + typedoc)
> **No agentic arch:** Stories 6+7 frozen registries are byte-stable invariant (V-AG-1) — Story 9 does NOT touch agentic surfaces

## 1. Python package surface inventory

| Package | Path | Pre-bump version | Post-bump | Notes |
|---|---|---|---|---|
| luana-core-platform | `core/luana-core-platform/` | 0.0.1-alpha | 0.1.0 | Story 2 |
| luana-core-llm | `core/luana-core-llm/` | 0.0.1-alpha | 0.1.0 | Story 2 |
| luana-core-channels | `core/luana-core-channels/` | 0.0.1-alpha | 0.1.0 | Story 2 |
| luana-core-idempotency | `core/luana-core-idempotency/` | 0.0.1-alpha | 0.1.0 | Story 2 |
| luana-core-observability | `core/luana-core-observability/` | 0.0.1-alpha | 0.1.0 | Story 2 (callback + cost recorder lifted) |
| luana-core-events | `core/luana-core-events/` | 0.0.1-alpha | 0.1.0 | Story 2 |
| luana-core-extraction | `core/luana-core-extraction/` | 0.0.1-alpha | 0.1.0 | Story 2 |
| luana-core-compliance | `core/luana-core-compliance/` | 0.0.1-alpha | 0.1.0 | Story 2 |
| luana-core-billing | `core/luana-core-billing/` | 0.0.1-alpha | 0.1.0 | Story 2 |
| luana-core-iam | `core/luana-core-iam/` | 0.0.1-alpha | 0.1.0 | Story 3 |
| luana-core-tenant-profile | `core/luana-core-tenant-profile/` | 0.0.1-alpha | 0.1.0 | Story 3 |
| luana-core-tenant-domains | `core/luana-core-tenant-domains/` | 0.0.1-alpha | 0.1.0 | Story 3 |
| luana-core-commercial-calendar | `core/luana-core-commercial-calendar/` | 0.0.1-alpha | 0.1.0 | Story 3 |
| luana-core-social-proof | `core/luana-core-social-proof/` | 0.0.1-alpha | 0.1.0 | Story 3 |
| luana-core-assets | `core/luana-core-assets/` | 0.0.1-alpha | 0.1.0 | Story 3 |
| luana-core-crm | `core/luana-core-crm/` | 0.0.1-alpha | 0.1.0 | Story 4 |
| luana-core-analytics-engine | `core/luana-core-analytics-engine/` | 0.0.1-alpha | 0.1.0 | Story 4 |
| luana-core-landing | `core/luana-core-landing/` | 0.0.1-alpha | 0.1.0 | Story 4 |
| luana-core-connections | `core/luana-core-connections/` | 0.0.1-alpha | 0.1.0 | Story 4 |
| luana-core-brand-studio | `core/luana-core-brand-studio/` | 0.0.1-alpha | 0.1.0 | Story 5 |
| luana-core-offer-studio | `core/luana-core-offer-studio/` | 0.0.1-alpha | 0.1.0 | Story 5 |
| luana-core-copilot | `core/luana-core-copilot/` | **0.0.6-alpha** | 0.1.0 | Story 6 (agentic — byte-stable runtime) |
| luana-core-sales-agent | `core/luana-core-sales-agent/` | **0.0.7-alpha** | 0.1.0 | Story 7 (agentic — byte-stable runtime) |
| luana-core-campaigns | `core/luana-core-campaigns/` | **0.0.8-alpha** | 0.1.0 | Story 8 |
| luana-core-extension-sdk | `core/luana-core-extension-sdk/` | **0.0.8-alpha** | 0.1.0 | Story 8 |
| test-brand | `apps/test-brand/` | **0.0.8-alpha** | 0.1.0 | Story 8 smoke pack |
| nicolify-app | `nicolify/` | 0.0.1-alpha | 0.1.0 | Brand stub (coherence) |
| vitalia-app | `vitalia/` | 0.0.1-alpha | 0.1.0 | Brand stub |
| comunify-app | `comunify/` | 0.0.1-alpha | 0.1.0 | Brand stub |
| lupulo-app | `lupulo/` | 0.0.1-alpha | 0.1.0 | Brand stub |

**Workspace root `core/pyproject.toml`:** has `[project] name = "luana-core" version = "0.0.1-alpha"` — bump to 0.1.0 for coherence (NOT publishable per uv workspace pattern).

**Workspace top root `/pyproject.toml`:** NO `[project]` section (uv workspace root only declares `[tool.uv.workspace]`). NO bump needed.

## 2. Python publish mechanics

### 2.1 Build (sequential, ~10-20s per pkg)

```bash
for pkg in core/luana-core-* apps/test-brand; do
  if [ -f "$pkg/pyproject.toml" ]; then
    uv build --package "$(basename $pkg)" --out-dir dist/
  fi
done
```

Output: `dist/luana_core_X-0.1.0.tar.gz` + `dist/luana_core_X-0.1.0-py3-none-any.whl` per package.

Total: 26 sdist + 26 wheel = 52 files.

### 2.2 Publish (per-file, fail-fast)

```bash
export UV_PUBLISH_TOKEN="${GH_PACKAGES_TOKEN}"  # or GITHUB_TOKEN
export UV_PUBLISH_URL="https://pypi.pkg.github.com/alpacapurpura/"

for f in dist/*.tar.gz dist/*.whl; do
  uv publish "$f" || { echo "::error::Publish failed: $f"; exit 1; }
done
```

**Atomicity:** publish is per-file. If file 5 fails, files 1-4 are published. NOT atomic. Mitigation: workflow fails fast (exit 1) → maintainer manually deletes partial pkgs via `gh api DELETE /orgs/alpacapurpura/packages/pypi/{name}/versions/{ver}` then re-tags.

**Rollback procedure documented in `docs/RELEASES.md`:** maintainer runs cleanup script `scripts/rollback_partial_publish.sh v0.1.0` (architect emits if rollback observed).

### 2.3 Auth surface

Two paths (workflow uses `${{ secrets.GH_PACKAGES_TOKEN || secrets.GITHUB_TOKEN }}`):

| Path | Setup | Scope | Recommended for |
|---|---|---|---|
| A. `GITHUB_TOKEN` (default workflow secret) | None (auto-injected) | Implicitly scoped to repo (read+write packages if repo settings allow) | CI default |
| B. `GH_PACKAGES_TOKEN` (custom PAT) | `gh auth login --scopes read:packages,write:packages` → store via `gh secret set GH_PACKAGES_TOKEN` | Explicit `read:packages,write:packages` | Long-lived debug, cross-org |

Both documented in `docs/RELEASES.md` §Token-setup.

## 3. Workspace bump mechanics

### 3.1 Idempotent sed (safe to re-run)

```bash
# Python: replace ANY 0.0.x-alpha → 0.1.0
find core/ apps/test-brand/ nicolify/ vitalia/ comunify/ lupulo/ -maxdepth 2 -name "pyproject.toml" \
  -exec sed -i -E 's/^version = "0\.0\.[0-9]+-alpha"$/version = "0.1.0"/' {} \;

# Same for core/pyproject.toml (workspace internal root)
sed -i -E 's/^version = "0\.0\.[0-9]+-alpha"$/version = "0.1.0"/' core/pyproject.toml
```

**Idempotency check:** running sed twice is no-op (already at 0.1.0 — regex doesn't match). Validator V-NF-2/3 confirms.

### 3.2 TS bump (pnpm-native + manual for brand stubs)

```bash
# Workspace-aware: pnpm updates internal deps automatically
pnpm -r --filter "./core/@luana/*" exec npm version 0.1.0 --no-git-tag-version --allow-same-version

# Brand stubs (outside @luana scope filter)
for pkgjson in nicolify/package.json vitalia/package.json comunify/package.json lupulo/package.json; do
  jq '.version = "0.1.0"' "$pkgjson" > "${pkgjson}.tmp" && mv "${pkgjson}.tmp" "$pkgjson"
done

# Top-level root
jq '.version = "0.1.0"' package.json > package.json.tmp && mv package.json.tmp package.json
```

### 3.3 Lockfile regen

```bash
uv lock --upgrade
pnpm install --lockfile-only
```

Both lockfiles committed alongside pyproject/package.json bumps in single commit (T-1).

## 4. Python API docs (pdoc)

### 4.1 Script (`scripts/generate_api_docs.sh`)

```bash
#!/bin/bash
set -euo pipefail

OUTPUT_DIR="docs/api/python"
mkdir -p "$OUTPUT_DIR"

# pdoc per package (HTML output)
for pkg in core/luana-core-*; do
  if [ -f "$pkg/pyproject.toml" ]; then
    name=$(basename "$pkg")
    src_module=$(echo "$name" | tr '-' '_')  # luana-core-platform → luana_core_platform
    if [ -d "$pkg/src/$src_module" ]; then
      echo "Generating pdoc for $name"
      uv run pdoc "$pkg/src/$src_module" \
        --output-dir "$OUTPUT_DIR/$name" \
        --docformat google \
        --no-show-source || echo "::warning::pdoc failed for $name (continuing)"
    fi
  fi
done

# typedoc for TS (single invocation, monorepo-aware)
OUTPUT_DIR_TS="docs/api/typescript"
mkdir -p "$OUTPUT_DIR_TS"
pnpm exec typedoc \
  --entryPointStrategy packages \
  ./core/@luana/* \
  --out "$OUTPUT_DIR_TS" \
  --readme none || echo "::warning::typedoc had warnings"

echo "API docs generated: $(ls $OUTPUT_DIR | wc -l) Python + $(ls $OUTPUT_DIR_TS 2>/dev/null | wc -l) TS"
```

### 4.2 Best-effort gate

Per Risk 10 (01-spec §10): script aborts on first hard error but warns on per-package failures. Validator V-F-release-6 asserts ≥ 80% packages have docs (best-effort threshold).

## 5. Conventional Commits + commitlint setup (deferred to Story 10+ but documented)

Story 9 emits `commitlint.config.cjs` placeholder at root + `.husky/commit-msg` script (optional — `production_code=false`, so no auto-install — devs opt-in via `pnpm install` post-merge). Cement F1-F6 SemVer enforcement via docs only Story 9. Active enforcement → Story 10+.

`commitlint.config.cjs` seed:

```js
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'subject-case': [0],
    'subject-max-length': [2, 'always', 100],
  },
};
```

## 6. Downstream regression (V-AG-2 Scenario 8)

Pre-bump baseline (Story 8 merge 2026-05-12 per 07-merge.md):

| Package | GREEN | Skipped | Failed |
|---|---|---|---|
| luana-core-copilot | 1603 | 25 | 0 |
| luana-core-sales-agent | 429 | 0 | **40 PRE-EXISTING + 1 collection error** |
| luana-core-brand-studio | 470 | 0 | 0 |
| luana-core-offer-studio | 633 | 0 | 0 |
| luana-core-campaigns | 446 | 0 | 0 |
| luana-core-extension-sdk | 92 | 0 | 0 |
| Story 8 arch fitness | 12 NEW | 0 | 0 |

Post-bump validator (V-AG-2): delta = 0. Same numbers. NEW failures introduced by Story 9 = 0.

**Pre-existing 40 failures policy:** DEFER to Story 10+ cleanup ticket. Architect Story 9 decision (per spec §6 + §8 policy). Documented:
- CHANGELOG.md "Known issues" entry
- `DEFERRED-FILES.md` in luana-platform (architect ticket appends)
- `docs/migration-from-nicolify.md` §6 troubleshooting mentions "if running sales-agent tests, expect 40 pre-existing test fixture failures — see Story 7 carry-over"

## 7. apps/test-brand re-run vs published (V-AG-1 Scenario 4)

Script approach (architect lifts pattern from Scenario 4):

```bash
# 1. Snapshot current workspace-deps test-brand
cp apps/test-brand/pyproject.toml apps/test-brand/pyproject.toml.workspace.bak

# 2. Swap deps to pinned versions
sed -i 's/luana-core-extension-sdk/luana-core-extension-sdk==0.1.0/' apps/test-brand/pyproject.toml

# 3. Reinstall from published registry
cd apps/test-brand
uv sync --reinstall  # forces pull from registry per pyproject pin

# 4. Run smoke pack
uv run pytest tests/ -x -q

# 5. Restore (idempotent — workspace local dev re-enabled)
mv pyproject.toml.workspace.bak pyproject.toml
uv sync
```

**Env-gated:** ticket only runs this if `STORY_9_PUBLISH_REGRESSION=1`. Default skip in local dev. CI workflow `smoke-test-published` job runs it post-publish.

## 8. CI surface (release.yml jobs detail)

See 03-arch.md §3 for full YAML. Backend-specific notes:

- `build-python` job — uses `uv build --package $(basename pkg) --out-dir dist/` (workspace-aware). NOT `uv build .` (would build only root).
- `publish-python` job — per-file loop (NOT batch). Reason: uv publish doesn't support batch upload, atomicity per-file.
- `smoke-test-published` job — runs `scripts/publish_smoke_test.sh` AFTER both publish jobs. Failure does NOT roll back (already published — manual cleanup if smoke catches a bug). Logs warning + creates issue.

## 9. Cross-cutting (BE-side)

- **No DB migrations Story 9** (release infra only, V-NF cement)
- **No model changes** (all pyproject toml metadata only)
- **No alembic** (no DB at all)
- **Async-first** (N/A — no runtime BE code; CLI tools only)
- **`structlog`** (N/A — no runtime code; bash scripts use `echo`)
- **Tenant isolation** (N/A — no DB queries)

## 10. Test surfaces (BE-side TDD)

- `tests/architecture/test_workspace_versions_uniform_at_v0_1_0.py` — RED first (creates test with 33 pkgs assertion, FAILS until T-1 bumps), GREEN after T-1
- `tests/architecture/test_release_workflow_yaml_valid.py` — RED first (validates YAML shape, FAILS without `release.yml`), GREEN after T-2
- `tests/architecture/test_releaserc_config_valid.py` — RED first, GREEN after T-2
- `tests/architecture/test_docs_v0_1_0_deliverables_present.py` — RED first (asserts 5 docs files exist), GREEN after T-3
- `tests/architecture/test_aisaleshT_untouched_story_9.py` — best-effort guard (skips if no AISALESHT_PATH env)

## 11. Open issues for Phase 0 builder (none — all resolved)

All decisions cement in 03-arch.md §0 cement table.
