---
story_id: luana-brand-offer-studios
guidelines_version: 1
last_modified: 2026-05-11
drafted_by: /architect (claude-opus-4-7)
authority: 03-arch.md + 00-story.md + outcome §7.3 lift mode + §7.2 Story 5 autonomy + ADR-001 §2.4 + Story 4 05-guidelines.md pattern
---

# 05-guidelines.md — luana-brand-offer-studios

> /dev-team reads this BEFORE picking up any ticket. Defines patterns required/forbidden, files in scope, skills to load, halt criteria. Sub-builders inherit this guidance verbatim.

## §1. Patterns Required

### §1.1 Lift mode (per outcome §7.3, identical to Stories 2-4 §1.1)

- **Verbatim file copy.** Use `cp -r` to lift source → destination. Do NOT rewrite, do NOT reformat, do NOT renumber lines.
- **Preserve DDD layering.** `domain/` → `infrastructure/` → `application/` → `api/` boundaries stay intact within each package.
- **Preserve class/function/module names.** `BrandSettings` stays `BrandSettings`. `PersonalityCompiler` stays `PersonalityCompiler`. `Offer` stays `Offer`. `OFFER_TYPE_PRESET_CATALOG` stays as is.
- **Preserve public API surface.** Re-export shape via `__init__.py` matches AISALESHT verbatim.
- **Preserve tests.** Lift `backend/tests/modules/<m>/test_*.py` alongside source. EXCEPT files in §3.3 DEFERRED list.
- **Preserve catalogs.** All 7 offer catalogs (DAG) + 76 presets + 21 sections lift byte-equal. NO `_CATALOG_VERSION` bump (lift = identical content; bumping the version triggers FE cache invalidation falsely).
- **Preserve PersonalityCompiler placement** (ADR-001 §2.4). Lift to `luana_core_brand_studio.domain.personality` verbatim. NO refactor to introduce BrandVoicePort in Story 5 (Story 7 owns the consumer-side port intro per §3.3).
- **Per-package `pyproject.toml` at version `"0.0.1-alpha"`** (template literals in 03-arch.md §8).
- **Update import paths INTERNOS to luana-platform only.** Use search-and-replace mapping in 03-arch.md §5.

### §1.2 Workspace registration (single ticket T-1)

- Add 2 new Python packages to `~/luana-platform/pyproject.toml` `[tool.uv.workspace] members` AND `[tool.uv.sources]` (template in 03-arch.md §4.1).
- Run `cd ~/luana-platform && uv sync --all-packages` after pyproject update — confirms registration (will resolve fully after T-2..T-13 land packages).

### §1.3 Import path rewriting (verbatim mechanical sed)

Inside each newly lifted package, apply these sed patterns. Use the **exact patterns** below — over-broad sed corrupts strings inside docstrings/test fixtures.

