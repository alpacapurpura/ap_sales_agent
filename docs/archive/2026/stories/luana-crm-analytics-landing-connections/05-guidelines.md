---
story_id: luana-crm-analytics-landing-connections
guidelines_version: 1
last_modified: 2026-05-11
drafted_by: /architect (claude-opus-4-7)
authority: 03-arch.md + 01-spec.md + outcome §7.3 lift mode + Story 3 05-guidelines.md pattern
---

# 05-guidelines.md — luana-crm-analytics-landing-connections

> /dev-team reads this BEFORE picking up any ticket. Defines patterns required/forbidden, files in scope, skills to load, halt criteria. Sub-builders inherit this guidance verbatim.

## §1. Patterns Required

### §1.1 Lift mode (per outcome §7.3, identical to Stories 2-3 §1.1)

- **Verbatim file copy.** Use `cp -r` to lift source → destination. Do NOT rewrite, do NOT reformat, do NOT renumber lines.
- **Preserve DDD layering.** `domain/` → `infrastructure/` → `application/` → `api/` boundaries stay intact within each package.
- **Preserve class/function/module names.** `Lead` stays `Lead`. `MetricCatalog` stays `MetricCatalog`. `LandingService` stays `LandingService`. `ChannelType` stays `ChannelType`.
- **Preserve public API surface.** Re-export shape via `__init__.py` matches AISALESHT verbatim.
- **Preserve tests.** Lift `backend/tests/modules/<m>/test_*.py` alongside source. EXCEPT files in §3 DEFERRED list.
- **Per-package `pyproject.toml` at version `"0.0.1-alpha"`** (template literals in 03-arch.md §8).
- **Update import paths INTERNOS to luana-platform only.** Use search-and-replace mapping in 03-arch.md §5.

### §1.2 Workspace registration (single ticket T-1)

- Add 4 new Python packages to `~/luana-platform/pyproject.toml` `[tool.uv.workspace] members` AND `[tool.uv.sources]` (template in 03-arch.md §4.1).
- Run `cd ~/luana-platform && uv sync --all-packages` after each package added — confirms registration.

### §1.3 Import path rewriting (verbatim mechanical sed)

Inside each newly lifted package, apply these sed patterns. Use the **exact patterns** below — over-broad sed corrupts strings inside docstrings/test fixtures.

