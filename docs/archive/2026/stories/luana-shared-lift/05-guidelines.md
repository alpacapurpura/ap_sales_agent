---
story_id: luana-shared-lift
guidelines_version: 1
last_modified: 2026-05-11
drafted_by: /architect (claude-opus-4-7)
authority: 03-arch.md + 01-spec.md + outcome §7.3 lift mode
---

# 05-guidelines.md — luana-shared-lift

> /dev-team reads this BEFORE picking up any ticket. Defines patterns required/forbidden, files in scope, skills to load, halt criteria. Sub-builders inherit this guidance verbatim.

## §1. Patterns Required

### §1.1 Lift mode (per outcome §7.3)

- **Verbatim file copy.** Use `cp` to lift source → destination. Do NOT rewrite, do NOT reformat, do NOT renumber lines.
- **Preserve DDD layering.** `domain/` → `infrastructure/` → `application/` → `api/` boundaries stay intact.
- **Preserve class/function/module names.** `BudgetGuard` stays `BudgetGuard`. `sanitize_payload` stays `sanitize_payload`.
- **Preserve public API surface.** Re-export shape via `__init__.py` matches AISALESHT verbatim.
- **Preserve tests.** Lift `backend/tests/shared/<area>/test_*.py` alongside source.
- **Per-package `pyproject.toml`/`package.json` at version `"0.0.1-alpha"`** (template literals in 03-arch.md §8).
- **Update import paths INTERNOS to luana-platform only.** Use search-and-replace mapping in 03-arch.md §5.
- **Use `git mv` or fresh write** — both acceptable. Builder picks. Fresh write recommended for first ticket per package (cleaner diff).

### §1.2 Workspace registration

- Add each new Python package to `~/luana-platform/pyproject.toml` `[tool.uv.workspace] members` AND `[tool.uv.sources]` (template in 03-arch.md §4.1).
- Add each new TS package implicitly via `core/@luana/*` glob in `pnpm-workspace.yaml` (already configured).
- Run `cd ~/luana-platform && uv sync --all-packages` after each package added — confirms registration.
- Run `cd ~/luana-platform && pnpm install --frozen-lockfile` after each TS package added.

### §1.3 Import path rewriting (verbatim mechanical sed)

Inside each newly lifted package:

```bash
# Python — per package
cd ~/luana-platform/core/luana-core-<name>/src/luana_core_<name>
find . -name "*.py" -exec sed -i 's|from src\.shared\.agent_observability\.|from luana_core_observability.|g' {} \;
find . -name "*.py" -exec sed -i 's|from src\.shared\.billing\.|from luana_core_billing.|g' {} \;
find . -name "*.py" -exec sed -i 's|from src\.shared\.compliance\.|from luana_core_compliance.|g' {} \;
find . -name "*.py" -exec sed -i 's|from src\.shared\.idempotency\.|from luana_core_idempotency.|g' {} \;
find . -name "*.py" -exec sed -i 's|from src\.shared\.infrastructure\.llm\.|from luana_core_llm.|g' {} \;
find . -name "*.py" -exec sed -i 's|from src\.shared\.application\.extraction\.|from luana_core_extraction.|g' {} \;
find . -name "*.py" -exec sed -i 's|from src\.shared\.domain_events\.|from luana_core_events.|g' {} \;
find . -name "*.py" -exec sed -i 's|from src\.shared\.agent_observability\.channels\.|from luana_core_channels.|g' {} \;
find . -name "*.py" -exec sed -i 's|from src\.shared\.infrastructure\.channels\.|from luana_core_channels.infrastructure.channels.|g' {} \;
# Platform consumes everything else from src.shared.* + src.core.*:
find . -name "*.py" -exec sed -i 's|from src\.shared\.domain\.|from luana_core_platform.domain.|g' {} \;
find . -name "*.py" -exec sed -i 's|from src\.shared\.links\.|from luana_core_platform.links.|g' {} \;
find . -name "*.py" -exec sed -i 's|from src\.shared\.workers\.|from luana_core_platform.workers.|g' {} \;
find . -name "*.py" -exec sed -i 's|from src\.shared\.api\.|from luana_core_platform.api.|g' {} \;
find . -name "*.py" -exec sed -i 's|from src\.shared\.infrastructure\.\(files\|prompts\|database\|external\|web\|models\)\.|from luana_core_platform.infrastructure.\1.|g' {} \;
find . -name "*.py" -exec sed -i 's|from src\.shared\.application\.\(ai_action_service\|brand_summary_event_handlers\|field_diff\|progress_emitter\)|from luana_core_platform.application.\1|g' {} \;
find . -name "*.py" -exec sed -i 's|from src\.core\.|from luana_core_platform.core.|g' {} \;
```

