<!-- voseo-allowed: spec references rules + glossary verbatim for traceability per R25 -->
---
story_id: luana-v0-1-0-publish
type: service-story
module: luana-platform (release engineering — cross-package)
capability: luana-core/release-engineering
po_version: 1
spec_version: 1
drafted_by: /po Opus (claude-opus-4-7-1m)
drafted_at: 2026-05-12
last_modified: 2026-05-12
ratified_by_chris: true                            # ★ Pre-auth per outcome §7.5.2 D7=B + checkpoint binding_decisions ★
binding_decisions_ref: docs/product/outcomes/luana-platform-migration.md §7.1 + §7.5.2 D4 + §7.5.2 D7
links:
  story_md: "00-story.md"
  checkpoint: "checkpoint.md"
  outcome: "../../outcomes/luana-platform-migration.md"
  story_8_merge: "../../../archive/2026/stories/luana-campaigns-extension-sdk/07-merge.md"
---

# 01-spec — Story 9: Luana v0.1.0 Release Pipeline

## 1. Outcome alignment

Story 9 cierra el ciclo de **release engineering** del outcome `luana-platform-migration` (posición 9/14 del DAG). Su misión: promover Luana desde el régimen actual de versionado alpha mixto (`0.0.1-alpha`..`0.0.8-alpha` cross-package, ver §3 inventario) a la primera versión pública estable **`v0.1.0`** publicada a **GitHub Packages private registry** (license proprietary), cementando SemVer discipline real desde este punto en adelante.

Story 9 desbloquea Stories 10-14 (Nicolify migration + 3 brand bootstraps + brand voice elevation) — todas las stories downstream consumen `luana-core-*==0.1.0` (Python) y `@luana/*@0.1.0` (TypeScript) como dependencias publicadas, no como workspace internals.

**Binding decisions pre-ratified (no requieren Chris ratification mid-spec):**

| Decisión | Valor | Fuente |
|---|---|---|
| License | proprietary (All rights reserved, private registry) | outcome §7.1 (2026-05-10) |
| Repo topology | monorepo (`alpacapurpura/luana-platform`) | outcome §7.1 (2026-05-10) |
| GH Packages strategy | introduce publish pipeline (Story 9 IS the implementation) | outcome §7.1 + checkpoint binding_decisions |
| Versioning regime | real SemVer flip desde v0.1.0 onwards | outcome §7.5.2 D4=C |
| Publish target | `v0.1.0` (sin sufijo `-alpha` — "production-grade alpha" semantic per 00-story.md) | spawn prompt + 00-story §Acceptance |
| Session topology | Stories 8+9 secuencial autonomous Session 4 | outcome §7.5.2 D7=B + §7.4 cap extendido a 3 stories Tier 3 |
| Production code flag | `production_code: false` (pure CI/CD + release infra) | checkpoint frontmatter |
| Owner eligibility | `[opus, sonnet]` — R23 NOT triggered | checkpoint frontmatter |

## 2. Resumen ejecutivo

Story 9 es **release infra pura, no business logic**. Construye el pipeline mecánico que toma el monorepo actual (26 Python packages + 7 TypeScript packages, Story 8 merge state 2026-05-12) y produce un release `v0.1.0` publicado a GitHub Packages private registry con:

1. Version bumps cross-package homogéneos (`0.0.x-alpha` → `0.1.0` en los 33 packages).
2. Config semantic-release que automatiza tags subsiguientes desde Conventional Commits.
3. Workflow GitHub Actions `release.yml` que builds + publishes + genera changelog + crea GitHub release on `v*.*.*` tag push.
4. Documentación de release: `CHANGELOG.md` cross-package (Stories 1-9), `docs/migration-from-nicolify.md` (consumer migration guide), `docs/api/` API reference auto-gen (Python + TS).
5. Smoke test post-publish que valida la consumibilidad real (`pip install luana-core-platform==0.1.0` + `npm install @luana/extension-sdk@0.1.0`) + re-run `apps/test-brand` smoke pack contra packages publicados (regression check Story 8 EPs).
6. SemVer discipline cement: documentación + arch fitness tests que forzan major/minor/patch bumps en violations futuras.

Story 9 **NO toca** business logic de ningún package — el código de Stories 1-8 queda byte-stable salvo el campo `version` en `pyproject.toml` + `package.json`. AISALESHT permanece intocado (V-NF-4 invariant cumulative 9 stories).

**Halt criterion cardinal:** si GH Packages org-level config (token + billing + permissions) requiere setup manual por Chris fuera del scope autonomous, Story 9 HALTS y escala. Architect Story 9 verificará en Phase 0 si auth strategy es resolvible vía secrets de repo (`GITHUB_TOKEN` default + `secrets.GH_PACKAGES_TOKEN` opcional) o requiere intervention.

## 3. Inventario pre-Story-9 (estado workspace post-Story-8 merge 2026-05-12)

### 3.1 Python packages (26 total — `core/pyproject.toml` workspace members)

| Story origen | Packages | Versión actual |
|---|---|---|
| Story 2 (shared lift) | luana-core-platform, luana-core-llm, luana-core-channels, luana-core-idempotency, luana-core-observability, luana-core-events, luana-core-extraction, luana-core-compliance, luana-core-billing | `0.0.1-alpha` (9 pkgs) |
| Story 3 (IAM + tenancy + content) | luana-core-iam, luana-core-tenant-profile, luana-core-tenant-domains, luana-core-commercial-calendar, luana-core-social-proof, luana-core-assets | `0.0.1-alpha` (6 pkgs) |
| Story 4 (CRM + analytics + landing + connections) | luana-core-crm, luana-core-analytics-engine, luana-core-landing, luana-core-connections | `0.0.1-alpha` (4 pkgs) |
| Story 5 (brand + offer studios) | luana-core-brand-studio, luana-core-offer-studio | `0.0.1-alpha` (2 pkgs) |
| Story 6 (copilot engine) | luana-core-copilot | `0.0.6-alpha` (1 pkg) |
| Story 7 (sales agent engine) | luana-core-sales-agent | `0.0.7-alpha` (1 pkg) |
| Story 8 (campaigns + extension SDK) | luana-core-campaigns, luana-core-extension-sdk | `0.0.8-alpha` (2 pkgs) |
| **Story 1 root** | `core/pyproject.toml` (workspace root, not a publishable package) | `0.0.1-alpha` |

**Heterogeneity:** 22 packages at `0.0.1-alpha`, 1 at `0.0.6-alpha`, 1 at `0.0.7-alpha`, 2 at `0.0.8-alpha`. Story 9 unifica los 26 a `0.1.0`.