```bash
# Replace <m> with original module slug (crm, analytics, landing, connections)
# Replace <pkg_snake> with destination (luana_core_crm, luana_core_analytics_engine, luana_core_landing, luana_core_connections)
cd ~/luana-platform/core/luana-core-<name>

# 1. Self-imports: src.modules.<m>.<X> → <pkg_snake>.<X>
find src tests -name "*.py" -exec sed -i 's|from src\.modules\.<m>\.|from <pkg_snake>.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|import src\.modules\.<m>\.|import <pkg_snake>.|g' {} \;

# 2. Cross-module Story 4 → Story 3 iam
find src tests -name "*.py" -exec sed -i 's|from src\.modules\.iam\.|from luana_core_iam.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|import src\.modules\.iam\.|import luana_core_iam.|g' {} \;

# 3. Cross-module Story 4 → Story 2 platform (shared.* + core.*)
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.domain\.|from luana_core_platform.domain.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.links\.|from luana_core_platform.links.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.infrastructure\.|from luana_core_platform.infrastructure.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.application\.|from luana_core_platform.application.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.workers\.|from luana_core_platform.workers.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.api\.|from luana_core_platform.api.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.core\.|from luana_core_platform.core.|g' {} \;

# 4. NOTE: DO NOT rewrite imports of src.modules.{campaigns,sales_agent,copilot}.
#    Those imports are DEFERRED SIGNAL (§3.3) — the file is in DEFERRED list,
#    skip during cp -r. If you find the import surfaced in NON-deferred files
#    after sed, escalate per §6 halt #5 (silent forward coupling).
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

### §1.6 ETL extraction-contract regen workflow (Story 4-specific — analytics)

Per 03-arch.md §10, analytics owns the `make extraction-contract` workflow:

1. **Lift the regen script** with path adjustment:
   ```
   backend/scripts/generate_extraction_contract_doc.py
     → core/luana-core-analytics-engine/scripts/generate_extraction_contract_doc.py
   ```

2. **Update the script's imports** (mechanical sed inside the script body):
   ```bash
   sed -i 's|from src\.modules\.analytics\.|from luana_core_analytics_engine.|g' \
       core/luana-core-analytics-engine/scripts/generate_extraction_contract_doc.py
   ```

3. **Update the output path constant** in the script:
   - Before: writes to `docs/etl/extraction-contract.md` (repo root)
   - After: writes to `docs/extraction-contract.md` (package root)
   - Locate the output assignment (likely near top of script) and adjust path.

4. **Create per-package Makefile** per 03-arch.md §10.2:
   ```makefile
   .PHONY: extraction-contract
   extraction-contract:
       cd $(CURDIR) && uv run python scripts/generate_extraction_contract_doc.py
   ```

5. **Smoke test** the regen and idempotency:
   ```bash
   cd ~/luana-platform/core/luana-core-analytics-engine
   make extraction-contract
   sha256sum docs/extraction-contract.md
   make extraction-contract
   sha256sum docs/extraction-contract.md  # must match
   ```

### §1.7 Brand-agnostic engines verification (Story 4-specific)

Before declaring T-2..T-5 done, verify each lifted package stays brand-agnostic via local smoke (full arch test runs in T-11):

```bash
cd ~/luana-platform/core/luana-core-<name>/src
grep -rEn 'if\s+brand\s*==|if\s+tenant\.brand\s*==|brand\s*==\s*"(nicolify|vitalia|comunify|lupulo)"' luana_core_<name>/ || echo "OK: no brand control flow"
grep -rEn '(API_KEY|SECRET|TOKEN)\s*=\s*"(?!\$|os\.|settings\.).{8,}"' luana_core_<name>/ || echo "OK: no hardcoded credentials"
```

If either grep finds matches → escalate per §6 halt #5 (lift mode violation: source has brand-aware code that shouldn't have been merged to AISALESHT either).

### §1.8 No cyclic deps — Story 4 (DAG-clean)

Story 4 has no cyclic deps. All 4 packages depend on Story 2+3 (platform + iam), zero inter-Story-4 deps. Pure DAG. No special handling needed.

## §2. Patterns Forbidden

### §2.1 Lift mode violations (auto-FAIL, per Stories 2-3 §2.1)

- ❌ **Renaming any class, function, module, or symbol.** Original names preserved.
- ❌ **Refactor logic** while lifting — even "obvious improvements" — escalate per outcome §7.4.
- ❌ **Splitting modules.** A module file stays a module file.
- ❌ **Merging modules.** Two files stay two files.
- ❌ **Adding new abstractions** (factories, registries, adapters) not present in AISALESHT. EXCEPTION: per-package Makefile (§1.6) is mechanical lift of the AISALESHT-root Makefile target, NOT a new abstraction — it's the same shell-recipe encapsulated.
- ❌ **Changing public API signatures.** Same args, same return types, same exceptions.
- ❌ **Removing code** during lift — even if "clearly dead".
- ❌ **Reformatting** beyond what `ruff format` would do automatically on save.

### §2.2 Mutating AISALESHT (auto-FAIL — Scenario D of 01-spec.md)

- ❌ **Any file under `backend/src/modules/{crm,analytics,landing,connections}/`** is READ-ONLY in Story 4.
- ❌ **Any file under `backend/tests/modules/{crm,analytics,landing,connections}/`** is READ-ONLY.
- ❌ **Modifying AISALESHT root pyproject.toml, alembic migrations, conftest.py at root.** Out of scope.
- ❌ **Modifying AISALESHT root Makefile** to update the `extraction-contract` target. Story 10 will handle AISALESHT teardown.
- ❌ **Running `make ci-parity` against AISALESHT to "verify lift didn't break it"** — Story 4 doesn't change AISALESHT. Story 10 will validate.

### §2.3 Brand-aware code in engines (auto-FAIL — Story 4-specific)

- ❌ **`if brand == "..."` or `if tenant.brand == "..."`** control flow in any of the 4 engine packages.
- ❌ **Hardcoded brand IDs / API keys / secrets** in engine source. Tenant config via DI only.
- ❌ **`from nicolify.X` or `import nicolify.X`** — engines stay brand-agnostic.
- ❌ **Adding a `brand_id` column or constructor param** to CRM Lead/Customer/etc — that's refactor + scope expansion.

### §2.4 Forward-Story coupling (auto-FAIL)

- ❌ **Importing from Story 5/6/7/8 packages** (`luana_core_{brand,offer,copilot,sales_agent,campaigns,scheduling}`) in any Story 4 source file outside the DEFERRED set.
- ❌ **Importing from `src.modules.*`** in any Story 4 source file (lift incomplete — caller forgot sed pass).

### §2.5 ETL contract drift

- ❌ **Modifying `extraction_contract.py` content** during lift (semantic change).
- ❌ **Skipping the regen step** after the lift (`docs/extraction-contract.md` must be regenerated in T-9).
- ❌ **Hardcoding output path or paths inside the script** beyond the package-relative mapping (§1.6 step 3).

## §3. Files in Scope

### §3.1 AISALESHT (READ-ONLY source)

**Lift these:**
- `backend/src/modules/crm/{api,application,domain,infrastructure}/**` (49 files, excluding copilot_provider/)
- `backend/src/modules/analytics/{api,application,domain,infrastructure,workers}/**` (122 files, excluding copilot_provider/)
- `backend/src/modules/landing/{api,application,domain,infrastructure}/**` (20 files, excluding copilot_provider/)
- `backend/src/modules/connections/{api,application,domain,infrastructure}/**` (65 files, excluding copilot_provider/ and api/dependencies/__init__.py)
- `backend/tests/modules/crm/*.py` (28 files, excluding test_contacts_api.py)
- `backend/tests/modules/analytics/*.py` (102 files)
- `backend/tests/modules/landing/*.py` (13 files)
- `backend/tests/modules/connections/*.py` (33 files)
- `backend/scripts/generate_extraction_contract_doc.py` → `core/luana-core-analytics-engine/scripts/generate_extraction_contract_doc.py`

### §3.2 luana-platform (CREATE)

**Create:**
- `~/luana-platform/core/luana-core-crm/{pyproject.toml,README.md,src/luana_core_crm/**,tests/**}`
- `~/luana-platform/core/luana-core-analytics-engine/{pyproject.toml,README.md,Makefile,scripts/generate_extraction_contract_doc.py,docs/extraction-contract.md,src/luana_core_analytics_engine/**,tests/**}`
- `~/luana-platform/core/luana-core-landing/{pyproject.toml,README.md,src/luana_core_landing/**,tests/**}`
- `~/luana-platform/core/luana-core-connections/{pyproject.toml,README.md,src/luana_core_connections/**,tests/**}`
- `~/luana-platform/core/tests/architecture/test_story4_brand_agnostic_engines.py`
- `~/luana-platform/core/tests/architecture/test_story4_no_forward_module_imports.py`
- `~/luana-platform/core/tests/architecture/test_analytics_extraction_contract_drift.py`
- `~/luana-platform/core/luana-core-connections/tests/test_engine_stub_adapter_registration.py`

**Modify:**
- `~/luana-platform/pyproject.toml` (workspace + sources registration)
- `~/luana-platform/core/DEFERRED-FILES.md` (append Story 4 entries)

### §3.3 DEFERRED list — DO NOT LIFT, DO NOT TOUCH

#### Defer to Story 6 (copilot lift) — 4 copilot_provider/ subfolders

```
backend/src/modules/crm/copilot_provider/__init__.py
backend/src/modules/crm/copilot_provider/data_access.py
backend/src/modules/crm/copilot_provider/provider.py

backend/src/modules/analytics/copilot_provider/__init__.py
backend/src/modules/analytics/copilot_provider/provider.py

backend/src/modules/landing/copilot_provider/__init__.py
backend/src/modules/landing/copilot_provider/provider.py

backend/src/modules/connections/copilot_provider/__init__.py
backend/src/modules/connections/copilot_provider/provider.py
```

**Detection rule:** `grep -l "from src.modules.copilot" <file>` → DEFERRED to Story 6.

#### Defer to Story 7 (sales_agent lift) — composition root

```
backend/src/modules/connections/api/dependencies/__init__.py
```

This file's docstring marks itself as composition root for `MessageHandlerPort = ChatOrchestrator` singleton wiring.

**Detection rule:** `grep -l "from src.modules.sales_agent" <file>` → DEFERRED to Story 7.

#### Defer to Story 8 (campaigns lift) — CRM contacts surface

```
backend/src/modules/crm/api/contacts.py
backend/src/modules/crm/application/services/contact_query_service.py
backend/tests/modules/crm/test_contacts_api.py
```

These files import `src.modules.campaigns.api._dependencies::get_campaigns_async_session` + `src.modules.campaigns.application.dtos.pagination::PaginatedResponse`.

**Detection rule:** `grep -l "from src.modules.campaigns" <file>` → DEFERRED to Story 8.

#### Reserved (NOT existing, NOT deferred)

Future brand-specific channel adapters (Lupulo POS, Vitalia gateway, Comunify-specific connectors) **do not exist** in AISALESHT today. They are net-new code for Stories 11-13 in `vertical-{niche}/connections/` packages.

### §3.4 Skip during cp -r — mechanical recipe per module

When running `cp -r` for each module, use explicit per-subfolder copy (NOT `cp -r module/*`) to skip deferred subfolders:

```bash
# crm — skip copilot_provider/ AND tag contacts.py + contact_query_service.py for separate handling
for sub in api application domain infrastructure __init__.py; do
  if [ -e "/home/chris/AISALESHT/backend/src/modules/crm/$sub" ]; then
    cp -r "/home/chris/AISALESHT/backend/src/modules/crm/$sub" \
          ~/luana-platform/core/luana-core-crm/src/luana_core_crm/
  fi
done
# Post-copy: delete deferred-to-Story-8 files
rm -f ~/luana-platform/core/luana-core-crm/src/luana_core_crm/api/contacts.py
rm -f ~/luana-platform/core/luana-core-crm/src/luana_core_crm/application/services/contact_query_service.py

# analytics — skip copilot_provider/
for sub in api application domain infrastructure workers __init__.py; do
  if [ -e "/home/chris/AISALESHT/backend/src/modules/analytics/$sub" ]; then
    cp -r "/home/chris/AISALESHT/backend/src/modules/analytics/$sub" \
          ~/luana-platform/core/luana-core-analytics-engine/src/luana_core_analytics_engine/
  fi
done

# landing — skip copilot_provider/
for sub in api application domain infrastructure __init__.py; do
  if [ -e "/home/chris/AISALESHT/backend/src/modules/landing/$sub" ]; then
    cp -r "/home/chris/AISALESHT/backend/src/modules/landing/$sub" \
          ~/luana-platform/core/luana-core-landing/src/luana_core_landing/
  fi
done

# connections — skip copilot_provider/, skip api/dependencies/__init__.py
for sub in api application domain infrastructure __init__.py; do
  if [ -e "/home/chris/AISALESHT/backend/src/modules/connections/$sub" ]; then
    cp -r "/home/chris/AISALESHT/backend/src/modules/connections/$sub" \
          ~/luana-platform/core/luana-core-connections/src/luana_core_connections/
  fi
done
# Post-copy: delete deferred-to-Story-7 file
rm -rf ~/luana-platform/core/luana-core-connections/src/luana_core_connections/api/dependencies
```

**Verify zero leaks after each lift:**

```bash
grep -rEn "from src\.modules\.(copilot|sales_agent|campaigns)" \
    ~/luana-platform/core/luana-core-<name>/src/ \
    && echo "FAIL: deferred file leaked into lift" || echo "OK"
```

## §4. Skills + Rules to Load

| Skill / Rule | When |
|---|---|
| `backend-expert` (this skill) | All Story 4 tickets |
| `metrics-expert` | T-3a, T-3b, T-3c (analytics lift) — for ETL extraction contract familiarity |
| `tessl__fastapi` | All Story 4 tickets — FastAPI router preservation |
| `tessl__pytest-api-testing` | Test lifts (verify mock paths) |
| `.claude/rules/etl-extraction-contract.md` | T-9 (extraction-contract regen integration) |
| `.claude/rules/anti-duplication.md` | T-1 (workspace registration) — verify no parallel layer added |
| `.claude/rules/auditor-downstream-regression.md` | All tickets — tests lift alongside source |
| `.claude/rules/tdd-mandatory.md` | T-10, T-11, T-12 (new arch fitness + smoke tests) |
| `.claude/rules/parallel-safety.md` | All tickets — single development branch, no force push |

## §5. Commit conventions (per ticket)

```
chore(workspace): register Story 4 packages in uv workspace                      # T-1
feat(luana-core-crm): lift crm module (verbatim, skip copilot_provider + contacts.py deferred)  # T-2
feat(luana-core-analytics-engine): lift analytics framework + domain             # T-3a
feat(luana-core-analytics-engine): lift analytics providers + ETL pipeline       # T-3b
feat(luana-core-analytics-engine): lift analytics scheduler + workers            # T-3c
feat(luana-core-landing): lift landing module (verbatim, skip copilot_provider)  # T-4
feat(luana-core-connections): lift connections engine (verbatim, skip copilot_provider + api/dependencies/ deferred)  # T-5
test(luana-platform): cross-package smoke + aggregate pytest GREEN               # T-8
feat(luana-core-analytics-engine): lift extraction-contract regen + per-package Makefile  # T-9
test(luana-core-connections): engine accepts stub adapter (brand-agnostic smoke) # T-10
test(arch): Story 4 engines brand-agnostic invariant                              # T-11
test(arch): Story 4 no forward module imports                                     # T-12
chore(luana-platform): Story 4 lint + AISALESHT untouched + DEFERRED-FILES update + READMEs  # T-13
```

Conventional Commits format. All on `development` branch in `~/luana-platform/`. Push after each ticket GREEN.

## §6. Halt criteria (per outcome §7.4 + spec §4)

Halt + escalate to Chris if any of these triggers:

1. **Cross-Story-4 coupling discovered** — if grep reveals crm/analytics/landing/connections cross-importing (after deferrals applied), DAG breaks → escalate.
2. **ETL contract regen architecture impossible per lift mode** — if `make extraction-contract` requires script refactor beyond path-adjustment sed.
3. **Connections engine + adapter separation reveals tight coupling** — if removing `api/dependencies/__init__.py` breaks other connections files (it should NOT — file is composition root only).
4. **Auditor REJECTED + 3 auto-fix Opus iter fail** — per outcome §7.4 cap_reached.
5. **Scope expansion needed** — any "small refactor" that requires touching files beyond §3 list.
6. **Cumulative cost > $1500** — soft check-in with Chris.
7. **Brand-specific code in supposedly brand-agnostic engine** — arch fitness §7.1 fails after lift → source has pre-existing brand contamination → escalate (it shouldn't have been merged to AISALESHT either).
8. **DEFERRED file leaks into lift** — `grep "from src.modules.(copilot|sales_agent|campaigns)"` in lifted code post-sed reveals a deferred file got copied → revert + re-lift with explicit subfolder loop (§3.4).
9. **Test count drop > 5%** — preserve test count from AISALESHT baseline EXCEPT documented deferrals. Drop indicates lost test files. Escalate.
10. **`make extraction-contract` regen not idempotent** — V-F-etl-2 FAIL → likely the script's MD output has non-deterministic ordering (sort order, timestamp embed). Diagnose root cause, NO defer.

## §7. Sub-builder spawn template

When /dev-team spawns sub-builder for a ticket:

```
Agent({
  description: "Lift <module> — T-N",
  subagent_type: "builder-backend",
  model: "sonnet",  // R23 — production_code: false (lift, no agentic logic)
  prompt: "
    <pr_folder>: /home/chris/AISALESHT/docs/product/stories/luana-crm-analytics-landing-connections
    <ticket>: T-N

    Lift <module> from AISALESHT to luana-platform per:
    - 01-spec.md §2.2 + scope
    - 03-arch.md §3 (per-package structure) + §5 (import mapping) + §9 (DEFERRED list)
    - 05-guidelines.md §1.3 (sed patterns) + §3.4 (per-module cp -r recipe) + §3.3 (deferred files)
    - Validators GREEN: V-NF-2, V-F-py-N (run per-ticket-listed)

    DO NOT TOUCH AISALESHT.
    DO NOT lift files in §3.3 DEFERRED list.
    Conventional commit per §5.
    Last line: 'done -> <commit-sha>' or 'failed -> <reason>'.
  "
})
```

## §8. Verification recipe per ticket close

After each ticket:

```bash
# 1. Per-package tests GREEN
cd ~/luana-platform && uv run pytest core/luana-core-<name>/tests/ -x -q --tb=short

# 2. Ruff clean
cd ~/luana-platform && uv run ruff check core/luana-core-<name>/

# 3. No leaked deferred imports
grep -rEn "from src\.modules\.(copilot|sales_agent|campaigns)" ~/luana-platform/core/luana-core-<name>/src/ && echo "FAIL: deferred leak" || echo "OK"

# 4. No forward Story imports
grep -rEn "from luana_core_(brand|offer|copilot|sales_agent|campaigns|scheduling)\." ~/luana-platform/core/luana-core-<name>/src/ && echo "FAIL: forward import" || echo "OK"

# 5. AISALESHT untouched (Story 4 surfaces)
cd /home/chris/AISALESHT
git diff HEAD --name-only | grep -E '^(backend/src/modules/(crm|analytics|landing|connections)|backend/tests/modules/(crm|analytics|landing|connections))/' && echo "FAIL: AISALESHT mutated" || echo "OK"
```

All 5 checks GREEN → close ticket. ANY check FAILS → halt, fix, re-verify.

## §9. Common pitfalls + remedies

| Pitfall | Symptom | Remedy |
|---|---|---|
| `cp -r module/*` copies deferred subfolder | `from src.modules.copilot` leaks post-sed | Use explicit per-subfolder loop (§3.4). Delete deferred files post-copy. |
| Over-broad sed corrupts test fixtures | Strings inside docstrings/fixtures replaced unintentionally | Use exact patterns in §1.3 (anchored on `from \. ` / `import \. `). Verify with `git diff` before commit. |
| `monkeypatch.setattr("src.modules.X")` left in tests | Tests pass but mock targets wrong module | Run sed on tests too. Verify with `grep "src.modules" tests/` post-lift. |
| Analytics regen script writes to wrong path | `make extraction-contract` creates file at unexpected location | Update script's output-path constant (§1.6 step 3). |
| Hatchling can't find package | `uv sync` fails post-package-creation | Verify `[tool.hatch.build.targets.wheel] packages = ["src/luana_core_<name>"]` matches actual snake_case folder name. |
| ARQ worker imports fail | Pytest can't import `workers/scheduler.py` | Verify `arq>=0.26` in `pyproject.toml` dependencies. |
| Connections stub adapter test references wrong ABC | T-10 test FAILs with ImportError | Inspect actual lifted `infrastructure/channels/whatsapp/interface.py` or equivalent for real protocol class. Adjust §7.4 test stub. |
| Story 3 packages regress post-Story-4 workspace deps | V-F-x-2 aggregate pytest fails on Story 2/3 tests | Likely a transitive dep conflict. Check `uv pip list` vs Story 3 baseline. Pin offending dep in Story 4 pyproject. |