```bash
# Replace <m> with original module slug (brand, offer)
# Replace <pkg_snake> with destination (luana_core_brand_studio, luana_core_offer_studio)
cd ~/luana-platform/core/luana-core-<name>

# 1. Self-imports: src.modules.<m>.<X> → <pkg_snake>.<X>
find src tests -name "*.py" -exec sed -i 's|from src\.modules\.<m>\.|from <pkg_snake>.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|import src\.modules\.<m>\.|import <pkg_snake>.|g' {} \;

# 2. Cross-module Story 5 → Story 3 iam
find src tests -name "*.py" -exec sed -i 's|from src\.modules\.iam\.|from luana_core_iam.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|import src\.modules\.iam\.|import luana_core_iam.|g' {} \;

# 3. Cross-module Story 5 → Story 2 platform (shared.* + core.*)
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.domain\.|from luana_core_platform.domain.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.links\.|from luana_core_platform.links.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.infrastructure\.|from luana_core_platform.infrastructure.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.application\.|from luana_core_platform.application.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.workers\.|from luana_core_platform.workers.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.api\.|from luana_core_platform.api.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.domain_events\.|from luana_core_platform.domain_events.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.core\.|from luana_core_platform.core.|g' {} \;

# 4. NOTE: DO NOT rewrite imports of src.modules.{copilot,sales_agent,advertising,campaigns}.
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

### §1.6 Per-test skip discipline (offer_ai endpoint case)

`test_offer_ai_endpoint.py` lifts to `core/luana-core-offer-studio/tests/test_offer_ai_endpoint.py`. Some tests inside may exercise the deferred `offer_ai.py` route. If GREEN check fails:

1. Identify the failing tests via `pytest --tb=short`.
2. For tests touching deferred routes, add per-test skip ONLY (NOT whole-file skip):
   ```python
   @pytest.mark.skip(reason="DEFERRED Story 6 — offer_ai.py routes need copilot.offer_psychology_service")
   def test_offer_ai_generate_psychology(...): ...
   ```
3. Budget: ≤5% test drop per outcome §7.4 halt #9. If skipped count exceeds 5% of total → escalate.

### §1.7 Brand-agnostic engines verification (Story 5-specific, mirror Story 4 §1.7)

Before declaring T-2..T-13 done, verify each lifted package stays brand-agnostic via local smoke (full arch test runs in T-15):

```bash
cd ~/luana-platform/core/luana-core-<name>/src
grep -rEn 'if\s+brand\s*==|if\s+tenant\.brand\s*==|brand\s*==\s*"(nicolify|vitalia|comunify|lupulo)"' luana_core_<name>/ || echo "OK: no brand control flow"
grep -rEn '(API_KEY|SECRET|TOKEN)\s*=\s*"(?!\$|os\.|settings\.).{8,}"' luana_core_<name>/ || echo "OK: no hardcoded credentials"
```

If either grep finds matches → escalate per §6 halt #7 (lift mode violation: source has brand-aware code that shouldn't have been merged to AISALESHT either).

### §1.8 No cyclic deps — Story 5 (DAG-clean)

Story 5 has no cyclic deps. Both packages depend on Story 2+3 (platform + iam), zero inter-Story-5 deps (brand ⊥ offer at production code level). Pure DAG. No special handling needed.

### §1.9 Voice compiler placement verification (ADR-001 §2.4 cement)

T-17 introduces arch fitness test `test_story5_voice_compiler_in_brand_studio.py` per 03-arch.md §7.3 + §10.

Acceptance: PersonalityCompiler class lives ONLY in `core/luana-core-brand-studio/src/luana_core_brand_studio/domain/personality.py`. Anti-mirror rule enforces no duplicate elsewhere. Builder DOES NOT introduce BrandVoicePort port in Story 5 — that's Story 7's consumer-side concern per 03-arch.md §9.4 + §10.3.

If builder finds itself drafting a `BrandVoicePort` Protocol or `BrandVoiceService` class in Story 5 → STOP, that's NEW abstraction, escalate per §6 halt #5.

## §2. Patterns Forbidden

### §2.1 Lift mode violations (auto-FAIL, per Stories 2-4 §2.1)

- ❌ **Renaming any class, function, module, or symbol.** Original names preserved.
- ❌ **Refactor logic** while lifting — even "obvious improvements" — escalate per outcome §7.4.
- ❌ **Splitting modules.** A module file stays a module file.
- ❌ **Merging modules.** Two files stay two files.
- ❌ **Adding new abstractions** (factories, registries, adapters, ports) not present in AISALESHT. EXCEPTION: NONE in Story 5 (no analytics Makefile equivalent — brand + offer don't have AISALESHT-root scripts to lift).
- ❌ **Changing public API signatures.** Same args, same return types, same exceptions.
- ❌ **Removing code** during lift — even if "clearly dead".
- ❌ **Reformatting** beyond what `ruff format` would do automatically on save.
- ❌ **Bumping `_CATALOG_VERSION`** in `offer_type_presets.py`. Lift = identical content, no version change.

### §2.2 Mutating AISALESHT (auto-FAIL — outcome §7.3)

- ❌ **Any file under `backend/src/modules/{brand,offer}/`** is READ-ONLY in Story 5.
- ❌ **Any file under `backend/tests/modules/{brand,offer}/`** is READ-ONLY.
- ❌ **Modifying AISALESHT root pyproject.toml, alembic migrations, conftest.py at root.** Out of scope.
- ❌ **Running `make ci-parity` against AISALESHT to "verify lift didn't break it"** — Story 5 doesn't change AISALESHT. Story 10 will validate.

### §2.3 Brand-aware code in engines (auto-FAIL — Story 5-specific cement)

- ❌ **`if brand == "..."` or `if tenant.brand == "..."`** control flow in brand-studio or offer-studio.
- ❌ **Hardcoded brand IDs / API keys / secrets** in engine source. Tenant config via DI only.
- ❌ **`from nicolify.X` or `import nicolify.X`** — engines stay brand-agnostic.
- ❌ **Adding a `brand_id` column or constructor param** to BrandSettings or Offer — that's refactor + scope expansion.

### §2.4 Forward-Story coupling (auto-FAIL)

- ❌ **Importing from Story 6/7/8 packages** (`luana_core_{copilot,sales_agent,campaigns,advertising,scheduling}`) in any Story 5 source file outside the DEFERRED set.
- ❌ **Importing from `src.modules.*`** in any Story 5 source file (lift incomplete — caller forgot sed pass).

### §2.5 Voice compiler architectural violations (Story 5-specific — ADR-001 §2.4 cement)

- ❌ **Introducing `BrandVoicePort` Protocol in Story 5.** Consumer-side port is Story 7's territory. Per outcome §7.3 "no new abstractions" + 03-arch.md §9.4.
- ❌ **Introducing `BrandVoiceService` adapter class in Story 5.** Same reason.
- ❌ **Creating a mirror `class PersonalityCompiler` outside brand-studio.** Arch test V-AG-3 BLOCKS this. ADR-001 §2.4 SSoT.
- ❌ **Refactoring `PersonalityCompiler.compile()` signature.** Lift verbatim — same args, same return.
- ❌ **Introducing voice cloning pipeline code.** Per 03-arch.md §9.5: doesn't exist in AISALESHT, Stories 11-13 territory.

### §2.6 Catalog drift (Story 5-specific)

- ❌ **Modifying `OFFER_TYPE_PRESET_CATALOG` content** during lift (must be byte-equal to AISALESHT).
- ❌ **Modifying `ARCHETYPE_CATALOG`, `VALUE_LEVEL_CATALOG`, `FORMAT_CATALOG`, `SECTION_CATALOG`, `OFFER_LADDER_HINTS`, `VARIANT_STRUCTURE_CATALOG`** during lift.
- ❌ **Bumping `_CATALOG_VERSION`** (per §2.1).
- ❌ **Reordering catalog entries** (test_catalogs_dag_smoke uses sets, but ordering matters for downstream FE cache keys — preserve verbatim).

## §3. Files in Scope

### §3.1 AISALESHT (READ-ONLY source)

**Lift these:**

#### brand-studio (75 production + 34 tests)
- `backend/src/modules/brand/{__init__,api,application,domain,infrastructure,tests,workers}/**`
  - SKIP: `backend/src/modules/brand/copilot_provider/` (DEFERRED Story 6)
- `backend/tests/modules/brand/**`
  - SKIP: `test_brand_context_injector.py`, `test_buyer_persona_fields_dropped_regression.py`, `test_worker_emits_summary_and_pills.py` (DEFERRED Story 6)

#### offer-studio (88 production + 73 tests)
- `backend/src/modules/offer/{__init__,api,application,domain,infrastructure,workers}/**`
  - SKIP: `backend/src/modules/offer/copilot_provider/` (DEFERRED Story 6)
  - SKIP: `backend/src/modules/offer/api/offer_ai.py` (DEFERRED Story 6)
  - SKIP: `backend/src/modules/offer/api/counts.py` (DEFERRED Story 8)
  - SKIP: `backend/src/modules/offer/api/campaigns.py` (DEFERRED Story 8)
- `backend/tests/modules/offer/**`
  - SKIP: `test_offer_data_access_provider.py` (DEFERRED Story 6)

### §3.2 luana-platform (CREATE)

**Create:**
- `~/luana-platform/core/luana-core-brand-studio/{pyproject.toml,README.md,src/luana_core_brand_studio/**,tests/**}`
- `~/luana-platform/core/luana-core-offer-studio/{pyproject.toml,README.md,src/luana_core_offer_studio/**,tests/**}`
- `~/luana-platform/core/tests/architecture/test_story5_brand_agnostic_engines.py`
- `~/luana-platform/core/tests/architecture/test_story5_no_forward_module_imports.py`
- `~/luana-platform/core/tests/architecture/test_story5_voice_compiler_in_brand_studio.py`
- `~/luana-platform/core/luana-core-offer-studio/tests/test_catalogs_dag_smoke.py`

**Modify:**
- `~/luana-platform/pyproject.toml` (workspace + sources registration)
- `~/luana-platform/core/DEFERRED-FILES.md` (append Story 5 entries)

### §3.3 DEFERRED list — DO NOT LIFT, DO NOT TOUCH

#### Defer to Story 6 (copilot lift) — copilot_provider/ subfolders + 1 offer/api + 4 tests

```
# brand copilot_provider/ — 8 files
backend/src/modules/brand/copilot_provider/__init__.py
backend/src/modules/brand/copilot_provider/context_inject.py
backend/src/modules/brand/copilot_provider/module_data.py
backend/src/modules/brand/copilot_provider/provider.py
backend/src/modules/brand/copilot_provider/summary.py
backend/src/modules/brand/copilot_provider/tools.py
backend/src/modules/brand/copilot_provider/workflow_handlers.py
backend/src/modules/brand/copilot_provider/workflows.py

# offer copilot_provider/ — 5 files
backend/src/modules/offer/copilot_provider/__init__.py
backend/src/modules/offer/copilot_provider/data_access.py
backend/src/modules/offer/copilot_provider/provider.py
backend/src/modules/offer/copilot_provider/workflow_handlers.py
backend/src/modules/offer/copilot_provider/workflows.py

# offer/api with copilot dep — 1 file
backend/src/modules/offer/api/offer_ai.py

# tests importing copilot — 4 files
backend/tests/modules/brand/test_brand_context_injector.py
backend/tests/modules/brand/test_buyer_persona_fields_dropped_regression.py
backend/tests/modules/brand/test_worker_emits_summary_and_pills.py
backend/tests/modules/offer/test_offer_data_access_provider.py
```

**Detection rule:** `grep -l "from src.modules.copilot" <file>` → DEFERRED to Story 6.

#### Defer to Story 8 (campaigns/advertising lift) — 2 offer/api files

```
backend/src/modules/offer/api/counts.py
backend/src/modules/offer/api/campaigns.py
```

These import `src.modules.advertising.application.services.offer_campaigns_read_adapter` (advertising = Story 8 batch per outcome §2).

**Detection rule:** `grep -l "from src.modules.advertising" <file>` → DEFERRED to Story 8.

#### Reserved (NOT existing, NOT deferred — future stories own creation)

- **BrandVoicePort Protocol** → Story 7 (consumer-side intro). Creator: Story 7 architect.
- **BrandVoiceService adapter** → Story 7 OR Story 14 (brand-voice elevation refactor). Per ADR-001 §2.4 + 03-arch.md §9.4.
- **`voice_cloning: bool` BrandConfig field** → Stories 11-13 (per-brand value at vertical bootstrap; schema itself Story 8/9).
- **Voice cloning pipeline (LLM-distillation from 50+ chat samples)** → Stories 11-13 (NEW code, doesn't exist in AISALESHT today).

### §3.4 Skip during cp -r — mechanical recipe per module

When running `cp -r` for each module, use explicit per-subfolder copy (NOT `cp -r module/*`) to skip deferred subfolders:

```bash
# ─────────────────────────────────────────────────────────────────────
# brand — skip copilot_provider/
# ─────────────────────────────────────────────────────────────────────
for sub in api application domain infrastructure tests workers __init__.py; do
  if [ -e "/home/chris/AISALESHT/backend/src/modules/brand/$sub" ]; then
    cp -r "/home/chris/AISALESHT/backend/src/modules/brand/$sub" \
          ~/luana-platform/core/luana-core-brand-studio/src/luana_core_brand_studio/
  fi
done
# (DO NOT cp -r brand/copilot_provider — DEFERRED Story 6)

# Lift brand tests, EXCLUDE 3 deferred files
rsync -av \
      --exclude='test_brand_context_injector.py' \
      --exclude='test_buyer_persona_fields_dropped_regression.py' \
      --exclude='test_worker_emits_summary_and_pills.py' \
      /home/chris/AISALESHT/backend/tests/modules/brand/ \
      ~/luana-platform/core/luana-core-brand-studio/tests/

# ─────────────────────────────────────────────────────────────────────
# offer — skip copilot_provider/ AND post-copy delete offer_ai.py + counts.py + campaigns.py
# ─────────────────────────────────────────────────────────────────────
for sub in api application domain infrastructure workers __init__.py; do
  if [ -e "/home/chris/AISALESHT/backend/src/modules/offer/$sub" ]; then
    cp -r "/home/chris/AISALESHT/backend/src/modules/offer/$sub" \
          ~/luana-platform/core/luana-core-offer-studio/src/luana_core_offer_studio/
  fi
done
# (DO NOT cp -r offer/copilot_provider — DEFERRED Story 6)

# Post-copy: delete deferred-Story-6 + Story-8 files (lifted as part of api/ subfolder)
rm -f ~/luana-platform/core/luana-core-offer-studio/src/luana_core_offer_studio/api/offer_ai.py
rm -f ~/luana-platform/core/luana-core-offer-studio/src/luana_core_offer_studio/api/counts.py
rm -f ~/luana-platform/core/luana-core-offer-studio/src/luana_core_offer_studio/api/campaigns.py

# Lift offer tests, EXCLUDE 1 deferred file
rsync -av \
      --exclude='test_offer_data_access_provider.py' \
      /home/chris/AISALESHT/backend/tests/modules/offer/ \
      ~/luana-platform/core/luana-core-offer-studio/tests/
```

**Verify zero leaks after each lift:**

```bash
grep -rEn "from src\.modules\.(copilot|sales_agent|advertising|campaigns)" \
    ~/luana-platform/core/luana-core-<name>/src/ \
    && echo "FAIL: deferred file leaked into lift" || echo "OK"
```

## §4. Skills + Rules to Load

| Skill / Rule | When |
|---|---|
| `backend-expert` (this skill) | All Story 5 tickets |
| `brand-expert` | T-2 through T-8 (brand-studio lift) — for BrandSettings + PersonalityProfile + StyleAnalyzer + BuyerPersona SSoT |
| `offer-expert` | T-9 through T-13 (offer-studio lift) — for 7 catalogs DAG + 76 presets + section_catalog + ladder hints SSoT |
| `offer-type-preset-expert` | T-9 (offer domain lift) — narrow scope L7 preset catalog SSoT |
| `tessl__fastapi` | All tickets — FastAPI router preservation |
| `tessl__langgraph` | T-6 (brand StyleAnalyzer LangGraph agent lift) — preserve graph topology |
| `.claude/rules/offer-catalogs.md` | T-9, T-11, T-12 (catalog + preset lift) |
| `.claude/rules/anti-duplication.md` | T-1 (workspace registration) + T-17 (voice compiler placement) — verify no parallel layer added |
| `.claude/rules/auditor-downstream-regression.md` | All tickets — tests lift alongside source |
| `.claude/rules/tdd-mandatory.md` | T-15, T-16, T-17 (new arch fitness + smoke tests) |
| `.claude/rules/parallel-safety.md` | All tickets — single development branch, no force push |

## §5. Commit conventions (per ticket)

```
chore(workspace): register Story 5 packages in uv workspace                                # T-1
feat(luana-core-brand-studio): skeleton + pyproject.toml + README                          # T-2
feat(luana-core-brand-studio): lift brand domain layer + tests                             # T-3
feat(luana-core-brand-studio): lift brand infrastructure layer + tests                     # T-4
feat(luana-core-brand-studio): lift brand application + services layer + tests             # T-5
feat(luana-core-brand-studio): lift brand voice-fidelity + style-analyzer LangGraph agent  # T-6
feat(luana-core-brand-studio): lift brand api layer + tests (skip copilot_provider)        # T-7
feat(luana-core-brand-studio): lift brand workers + tests                                  # T-8
feat(luana-core-offer-studio): skeleton + pyproject.toml + README + lift offer domain (7 catalogs DAG, 76 presets verbatim)  # T-9
feat(luana-core-offer-studio): lift offer infrastructure layer + tests                     # T-10
feat(luana-core-offer-studio): lift offer application layer + tests                        # T-11
feat(luana-core-offer-studio): lift offer api layer + tests (skip 3 deferred)              # T-12
feat(luana-core-offer-studio): lift offer workers + tests                                  # T-13
test(luana-platform): cross-package smoke + aggregate pytest GREEN (21 packages)           # T-14
test(arch): Story 5 brand-agnostic engines invariant                                       # T-15
test(arch): Story 5 no forward module imports                                              # T-16
test(arch): voice compiler SSoT cement in brand-studio per ADR-001 §2.4 + catalogs DAG smoke  # T-17
chore(luana-platform): Story 5 lint + AISALESHT untouched + DEFERRED-FILES update + READMEs  # T-18
```

Conventional Commits format. All on `development` branch in `~/luana-platform/`. Push after each ticket GREEN.

## §6. Halt criteria (per outcome §7.4 + 03-arch.md)

Halt + escalate to Chris if any of these triggers:

1. **Cross-Story-5 coupling discovered** — if grep reveals brand/offer cross-importing (which audit confirmed they don't), DAG breaks → escalate.
2. **Voice compiler ELEVATION requires refactor** — if `PersonalityCompiler.compile()` has hidden cross-module dep that forces signature change → STOP (would violate ADR-001 §2.4 verbatim lift).
3. **BrandVoicePort scope-expansion temptation** — if builder thinks "I should add BrandVoicePort for Story 7 to consume" → STOP. That's Story 7 territory per 03-arch.md §9.4 + §10.3.
4. **Auditor REJECTED + 3 auto-fix Opus iter fail** — per outcome §7.4 cap_reached.
5. **Scope expansion needed** — any "small refactor" that requires touching files beyond §3 list. Includes: introducing new ports, factories, adapters, or BrandVoicePort/BrandVoiceService classes.
6. **Cumulative cost > $1500** — soft check-in with Chris.
7. **Brand-specific code in supposedly brand-agnostic engine** — arch fitness §7.1 (V-AG-1) fails after lift → source has pre-existing brand contamination → escalate (it shouldn't have been merged to AISALESHT either).
8. **DEFERRED file leaks into lift** — `grep "from src.modules.(copilot|sales_agent|advertising|campaigns)"` in lifted code post-sed reveals a deferred file got copied → revert + re-lift with explicit subfolder loop (§3.4).
9. **Test count drop > 5%** — preserve test count from AISALESHT baseline EXCEPT documented deferrals (4 brand tests, 1 offer test). Drop indicates lost test files or excessive per-test skips on `test_offer_ai_endpoint.py`. Escalate.
10. **Catalog content drift** — if `OFFER_TYPE_PRESET_CATALOG` or any of the other 6 offer catalogs differ byte-equal vs AISALESHT post-lift, sed corrupted catalog string literals → revert + re-apply sed with narrower pattern.
11. **Voice compiler mirror detected** — V-AG-3 fails (`PersonalityCompiler` declared outside brand-studio). Indicates lift bug or accidental mirror creation. Revert + investigate.

## §7. Sub-builder spawn template

When /dev-team spawns sub-builder for a ticket:

```
Agent({
  description: "Lift <module> — T-N",
  subagent_type: "builder-backend",
  model: "sonnet",  // R23 — production_code: false (lift, no agentic logic runtime changes)
  prompt: "
    <pr_folder>: /home/chris/AISALESHT/docs/product/stories/luana-brand-offer-studios
    <ticket>: T-N

    Lift <module> from AISALESHT to luana-platform per:
    - 00-story.md scope
    - 03-arch.md §3 (per-package structure) + §5 (import mapping) + §9 (DEFERRED list)
    - 05-guidelines.md §1.3 (sed patterns) + §3.4 (per-module cp -r recipe) + §3.3 (deferred files)
    - Validators GREEN: V-NF-2, V-F-py-N (run per-ticket-listed)

    DO NOT TOUCH AISALESHT.
    DO NOT lift files in §3.3 DEFERRED list.
    DO NOT introduce BrandVoicePort or BrandVoiceService in Story 5 (Story 7 territory).
    DO NOT modify catalog content (lift verbatim).
    DO NOT bump _CATALOG_VERSION.
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
grep -rEn "from src\.modules\.(copilot|sales_agent|advertising|campaigns)" ~/luana-platform/core/luana-core-<name>/src/ && echo "FAIL: deferred leak" || echo "OK"

# 4. No forward Story imports
grep -rEn "from luana_core_(copilot|sales_agent|campaigns|advertising|scheduling)\." ~/luana-platform/core/luana-core-<name>/src/ && echo "FAIL: forward import" || echo "OK"

# 5. AISALESHT untouched (Story 5 surfaces)
cd /home/chris/AISALESHT
git diff HEAD --name-only | grep -E '^(backend/src/modules/(brand|offer)|backend/tests/modules/(brand|offer))/' && echo "FAIL: AISALESHT mutated" || echo "OK"

# 6. (after T-17) Voice compiler SSoT placement
cd ~/luana-platform && uv run pytest core/tests/architecture/test_story5_voice_compiler_in_brand_studio.py -x -q
```

All 5-6 checks GREEN → close ticket. ANY check FAILS → halt, fix, re-verify.

## §9. Common pitfalls + remedies

| Pitfall | Symptom | Remedy |
|---|---|---|
| `cp -r module/*` copies deferred subfolder | `from src.modules.copilot` leaks post-sed | Use explicit per-subfolder loop (§3.4). Delete deferred files post-copy. |
| Over-broad sed corrupts test fixtures | Strings inside docstrings/fixtures replaced unintentionally | Use exact patterns in §1.3 (anchored on `from src\.` / `import src\.`). Verify with `git diff` before commit. |
| `monkeypatch.setattr("src.modules.X")` left in tests | Tests pass but mock targets wrong module | Run sed on tests too. Verify with `grep "src.modules" tests/` post-lift. |
| StyleAnalyzer LangGraph agent imports langgraph/langchain at module-load | T-6 pytest collection fails on missing dep | Verify `langgraph>=0.2` + `langchain-core>=0.3` in brand-studio pyproject.toml dependencies. |
| Qdrant client missing for style_anchor_store | `test_style_anchor_store.py` fails ImportError | Verify `qdrant-client>=1.10` in brand-studio pyproject.toml. |
| offer.workers imports `arq` | T-13 import error | Verify `arq>=0.26` in offer-studio pyproject.toml. |
| Catalog test counts drift | V-F-cat-1 fails on assertion (5 ≠ 4 archetypes, 76 ≠ 75 presets, etc.) | Inspect AISALESHT current counts: `grep -c "OfferTypePreset(" backend/src/modules/offer/domain/offer_type_preset_catalog.py`. Adjust assertions in `test_catalogs_dag_smoke.py` to actual lifted values + document in T-17 commit body. |
| PersonalityCompiler test fails post-lift | T-17 V-AG-3 finds class missing or in wrong location | Check `grep -n "class PersonalityCompiler" core/luana-core-brand-studio/src/luana_core_brand_studio/domain/personality.py`. If line position differs from AISALESHT line 440 — sed corrupted. Revert + narrow sed. |
| Story 4 packages regress post-Story-5 workspace deps | V-F-x-2 aggregate pytest fails on Story 2/3/4 tests | Likely a transitive dep conflict. Check `uv pip list` vs Story 4 baseline. Pin offending dep in Story 5 pyproject. |
| `test_offer_ai_endpoint.py` fails due to deferred offer_ai.py | T-12 pytest fails | Per §1.6, add per-test skips with reason. Budget ≤5% test drop per §6 halt #9. |