**TS equivalent (per package):**

```bash
cd ~/luana-platform/core/@luana/<name>/src
find . -name "*.ts" -o -name "*.tsx" | xargs sed -i 's|@/components/ui|@luana/ui-kit|g'
find . -name "*.ts" -o -name "*.tsx" | xargs sed -i 's|@/lib/format-money|@luana/format/format-money|g'
find . -name "*.ts" -o -name "*.tsx" | xargs sed -i 's|@/lib/format-date|@luana/format/format-date|g'
find . -name "*.ts" -o -name "*.tsx" | xargs sed -i 's|@/lib/utils|@luana/format/utils|g'
find . -name "*.ts" -o -name "*.tsx" | xargs sed -i 's|@/lib/constants|@luana/format/constants|g'
find . -name "*.ts" -o -name "*.tsx" | xargs sed -i 's|@/lib/tokens|@luana/design-tokens|g'
find . -name "*.ts" -o -name "*.tsx" | xargs sed -i 's|@/lib/http-client|@luana/api-client/http-client|g'
find . -name "*.ts" -o -name "*.tsx" | xargs sed -i 's|@/hooks/use-|@luana/hooks/use-|g'
```

### §1.4 Per-package barrel exports (index.ts/__init__.py)

Each new package gets an explicit barrel (preserving AISALESHT re-export shape):

- Python: `core/luana-core-<name>/src/luana_core_<name>/__init__.py` re-exports same symbols as `backend/src/shared/<area>/__init__.py`.
- TS: `core/@luana/<name>/src/index.ts` re-exports all public types/functions.

### §1.5 Test execution per package

After lift, run that package's tests in isolation BEFORE adding to workspace aggregate:

```bash
cd ~/luana-platform/core/luana-core-<name>
uv run pytest tests/ -x -q --tb=short
# Or:
pnpm --filter @luana/<name> test
```

GREEN per-package, then proceed to next ticket.

### §1.6 Cyclic dep declaration (platform ↔ llm)

`luana-core-platform/pyproject.toml` declares `luana-core-llm` as dep (see §8 template). `luana-core-llm/pyproject.toml` declares `luana-core-platform` as dep. uv resolves via `[tool.uv.sources]` workspace declarations.

After lift, verify cycle works:

```bash
cd ~/luana-platform && uv sync --all-packages
uv run python -c "
from luana_core_platform.application.ai_action_service import AIActionService  # uses llm
from luana_core_llm.factory import LLMFactory  # uses platform.domain
print('cycle OK')
"
```

## §2. Patterns Forbidden

### §2.1 Lift mode violations (auto-FAIL)

- ❌ **Renaming any class, function, module, or symbol.** Original names preserved.
- ❌ **Refactor logic** while lifting. Even "obvious improvements" — escalate per outcome §7.4.
- ❌ **Splitting modules.** A module file stays a module file.
- ❌ **Merging modules.** Two files stay two files.
- ❌ **Adding new abstractions** (factories, registries, adapters) not present in AISALESHT.
- ❌ **Changing public API signatures.** Same args, same return types, same exceptions.
- ❌ **Removing code** during lift — even if "clearly dead".
- ❌ **Reformatting** (line breaks, indentation, trailing whitespace) beyond what `ruff format` would do automatically on save.

### §2.2 Mutating AISALESHT (auto-FAIL — Scenario C of 01-spec.md)

- ❌ **Any file under `backend/src/shared/`** is READ-ONLY in Story 2.
- ❌ **Any file under `frontend/src/{components/ui,lib,hooks,__tests__}/`** is READ-ONLY.
- ❌ **Modifying AISALESHT pyproject.toml, alembic migrations, conftest.py.** Out of scope.
- ❌ **Running `make ci-parity` against AISALESHT to "verify lift didn't break it"** — Story 2 doesn't change AISALESHT, no need. Story 10 will validate.

### §2.3 Publishing artifacts (Story 9 territory — auto-FAIL)

- ❌ `publishConfig` field in any `package.json`.
- ❌ `.releaserc.json` or semantic-release configuration.
- ❌ `.github/workflows/release*.yml` or `publish*.yml`.
- ❌ `[project.urls]` pointing to GH Packages registry in pyproject.toml.
- ❌ Any reference to `npm publish` or `uv publish` in scripts.

### §2.4 Scope expansion (escalate, not fix)

