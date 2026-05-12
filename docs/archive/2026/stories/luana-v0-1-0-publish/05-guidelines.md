---
story_id: luana-v0-1-0-publish
guidelines_version: 1
architect_owner: claude-opus-4-7
ratified_by_chris: true
last_modified: 2026-05-12
---

# 05-guidelines — Story 9 build patterns + constraints

> **Audience:** `/dev-team` builder agents (Sonnet eligible all tickets — R23 NOT triggered)
> **Scope:** release infra only. No business logic. No agentic surface.

## §0 Cardinal directives (read FIRST)

1. **AISALESHT untouchable** — work entirely in `/home/chris/luana-platform/`. NO edits to `/home/chris/AISALESHT/backend/`, `/home/chris/AISALESHT/frontend/`, or any AISALESHT business code. The only AISALESHT edits permitted are Story 9 SSoT artifacts under `docs/product/stories/luana-v0-1-0-publish/` (impl-logs, checkpoint transitions) + `docs/product/outcomes/luana-platform-migration.md` (state updates) + auto-gen BACKLOG.{yaml,md}. Validator V-NF-1 cement.

2. **NO scope expansion** — Story 9 = release infra only. NO new EPs, NO business logic, NO refactor of Stories 6+7 frozen registries, NO refactor of Story 8 SDK contracts. Pure `version` field bumps + new infra files.

3. **NO publish to public registries** — proprietary license cement. ONLY GitHub Packages private registry. NEVER `npm publish` without registry override. NEVER `uv publish` to `pypi.org`.

4. **NO `-alpha` suffix in v0.1.0** — spec resolution per /po notes. "production-grade alpha" semantic per 00-story.md. Validator V-NF-7 cement.

5. **NO Opus required** — `production_code: false` per checkpoint. Sonnet eligible all tickets. If Sonnet hits `cap_reached` → Opus rescue ONLY that ticket (per outcome §7.2 audit failure response).

## §1 Required patterns

### §1.1 Idempotent version bump

ALL bump operations MUST be idempotent (safe to re-run):

```bash
# Python — sed with strict regex
sed -i -E 's/^version = "0\.0\.[0-9]+-alpha"$/version = "0.1.0"/' pyproject.toml

# TS — jq atomic write (idempotent — same input → same output)
jq '.version = "0.1.0"' package.json > package.json.tmp && mv package.json.tmp package.json
```

Re-running the same command on already-bumped files = no-op. Builder can run `T-1` twice safely.

### §1.2 Workflow YAML structure

`.github/workflows/release.yml` MUST:
- Trigger ONLY on `push.tags: ['v*.*.*']` (regex pattern)
- Have job dependency: `publish-typescript` depends_on `publish-python` (atomicity — Scenario 5 fail-fast)
- Include `timeout-minutes` per job (publish ≤ 15min, build ≤ 20min, smoke ≤ 10min)
- Reference secrets via `${{ secrets.GH_PACKAGES_TOKEN || secrets.GITHUB_TOKEN }}` (fallback pattern)
- Validate SemVer regex in `validate-tag` job before downstream

Pass `actionlint` (if available) + Python `yaml.safe_load` parse.

### §1.3 release-please config schema

`release-please-config.json` MUST:
- `$schema` field pointing to canonical schema URL
- 33 entries in `packages` (26 Python + 7 TS)
- `release-type: python` for `core/luana-core-*` entries
- `release-type: node` for `core/@luana/*` entries
- `linked-versions` plugin configured for monolithic version bumps

`.release-please-manifest.json` MUST seed all 33 packages at `0.1.0`.

### §1.4 CHANGELOG.md format

Keep-a-Changelog 1.1.0 format:
- `## [VERSION] — YYYY-MM-DD` headers (not `## VERSION`)
- Sections per Story (Foundations, Shared lift, IAM+Tenancy, CRM+Analytics, Brand+Offer, Copilot Engine, Sales Agent Engine, Campaigns+SDK, Release Engineering)
- "Known issues" subsection mentions 40 sales-agent PRE-EXISTING failures
- Bottom: tagref `[0.1.0]: https://github.com/...`