### 3.2 TypeScript packages (7 total — `pnpm-workspace.yaml` packages `core/@luana/*`)

| Package | Versión actual |
|---|---|
| @luana/api-client | `0.0.1-alpha` |
| @luana/design-tokens | `0.0.1-alpha` |
| @luana/format | `0.0.1-alpha` |
| @luana/hooks | `0.0.1-alpha` |
| @luana/schemas | `0.0.1-alpha` |
| @luana/ui-kit | `0.0.1-alpha` |
| @luana/extension-sdk | `0.0.8-alpha` |

**Heterogeneity:** 6 packages at `0.0.1-alpha`, 1 at `0.0.8-alpha`. Story 9 unifica los 7 a `0.1.0`.

### 3.3 Apps + brand stubs (NO publish — pnpm workspace internal)

| Workspace member | Tipo | Versión actual | Story 9 action |
|---|---|---|---|
| `apps/test-brand` | Smoke test pack | `0.0.8-alpha` | Bump a `0.1.0` (consumer del SDK — debe tracker SDK version) |
| `nicolify`, `vitalia`, `comunify`, `lupulo` | Brand app stubs (TS + Python) | `0.0.1-alpha` (root package.json + per-pyproject si existe) | NO publish (brand apps), bump opcional para coherencia visual workspace |

### 3.4 CI existing (pre-Story-9)

- `.github/workflows/ci.yml` — Story 1 CI baseline (lint + test python + ts, placeholder echoes pre-test era). Story 9 NO modifica `ci.yml` (orthogonal — ci.yml es PR/push validation; release.yml es tag-triggered).

### 3.5 Docs existing (pre-Story-9)

- `docs/ARCHITECTURE.md` (Story 1)
- `docs/CONTRIBUTING.md` (Story 1)
- `docs/RELEASES.md` (Story 1 placeholder — Story 9 puede extender o reemplazar contenido si arquitecto lo decide)
- `docs/extension-points.md` (Story 8, 1354 líneas — Story 9 actualiza con stamp v0.1.0 finalization)
- `docs/architecture/` (Story 1+ ADRs)

## 4. Acceptance Criteria (Gherkin AI-resistant)

Mínimo 6 scenarios cubriendo happy + negative + edge + adversarial + regression + SemVer-discipline.

### Scenario 1 — `release-pipeline-happy` (`type: happy`)

**Given:**
- Repo `alpacapurpura/luana-platform` en branch `main`, Story 8 merged, 26 Python + 7 TS packages en versiones mixtas (§3.1, §3.2).
- `.github/workflows/release.yml` emitido por Story 9 + `.releaserc.json` (o `.releaserc.cjs`) en root.
- 33 packages (26 Python + 7 TS) bumped a `version = "0.1.0"`.
- `apps/test-brand` bumped a `0.1.0`.
- GitHub Packages registry private habilitado para el repo + `GITHUB_TOKEN` con scope `write:packages` disponible en GH Actions.

**When:**
- Maintainer ejecuta `git tag v0.1.0 && git push origin v0.1.0` (manual first tag — no auto-derived desde commits pre-`0.0.x-alpha`).

**Then:**
- Workflow `release.yml` se dispara en evento `push.tags == 'v0.1.0'`.
- Job `build-python` ejecuta `uv build` sobre cada uno de los 26 workspace members → 26 sdist + 26 wheel files generados en `dist/` per-package.
- Job `build-typescript` ejecuta `pnpm -r build` sobre los 7 `@luana/*` packages → 7 `dist/` directories con compilación TS válida.
- Job `publish-python` publica los 26 packages a GitHub Packages Python registry (`https://pypi.pkg.github.com/alpacapurpura/`).
- Job `publish-typescript` publica los 7 packages a GitHub Packages npm registry (`https://npm.pkg.github.com/@luana/`).
- Job `generate-changelog` emite `CHANGELOG.md` cross-package con sección `## v0.1.0 — 2026-05-XX` agregando entries de Stories 1-9 (1 entry por package + 1 entry "Release Engineering" para Story 9 changes).
- Job `create-github-release` crea release `v0.1.0` en `https://github.com/alpacapurpura/luana-platform/releases/tag/v0.1.0` con release notes (auto-gen desde CHANGELOG.md) + assets (sdist/wheel tarballs opcionales).
- Workflow termina con `exit 0` y todos los jobs GREEN.

**Graders:**
- shell command `gh api /orgs/alpacapurpura/packages/pypi/luana-core-platform/versions --jq '.[0].name'` → returns `"0.1.0"`
- shell command `gh api /orgs/alpacapurpura/packages/npm/extension-sdk/versions --jq '.[0].name'` → returns `"0.1.0"` (handle `@luana/` scope encoding)
- shell command `gh release view v0.1.0 --repo alpacapurpura/luana-platform --json tagName --jq .tagName` → returns `"v0.1.0"`
- file `CHANGELOG.md` contains section `## [0.1.0]` + cross-package entries (regex `^- \w+(/\w+)?: ` count ≥ 26)
- workflow run status — `gh run list --workflow=release.yml --limit=1 --json conclusion --jq '.[0].conclusion'` → returns `"success"`

---

### Scenario 2 — `version-bumps-uniform` (`type: happy`)

**Given:**
- Repo en estado pre-Story-9 con 22 Python packages at `0.0.1-alpha`, 1 at `0.0.6-alpha`, 1 at `0.0.7-alpha`, 2 at `0.0.8-alpha` (§3.1).
- 6 TS packages at `0.0.1-alpha`, 1 at `0.0.8-alpha` (§3.2).

**When:**
- Story 9 ticket "version bumps" ejecuta script o edits manuales sobre `pyproject.toml` (Python) + `package.json` (TS) en todos los workspace members + root.

**Then:**
- Todos los 26 `core/luana-core-*/pyproject.toml` declaran `version = "0.1.0"` exacto (string match, no `-alpha`, no `-rc`, no `0.1.0a1`).
- Todos los 7 `core/@luana/*/package.json` declaran `"version": "0.1.0"` exacto.
- `apps/test-brand/pyproject.toml` declara `version = "0.1.0"`.
- `core/pyproject.toml` (workspace root) bumped a `version = "0.1.0"` (coherence — aunque no publishable).
- Root `/package.json` bumped a `"version": "0.1.0"` (coherence).
- Cross-package internal deps (si alguna pin explícita con versión hard-coded) updated a `==0.1.0` (Python) o `"0.1.0"` (TS).
- Brand app stubs `nicolify/`, `vitalia/`, `comunify/`, `lupulo/` quedan en `0.0.1-alpha` (NO publishable — solo workspace members) **O** bumped a `0.1.0` a discreción del architect — ambos opciones válidas.
- `git diff --name-only` muestra ≥ 34 archivos modificados (33 packages + workspace roots) con cambios mínimos (solo línea `version`).