- ❌ Lifting modules NOT in 03-arch.md §1 scope (iam/, tenant_profile/, crm/, brand/, offer/, copilot/, sales_agent/ → out of scope, Stories 3-7).
- ❌ Lifting the 4 deferred files (workers/copilot_*.py, workers/sales_agent_*.py, application/personality_event_handlers.py + their tests).
- ❌ Creating new luana-core-* packages not in 03-arch.md.
- ❌ Modifying outcome §7.3 lift mode constraints.

### §2.5 Schema/migration changes (escalate)

- ❌ Touching Alembic migrations in AISALESHT or luana-platform.
- ❌ Changing SQLA model schemas — even adding indexes.
- ❌ Migration generation. Schema stays in AISALESHT (Story 4 territory).

## §3. Files in Scope

### §3.1 SOURCE (AISALESHT — READ-ONLY)

**Backend Python (lift verbatim):**

```
backend/src/shared/
  agent_observability/{recording,persistence,cost,pricing,application,workers,reporting}/  → luana-core-observability
  agent_observability/channels/                                                              → luana-core-channels
  infrastructure/channels/                                                                   → luana-core-channels
  domain_events/                                                                             → luana-core-events
  billing/                                                                                   → luana-core-billing
  compliance/                                                                                → luana-core-compliance
  idempotency/                                                                               → luana-core-idempotency
  infrastructure/llm/                                                                        → luana-core-llm
  application/extraction/                                                                    → luana-core-extraction
  domain/                                                                                    → luana-core-platform/domain/
  links/                                                                                     → luana-core-platform/links/
  infrastructure/{files,prompts,database,external,web,models}/                               → luana-core-platform/infrastructure/<sub>/
  workers/brand_summary_regen.py                                                             → luana-core-platform/workers/
  api/                                                                                       → luana-core-platform/api/
  application/{ai_action_service,brand_summary_event_handlers,field_diff,progress_emitter}.py → luana-core-platform/application/

backend/src/core/                                                                            → luana-core-platform/core/   ★ DEVIATION FROM SPEC §2.2 — see 03-arch.md §9
```

**Backend tests (lift verbatim):**

```
backend/tests/shared/agent_observability/        → core/luana-core-observability/tests/
backend/tests/shared/billing/                    → core/luana-core-billing/tests/
backend/tests/shared/compliance/                 → core/luana-core-compliance/tests/
backend/tests/shared/idempotency/                → core/luana-core-idempotency/tests/
backend/tests/shared/domain_events/              → core/luana-core-events/tests/
backend/tests/shared/infrastructure/llm/         → core/luana-core-llm/tests/
backend/tests/shared/application/extraction/     → core/luana-core-extraction/tests/
backend/tests/shared/application/{test_brand_summary_event_handlers,test_field_diff,test_progress_emitter}.py → core/luana-core-platform/tests/application/
backend/tests/shared/workers/test_brand_summary_regen.py → core/luana-core-platform/tests/workers/
backend/tests/shared/test_*.py (root-level)      → core/luana-core-platform/tests/

backend/tests/architecture/test_shared_agent_observability_purity.py → core/tests/architecture/test_observability_no_module_deps.py (rename)
backend/tests/architecture/test_outbox_invariants.py                 → core/tests/architecture/test_events_outbox_invariants.py
backend/tests/architecture/test_extraction_orchestrator_inheritance.py → core/tests/architecture/test_extraction_orchestrator_inheritance.py
backend/tests/architecture/test_llm_routing_ssot.py                  → core/tests/architecture/test_llm_routing_ssot.py
backend/tests/architecture/test_channel_router_registry_invariants.py → core/tests/architecture/test_channels_router_invariants.py
```

**Frontend (lift verbatim):**

```
frontend/src/components/ui/         → core/@luana/ui-kit/src/
frontend/src/lib/tokens/            → core/@luana/design-tokens/src/
frontend/src/lib/format-date.ts     → core/@luana/format/src/format-date.ts
frontend/src/lib/format-money.ts    → core/@luana/format/src/format-money.ts
frontend/src/lib/utils.ts           → core/@luana/format/src/utils.ts           ★ DEVIATION — see 03-arch.md §1.3
frontend/src/lib/constants/         → core/@luana/format/src/constants/         ★ DEVIATION
frontend/src/lib/case-conversion.ts → core/@luana/format/src/case-conversion.ts
frontend/src/lib/config.ts          → core/@luana/api-client/src/config.ts
frontend/src/lib/http-client.ts     → core/@luana/api-client/src/http-client.ts
frontend/src/lib/api/               → core/@luana/api-client/src/api/
frontend/src/hooks/                 → core/@luana/hooks/src/

frontend/src/components/ui/__tests__/     → core/@luana/ui-kit/tests/
frontend/src/lib/__tests__/format-*.test.ts → core/@luana/format/tests/
frontend/src/hooks/__tests__/             → core/@luana/hooks/tests/
```