### §1.5 Spanish neutro LatAm (user-facing docs)

`docs/migration-from-nicolify.md` user-facing → **español neutro tuteo**. Sin voseo.

Glossary (per `.claude/rules/spanish-text.md`):
- "puedes" (NOT "podés")
- "necesitas" (NOT "necesitás")
- "tu repo" (NOT "tu repo loco")
- "instala" (NOT "instalá")

**English OK:**
- README.md (root)
- CHANGELOG.md (devs read it)
- docs/RELEASES.md (release procedure — technical)
- docs/api/ auto-gen (pdoc/typedoc output English by design)
- Code comments + commit messages

**Voseo magic comment** if doc cites glossary verbatim (rare in Story 9):
```markdown
<!-- voseo-allowed: docs cite Story 7 sales_agent voice example with voseo -->
```

### §1.6 Native-first execution (NEVER docker exec)

All lint/test/build commands run native WSL:
- `cd /home/chris/luana-platform && uv sync --all-packages`
- `cd /home/chris/luana-platform && uv run ruff check`
- `cd /home/chris/luana-platform && pnpm install --frozen-lockfile`
- `cd /home/chris/luana-platform && pnpm -r build`
- `cd /home/chris/luana-platform && uv run pytest`

Docker only for `make ci-parity` (if invoked — usually not in Story 9 scope since lift mode pre-cement passes).

### §1.7 TDD layer order

Tests RED first per layer:
1. Write arch fitness test (e.g., `test_workspace_versions_uniform_at_v0_1_0.py`) — FAILS without bump
2. Execute version bump (T-1)
3. Run arch test → GREEN
4. Commit

Same for workflow YAML, releaserc config, docs deliverables.

## §2 Forbidden patterns

### §2.1 NEVER touch