**Graders:**
- pytest arch fitness `test_workspace_versions_uniform_at_v0_1_0.py` — itera workspace members + assert `version == "0.1.0"` para los 26+7+1 packages (excepción brand stubs si architect decide dejarlos `0.0.1-alpha`)
- shell `find core -name pyproject.toml -exec grep -L '^version = "0.1.0"' {} \;` → empty output (todos matchearon)
- shell `find core/@luana -name package.json -exec grep -L '"version": "0.1.0"' {} \;` → empty output
- shell `grep -r "0.0.[0-9]*-alpha" core/ apps/test-brand/ --include=pyproject.toml --include=package.json` → empty output (no straggler alpha versions, excepto brand stubs si aplica)

---

### Scenario 3 — `consumer-smoke-test-post-publish` (`type: happy`)

**Given:**
- Workflow `release.yml` completó exitosamente Scenario 1 + Scenario 2.
- GitHub Packages contiene 26 Python packages + 7 TS packages publicados v0.1.0.
- Repo separado o directory ephemeral `/tmp/luana-v0-1-0-smoke/` con `~/.netrc` o `pip config` apuntando a `https://pypi.pkg.github.com/alpacapurpura/` (Python) + `.npmrc` apuntando a `@luana:registry=https://npm.pkg.github.com/` (TS).

**When:**
- Smoke test ejecuta:
  ```bash
  cd /tmp/luana-v0-1-0-smoke
  pip install luana-core-platform==0.1.0 luana-core-extension-sdk==0.1.0
  npm install @luana/extension-sdk@0.1.0
  python -c "from luana_core_platform import __version__; assert __version__ == '0.1.0', f'got {__version__}'"
  python -c "from luana_core_extension_sdk import ExtensionPointRegistry, BrandContext; r = ExtensionPointRegistry(); print(r)"
  node -e "const sdk = require('@luana/extension-sdk'); console.log(Object.keys(sdk).length > 0 ? 'OK' : 'FAIL')"
  ```

**Then:**
- `pip install` succeeds with exit 0 (auth correcto, package found en registry, deps resueltas).
- `npm install` succeeds with exit 0.
- Python smoke: `__version__` matches `'0.1.0'` exacto, `ExtensionPointRegistry()` instantiable, `BrandContext` importable.
- TS smoke: `require('@luana/extension-sdk')` returns object con ≥ 1 named export.
- Test exit code 0 cumulative.

**Graders:**
- shell command exit code (smoke script) → 0
- pytest test `test_consumer_install_smoke.py` — invoca el script + asserts exit 0 + parses output (env-gated `STORY_9_PUBLISH_SMOKE=1` opcional para no correr en CI default).
- workflow log artifact — smoke test job output contains string `"luana-core-platform==0.1.0 installed OK"` + `"@luana/extension-sdk@0.1.0 installed OK"`

---

### Scenario 4 — `apps-test-brand-regression-vs-published` (`type: happy` regression)

**Given:**
- Story 8 dejó `apps/test-brand/` con FastAPI lifespan + 18 register_all handlers + 10 smoke scenarios GREEN consumiendo `luana-core-extension-sdk` via workspace.
- Story 9 published v0.1.0 a GitHub Packages.

**When:**
- Story 9 ejecuta variant de `apps/test-brand/` smoke pack apuntando a published packages (no workspace) — vía `pyproject.toml` con `luana-core-extension-sdk = "==0.1.0"` (no `{workspace = true}`), reinstall env, re-run smoke pack.

**Then:**
- 10 smoke scenarios EP-1..EP-5 + EP-6..EP-18 stub registration GREEN vs published v0.1.0 packages.
- BrandContext frozen 9-field GREEN.
- CC-1..CC-5 runtime enforcement GREEN (namespace, duplicate, lock, immutable, mode flag).
- `test_no_ep19_method_in_registry.py` GREEN (arch fitness Story 8 invariant preserved).
- EP-3 ToolRegistry adapter byte-stable (Stories 6+7 frozen registries golden snapshots).
- EP-4 WorkflowRegistry adapter byte-stable.

**Graders:**
- pytest `apps/test-brand/tests/` full suite GREEN against published packages env (env-gated `STORY_9_PUBLISH_REGRESSION=1`).
- shell smoke runner `apps/test-brand/scripts/smoke.sh --published` exit 0 (or equivalent — architect decide invocation form).
- Story 8 arch fitness 12 NEW tests re-run GREEN against installed-from-registry packages.

---

### Scenario 5 — `gh-packages-auth-missing` (`type: negative`)

**Given:**
- Repo Story 9 ready package complete.
- Maintainer push tag `v0.1.0` PERO `secrets.GITHUB_TOKEN` NO tiene scope `write:packages` (o GitHub Packages no habilitado para org `alpacapurpura/`).

**When:**
- Workflow `release.yml` se dispara.

**Then:**
- Job `build-python` ejecuta GREEN (no requiere auth).
- Job `build-typescript` ejecuta GREEN.
- Job `publish-python` FAILS con error claro de auth (e.g., `403 Forbidden`, `Authentication required`, `Permission denied: packages.write`).
- Workflow termina con `exit ≠ 0` y status `failure`.
- NO se crea release `v0.1.0` en GitHub (job `create-github-release` no se ejecuta porque depends_on `publish-python` failed).
- NO se publica package alguno (Python ni TS) — fail-fast antes de publish parcial.
- GitHub release tag `v0.1.0` queda en repo (push del tag fue OK) PERO sin release notes asociadas — maintainer puede deleter tag + retry post-fix.
- Error message en log contiene hint accionable: `"Verify GITHUB_TOKEN has write:packages scope OR set GH_PACKAGES_TOKEN secret per docs/RELEASES.md §Token-setup"`.

**Graders:**
- workflow log artifact — job `publish-python` log contains regex `(403|Authentication|Permission denied|write:packages)`.
- shell `gh run list --workflow=release.yml --limit=1 --json conclusion --jq '.[0].conclusion'` → returns `"failure"`.
- shell `gh api /orgs/alpacapurpura/packages/pypi/luana-core-platform/versions --jq 'length'` → returns `0` (or 404 if package never existed) — confirma publish atómico no partial.
- pytest `test_release_workflow_handles_auth_missing.py` — parses workflow YAML + asserts error handling step present (best-effort static check).