### §3.2 DESTINATION (luana-platform — CREATE)

```
~/luana-platform/
├── pyproject.toml                  # MODIFY: add 9 workspace members + sources
├── pnpm-workspace.yaml             # Already includes core/@luana/* glob (Story 1)
├── core/
│   ├── luana-core-platform/        # CREATE (T-2)
│   ├── luana-core-llm/             # CREATE (T-3)
│   ├── luana-core-channels/        # CREATE (T-4)
│   ├── luana-core-idempotency/     # CREATE (T-5)
│   ├── luana-core-observability/   # CREATE (T-6)
│   ├── luana-core-events/          # CREATE (T-7)
│   ├── luana-core-extraction/      # CREATE (T-8)
│   ├── luana-core-compliance/      # CREATE (T-9)
│   ├── luana-core-billing/         # CREATE (T-10)
│   ├── @luana/
│   │   ├── design-tokens/          # CREATE (T-11)
│   │   ├── hooks/                  # CREATE (T-11)
│   │   ├── format/                 # CREATE (T-11)
│   │   ├── ui-kit/                 # CREATE (T-12)
│   │   ├── api-client/             # CREATE (T-12)
│   │   └── schemas/                # CREATE (T-12, placeholder)
│   └── tests/
│       └── architecture/           # CREATE (T-16) — 5 arch fitness tests migrated
```

### §3.3 EXPLICITLY DEFERRED (Story 6/7 — DO NOT LIFT)

```
backend/src/shared/workers/copilot_quality_eval.py        ← Story 6
backend/src/shared/workers/copilot_rag_eval.py            ← Story 6
backend/src/shared/workers/sales_agent_quality_eval.py    ← Story 7
backend/src/shared/application/personality_event_handlers.py ← Story 7
backend/tests/shared/workers/test_copilot_quality_eval.py ← Story 6
backend/tests/shared/workers/test_copilot_rag_eval.py     ← Story 6
backend/tests/shared/application/test_personality_event_handlers.py ← Story 7
```

## §4. Skills + Rules to Load

### §4.1 Mandatory skills (auto-load per ticket)

| Trigger | Skill |
|---|---|
| Touching `core/luana-core-*` Python | `backend-expert` (DDD layering, SQLA 2.0 patterns) |
| Touching `core/@luana/*` TS | `frontend-expert` (FSD patterns, though here packages are independent) |
| Touching Python package config | `tessl__fastapi` (for FastAPI conventions in luana-core-platform/api) |
| Touching observability lift | `copilot-expert` (anti-duplication §0 — verifies no mirror) |
| Touching billing/compliance lift | `sales-agent-expert` (consumer awareness, but no consumer code in Story 2) |

### §4.2 Mandatory rules (auto-load — already in CLAUDE.md)

