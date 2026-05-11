---
story_id: luana-iam-tenancy-content
guidelines_version: 1
last_modified: 2026-05-11
drafted_by: /architect (claude-opus-4-7)
authority: 03-arch.md + 01-spec.md + outcome §7.3 lift mode + Story 2 05-guidelines.md pattern
---

# 05-guidelines.md — luana-iam-tenancy-content

> /dev-team reads this BEFORE picking up any ticket. Defines patterns required/forbidden, files in scope, skills to load, halt criteria. Sub-builders inherit this guidance verbatim.

## §1. Patterns Required

### §1.1 Lift mode (per outcome §7.3, identical to Story 2 §1.1)

- **Verbatim file copy.** Use `cp -r` to lift source → destination. Do NOT rewrite, do NOT reformat, do NOT renumber lines.
- **Preserve DDD layering.** `domain/` → `infrastructure/` → `application/` → `api/` boundaries stay intact within each package.
- **Preserve class/function/module names.** `User` stays `User`. `TenantService` stays `TenantService`. `verify_clerk_token` stays `verify_clerk_token`. `DomainStatus` stays `DomainStatus`.
- **Preserve public API surface.** Re-export shape via `__init__.py` matches AISALESHT verbatim.
- **Preserve tests.** Lift `backend/tests/modules/<m>/test_*.py` alongside source.
- **Per-package `pyproject.toml` at version `"0.0.1-alpha"`** (template literals in 03-arch.md §8).
- **Update import paths INTERNOS to luana-platform only.** Use search-and-replace mapping in 03-arch.md §5.

### §1.2 Workspace registration (single ticket T-1)

- Add each new Python package to `~/luana-platform/pyproject.toml` `[tool.uv.workspace] members` AND `[tool.uv.sources]` (template in 03-arch.md §4.1).
- Run `cd ~/luana-platform && uv sync --all-packages` after each package added — confirms registration.

### §1.3 Import path rewriting (verbatim mechanical sed)