**Halt criterion:** este scenario describe SISTEMÁTICAMENTE el halt_criteria #1 del checkpoint. Si Story 9 dev encuentra que auth no resuelve vía `GITHUB_TOKEN` default + scope packages, ESCALATE Chris para token + billing setup. Architect Story 9 debe documentar paths de resolución alternativos (e.g., `GH_PACKAGES_TOKEN` personal access token con `packages:write` scope, instructions de setup en `docs/RELEASES.md`).

---

### Scenario 6 — `semantic-release-config-conflict` (`type: negative`)

**Given:**
- Story 9 ready package incluye `.releaserc.json` (o `.cjs`) en root con plugins monorepo-aware.
- Architect Story 9 verificó compat de plugins con stack actual.

**When:**
- semantic-release ejecuta en dry-run mode (validation step pre-publish) o invoked manual.

**Then (success path):**
- Validation passes: config valid, plugins compatible (semantic-release-monorepo o equivalente + @semantic-release/changelog + @semantic-release/github + custom python publisher).
- Próximo tag derivable desde Conventional Commits (e.g., siguiente commit `feat:` → bump minor, `fix:` → patch).

**Then (conflict path — halt criterion):**
- Validation FAILS por incompat plugin (e.g., monorepo plugin requires específica versión Node, conflict con pnpm workspace, Python publish requires plugin custom no disponible).
- Story 9 ESCALATES Chris con error diagnostico + alternativas (e.g., "use release-please en vez de semantic-release", "split en 2 tools: changesets para TS + custom script Python").
- Story 9 HALTS hasta resolution.

**Graders:**
- shell `npx semantic-release --dry-run --no-ci` exit 0 (success path) o exit ≠ 0 + error msg parseable (conflict path).
- file `.releaserc.json` exists + valid JSON schema (`jq . .releaserc.json` exit 0).
- file `.releaserc.json` contains plugins for: monorepo-aware, conventional commits parser, changelog gen, GitHub release create, Python publisher (custom or via @semantic-release/exec hook), npm publisher con registry override a GitHub Packages.

---

### Scenario 7 — `semver-discipline-major-bump-required` (`type: edge` + adversarial)

**Given:**
- Post Story 9 published v0.1.0.
- Developer (Story 10+) modifica un EP signature en `luana-core-extension-sdk` — por ejemplo, agrega un required field a `BrandContext` (breaking change per SemVer).
- Conventional Commits enforcement está activo: commit message debe declarar `BREAKING CHANGE:` footer o usar `feat!:` / `fix!:` notation.

**When:**
- Developer ejecuta `git commit -m "feat: add brand_tier_v2 to BrandContext"` (sin marker breaking).
- Pre-commit hook valida Conventional Commits.

**Then:**
- Pre-commit hook (o CI lint job) DETECTA que el cambio toca `BrandContext` (path-based heuristic O AST-based) y FALLA con error: `"BrandContext signature change requires BREAKING CHANGE declaration per outcome §7.5.2 D4=C SemVer discipline + .claude/rules/anti-default-flip-audit.md analog"`.
- Developer corrige a `git commit -m "feat!: add brand_tier_v2 to BrandContext\n\nBREAKING CHANGE: BrandContext now requires brand_tier_v2 — existing handlers must be updated to accept this field"`.
- semantic-release reconoce `!` + footer → próximo release auto-bump major (`v1.0.0`).

**Alternative path (non-breaking field addition):**
- Si field es optional con default → minor bump (`v0.2.0`).
- Si field es type alias compatible → patch bump (`v0.1.1`).

**Graders:**
- pytest `test_semver_discipline_breaking_change_enforced.py` — invokes mock commit + assert hook rejection.
- file `docs/RELEASES.md` o `docs/migration-from-nicolify.md` documents SemVer rules: major = breaking, minor = additive, patch = fix. F1-F6 enumerated.
- arch fitness `test_brand_context_change_requires_breaking_declaration.py` (best-effort static — may be doc-only enforcement if AST detection complex).

---

### Scenario 8 — `downstream-regression-stories-1-8-zero-new-failures` (`type: regression` adversarial)

**Given:**
- Story 9 in flight (version bumps + release.yml + .releaserc.json + docs added).
- AISALESHT untouched (V-NF-4 invariant cumulative 9 stories).

**When:**
- Story 9 test suite ejecuta `uv run pytest -x -q` cross-workspace post-version-bump (antes de publish).
- Story 9 ejecuta `pnpm -r test` cross-workspace post-version-bump.

**Then:**
- Stories 1-8 tests cumulative GREEN at minimum equivalent al baseline 2026-05-12 post-Story-8 merge (07-merge.md §"Downstream regression"):
  - luana-core-copilot: 1603 GREEN / 25 skipped (baseline preserved)
  - luana-core-sales-agent: 429/469 GREEN (40 PRE-EXISTING failures — Story 7 carry-over, NOT introduced by Story 9, may or may not be addressed Story 9 — see §10 Risk 6)
  - luana-core-brand-studio: 470 GREEN
  - luana-core-offer-studio: 633 GREEN
  - luana-core-campaigns: 446 GREEN (Story 8)
  - luana-core-extension-sdk: 92 GREEN + 12 arch fitness GREEN (Story 8)
  - luana-core-observability + luana-core-shared + others: GREEN
- TS test suites preservadas equivalentes.
- Zero NEW failures introduced by Story 9 version bumps (verified vía `git diff` analysis: solo `version` strings changed, no code).
- Si `pip install --upgrade` resuelve dependencies cross-package correctamente (uv lockfile consistent).

**Graders:**
- pytest full suite log artifact comparado con Story 8 baseline (07-merge.md `Downstream regression` table) — delta failures = 0.
- shell `uv lock --upgrade` + `uv sync --all-packages` exit 0 (lockfile resolvable post-bump).
- arch fitness `test_no_regression_post_version_bump_story_9.py` (best-effort — parses test results JSON or invokes subset).

**Pre-existing failures policy:** Story 9 NO está obligado a fix las 40 sales-agent PRE-EXISTING failures de Story 7 (per 07-merge.md PRE-1/PRE-2/PRE-3 trivial findings). Architect Story 9 decide si abordar como cleanup ticket dentro Story 9 OR deferr a Story 9.5 OR aceptar carry-over a Story 10. Si aborda en Story 9, ticket dedicado con scope quirúrgico (no expansion). Si defer, documentar en DEFERRED-FILES.

---

### Scenario 9 — `documentation-deliverables-complete` (`type: happy`)

**Given:**
- Story 9 in flight.

**When:**
- Documentation tickets ejecutan: CHANGELOG.md emission, migration guide, API reference auto-gen, extension-points.md stamp update.