- `.claude/rules/anti-duplication.md` — Story 2 LIFTS shared abstractions canonically. NO mirror in modules/* yet (Stories 6/7 will).
- `.claude/rules/backend-ddd.md` — Inside-Out layering preserved within each package.
- `.claude/rules/tenant-isolation.md` — every entity carries `tenant_id` (verbatim from AISALESHT).
- `.claude/rules/tdd-mandatory.md` — tests lift alongside source (preserves RED→GREEN guarantee).
- `.claude/rules/parallel-safety.md` — single branch `development` in AISALESHT, BUT luana-platform is a SEPARATE git repo. /dev-team commits to luana-platform separately. NO `--force`, NO `pull`. Same `add by name` discipline.
- `.claude/rules/git-safety.md` — applies to luana-platform repo too.

### §4.3 Optional helper

- `tessl__graceful-degradation` — NOT applicable to Story 2 (lift, no new external calls). Skip.

## §5. Build Coordination (concurrency)

- /dev-team picks tickets per DAG order in 03-arch.md §2. Foundation tickets sequential (T-1 → T-2). Batch 2 tickets (T-3, T-4, T-5) parallelizable. Batch 3 tickets (T-6 through T-10) parallelizable.
- BUT: 1 Claude session sequentially per outcome §7.4. /dev-team picks ONE ticket at a time, GREEN validators before next pick.
- Tickets T-13 (workspace integration) + T-14 (lint) + T-15 (no-publish + no-AISALESHT-mutation verify) + T-16 (arch fitness) + T-17 (READMEs) run AFTER all lift tickets done.

## §6. Halt Criteria (auto-stop + escalate Chris)

Per outcome §7.4 + 01-spec.md §4 + 03-arch.md §10:

1. **Coupling oculto discovered** — file in scope imports from path not in 03-arch.md §1.2 DAG. Likely root cause: deferred-file boundary wrong. Escalate.
2. **Tests fail after lift** — re-run with `uv run pytest --tb=long`. If failure is mock path stale (`monkeypatch.setattr("src.shared...")`), update mock to new path verbatim. If failure is logic error → escalate (lift mode forbids fix-while-lift).
3. **3 auto-fix iter fail per ticket** — Sonnet → Opus rescue per outcome §7.4. After Opus rescue cap_reached → escalate.
4. **uv sync fails** with cyclic dependency error post platform↔llm declaration — escalate, /architect re-evaluates topology (may need workspace dep declaration tweak per uv docs).
5. **Scope expansion needed** — any refactor required to lift cleanly → escalate, NOT proceed.
6. **Cumulative session cost > $1500** — soft check-in per outcome §7.2.
7. **Cross-brand decision discovered** — escalate (Story 2 is single-brand foundation, no cross-brand decisions allowed).
8. **AISALESHT modification accidentally introduced** (V-NF-4 fails) — revert immediately, escalate cause (likely sed pattern bug or paste error).

## §7. Commit Conventions

Each ticket emits ONE commit to luana-platform repo. Each commit follows:

```
feat(luana-core-<name>): lift {module} from AISALESHT shared/{path}

- Lift backend/src/shared/{path}/ → core/luana-core-<name>/src/luana_core_<name>/
- Lift tests backend/tests/shared/{path}/ → core/luana-core-<name>/tests/
- Add pyproject.toml at version 0.0.1-alpha
- Update internal imports per 03-arch.md §5.1 mapping
- Verbatim lift per outcome §7.3 lift mode constraint

Ticket: T-{n} (story luana-shared-lift)
Validators addressed: V-F-py-{n}, V-NF-{n}

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

**Stage by exact filename** per parallel-safety.md. NO `git add .`.

## §8. Per-Ticket Validators Cross-Reference

See 06-tickets.yaml `validators_addressed` per ticket. Each ticket cites which V-* validators it must turn GREEN before completion.

## §9. Common Pitfalls (avoid these)

1. **`src.core` lift forgotten.** Without it, 17 shared/ files fail to import. T-2 includes `src/core/` lift into `luana-core-platform/core/` subpackage.
2. **Cyclic platform↔llm dep missed.** Without both pyproject.toml declarations, `uv sync` fails. T-3 includes the `luana-core-platform` source declaration in llm/pyproject.toml.
3. **Sed pattern over-broad.** A naive `sed 's|src.shared|luana_core|g'` would corrupt strings inside docstrings or test fixtures. Use precise patterns from §1.3.
4. **FE `@/lib/utils` ambiguity.** `cn()` lives in `@/lib/utils`. Lift target = `@luana/format/utils`. Verify deep-import resolution in tsconfig paths.
5. **Test fixtures use absolute paths.** `monkeypatch.setattr("src.shared...")` in lifted tests must update to new path. Grep `monkeypatch.setattr` in lifted tests, update.
6. **conftest.py at multiple levels.** Lift each level (`tests/conftest.py`, `tests/shared/conftest.py`, `tests/shared/<area>/conftest.py`). Don't merge; preserve hierarchy.
7. **`__init__.py` re-exports.** Each lifted directory needs the `__init__.py` lifted too (some are empty, but they mark Python packages).
8. **Deferred files clue.** Builder may notice grep matches in `shared/workers/` then think "missing files". They're DEFERRED per §3.3. Check this guidelines file BEFORE escalating.

## §10. Anti-duplication discipline (per anti-duplication.md)

Story 2 LIFTS shared abstractions canonically. The act of lifting CONSOLIDATES SSoT (was scattered in AISALESHT shared/, becomes luana-core-*). Does NOT create duplicates because:

- Source AISALESHT shared/ files untouched (Story 10 swaps imports there).
- During Story 2-9 window, BOTH versions coexist (AISALESHT shared/ + luana-core-*). Outcome §7.3 explicitly accepts this temporary duplication as known cost.
- Story 10 closes the window by mass-rewriting AISALESHT imports to `@luana/*` and deleting `backend/src/shared/`.

If builder discovers a class/function in `shared/` already exists in `luana-core-*` from a previous ticket — that's expected (lift might happen across batches). The dependency declaration in pyproject.toml MUST cite the canonical lift, not re-lift.