Inside each newly lifted package, apply these sed patterns. Use the **exact patterns** below — over-broad sed corrupts strings inside docstrings/test fixtures (Story 2 §9 pitfall #3).

```bash
# Per Story 3 module (PKG_SNAKE = luana_core_iam, luana_core_tenant_profile, etc.)
# Replace <m> with original module slug (iam, tenant_profile, ...) and <pkg_snake> with destination (luana_core_iam, ...).
cd ~/luana-platform/core/luana-core-<name>

# 1. Self-imports: src.modules.<m>.<X> → <pkg_snake>.<X>
find src tests -name "*.py" -exec sed -i 's|from src\.modules\.<m>\.|from <pkg_snake>.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|import src\.modules\.<m>\.|import <pkg_snake>.|g' {} \;

# 2. Cross-module Story 3 → iam (only Batch 2 packages need this)
find src tests -name "*.py" -exec sed -i 's|from src\.modules\.iam\.|from luana_core_iam.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|import src\.modules\.iam\.|import luana_core_iam.|g' {} \;

# 3. Cross-module Story 3 → Story 2 platform (shared.* + core.*)
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.domain\.|from luana_core_platform.domain.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.links\.|from luana_core_platform.links.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.infrastructure\.|from luana_core_platform.infrastructure.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.workers\.|from luana_core_platform.workers.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.api\.|from luana_core_platform.api.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.application\.\(ai_action_service\|brand_summary_event_handlers\|field_diff\|progress_emitter\)|from luana_core_platform.application.\1|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.domain\.events|from luana_core_platform.domain.events|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.core\.|from luana_core_platform.core.|g' {} \;

# 4. NOTE: do NOT rewrite imports of src.modules.copilot — that's the DEFERRED skip signal (§3.3).
# If you find such an import in source you're lifting → check §3.3, the file is in DEFERRED list.
```

### §1.4 Per-package barrel exports (`__init__.py`)

Each lifted directory needs `__init__.py` lifted too. Some are empty markers; preserve hierarchy. Do NOT consolidate or strip them.

### §1.5 Test execution per package

After lift, run that package's tests in isolation BEFORE adding to workspace aggregate:

```bash
cd ~/luana-platform
uv run pytest core/luana-core-<name>/tests/ -x -q --tb=short
```

GREEN per-package, then proceed to next ticket.

### §1.6 Brand-agnostic IAM verification (NEW — Story 3-specific)

Before declaring T-2 done, verify iam stays brand-agnostic via:

```bash
# Quick local smoke (full arch test runs in T-8)
cd ~/luana-platform/core/luana-core-iam/src
grep -rEn 'if\s+brand\s*==|if\s+tenant\.brand\s*==|brand\s*==\s*"(nicolify|vitalia|comunify|lupulo)"' luana_core_iam/ || echo "OK: no brand control flow"
grep -rEn 'CLERK_PUBLISHABLE_KEY\s*=\s*"[^o].' luana_core_iam/ || echo "OK: no hardcoded Clerk keys"
```

If either grep finds matches → escalate per §6 halt criterion 5 (lift mode violation: source has brand-aware code that shouldn't have been merged to AISALESHT either).

### §1.7 Cyclic dep — N/A

Unlike Story 2 (platform↔llm cycle), Story 3 has no cyclic deps. iam depends on platform; Batch 2 depends on iam + platform. Pure DAG.

## §2. Patterns Forbidden

### §2.1 Lift mode violations (auto-FAIL, per Story 2 §2.1)

- ❌ **Renaming any class, function, module, or symbol.** Original names preserved.
- ❌ **Refactor logic** while lifting — even "obvious improvements" — escalate per outcome §7.4.
- ❌ **Splitting modules.** A module file stays a module file.
- ❌ **Merging modules.** Two files stay two files.
- ❌ **Adding new abstractions** (factories, registries, adapters) not present in AISALESHT.
- ❌ **Changing public API signatures.** Same args, same return types, same exceptions.
- ❌ **Removing code** during lift — even if "clearly dead".
- ❌ **Reformatting** beyond what `ruff format` would do automatically on save.

### §2.2 Mutating AISALESHT (auto-FAIL — Scenario D of 01-spec.md)

- ❌ **Any file under `backend/src/modules/{iam,tenant_profile,tenant_domains,commercial_calendar,social_proof,assets}/`** is READ-ONLY in Story 3.
- ❌ **Any file under `backend/tests/modules/<same set>/`** is READ-ONLY.
- ❌ **Modifying AISALESHT pyproject.toml, alembic migrations, conftest.py at root.** Out of scope.
- ❌ **Running `make ci-parity` against AISALESHT to "verify lift didn't break it"** — Story 3 doesn't change AISALESHT. Story 10 will validate.

### §2.3 Brand-aware code in luana-core-iam (auto-FAIL — Story 3-specific)

- ❌ **`if brand == "..."` or `if tenant.brand == "..."`** control flow in iam source.
- ❌ **Hardcoded Clerk publishable key, app ID, or instance ID** in iam source.
- ❌ **`from nicolify.X` or `import nicolify.X`** — iam stays brand-agnostic engine.
- ❌ **Adding a `brand_id` column or constructor param** to User/Tenant/anything iam — that's refactor + scope expansion.

ClerkService MUST be instantiated with config from settings/env/DI ONLY. The AISALESHT current pattern already satisfies this (ClerkService reads `settings.CLERK_SECRET_KEY`). Preserve verbatim.

### §2.4 Lifting deferred files (auto-FAIL — per §3.3)

- ❌ `backend/src/modules/commercial_calendar/copilot_provider/` → DEFERRED Story 6.
- ❌ `backend/src/modules/social_proof/copilot_provider/` → DEFERRED Story 6.
- ❌ Any test file specifically testing the deferred copilot_provider/ shims (grep for `test_copilot_provider*` in test directories — none found currently; if you discover one, treat as DEFERRED).

When lifting commercial_calendar/social_proof, **SKIP** the `copilot_provider/` sub-folder explicitly:

```bash
# Correct lift of commercial_calendar (excludes copilot_provider/):
cd /home/chris/AISALESHT/backend/src/modules/commercial_calendar
for sub in api application domain infrastructure __init__.py; do
  cp -r "$sub" ~/luana-platform/core/luana-core-commercial-calendar/src/luana_core_commercial_calendar/
done
# DO NOT: cp -r copilot_provider ...
```

### §2.5 Publishing artifacts (Story 9 territory — auto-FAIL)

- ❌ `publishConfig` field in any `pyproject.toml`.
- ❌ `.releaserc.json` or semantic-release configuration.
- ❌ `.github/workflows/release*.yml` or `publish*.yml`.
- ❌ `[project.urls]` pointing to GH Packages registry.
- ❌ Any reference to `uv publish` or `twine upload` in scripts.

### §2.6 Scope expansion (escalate, not fix)

- ❌ Lifting modules NOT in 03-arch.md §1.2 scope (brand/, offer/, crm/, etc. → out of scope, Stories 4-7).
- ❌ Creating new luana-core-* packages not in 03-arch.md.
- ❌ Stubbing `BaseCopilotProvider` Protocol in `luana-core-platform.links.ports` to "unblock copilot_provider/ lift" — that's REFACTOR + cross-story coupling. Defer.
- ❌ Modifying outcome §7.3 lift mode constraints.

### §2.7 Schema/migration changes (escalate)

- ❌ Touching Alembic migrations in AISALESHT or luana-platform.
- ❌ Changing SQLA model schemas — even adding indexes.
- ❌ Migration generation. Schema stays in AISALESHT (Story 4+ territory).

## §3. Files in Scope

### §3.1 SOURCE (AISALESHT — READ-ONLY)

**Backend Python (lift verbatim, EXCLUDING `copilot_provider/` subfolders):**

```
backend/src/modules/iam/                                  → luana-core-iam (28 files)
  api/, application/, domain/, infrastructure/             (no copilot_provider)

backend/src/modules/tenant_profile/                       → luana-core-tenant-profile (18 files)
  api/, application/, domain/, infrastructure/, __init__.py

backend/src/modules/tenant_domains/                       → luana-core-tenant-domains (18 files)
  api/, application/, domain/, infrastructure/, workers/, __init__.py
  # workers/tasks.py LIFTS (small ARQ worker, no module coupling — verified)

backend/src/modules/commercial_calendar/                  → luana-core-commercial-calendar (17-1=16 files)
  api/, application/, domain/, infrastructure/, __init__.py
  copilot_provider/  ← DEFERRED Story 6 (DO NOT COPY)

backend/src/modules/social_proof/                         → luana-core-social-proof (39-X files)
  api/, application/, domain/, infrastructure/, __init__.py
  copilot_provider/  ← DEFERRED Story 6 (DO NOT COPY)

backend/src/modules/assets/                               → luana-core-assets (24 files)
  api/, application/, domain/, infrastructure/             (no copilot_provider)
```

**Backend tests (lift verbatim):**

```
backend/tests/modules/iam/                  → core/luana-core-iam/tests/                  (16 files)
backend/tests/modules/tenant_profile/       → core/luana-core-tenant-profile/tests/        (6 files)
backend/tests/modules/tenant_domains/       → core/luana-core-tenant-domains/tests/        (7 files)
backend/tests/modules/commercial_calendar/  → core/luana-core-commercial-calendar/tests/   (6 files)
backend/tests/modules/social_proof/         → core/luana-core-social-proof/tests/          (6 files; preserves unit/ + integration/ subdirs)
backend/tests/modules/assets/               → core/luana-core-assets/tests/                (9 files)
```

### §3.2 DESTINATION (luana-platform — CREATE)

```
~/luana-platform/
├── pyproject.toml                  # MODIFY: add 6 workspace members + sources
├── core/
│   ├── luana-core-iam/             # CREATE (T-2)
│   ├── luana-core-tenant-profile/  # CREATE (T-3)
│   ├── luana-core-tenant-domains/  # CREATE (T-4)
│   ├── luana-core-commercial-calendar/  # CREATE (T-5)
│   ├── luana-core-social-proof/    # CREATE (T-6)
│   ├── luana-core-assets/          # CREATE (T-6)
│   ├── tests/architecture/         # EXTEND (T-8) — 2 NEW arch tests
│   │   ├── test_iam_brand_agnostic.py            # NEW
│   │   └── test_story3_no_forward_module_imports.py  # NEW
│   └── DEFERRED-FILES.md           # APPEND (T-11) — Story 3 entries
```

### §3.3 EXPLICITLY DEFERRED (Story 6 — DO NOT LIFT)

```
backend/src/modules/commercial_calendar/copilot_provider/   ← Story 6 (imports src.modules.copilot.domain.ports)
backend/src/modules/social_proof/copilot_provider/          ← Story 6 (same reason)
```

**Detection rule:** if grep `from src.modules.copilot` in any file you're lifting → file is DEFERRED. STOP lifting that file. Document in commit body + append to `core/DEFERRED-FILES.md`.

## §4. Skills + Rules to Load

### §4.1 Mandatory skills (auto-load per ticket)

| Trigger | Skill |
|---|---|
| Touching `core/luana-core-iam/` | `backend-expert` (DDD layering, SQLA 2.0 patterns) + Clerk-via-env preserve |
| Touching `core/luana-core-tenant-{profile,domains}/` | `backend-expert` |
| Touching `core/luana-core-{commercial-calendar,social-proof,assets}/` | `backend-expert` |
| Touching iam (skipping copilot_provider only) | `copilot-expert` § anti-duplication awareness — verify NO mirror behavior in iam (none expected) |
| Touching arch fitness tests | `backend-expert` references/architectural-fitness.md |

### §4.2 Mandatory rules (auto-load — already in CLAUDE.md)

- `.claude/rules/anti-duplication.md` — Story 3 LIFTS module code, NOT shared abstractions. No mirror risk WITHIN Story 3 scope (different from Story 2).
- `.claude/rules/backend-ddd.md` — Inside-Out layering preserved within each package.
- `.claude/rules/tenant-isolation.md` — every entity carries `tenant_id` (verbatim from AISALESHT).
- `.claude/rules/tdd-mandatory.md` — tests lift alongside source.
- `.claude/rules/parallel-safety.md` — single branch `development` in AISALESHT, luana-platform is SEPARATE git repo. Same `add by name` discipline.
- `.claude/rules/git-safety.md` — applies to luana-platform repo too.

### §4.3 Optional helper

- `tessl__fastapi` — applicable for iam (FastAPI routes lift verbatim, no new). Skim if unfamiliar with `response_model=` convention.
- `tessl__graceful-degradation` — N/A to Story 3 (lift, no new external calls).

## §5. Build Coordination (concurrency)

- /dev-team picks tickets per DAG order in 06-tickets.yaml. Foundation tickets sequential (T-1 → T-2). Batch 2 tickets (T-4, T-5, T-6) parallelizable but **1 Claude session sequentially** per outcome §7.4. /dev-team picks ONE ticket at a time, GREEN validators before next pick.
- Tickets T-7 (workspace integration) + T-8 (arch fitness) + T-9 (lint) + T-10 (no-publish + no-AISALESHT-mutation verify) + T-11 (READMEs + DEFERRED-FILES) run AFTER all lift tickets done.

## §6. Halt Criteria (auto-stop + escalate Chris)

Per outcome §7.4 + 01-spec.md §4 + 03-arch.md §10:

1. **Cross-Story-3-to-Story-4/5 coupling discovered** — file in scope imports from `src.modules.{brand,offer,landing,crm,analytics,advertising,social_media,scheduling,connections}` (NOT just `src.modules.copilot` which is documented §3.3). Escalate per spec §4.1.
2. **iam runtime requires brand-specific config** — would break brand-agnostic invariant. Escalate per spec §4.2.
3. **Tests fail after lift** — re-run with `uv run pytest --tb=long`. If failure is mock path stale (`monkeypatch.setattr("src.modules.iam...")`), update mock to `luana_core_iam.X` verbatim. If failure is logic error → escalate (lift mode forbids fix-while-lift).
4. **3 auto-fix iter fail per ticket** — Sonnet → Opus rescue per outcome §7.4. After Opus rescue cap_reached → escalate per spec §4.3.
5. **Scope expansion needed** — any refactor required to lift cleanly → escalate per spec §4.4, NOT proceed.
6. **Cumulative session cost > $1500** — soft check-in per outcome §7.2 + spec §4.5.
7. **AISALESHT modification accidentally introduced** (V-NF-4 fails) — revert immediately, escalate cause (likely sed pattern bug or paste error).
8. **uv sync fails** with dependency resolution error post Story 3 registration — escalate, /architect re-evaluates topology.
9. **Brand-aware code discovered in lifted iam** (V-AG-1 fails) — escalate. Means AISALESHT iam already had brand contamination that Story 3 surfaced. Decision: either fix-in-AISALESHT first (out of Story 3 scope) or accept arch test failure as-is.

## §7. Commit Conventions

Each ticket emits ONE commit to luana-platform repo. Each commit follows:

```
feat(luana-core-<name>): lift {module} from AISALESHT modules/{path}

- Lift backend/src/modules/{path}/ → core/luana-core-<name>/src/luana_core_<name>/
- Lift tests backend/tests/modules/{path}/ → core/luana-core-<name>/tests/
- Add pyproject.toml at version 0.0.1-alpha
- Update internal imports per 03-arch.md §5.1 mapping
- Verbatim lift per outcome §7.3 lift mode constraint
- [if applicable] copilot_provider/ subfolder DEFERRED to Story 6 (see 03-arch.md §9)

Ticket: T-{n} (story luana-iam-tenancy-content)
Validators addressed: V-F-py-{n}, V-NF-{n}

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

**Stage by exact filename** per parallel-safety.md. NO `git add .` / `git add -A` / `git add -u`.

## §8. Per-Ticket Validators Cross-Reference

See 06-tickets.yaml `validators_addressed` per ticket. Each ticket cites which V-* validators it must turn GREEN before completion.

## §9. Common Pitfalls (avoid these — informed by Story 2)

1. **copilot_provider/ subfolder accidentally lifted.** Easy mistake when using `cp -r commercial_calendar/* dest/`. Use explicit sub-dir list (§2.4 example) or `--exclude=copilot_provider` rsync flag.
2. **conftest.py at module level forgotten.** Each `backend/tests/modules/<m>/conftest.py` lifts verbatim. If skipped, pytest may not discover fixtures.
3. **Sed pattern over-broad.** Naive `sed 's|src.modules|luana_core|g'` would corrupt strings in docstrings, mock paths inside conftest, AISALESHT module references in comments. Use precise patterns from §1.3.
4. **Test fixtures use string paths.** `monkeypatch.setattr("src.modules.iam.api.dependencies.get_current_user", ...)` — must rewrite to `"luana_core_iam.api.dependencies.get_current_user"`. Grep `monkeypatch.setattr` + `mocker.patch` + `patch(` in lifted tests, update each.
5. **`__init__.py` re-exports.** iam's `__init__.py` files re-export key symbols. Lift verbatim. Verify cross-package import V-F-x-1 passes after lift.
6. **`get_current_user` ripple.** Batch 2 packages (tenant_domains, commercial_calendar, social_proof, assets) all import `from src.modules.iam.api.dependencies import get_current_user`. AFTER iam lifts, T-4..T-6 must update this import to `from luana_core_iam.api.dependencies import get_current_user`. T-1 alone doesn't fix this — T-4..T-6 sed runs.
7. **`User` type import ripple.** Same as above — `from src.modules.iam.domain.user import User` in 4 Batch 2 packages. Rewrite via §1.3 sed pattern #2.
8. **Cross-test cross-module fixture sharing.** AISALESHT tests/modules/<m>/conftest.py may reference fixtures from `tests/modules/iam/conftest.py` (shared User fixture). Verify per package: `grep -rE "from tests\.modules\.iam" core/luana-core-<name>/tests/`. If found → update path or duplicate fixture. Escalate if logic refactor needed.
9. **`ARQ` worker import.** `tenant_domains/workers/tasks.py` may import `arq` symbols. Lift verbatim. Add `arq>=0.26` to `luana-core-tenant-domains/pyproject.toml` (already in §8.3 of 03-arch.md).
10. **`FileParsingService` import.** assets/application imports `from src.shared.infrastructure.files.file_parsing_service import FileParsingService`. Rewrite to `from luana_core_platform.infrastructure.files.file_parsing_service import FileParsingService` (Story 2 lifted this into platform).

## §10. Anti-duplication discipline (per anti-duplication.md)

Story 3 LIFTS module code (NOT shared abstractions). Different from Story 2:

- Story 2: lifted SSoT abstractions (`BaseObservabilityContext`, `FXResolver`, etc.) that copilot + sales_agent + others CONSUME.
- Story 3: lifts MODULE code (iam, tenant_profile, tenant_domains, content modules) that has ONE consumer (the brand app via FastAPI mount).

No mirror risk WITHIN Story 3 scope. iam's `ClerkService` is consumed via `luana_core_platform.infrastructure.external.clerk` — that's a Story 2 SSoT already.

If builder discovers a new `ClerkService` instance or shared abstraction during lift → that's a Story 2 oversight, not a Story 3 concern. Document + escalate.

## §11. Story 3 → Stories 4-10 forward awareness

- **Story 4** lifts crm/, analytics/, advertising/, social_media/, landing/, connections/. Story 4 will import from `luana_core_iam` (User) and `luana_core_tenant_profile` (settings). Story 3 packages MUST stay backward-stable.
- **Story 5** lifts brand/, offer/. Will likely consume `luana_core_assets` (Asset attached to brand visuals) + `luana_core_social_proof` (testimonials placement).
- **Story 6** lifts copilot/. Will lift the 2 deferred `copilot_provider/` subfolders into commercial_calendar + social_proof packages. Story 3 packages MUST tolerate the future addition (the test directories will see new tests, source dirs see new subfolders — both additive).
- **Story 9** publishes packages to GH Packages. Story 3 packages stay at `0.0.1-alpha` until then.
- **Story 10** rewrites AISALESHT imports to `luana_core_*`. Story 3 contracts MUST stay byte-stable so Story 10 sed is mechanical.

For all forward awareness: **lift mode discipline = best forward stability**. Do NOT refactor, do NOT rename, do NOT optimize. Stories 4-10 depend on Story 3 contracts being identical to AISALESHT modules.