**Then:**
- `/CHANGELOG.md` exists en root, contains:
  - Section `## [0.1.0] — 2026-05-XX` (date al merge).
  - Per-package entries (≥ 26 Python + 7 TS = 33 entries, agrupadas por package o por Story).
  - Cross-Story summary: Stories 1-9 listadas con outcome breve cada una.
  - Format Keep-a-Changelog compatible OR semantic-release auto-gen format (architect decide).
- `/docs/migration-from-nicolify.md` exists con secciones:
  - **§1 Audience:** Nicolify maintainers + future brand consumers.
  - **§2 Pre-migration checklist:** Python ≥ 3.12, Node ≥ 22, pnpm ≥ 9, uv installed, `.npmrc` + `~/.pypirc` auth setup to GitHub Packages.
  - **§3 Import migration:** mapping `from src.shared.X import Y` → `from luana_core_X import Y` (Python) + `from '@/...'` → `from '@luana/...'` (TS). Reusa work de Story 10 si ya existe, else preview.
  - **§4 Dependency setup:** `pip install luana-core-platform==0.1.0` patterns + `pnpm add @luana/extension-sdk@0.1.0`.
  - **§5 Extension SDK consumer pattern:** wire FastAPI lifespan + register_all + 18 EPs (link to `docs/extension-points.md`).
  - **§6 Troubleshooting:** common errors (auth missing, version mismatch, namespace not found) + remediation.
- `/docs/api/` directory exists con:
  - Python API reference auto-gen vía `pdoc` o `sphinx` (architect decide simpler — pdoc preferred per spawn prompt). Output `/docs/api/python/` con HTML O markdown per-package.
  - TypeScript API reference auto-gen vía `typedoc`. Output `/docs/api/typescript/`.
  - Script invocation documented en `docs/RELEASES.md` o `Makefile`/`turbo.json` target.
- `/docs/extension-points.md` (Story 8 deliverable) updated con header stamp: `> **Versión:** v0.1.0 (estable pre-1.0 — production-grade alpha)` (replace previous "v0.1.0 (alpha)" si aplica).
- `/docs/RELEASES.md` (Story 1 placeholder) actualizado con sección "Release v0.1.0 (2026-05-XX)" + procedure para tags futuros.

**Graders:**
- shell `test -f CHANGELOG.md && grep -E '^## \[0.1.0\]' CHANGELOG.md` exit 0.
- shell `test -f docs/migration-from-nicolify.md` exit 0 + `grep -E '^## §[1-6]' docs/migration-from-nicolify.md | wc -l` ≥ 6.
- shell `test -d docs/api/python && test -d docs/api/typescript` exit 0.
- shell `ls docs/api/python/*.html OR docs/api/python/*.md | wc -l` ≥ 26 (1 per Python package).
- shell `ls docs/api/typescript/*.html OR docs/api/typescript/*.md | wc -l` ≥ 7.
- pytest arch fitness `test_docs_v0_1_0_deliverables_present.py` — itera lista mandatory deliverables + assert each exists + has minimum content threshold.

---

### Scenario 10 — `aisaleshT-untouched-invariant-cumulative-9-stories` (`type: adversarial`)

**Given:**
- Outcome cumulative invariant V-NF-4: 9 stories ahora; AISALESHT (`/home/chris/AISALESHT/`) MUST permanecer intocado salvo en `docs/product/stories/luana-v0-1-0-publish/**` (Story 9 SSoT artifacts) y `docs/product/outcomes/luana-platform-migration.md` (outcome state updates) y `docs/product/{BACKLOG.{md,yaml},BACKLOG-TLDR.md}` (auto-gen).

**When:**
- Story 9 ejecuta build + publish + docs en `/home/chris/luana-platform/` (separate repo).
- Auditor Story 9 ejecuta `git diff` en AISALESHT durante reviewing.

**Then:**
- AISALESHT `backend/src/**` zero diffs (no business code touched).
- AISALESHT `frontend/src/**` zero diffs.
- AISALESHT `docs/architecture/luana-platform/**` zero diffs (Story 1 audit + ADRs frozen).
- AISALESHT diffs limitados a:
  - `docs/product/stories/luana-v0-1-0-publish/` — Story 9 SSoT (spec, arch, validators, tickets, impl-logs, review, merge, checkpoint transitions)
  - `docs/product/outcomes/luana-platform-migration.md` — Story 9 added to stories_done list, capabilities count updated
  - `docs/product/{BACKLOG.{md,yaml},BACKLOG-TLDR.md}` — auto-regen via pre-commit hook
  - `docs/process/learnings.md` — Session 4 learnings entry (R12 process metric)
  - Possibly `docs/product/capabilities/luana-core/` if capability promoted (release-engineering capability bootstrap)
- Auditor Story 9 invariant `V-NF-AISALESHT-UNTOUCHED` (analog V-NF-4 Story 1-8) GREEN.

**Graders:**
- shell `cd /home/chris/AISALESHT && git diff --name-only main..development -- backend/ frontend/` → empty.
- shell `cd /home/chris/AISALESHT && git diff --name-only main..development | grep -vE '^docs/product/(stories/luana-v0-1-0-publish|outcomes/luana-platform-migration|BACKLOG|capabilities/luana-core)|^docs/process/learnings'` → empty (or expected exceptions only).
- pytest arch fitness `test_aisaleshT_untouched_story_9.py` — assert git diff scope limited (best-effort — environment-dependent).

## 5. Non-functional requirements

| Categoría | Requisito | Verificador |
|---|---|---|
| Workflow latency | Release workflow completes < 30 min total (build + publish + changelog + GH release create) | GitHub Actions duration metric + Risk 4 mitigation |
| Publish atomicity | Either all 33 packages publish OR none publish (no partial release v0.1.0) | Workflow job dependency graph + Scenario 5 fail-fast |
| AISALESHT untouchable | Diff scope per Scenario 10 graders | Auditor V-NF-AISALESHT-UNTOUCHED |
| Test downstream | Stories 1-8 baseline preserved (delta failures = 0) | Scenario 8 graders |
| Cost-routing R23 | NOT triggered (production_code=false) — Sonnet eligible for all tickets | checkpoint owner_eligibility verified |
| Spanish-neutro | Migration guide + extension-points.md stamp en español neutro tuteo. README + CHANGELOG en inglés técnico aceptado | Spanish-text grep (or magic comment `<!-- voseo-allowed -->` si glossary verbatim) |
| License surface | NO archivo expone proprietary code en public registries — solo GitHub Packages private | Auditor C5 cross-cutting check |
| Reproducibility | Re-running workflow desde tag v0.1.0 (post-delete + re-create) yields byte-identical packages OR documented why-not | uv build + pnpm build deterministic flags (architect verifica) |
| Cost ceiling | Session 4 cumulative ≤ $5000 (post-Story-8 ~$3000 spent, Story 9 estimated $1000-2000) — soft check-in markers @ $4000 + $4500 + $5000 | Process metric emission per R12 |