- ❌ AISALESHT `backend/`, `frontend/`, `docs/architecture/luana-platform/` (Story 1 frozen)
- ❌ luana-platform `core/luana-core-copilot/src/` (Story 6 frozen)
- ❌ luana-platform `core/luana-core-sales-agent/src/` (Story 7 frozen)
- ❌ luana-platform `core/luana-core-extension-sdk/src/` (Story 8 frozen — D-T1 byte-stable cement)
- ❌ luana-platform `core/luana-core-extension-sdk/src/_adapters.py` (Story 8 D-T1 underscore-private wrappers)
- ❌ luana-platform `.github/workflows/ci.yml` (Story 1 baseline — separate concern from release.yml)
- ❌ luana-platform `docs/ARCHITECTURE.md`, `docs/CONTRIBUTING.md` (Story 1 frozen)
- ❌ luana-platform `docs/architecture/` ADR folder (Story 1 frozen — new ADRs only if Story 9 surfaces architectural decision, which it shouldn't per cement table §0)

### §2.2 NEVER do

- ❌ `git push --force` / `--force-with-lease` (per parallel-safety.md cement)
- ❌ `git pull` / `git fetch && merge` (per parallel-safety.md)
- ❌ `git revert` without explicit Chris approval (per git-safety.md)
- ❌ `git add .` / `git add -A` (parallel sessions WIP) — stage by exact filename
- ❌ `git commit --no-verify` (pre-commit hooks mandatory)
- ❌ Pin Python cross-package deps to hardcoded `==0.0.x-alpha` (use `{ workspace = true }` for Story 1-8 pattern — bump leaves these as-is, only top-level version changes)
- ❌ Refactor `_adapters.py` underscore-private pattern (Story 8 cement)
- ❌ Add new EPs (Story 8 cement: 18 EPs frozen, EP-19 forbidden per §7.5.4 NO-EP-19 invariant)
- ❌ Fix the 40 PRE-EXISTING sales-agent failures inside Story 9 (defer Story 10+ cleanup — architect §0 cement)
- ❌ Publish to `pypi.org` or default `npm registry` (proprietary cement)
- ❌ Add `-alpha` suffix to v0.1.0 (spec resolution cement)

### §2.3 NEVER assume

- ❌ Don't assume `GITHUB_TOKEN` has `write:packages` scope by default (workflow tests this; fallback to `GH_PACKAGES_TOKEN` PAT)
- ❌ Don't assume cross-package deps are auto-bumped (release-please does this v0.2.0+, NOT v0.1.0 first-tag manual bump)
- ❌ Don't assume Python `__version__` attribute exists on every package (smoke test reads from installed metadata via `importlib.metadata.version()` if `__version__` absent)
- ❌ Don't assume actionlint is installed locally (CI installs it; local builders fallback to `python yaml.safe_load`)

## §3 Files in scope

Builder may edit / create:

**Workspace bumps (T-1):**
- `core/pyproject.toml` (workspace internal root — bump version)
- `core/luana-core-*/pyproject.toml` (×26)
- `core/@luana/*/package.json` (×7)
- `apps/test-brand/pyproject.toml`
- `nicolify/pyproject.toml` + `nicolify/package.json`
- `vitalia/pyproject.toml` + `vitalia/package.json`
- `comunify/pyproject.toml` + `comunify/package.json`
- `lupulo/pyproject.toml` + `lupulo/package.json`
- `package.json` (workspace top root)
- `uv.lock` (regen)
- `pnpm-lock.yaml` (regen)

**New release infra (T-2):**
- `.github/workflows/release.yml`
- `release-please-config.json`
- `.release-please-manifest.json`
- `commitlint.config.cjs` (seed — opt-in v0.2.0+)

**New docs (T-3):**
- `CHANGELOG.md` (root)
- `docs/migration-from-nicolify.md`
- `docs/api/` (directory tree — auto-gen by `scripts/generate_api_docs.sh`)
- `docs/RELEASES.md` (EXTEND — append v0.1.0 procedure + rollback + token setup + SemVer F1-F6)
- `docs/extension-points.md` (EXTEND — bump header stamp v0.1.0)

**New scripts (T-3):**
- `scripts/generate_api_docs.sh` (pdoc + typedoc runner)
- `scripts/publish_smoke_test.sh` (post-publish smoke)
- `scripts/rollback_partial_publish.sh` (manual rollback procedure)

**New arch fitness tests (T-4):**
- `tests/architecture/test_workspace_versions_uniform_at_v0_1_0.py`
- `tests/architecture/test_release_workflow_yaml_valid.py`
- `tests/architecture/test_releaserc_config_valid.py`
- `tests/architecture/test_docs_v0_1_0_deliverables_present.py`
- `tests/architecture/test_aisaleshT_untouched_story_9.py` (best-effort, env-gated)

**AISALESHT (Story 9 SSoT only — T-5):**
- `docs/product/stories/luana-v0-1-0-publish/T-{1..5}-impl-log.md`
- `docs/product/stories/luana-v0-1-0-publish/checkpoint.md` (state transitions)
- `docs/product/outcomes/luana-platform-migration.md` (stories_done update post-merge)
- `docs/product/BACKLOG.{yaml,md}` (auto-gen via pre-commit hook)

## §4 Rules + skills to load

### §4.1 Rules (cardinal)

| # | Rule | Trigger |
|---|---|---|
| 1 | `.claude/rules/git-safety.md` | Always |
| 2 | `.claude/rules/parallel-safety.md` | Always (single Claude sequential session 4) |
| 3 | `.claude/rules/tdd-mandatory.md` | Before writing arch fitness tests |
| 4 | `.claude/rules/spanish-text.md` | Before writing `docs/migration-from-nicolify.md` |
| 5 | `.claude/rules/anti-duplication.md` | Reference only (Story 9 introduces NEW layer — no existing release pipeline) |
| 6 | `.claude/rules/anti-default-flip-audit.md` | Reference (SemVer F6 cement — but Story 9 itself does NOT flip flags) |
| 7 | `.claude/rules/auditor-downstream-regression.md` | Auditor consumes (Story 9 = `shared/` analog: workspace pyproject changes ripple to ALL 26 packages' tests) |

### §4.2 Skills (consume on demand)

| Skill | When |
|---|---|
| `backend-expert` | Reference for release infra patterns (no new BE code surface) |
| `tessl__fastapi` | NOT triggered (no FastAPI surface) |
| `tessl__langgraph` | NOT triggered (no agentic surface) |
| `tessl__graceful-degradation` | Reference for workflow failure modes (fail-fast atomicity) |
| `copilot-expert` | NOT triggered (Story 9 doesn't touch copilot) |
| `sales-agent-expert` | NOT triggered |

## §5 Owner eligibility per ticket

Per checkpoint `owner_eligibility: [opus, sonnet]` + `production_code: false`:

| Ticket | Surface | Sonnet OK? | Notes |
|---|---|---|---|
| T-1 | Version bumps cross-pkg | ✅ Yes | Mechanical sed/jq — Sonnet eligible |
| T-2 | release.yml + releaserc + commitlint | ✅ Yes | CI/CD config — Sonnet eligible |
| T-3 | CHANGELOG + migration guide + API docs + RELEASES update | ✅ Yes | Doc emission — Sonnet eligible |
| T-4 | Arch fitness tests + smoke scripts | ✅ Yes | Test infra — Sonnet eligible |
| T-5 | Finalization (impl-logs + V-NF-1 verify + DEFERRED-FILES update + auto-fmt) | ✅ Yes | Closure mechanics — Sonnet eligible |

If any ticket surfaces unexpected Opus need (e.g., release-please conflict requires architectural fallback design), escalate to Opus rescue for that ticket only.

## §6 Commit conventions

Per `.claude/rules/git-safety.md` + `.claude/rules/anti-default-flip-audit.md` analog:

```
<type>(<scope>): <description>

<body — why, not what>

<footer — co-authors + breaking change if applicable>
```

**Types:**
- `feat` — new infra (release.yml, CHANGELOG seed, migration guide, api docs scripts)
- `chore` — version bumps cross-pkg, lockfile regen
- `docs` — RELEASES update, extension-points header bump
- `test` — arch fitness tests, smoke scripts
- `ci` — workflow tweaks

**Examples:**
- `chore(workspace): bump all 33 packages 0.0.x-alpha → 0.1.0`
- `feat(release): introduce GH Packages publish pipeline (release.yml + release-please)`
- `docs(release): emit CHANGELOG.md + migration-from-nicolify.md + RELEASES v0.1.0 procedure`
- `test(arch-fitness): cement workspace versions uniform 0.1.0 + workflow YAML valid + docs deliverables`

Co-author footer per session 4 mandate:
```
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```
(or Opus if Opus rescue invoked for ticket)

## §7 Failure modes + escalation

### §7.1 Halt criteria (escalate Chris)

Per outcome §7.2 audit failure response + checkpoint halt_criteria_session_4:

1. **GH Packages auth missing** (Scenario 5) — workflow setup discovers `GITHUB_TOKEN` lacks `write:packages` scope AND no `GH_PACKAGES_TOKEN` secret configured. Builder STOPS, documents `docs/RELEASES.md` token-setup procedure, escalates Chris for secret + scope config.

2. **release-please config conflict** — Phase 0 spike reveals release-please can't handle uv + pnpm monorepo cleanly. Builder switches to FALLBACK: changesets (TS-only) + custom Python bash publish script in `release.yml`. Documents choice in `docs/RELEASES.md`.

3. **Test downstream R3 breakage** — auditor runs Stories 1-8 tests, discovers NEW failures introduced by Story 9 bumps. Auto-fix cap 2 iter (per outcome §7.2). If still failing, escalate.

4. **Cumulative session 4 cost crosses $5000** — soft check-in. Claude reports progress + cost, Chris confirms continue.

### §7.2 Auto-fix iter cap (audit failure response)

Per outcome §7.2: cap 3 iter Opus auto-fix. Story 9 expected single-iter audit (lift-mode-equivalent simplicity). If 3 iters fail, escalate.

### §7.3 Common Story 9 gotchas

- **uv.lock regen fails:** `uv lock --upgrade` fails on dep conflict. Fallback: `uv lock --upgrade --resolution=lowest` then `--resolution=highest` for sanity check.
- **pnpm-lock.yaml drift:** `pnpm install --lockfile-only` flags drift. Run `pnpm install --no-frozen-lockfile` to regen, then commit.
- **TS `publishConfig` missing:** some `@luana/*` package.json may lack `"publishConfig": { "registry": "https://npm.pkg.github.com/" }`. Builder ADDS this in T-1 to enable pnpm publish later. NOT a refactor — it's release infra prep.
- **uv workspace bump doesn't auto-update internal deps:** if pkg A pins pkg B at hardcoded version (architect Phase 0 grep audit confirms NO hardcoded pins — all `{ workspace = true }`). If new pins surface, builder bumps explicit `==0.1.0`.
- **actionlint not installed:** validator V-F-release-2 has graceful fallback. CI installs actionlint; local builders rely on Python yaml.safe_load parse only.

## §8 Process metric emission (R12 layer 1)

Per outcome §7.2 process metrics:

```bash
# Post-ticket completion
python scripts/emit_process_metric.py \
  --story luana-v0-1-0-publish \
  --ticket T-1 \
  --status complete \
  --owner sonnet \
  --tokens <input>+<output> \
  --duration_min <wall_time>
```

Builder runs this per ticket (Step 5.5 per `/dev-team` skill).

## §9 Cross-Story-10 handoff cement

Story 9 outputs feed Story 10 (luana-nicolify-migration) consumer:
- 33 packages published to GitHub Packages at v0.1.0 (V-AG-5 callable)
- `docs/migration-from-nicolify.md` consumer guide (§3 import mapping = Story 10's playbook)
- `docs/api/` reference (Story 10 devs reference)
- `CHANGELOG.md` cross-package history (Story 10 audit baseline)
- `release.yml` workflow (Story 10 may trigger v0.2.0 post-Nicolify-migration if architect Story 10 decides additive features)

NO Story 10 contract changes invented in Story 9 — pure handoff via published artifacts.

## §10 Completion checklist (builder ratifies before transition to developed)

- [ ] All 23 validators in `04-validators.yaml` GREEN
- [ ] AISALESHT V-NF-1 verified post-bump (`git diff main..development -- backend/ frontend/` empty)
- [ ] 5 impl-log files emitted (T-1..T-5) in `docs/product/stories/luana-v0-1-0-publish/`
- [ ] `docs/product/outcomes/luana-platform-migration.md` `stories_active` and pending merge
- [ ] DEFERRED-FILES.md in luana-platform updated with Story 10+ cleanup items
- [ ] Pre-commit hooks GREEN cross-commits
- [ ] No magic comments added without justification (ruff/voseo)
- [ ] Spanish neutro LatAm verified in `docs/migration-from-nicolify.md`
- [ ] Lockfiles committed (uv.lock + pnpm-lock.yaml)
- [ ] Workflow `release.yml` does NOT auto-trigger on push to main (only on `v*.*.*` tag) — re-verify dry-run if available
- [ ] `release-please-config.json` 33 packages enumerated
- [ ] CHANGELOG.md v0.1.0 section emitted with cross-Story summary
- [ ] V-AG-2 zero NEW failures cement (40 sales-agent PRE-EXISTING preserved as baseline)