## 6. Constraints técnicos heredados

- `.claude/rules/git-safety.md` — single branch `main` para luana-platform (no feature branches), AISALESHT en `development` (no `main` push sin Chris approval). Force push prohibited. Tags `v*.*.*` push permitted (release mechanism).
- `.claude/rules/anti-default-flip-audit.md` — relevant para SemVer discipline scenarios 7 (breaking change requires audit). Story 9 NO flips de feature flags side-effect (es pure infra), pero documenta el pattern para future Stories 10+.
- `.claude/rules/anti-duplication.md` — no mirror release scripts cross-package (single workflow + single semantic-release config en root).
- `.claude/rules/parallel-safety.md` — Session 4 secuencial autonomous, no parallel sessions Story 9.
- `.claude/rules/spanish-text.md` — migration guide user-facing español neutro (excepción technical README + CHANGELOG inglés OK).
- `.claude/rules/tdd-mandatory.md` — Story 9 mostly CI infra, tests donde aplican (workflow YAML lint + version-bump arch fitness + smoke test + downstream regression). RED → GREEN para arch fitness tests novel.
- Outcome §7.3 lift mode contract — Story 9 NO touches business code (solo version bumps + new infra files). NO scope expansion. NO refactor module boundaries.
- Outcome §7.5.5 production deployment isolation — Story 9 deja claro en `docs/migration-from-nicolify.md` §6 troubleshooting que prod deployment per-brand requires separate K8s/server/etc (out of Story 9 scope).
- AISALESHT `CLAUDE.md` + `AGENTS.md` cross-cutting rules. Magic comment `<!-- voseo-allowed -->` si docs cite glossary verbatim (e.g., migration guide example commit messages with voseo from sales_agent brand voice exception).

## 7. Cross-module impact

- **Lee de:** todos los 26 Python + 7 TS packages workspace (version + package metadata).
- **Es leído por:** Stories 10-14 consumers (Nicolify migration + Vitalia + Comunify + Lupulo bootstraps + brand voice elevation) — todos consumirán `luana-core-*==0.1.0` y `@luana/*@0.1.0` desde GitHub Packages private registry.
- **Eventos emitidos:** ninguno runtime. Solo GitHub events (`release.published`, `release.created`) que pueden trigger downstream automation (Stories 10+ pueden suscribir).
- **Eventos consumidos:** GitHub Actions trigger `push.tags == 'v*.*.*'`.
- **Side-effects externos:**
  - GitHub Packages registry receives 33 new packages (one-time v0.1.0 emission).
  - GitHub release page `/releases/tag/v0.1.0` created.
  - CHANGELOG.md cross-package emitted as release notes asset.
  - GitHub Pages (if enabled by architect for `docs/api/`) receives docs site (opcional — architect decide si scope incluye GitHub Pages deploy o solo emite `docs/api/` artifacts).

## 8. Scope (out — explicit out-of-scope list)

Story 9 deliberadamente NO incluye:

1. ❌ **Nicolify migration to consume `luana-core@0.1.0`** — Story 10 separate scope. Story 9 publishes; Story 10 consumes.
2. ❌ **Vitalia / Comunify / Lupulo brand app bootstraps** — Stories 11-13. Story 9 NO toca `vitalia/`, `comunify/`, `lupulo/` brand directories (excepto coherence bump opcional version field).
3. ❌ **Brand voice elevation refactor** — Story 14 separate scope.
4. ❌ **Feature additions to existing packages** — Story 9 es **release infra only**. NO se agrega lógica, NO se modifica EP, NO se refactor.
5. ❌ **EP-6..EP-18 semantic implementations** — Story 8 dejó signature-only stubs raising `NotImplementedError`. Stories 11-13 implementan semantics per-brand. Story 9 preserva contracts byte-stable.
6. ❌ **CF tunnel multi-domain dev setup** — outcome §7.5.5, Stories 11-13 scope. Story 9 NO config cloudflared.
7. ❌ **npm public registry publish** — proprietary license. Story 9 publishes EXCLUSIVAMENTE a GitHub Packages private registry. NO `npm publish` con default registry.
8. ❌ **PyPI public registry publish** — same proprietary cement. Story 9 NO publishes a `pypi.org`.
9. ❌ **Public docs site marketing** — Story 14 o post-migration. Story 9 emite `docs/api/` reference técnica solo (architect decide si GitHub Pages deploy aplica — opcional).
10. ❌ **Custom GitHub Pages theme / branding cosmetics** — deferred. Default theme aceptado si docs site se deploya.
11. ❌ **Multi-arch Docker images (linux/amd64 + linux/arm64)** — post-migration brand deployment scope (Stories 11-13+).
12. ❌ **GitHub Discussions / community setup** — orthogonal.
13. ❌ **Stable release v1.0.0** — Story 9 emite `v0.1.0` (pre-1.0 production-grade alpha). v1.0.0 cement post-stabilization 4 sem (outcome §1 target_close_window 2026-09-15).
14. ❌ **Eval framework lift (PI-12 sales-agent eval-foundation)** — outcome §6 v0.2.0+ backlog. Story 9 NO bloquea on eval.
15. ❌ **Pre-existing 40 sales-agent test failures fix** — Story 7 carry-over, PRE-1/PRE-2/PRE-3 trivial per 07-merge.md. Story 9 documents en CHANGELOG.md "Known issues" pero NO obligated to fix (puede aborder opcional — ver Scenario 8).

## 9. Edge cases

- **GH Packages org-level token/billing not configured by Chris** → Scenario 5 + halt criterion checkpoint #1. Story 9 HALTS, escalate.
- **semantic-release plugin conflict (Python + TS monorepo)** → Scenario 6 + halt criterion checkpoint #2. Architect Story 9 verifica viability en Phase 0; alternativas docu si conflict (release-please, changesets, custom scripts).
- **First tag `v0.1.0` manual override** — semantic-release normally auto-derives versions from Conventional Commits. Pre-`0.0.x-alpha` commits no permiten derivation directa a `0.1.0`. Architect documenta procedure: first tag manual `git tag v0.1.0 && git push origin v0.1.0`, subsequent tags auto-derived.
- **Workflow timeout (GitHub Actions 6h default)** — Risk 4. Si build de 33 packages excede 6h, split workflow en parallel jobs (e.g., matrix strategy con 4 partitions) o aumentar timeout via `timeout-minutes:`. Architect verifica build time estimate baseline.
- **Publish atomicity rollback** — si publish-python succeeds for 20/26 packages then fails, registry queda con state parcial. Architect documenta rollback procedure (manual `gh api DELETE /orgs/.../packages/.../versions/...` per affected package + retry workflow). NO auto-rollback porque GitHub Packages no support atomic batch.
- **uv lockfile drift post-bump** — si version bump introduce dep mismatch en uv.lock o pnpm-lock.yaml, lockfile re-resolution puede fallar. Mitigation: `uv lock --upgrade` + `pnpm install --lockfile-only` ejecutados en ticket dedicado pre-publish.
- **Cross-package internal deps pinning** — algunos packages pueden tener `luana-core-platform = "==0.0.1-alpha"` hardcoded en pyproject (en vez de `{ workspace = true }`). Architect Phase 0 grep-audita estos casos y migra a `{ workspace = true }` OR bump explicit pin a `==0.1.0` consistente.
- **TS publishConfig.registry** — los 7 `@luana/*` packages requieren `"publishConfig": { "registry": "https://npm.pkg.github.com/" }` en `package.json` o equivalente. Architect verifica + adds donde missing.
- **Python publish auth** — uv publish requires `--token` o env `UV_PUBLISH_TOKEN`. Workflow setup uses `secrets.GITHUB_TOKEN` (default) o `secrets.GH_PACKAGES_TOKEN` (custom PAT) per architect decision.
- **40 sales-agent PRE-EXISTING failures** — Risk 6 + Scenario 8 policy. Architect decide fix-now vs defer.
- **brand-app stubs version coherence** — `nicolify/`, `vitalia/`, `comunify/`, `lupulo/` brand directories pueden quedar `0.0.1-alpha` (NO publishable — solo workspace internals) OR bump a `0.1.0`. Architect decide; both valid.
- **GitHub Pages enablement** — si architect decide emitir `docs/api/` via GitHub Pages, repo settings requieren enable Pages + source branch config. Pre-Story-9 disabled (verify), Story 9 ticket si aplica.

## 10. Risks

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| 1 | GH Packages org-level config (token + billing + permissions) requires manual Chris setup outside autonomous scope | High | Scenario 5 halt criterion. Architect Phase 0 verifica auth strategy. Doc `docs/RELEASES.md` token-setup procedure. Escalate Chris si fail. |
| 2 | semantic-release plugin compat Python + TS monorepo non-trivial (no off-the-shelf solution standard) | Medium-High | Scenario 6 halt criterion. Architect Phase 0 spike viability — fallbacks: release-please, changesets, custom scripts. Document chosen tool en `docs/RELEASES.md`. |
| 3 | First publish v0.1.0 requires manual tag (not auto-derived from `0.0.x-alpha` history) | Low | Architect documents procedure en spec + 03-arch.md. Maintainer executes manually post-merge. |
| 4 | Publishing 33 packages en single workflow excede GitHub Actions 6h timeout | Medium | Architect Phase 0 estimate build time. Si > 4h baseline, split workflow en matrix parallel partitions. |
| 5 | Reverting v0.1.0 publish post-fact requires deleting tag + GH release + republishing — risky | Medium | Architect documents rollback procedure en `docs/RELEASES.md` §Rollback. Recomienda Chris verify pre-merge. |
| 6 | 40 PRE-EXISTING sales-agent test failures (Story 7 carry-over) — Story 9 not obligated to fix but may surface as audit blocker | Medium | Scenario 8 policy. Architect decide fix-now (quirurgic scope) vs defer (DEFERRED-FILES + 07-merge.md note). Auditor accepts pre-existing baseline preservation. |
| 7 | Cross-package internal dep pin drift (hardcoded versions vs `{ workspace = true }`) breaks consumer install post-publish | Medium | Architect Phase 0 audit grep `version = "0.0\..*"` cross-pyproject + migrate to workspace markers or explicit `==0.1.0` pin. Validator V-AG. |
| 8 | uv.lock + pnpm-lock.yaml drift post-version-bump cause lockfile resolution failure | Low-Medium | Dedicated ticket `lockfile-regen` post-bump. `uv lock --upgrade --all-packages` + `pnpm install --lockfile-only`. CI gate ensures lockfile committed. |
| 9 | CHANGELOG.md format conflicts (Keep-a-Changelog vs semantic-release auto-gen) | Low | Architect decide standard upfront. Document choice. Both formats acceptable. |
| 10 | API reference auto-gen (pdoc vs sphinx; typedoc) tooling complexity for 26+7 packages | Low-Medium | Architect chooses simpler (spawn prompt suggests pdoc + typedoc). Script invocation documented. Best-effort emission — incomplete docs NOT a hard blocker if 80%+ packages covered. |
| 11 | Cumulative Session 4 cost crosses $5000 cap (post-Story-8 ~$3000 + Story 9 estimated $1000-2000) | Low (soft check-in) | Process metric emission per R12. Soft check-ins @ $4000 + $4500 + $5000. Chris external tracking — Claude reports progress no para. |

## 11. SemVer discipline cement (post-Story-9 invariant)

Story 9 cementa SemVer discipline real desde v0.1.0 onwards (outcome §7.5.2 D4=C "real_semver_flip"). Las siguientes reglas aplican a TODO commit post-Story-9 que toca un publishable package:

| Regla | Bump type | Trigger | Example |
|---|---|---|---|
| F1 | **major** (`1.0.0` next from `0.1.0`) | EP signature change (e.g., remove field, change param type, rename function) | `feat!: rename BrandContext.tenant_id to brand_tenant_id` |
| F2 | **minor** (`0.2.0` next) | New EP added OR new optional field added to BrandContext or DataClass models | `feat: add EP-19 vertical_dashboard_register (overrides §7.5.4 NO-EP-19 — requires outcome ADR ratification first)` |
| F3 | **patch** (`0.1.1` next) | Bug fix without API change | `fix: ExtensionPointRegistry duplicate detection case-sensitivity bug` |
| F4 | **minor** | BrandContext field addition with default (non-breaking) | `feat: add BrandContext.timezone with default 'UTC'` |
| F5 | **major** | BrandContext field removal | `feat!: remove BrandContext.deprecated_field_v0_0_5` |
| F6 | **special** | Default flag flip side-effect (per `.claude/rules/anti-default-flip-audit.md`) | major bump + grep tests path viejo + commit body audit section mandatory |

**Enforcement layers:**

1. Pre-commit hook (luana-platform repo) — Conventional Commits parser validates `feat!:` / `BREAKING CHANGE:` footer presence for paths matching EP signatures (best-effort static).
2. CI lint job — secondary check on PR.
3. semantic-release plugin — auto-bumps version based on commit messages, fails release if version drift detected.
4. Auditor C4 cross-cutting — manual review of bump-vs-changes alignment.
5. Documentation cement — `docs/RELEASES.md` enumerates F1-F6 with examples for future maintainers.

## 12. Validators preview (for architect 04-validators.yaml)

Architect Story 9 emits `04-validators.yaml` con minimum 20 validators across 4 categories. Preview list:

### Non-functional (V-NF-*)
- **V-NF-1:** AISALESHT untouchable invariant Scenario 10. `cd /home/chris/AISALESHT && git diff --name-only main..development -- backend/ frontend/` empty.
- **V-NF-2:** All 26 Python pyproject + 7 TS package.json version = `0.1.0` Scenario 2.
- **V-NF-3:** No `-alpha` suffix retained Scenario 2 grader.
- **V-NF-4:** apps/test-brand bumped to `0.1.0`.
- **V-NF-5:** Workspace roots (core/pyproject.toml + /package.json) bumped consistent.

### Functional (V-F-release-*)
- **V-F-release-1:** `.releaserc.json` or `.releaserc.cjs` emitted at root + valid JSON schema.
- **V-F-release-2:** `.github/workflows/release.yml` emitted + valid YAML syntax (`actionlint` o `yamllint`).
- **V-F-release-3:** `release.yml` triggers on `v*.*.*` tag push (yaml parse assertion).
- **V-F-release-4:** CHANGELOG.md emitted at root + section `## [0.1.0]` + ≥ 26 package entries.
- **V-F-release-5:** docs/migration-from-nicolify.md emitted + ≥ 6 sections.
- **V-F-release-6:** API reference docs auto-gen scripts/targets in `pyproject.toml` o `Makefile` o `turbo.json`. `docs/api/python/` + `docs/api/typescript/` directories exist.
- **V-F-release-7:** semantic-release dry-run validates config (or chosen alternative tool dry-run GREEN).
- **V-F-release-8:** uv.lock + pnpm-lock.yaml regenerated post-bump + committed.

### Agentic / Integration (V-AG-*)
- **V-AG-1:** `apps/test-brand/` smoke pack 10 scenarios re-run GREEN vs published v0.1.0 packages Scenario 4.
- **V-AG-2:** Downstream regression Stories 1-8 zero NEW failures Scenario 8.
- **V-AG-3:** EP-3 ToolRegistry adapter golden snapshot GREEN (Story 6+7 frozen registries byte-stable post-publish).
- **V-AG-4:** EP-4 WorkflowRegistry adapter golden snapshot GREEN.
- **V-AG-5:** 5 critical EPs (EP-1..EP-5) callable via published `luana-core-extension-sdk==0.1.0` consumer install.

### Documentation + cross-cutting (V-D-*)
- **V-D-1:** CHANGELOG.md ships with Stories 1-9 entries (cross-Story summary section).
- **V-D-2:** migration-from-nicolify.md ships with consumer migration guide §1-§6.
- **V-D-3:** docs/extension-points.md updated header stamp v0.1.0 finalization.
- **V-D-4:** docs/RELEASES.md updated procedure for v0.1.0 + future tags + rollback procedure + token setup.
- **V-D-5:** SemVer F1-F6 rules documented en docs/RELEASES.md o docs/migration-from-nicolify.md.

## 13. Open questions (for architect Story 9 Phase 0 resolution — NOT for Chris)

> Architect Story 9 resuelve estas en Phase 0 sin escalate Chris (within outcome §7.1 + §7.5 binding decisions). Si surfaces uno cardinal genuinamente NUEVO no cubierto, escalate per halt criteria.

1. **API doc tool choice:** pdoc vs sphinx for Python (spawn prompt suggests "architect decides simpler" → pdoc preferred). Typedoc lock for TS. Architect commits choice en 03-arch.md.
2. **CHANGELOG format:** Keep-a-Changelog vs semantic-release auto-gen vs hybrid. Architect commits choice + emits template.
3. **semantic-release alternative:** semantic-release-monorepo plugin viability vs release-please vs changesets vs custom scripts. Architect Phase 0 spike. Document chosen tool.
4. **GitHub Pages enablement:** publish `docs/api/` to Pages site? Opcional. Architect decide. Default: NO (emit `docs/api/` files but no Pages deploy en Story 9).
5. **Brand app stubs version coherence:** bump `nicolify/`, `vitalia/`, `comunify/`, `lupulo/` to `0.1.0` or leave `0.0.1-alpha`? Architect decide (both valid — coherence preferred).
6. **Pre-existing 40 sales-agent failures:** address en Story 9 quirurgic ticket vs defer? Architect decide based on root cause analysis (10 min spike) — if simple template-dir fix, address; if deep, defer.
7. **First-tag procedure documentation:** maintainer manual `git tag v0.1.0 && git push origin v0.1.0` vs workflow-driven via `gh release create v0.1.0`? Both valid. Architect documents preferred path.
8. **Multi-job parallelization estimate:** baseline build time 33 packages. If > 4h linear, split matrix. Architect estimates.

## 14. Cross-story handoff (Story 10 enablement)

Story 9 merge unblocks Story 10 (`luana-nicolify-migration`). Story 10 receives:

- 33 packages published to GitHub Packages private registry at `v0.1.0`.
- `docs/migration-from-nicolify.md` consumer guide.
- `docs/api/` API reference docs.
- `CHANGELOG.md` cross-package history.
- GitHub release `v0.1.0` con assets.

Story 10 will execute:
- Rename `AISALESHT` → `nicolify` (out of Story 9 scope).
- Swap imports `from src.shared.X` → `from luana_core_X` (out of Story 9 scope).
- Install `luana-core-*==0.1.0` + `@luana/*@0.1.0` deps (consumer of Story 9 publish).
- Validate zero regression vs Nicolify pre-migration baseline.

## 15. Próximo paso

- **Si auto-ratified (current state per checkpoint `ratified_by_chris: true`):** /pm transitions state=refining → refined → /architect picks up.
- /architect Story 9 lee este 01-spec.md + outcome §7.1 + §7.5 + Story 8 07-merge.md → produces 03-arch.md + 04-validators.yaml + 05-guidelines.md + 06-tickets.yaml = ready package.
- /dev-team Session 4 continuation picks up Story 9 secuencial autonomous per §7.5.2 D7=B + §7.4 cap extendido to 3 Tier 3 stories.
- /auditor Story 9 post developed → reviewing → CHECKPOINTS C1-C5.
- /pm merge → outcome stories_done = [Stories 1-9] → Story 10 unblocked.

## Changelog

- v1 2026-05-12 — /po Opus draft inicial post Story 8 merge (2026-05-12). Pre-ratified per outcome §7.5.2 D7=B + §7.1 scope decisions. Halt criteria documented Scenarios 5+6+8.
