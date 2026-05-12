<!-- voseo-allowed: arch doc cites rules + binding decisions verbatim for traceability per R25 -->
---
story_id: luana-nicolify-migration
arch_version: 1
sub_arch: consolidated (BE imports rewrite + FE workspace move + DB consolidation + /pm SSoT migration + AISALESHT archive)
architect_owner: claude-opus-4-7
ratified_by_chris: false                           # Architect emits — Chris reads/ratifies wording at refined→ready transition
last_modified: 2026-05-12
binding_decisions_ref: docs/product/outcomes/luana-platform-migration.md §7.6 (10 binding decisions)
halt_triggers_ref: docs/product/outcomes/luana-platform-migration.md §7.6.2 (11 triggers — Trigger #11 added Phase 1)
success_criteria_ref: docs/product/outcomes/luana-platform-migration.md §7.6.3
spec_ref: 01-spec.md (9 features × 4 scenarios = 36 Gherkin)
sibling_docs:
  - 03-arch-be.md            # BE deep dive (package-by-package mapping, alembic consolidation, fresh DB, Trigger #11 workflow)
  - 05-guidelines.md         # required/forbidden patterns + files in scope + sub-agent skill loading

links:
  outcome: "../../outcomes/luana-platform-migration.md"
  spec: "01-spec.md"
  arch_be: "03-arch-be.md"
  guidelines: "05-guidelines.md"
  checkpoint: "checkpoint.md"
  story_9_precedent: "../../../archive/2026/stories/luana-v0-1-0-publish/03-arch-be.md"
  migration_guide: "/home/chris/luana-platform/docs/migration-from-nicolify.md"
---

# 03-arch — Story 10 consolidated architecture overview

> **Purpose:** single-page mental model of the migration. Deep BE detail in `03-arch-be.md`. Process discipline (patterns required/forbidden, skill loading, files in scope) in `05-guidelines.md`. Executable validators + tickets in `04-validators.yaml` + `06-tickets.yaml` (separate spawn — Part 2).

> **Status:** Architect Part 1 — arch docs only. Validators + tickets follow in Part 2 spawn.

## 0. Context summary

- **Outcome:** `luana-platform-migration` Story 10/14 (pivot story — closes Stories 1-9 publish ↔ unlocks Stories 11-14 verticals).
- **Architect run on:** 2026-05-12 (Opus 4.7, 1M context). Knowledge cutoff Jan 2026; current pipeline/library state verified live via local file reads on 2026-05-12.
- **Scope (9 surfaces — features 1-9 spec §5):** BE imports rewrite (18 modules + 11 shared subsystems) · FE imports rewrite + workspace move · fresh `nicolify_dev` DB + alembic snapshot consolidation · test parity baseline + delta=0 enforcement · Playwright smoke E2E · `make ci-parity` root migration · /pm SSoT atomic `git mv` · AISALESHT archive + DB drop · Story 10 archive at new SSoT location.
- **Out of scope (DEFERRED):** Streamlit admin (`backend/src/admin/`) → Story 10b · workers (`backend/src/workers/` + per-module workers) → Story 10b/14 · 40 sales_agent pre-existing failures → Story 14 brand-voice-elevation · vertical brand bootstraps Vitalia/Comunify/Lupulo → Stories 11-13 · business logic refactor (zero new endpoints/DTOs).
- **Critical constraints (binding Chris framing):** cap paralelización ≤2 sub-agents simultaneous · Opus mayoritario crítico (imports rewrite cross-module, schema consolidation, /pm SSoT migration, Vercel reconfig) · halt-and-ask Chris on any of 11 §7.6.2 triggers · sub-agents smart blast radius (contained context).

### 0.1 Surface → builder/auditor mapping (PM uses to spawn correct agents)

| Surface | Tickets (preview Part 2) | Builder | Auditor |
|---|---|---|---|
| BE imports rewrite (18 modules + 11 shared subsystems — sharded by Wave) | T-2..T-7 (sharded — 2 BE business modules + 1 shared subsystem at a time, ≤2 paralelo) | `builder-backend` Sonnet OK (mechanical) BUT Opus 4.7 for cross-module rewrites involving `copilot`/`sales_agent` (anti-duplication risk + agentic surface) | `auditor-backend` Opus 4.7 |
| FE imports rewrite + `git mv frontend/` → `luana-platform/nicolify/frontend/` | T-8 + T-9 | `builder-frontend` Opus 4.7 (Vercel reconfig + workspace nesting non-trivial, R23 not applicable but criticality justifies) | `auditor-frontend` Opus 4.7 |
| Alembic snapshot consolidation + fresh `nicolify_dev` DB | T-10 | `builder-backend` Opus 4.7 (schema consolidation = high-risk, model↔DB drift detection per Scenario 3.2) | `auditor-backend` Opus 4.7 |
| Test parity baseline + delta=0 enforcement (script + arch fitness tests) | T-1 (baseline FIRST ticket) + T-N (final delta check) + new `scripts/test_delta_check.py` + `tests/architecture/test_no_legacy_src_paths.py` + `tests/architecture/test_no_legacy_src_mock_paths.py` | `builder-backend` Sonnet (script + arch tests are mechanical/TDD) | `auditor-backend` Sonnet (deterministic) |
| Playwright smoke E2E (Chris journey + tenant isolation + cost regression) | T-11 | `builder-frontend` Sonnet (E2E spec mechanical, follows `playwright-expert` skill patterns) | `auditor-frontend` Sonnet (deterministic) |
| CI parity root Makefile migration + pre-push hook update | T-12 | `builder-backend` Sonnet (Makefile + hook scripts) | `auditor-backend` Sonnet |
| /pm SSoT atomic `git mv` (`docs/product/` → `luana-platform/docs/product/`) + scripts migration + pre-commit hook path updates | T-13 (Phase 4 = merge time) | **`builder-backend` Opus 4.7** (high-risk cross-repo `git mv` + hardcoded path discovery per Decisión 4A halt) | `auditor-backend` Opus 4.7 |
| AISALESHT archive + DB drop closure + Story 10 archive at luana-platform | T-14 (final closure) | `builder-backend` Sonnet (GitHub API + psql DROP — mechanical, but Chris ratifies archive UI manually) | `auditor-backend` Sonnet |

### 0.2 Skills consulted

| Skill | Decisions captured |
|---|---|
| `backend-expert` | SQLA 2.0 only · DDD layers preserved post rewrite (imports only, no boundary refactor) · alembic raw SQL `IF NOT EXISTS` idempotent · tenant isolation cumulative |
| `frontend-expert` | FSD-Lite preserved post workspace move · `playwright-expert` invoke pattern for smoke E2E · live-verify via `chrome-devtools-verify` skill Vercel deployment |
| `copilot-expert` | Imports rewrite preserves anchors `[COPILOT-*]` (cap 36/36) · ratchet 22 frozen `copilot → módulo` imports respected (NO changes) · `module_registry` discovery pattern survives package rename — `luana_core_copilot` imports `luana_core_brand_studio:provider` if convention preserved |
| `sales-agent-expert` | §3 NO TOUCH (Closer Studio API/WS · SmartBufferService · OutputManager.process_response chunking · enrollment_*) preserved · 40 pre-existing failures DEFERRED Story 14 (Decisión 9B) · `BaseAgentCallbackHandler` shared abstraction (`luana_core_observability.recording.base_callback_handler`) imports preserve subclass `SalesAgentCallbackHandler` in `luana_core_sales_agent` |
| `brand-expert` | `BrandSettings` + `PersonalityProfile` byte-stable runtime preserved · `system_instruction` compilation unchanged · field contract registry imports rewritten to `luana_core_brand_studio.domain.field_contract` |
| `offer-expert` + `offer-type-preset-expert` | 84 presets + 7 catalogs DAG preserved · `_CATALOG_VERSION` NOT bumped (no preset changes Story 10) · `shared/links/ports/offer.py::get_offer_type_preset` rewritten path: `luana_core_offer_studio.links.ports.offer.get_offer_type_preset` |
| `metrics-expert` | ETL contract NOT touched Story 10 — `extraction_contract.py` lives in `luana_core_analytics_engine.domain` post rewrite. `make extraction-contract` target relocates to luana-platform/Makefile under brand-aware variant if needed (deferred or Story 10b — verify Phase 0) |
| `tessl__langgraph` | LangGraph state schemas + reducers in `luana_core_copilot` + `luana_core_sales_agent` preserved byte-stable runtime (Story 6+7 frozen) — imports rewrite ONLY |
| `tessl__fastapi` | `FastAPI(redirect_slashes=False)` preserved app-level in main.py · `response_model=` on every route preserved · `Annotated[..., Depends(...)]` patterns preserved |
| `tessl__graceful-degradation` | LiteLLM proxy timeouts + fallback preserved (luana_core_llm.router · luana_core_sales_agent has tenant isolation cross-leak adversarial smoke Scenario 5.4) |

### 0.3 capability YAML + modules/{m}.md updates required (post 2026-05 paradigma)

- **Capability promoted at merge** (per Feature 9 Scenario 9.1):
  - `docs/product/capabilities/luana-core/brand-consumer-migration.yaml` — NEW capability `status: done` (or per `/pm` skill template at merge time)
  - `docs/product/modules/luana-core.md` — narrative section "Nicolify es el primer consumer real de Luana Platform v0.1.0 (Story 10 closed 2026-05-13)"
- **NO module narratives updated for Nicolify modules** (brand/offer/sales_agent/etc.) — migration is mechanical, user-facing capability narrative unchanged. Future Stories 11-13 update verticals.

### 0.4 Architecture fitness gates that must keep passing

Run `make arch-test` (BE) + `cd frontend && npx vitest run src/__tests__/architecture/` (FE) post each rewrite ticket. Gates ratchet — allowlists shrink only.

**BE arch tests cumulative (must stay GREEN post each rewrite ticket):**
- `tests/architecture/test_no_cross_module_imports.py` — DDD boundary (cross-module imports via `shared/links/ports/` only, except `copilot` infra-like). Imports rewrite preserves boundary; path changes but pattern same.
- `tests/architecture/test_response_model_required.py` — every route `response_model=`. Preserved.
- `tests/architecture/test_no_sql_alchemy_1x.py` — no `session.query()` introduced. Preserved.
- `tests/architecture/test_no_hard_deletes.py` — soft delete only. Preserved.
- `tests/architecture/test_master_data_utc.py` — `DateTime(timezone=True)` + no `datetime.utcnow()`. Preserved.
- `tests/architecture/test_currency_no_hardcoded_usd.py` — `currency` field in monetary DTOs. Preserved.
- `tests/architecture/test_copilot_anchors.py` — 36/36 anchor cap. Preserved (imports rewrite NO touches anchors).
- `tests/architecture/test_no_new_copilot_module_imports.py` — 22 frozen ratchet. Preserved.
- `tests/architecture/test_copilot_provider_compliance.py` — registry discovery pattern. Preserved (convention `luana_core_X.copilot_provider:provider` if Story 5/6/7 preserved naming).
- `tests/architecture/test_workflow_compliance.py` — workflow registry. Preserved.
- `tests/architecture/test_channel_formatter_compliance.py` — channel format registry. Preserved.
- `tests/architecture/test_extraction_contract.py` — analytics ETL contract docs↔code. Preserved (architect verifies migration touches NO providers — if so, regen contract).
- `tests/architecture/test_offer_type_preset_catalog_completeness.py` — 187+ cases preset catalog invariants. Preserved.
- `tests/architecture/test_brand_editable_fields_baseline.py` + `test_buyer_persona_editable_fields_baseline.py` — field contract baselines. Preserved (no field changes).
- `tests/architecture/test_no_legacy_eventbus_mock_when_outbox_on.py` — outbox flag default on. Preserved (NO flag flips Story 10).
- `tests/architecture/test_personas_yaml_completeness.py` — eval simulator personas. Preserved.

**NEW arch tests Story 10 (created in T-1 baseline ticket):**
- `tests/architecture/test_no_legacy_src_paths.py` — `grep "from src\."` cumulative on `luana-platform/nicolify/backend/` returns 0. Fails build if any legacy import re-introduced post Story 10.
- `tests/architecture/test_no_legacy_src_mock_paths.py` — `grep -r 'patch\(["\']src\.' tests/` returns 0. Detects stale test mocks (Feature 1 Scenario 1.4 silent regression risk).
- `tests/architecture/test_consolidated_migration_idempotent.py` — parses `alembic/versions/001_initial_snapshot.py` raw SQL, asserts all DDL uses `IF NOT EXISTS` / `IF EXISTS` (Feature 3 Scenario 3.3).
- `tests/architecture/test_delta_zero_enforcement.py` — parses `baseline-{be,fe}-tests.json` vs final, asserts new_failures = [] (Feature 4 Scenario 4.2).

**FE arch tests preserved:**
- `src/__tests__/architecture/test-page-padding.test.ts` — design token consumption preserved
- `src/__tests__/architecture/test-fsd-boundaries.test.ts` — boundary matrix preserved
- (10 total FE arch tests — ratchet allowlists shrink only)

## 1. Architecture diagram — AISALESHT → luana-platform/nicolify/

```mermaid
graph TB
    subgraph AISALESHT [AISALESHT/ pre-Story-10]
        BE_old[backend/src/<br/>modules/X/<br/>shared/Y/<br/>workers/<br/>admin/]
        FE_old[frontend/<br/>src/features/<br/>src/components/<br/>src/lib/]
        DB_old[(visionarias_logs<br/>131 migrations)]
        PM_old[docs/product/<br/>BACKLOG.md<br/>outcomes/<br/>stories/]
        Makefile_old[Makefile<br/>ci-parity target]
    end

    subgraph LP [luana-platform/ post-Story-10]
        subgraph Core [core/ Story 9 published v0.1.0]
            Py_core[26 luana-core-* packages<br/>luana_core_brand_studio<br/>luana_core_sales_agent<br/>luana_core_copilot<br/>luana_core_observability<br/>... 22 more]
            Ts_core[7 @luana/* packages<br/>@luana/ui-kit<br/>@luana/api-client<br/>@luana/format<br/>@luana/hooks<br/>@luana/schemas<br/>@luana/design-tokens<br/>@luana/extension-sdk]
        end
        subgraph Nicolify [nicolify/ Story 10 destination]
            BE_new[backend/<br/>src/modules/X/<br/>src/shared/Y/<br/>imports: luana_core_*]
            FE_new[frontend/<br/>src/features/<br/>src/components/<br/>imports: @luana/*<br/>workspace member]
        end
        DB_new[(nicolify_dev<br/>001_initial_snapshot)]
        PM_new[docs/product/<br/>BACKLOG.md<br/>outcomes/<br/>stories/<br/>+ docs/archive/2026/]
        Makefile_new[Makefile root<br/>ci-parity cross-brand<br/>BRANDS := nicolify]
    end

    DEFERRED[/Story 10b/<br/>admin Streamlit<br/>workers ETL<br/>]
    DEF_FAIL[/Story 14/<br/>40 sales_agent failures<br/>brand-voice-elevation/]

    BE_old -.imports rewrite codemod libcst.->BE_new
    FE_old -.git mv + find-replace.->FE_new
    DB_old -.pg_dump schema-only<br/>+ consolidate 131 migrations.->DB_new
    PM_old -.git mv atomic Phase 4.->PM_new
    Makefile_old -.adapt paths + cross-brand pattern.->Makefile_new
    BE_old -.NOT migrated.-> DEFERRED
    BE_old -.40 pre-existing tests.-> DEF_FAIL

    BE_new --consumes--> Py_core
    FE_new --consumes--> Ts_core

    Archive[/GitHub AISALESHT<br/>archived: true<br/>1-click reversible/]
    AISALESHT -.Feature 8 closure.-> Archive

    style AISALESHT fill:#f9d5d5
    style LP fill:#d5f9d5
    style Archive fill:#e0e0e0
    style DEFERRED fill:#fff4cc
    style DEF_FAIL fill:#fff4cc
```

## 2. Migration mechanics per surface (9 features summary)

> **Detailed BE deep dive (codemod regex, package-by-package mapping, alembic strategy, Trigger #11 workflow) lives in `03-arch-be.md`.** This section is the high-level "what each surface does + which Wave it belongs to". Sub-agent prompts cite this section + 03-arch-be.md per ticket.

### Feature 1 — BE imports rewrite (26 luana-core packages target)

**Mechanic:** `libcst` AST-based codemod (NOT sed regex — preserves AST semantics, handles nested + relative imports). Per-package script in `scripts/codemod_be_imports.py` (new — T-2 produces). Mapping table per `migration-from-nicolify.md §3` (Story 9 deliverable).

**Mapping summary (full table in 03-arch-be.md §2):**

| Source (AISALESHT) | Target (luana-core) | Files | Wave |
|---|---|---|---|
| `from src.modules.brand.X` | `from luana_core_brand_studio.X` | 48 | 1 |
| `from src.modules.offer.X` | `from luana_core_offer_studio.X` | 74 | 1 |
| `from src.modules.copilot.X` | `from luana_core_copilot.X` | 150 | 2 (agentic — Opus) |
| `from src.modules.sales_agent.X` | `from luana_core_sales_agent.X` | 104 | 2 (agentic — Opus) |
| `from src.modules.{landing,assets,connections,scheduling,iam,crm,advertising,social_media,social_proof,tenant_domains,tenant_profile,commercial_calendar,campaigns}.X` | `from luana_core_{landing,assets,connections,...}.X` | 248 cumulative | 1 (sharded BE+FE Wave 1) |
| `from src.modules.analytics.X` | `from luana_core_analytics_engine.X` | 91 | 1 |
| `from src.shared.agent_observability.X` | `from luana_core_observability.X` | 18 | 2 (cross-cuts agentic) |
| `from src.shared.events.X` + `domain_events.X` | `from luana_core_events.X` | 10 | 2 |
| `from src.shared.billing.X` | `from luana_core_billing.X` | 17 | 2 |
| `from src.shared.compliance.X` | `from luana_core_compliance.X` | 11 | 2 |
| `from src.shared.idempotency.X` | `from luana_core_idempotency.X` | 3 | 2 |
| `from src.shared.infrastructure.llm.X` | `from luana_core_llm.X` | 22 | 2 |
| `from src.shared.application.extraction.X` | `from luana_core_extraction.X` | 6 | 2 |
| `from src.shared.{api,application,domain,links,workers}.X` | `from luana_core_platform.X` OR per-package re-export (architect verifies Phase 0 spike) | 32 | 2 |

**Test mocks parallel:** every codemod ticket MUST also rewrite test mocks in `backend/tests/modules/{m}/` that reference the legacy path. T-1 baseline captures count via `grep -r 'patch\(["\']src\.' tests/` (currently 0 — but T-1 verifies before rewrite to detect future drift mid-rewrite). New arch fitness `test_no_legacy_src_mock_paths.py` blocks regression.

**Halt Trigger #11 workflow (Phase 1 added):** if rewrite encounters test mock `patch("src.shared.X.Y")` where `Y` has NO equivalent in `luana_core_X` (legacy test infra mock, distinct from Trigger #1 which covers production imports) → halt + ask Chris between (A) inline value, (B) lift to Story 14, (C) magic comment skip `# luana-migration-defer` + Story 14 ticket. See `03-arch-be.md §6` for concrete workflow.

### Feature 2 — FE imports rewrite + workspace member move

**Mechanic 1 (move):** `git mv AISALESHT/frontend/ luana-platform/nicolify/frontend/` (preserves git history via `git log --follow`). Architect Phase 0 spike: verify whether `git mv` across repos requires intermediate cherry-pick or filter-branch. Most likely 2-step (mv filesystem + commit in luana-platform with retroactive history reference via `--follow`).

**Mechanic 2 (workspace registration):** update `luana-platform/pnpm-workspace.yaml` to recognize `nicolify/frontend` member. Update `nicolify/frontend/package.json`:
- `"name": "@luana/nicolify-web"` (or per architect — open Q3 in spec §11)
- Add deps `"@luana/api-client": "workspace:*"`, `"@luana/ui-kit": "workspace:*"`, `"@luana/format": "workspace:*"`, `"@luana/hooks": "workspace:*"`, `"@luana/schemas": "workspace:*"`, `"@luana/design-tokens": "workspace:*"`
- Run `pnpm install` from luana-platform root → workspace symlinks resolve `@luana/X` to `core/@luana/X/`.

**Mechanic 3 (find/replace):** `jscodeshift` codemod (NOT sed — TS AST). Per-target script in `scripts/codemod_fe_imports.ts` (new — T-8 produces).

**Mapping summary:**

| Source (`@/...`) | Target (`@luana/...`) |
|---|---|
| `from "@/components/ui/X"` | `from "@luana/ui-kit/X"` |
| `from "@/lib/api/fetchClient"` | `from "@luana/api-client"` |
| `from "@/lib/format"` | `from "@luana/format"` |
| `from "@/hooks/useTenantLocale"` (etc.) | `from "@luana/hooks"` |
| `from "@/lib/zod-schemas/X"` | `from "@luana/schemas"` |
| `from "@/lib/tokens/X"` | `from "@luana/design-tokens/X"` |

**Stay local (NICOLIFY-specific — no rewrite):** `from "@/app/..."` (Next.js routes), `from "@/features/..."` (Nicolify business features), `from "@/stores/..."` (Nicolify-local Zustand), `from "@/components/shared/..."` (Nicolify layouts).

**Vercel reconfig (Halt Trigger #3):** root directory → `nicolify/frontend`, install command `pnpm install --filter @luana/nicolify-web... --frozen-lockfile` (workspace-aware), build command `pnpm --filter @luana/nicolify-web build`, env vars preserved (Clerk + DB + LiteLLM proxy), connected repo switched AISALESHT → alpacapurpura/luana-platform.

**CF tunnel `dev-app.nicolify.com` (Halt Trigger #4):** verify mapping survives Vercel reconfig. May require re-establishing cloudflared config pointing to new Vercel preview URL. Chris verifies post-reconfig (smoke E2E Feature 5 catches if broken).

### Feature 3 — Fresh `nicolify_dev` DB + alembic snapshot consolidation

**Strategy (Decisión 2B):** drop replay of 131 historical migrations; build clean `001_initial_snapshot.py` reflecting current schema state.

**Phase 0 spike (architect decides Q2 spec §11):** which yields fewer drift surprises:
- (A) Handcraft from `pg_dump --schema-only visionarias_logs` (precise but verbose)
- (B) `alembic revision --autogenerate` from luana-core models on empty DB (model-driven but may surface drift Scenario 3.2)

**Recommended (architect choice, justify in 03-arch-be.md §3):** **Hybrid path A+B.** Run autogenerate on empty DB → diff vs `pg_dump --schema-only` → consolidate into single raw-SQL migration with `IF NOT EXISTS` idempotency. If diff non-trivial → Halt Trigger #5, escalate Chris between (A) update models to match prod, (B) include diff in snapshot, (C) defer to Story 10b.

**Migration file pattern (idempotent raw SQL per `.claude/rules/backend-migrations.md`):**
```python
def upgrade():
    op.execute("CREATE TABLE IF NOT EXISTS tenants (...)")
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS X ...")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tenants_X ON tenants (X)")
    # ... all tables from pg_dump, transformed to IF NOT EXISTS pattern
```

**Fresh DB workflow (T-10 sequence):**
1. `pg_dump --schema-only -U postgres visionarias_logs > /tmp/aisaleshT_schema.sql` (audit trail)
2. Phase 0 spike: produce `001_initial_snapshot.py`
3. `psql -U postgres -c "CREATE DATABASE nicolify_dev;"`
4. Update env + `docker-compose.dev.yml` `POSTGRES_DB=nicolify_dev`
5. `docker exec postgres alembic upgrade head` (apply consolidated)
6. Verify: `pg_dump --schema-only nicolify_dev > /tmp/nicolify_schema.sql` + `diff` → minimal (acceptable cosmetic diff: column order, comments; intolerable: missing tables/columns/FKs/indexes)
7. Run BE test suite on `nicolify_dev` (delta=0 vs T-1 baseline)
8. Idempotency stress test: re-run `alembic upgrade head` (second run) → must succeed no-op (per Scenario 3.3 arch test)

**AISALESHT DB drop (T-14 closure — Scenario 8.2):** ONLY after smoke green Feature 5 + 24h soak elapsed + Chris explicit ratification. Sub-agent verifies preconditions before `DROP DATABASE visionarias_logs;`.

### Feature 4 — Test parity baseline + delta=0 enforcement

**T-1 ticket (FIRST — captures baseline BEFORE any rewrite):**
```bash
cd /home/chris/AISALESHT/backend
.venv/bin/pytest --json-report --json-report-file=docs/product/stories/luana-nicolify-migration/baseline-be-tests.json --tb=short

cd /home/chris/AISALESHT/frontend
npx vitest run --reporter=json --outputFile=docs/product/stories/luana-nicolify-migration/baseline-fe-tests.json
```

Commit both JSON files at T-1 as audit trail. Capture summary in T-1-result.md: "Baseline: BE N pass / M fail / K skip; FE N pass / M fail / K skip" — M includes 40 sales_agent pre-existing failures (Decisión 9B baseline acknowledged).

**T-N final delta check (after all rewrites):**
```bash
cd /home/chris/luana-platform/nicolify/backend
uv run pytest --json-report --json-report-file=/tmp/final-be-tests.json --tb=short

python scripts/test_delta_check.py \
    docs/product/stories/luana-nicolify-migration/baseline-be-tests.json \
    /tmp/final-be-tests.json \
    --max-new-failures=0
```

Script output format:
```
Baseline BE: N pass / M fail / K skip
Final BE:    N' pass / M' fail / K' skip
New failures (in final, not in baseline): []
Delta: 0 new failures ✓
```

If new failure detected → halt-and-ask Trigger #10 if 2 auto-fix iter fail. Story 10 does NOT merge with delta > 0.

**Fix-on-discovery 5min cap (Decisión 5B):** if rewrite encounters test failure with trivial fix (e.g., mock path stale, 5-line replace), apply inline in same commit. Document in T-N-impl-log.md `## Fix-on-discovery applied`. NO scope expansion (no refactors, no new tests, no logic change).

**DEFERRED-FAILURES-STORY-10.md** generated by T-N final ticket with 40 sales_agent pre-existing failure paths + Story 14 cross-reference. Auditor C5 verifies file exists + delta=0 honored.

### Feature 5 — Playwright smoke E2E (Chris journey)

**Spec location:** `nicolify/frontend/e2e/specs/smoke/chris-journey-e2e.spec.ts` (new — T-11 produces).

**9-step Chris journey (Scenario 5.1):**
1. Navigate `dev-app.nicolify.com` (Vercel + CF tunnel)
2. Signup new tenant (Clerk testing token via `playwright-expert` auth fixture)
3. Dashboard land
4. Brand Studio → fill basics (name, voice tone)
5. Offer Studio → create offer (basic preset)
6. Sales Agent → start conversation runtime (LLM call via `luana_core_sales_agent` + `luana_core_llm.router`)
7. Verify conversation response visible (within 30s timeout)
8. Verify cards rendered (copilot via `luana_core_copilot` path — plan_card or proposal_card)
9. Sign out

**Cost regression guard (Scenario 5.3 — Story PI-12 S1 T-1.bis lesson):** post-test DB query asserts `cost_usd > 0` in `copilot_llm_call` table (no NULL — LiteLLM canonicalization preserved post import rewrite). Test helper script reads from `nicolify_dev` DB via tenant_id of test tenant.

**Tenant isolation cross-leak adversarial (Scenario 5.4):** smoke creates T1 + T2 tenants, T1 creates "Offer A", T2 creates "Offer B", T2 visits offer list, asserts ONLY "Offer B" visible (auto-injection of `X-Tenant-ID` via `@luana/api-client` preserved post import rewrite).

**Auth fixture freshness gate (Scenario 5.2 — `playwright-expert` skill):** post FE workspace move, `playwright/.clerk/user.json` storage state at new path `luana-platform/nicolify/frontend/playwright/.clerk/`. If stale (>24h) → auto-regen via Clerk testing token. If path missing entirely → Halt Trigger #4.

**Execution:** native WSL `cd luana-platform/nicolify/frontend && E2E_BASE_URL=https://dev-app.nicolify.com npx playwright test --project=smoke chris-journey-e2e.spec.ts` (NEVER Docker `make e2e*` — crashes WSL2 OOM per `e2e-testing.md`).

### Feature 6 — `make ci-parity` root cross-brand

**Source:** `AISALESHT/Makefile::ci-parity` → `bash scripts/ci-parity.sh` (wrapper calling BE + FE gates).

**Target adaptation:**
```makefile
# luana-platform/Makefile
BRANDS := nicolify

ci-parity: $(BRANDS:%=ci-parity-%)
	@echo "✓ ci-parity all brands GREEN"

ci-parity-nicolify:
	bash scripts/ci-parity.sh --brand=nicolify

# Stories 11-13 append: BRANDS := nicolify vitalia comunify lupulo
```

Script `scripts/ci-parity.sh` migrates to `luana-platform/scripts/ci-parity.sh` with `--brand=<slug>` flag. Internally:
```bash
cd ${ROOT}/${BRAND}/backend && uv run ruff check src/ tests/ && uv run pytest tests/architecture/ -v && uv run pytest --cov=...
cd ${ROOT}/${BRAND}/frontend && pnpm exec tsc --noEmit && pnpm exec eslint src/ --cache && pnpm exec vitest run --coverage
```

**Pre-push hook:** `luana-platform/.husky/pre-push` invokes `make ci-parity` from root. Symlinks `.git/hooks/pre-push` per Story 9 `install-hooks` pattern.

**Halt Trigger #6 (env divergence):** tests pass locally but `make ci-parity` fails on env-specific (TZ, locale, env var presence). Sub-agent diagnoses + reports.

### Feature 7 — /pm SSoT atomic `git mv` (Phase 4 — at merge time)

**Atomic sequence (T-13):**
1. Snapshot pre-move: `tar czf /tmp/pre-move-snapshot.tar.gz docs/product/` (audit trail)
2. Verify scripts pre-move work: `cd AISALESHT && python scripts/generate_backlog.py --dry-run` + `python scripts/reconcile_capabilities.py --check` → both exit 0
3. `git mv AISALESHT/docs/product/ ...` (architect Phase 0 spike Q: across-repo strategy — likely 2-step: filesystem `mv` + commit deletion in AISALESHT + commit addition in luana-platform; `git log --follow` retains traceability in destination repo)
4. Also migrate `scripts/generate_backlog.py` + `scripts/reconcile_capabilities.py` + relevant Python tests to luana-platform/ (or per architect choice — could remain at root with relative `pathlib.Path(__file__).parents[N]` patterns)
5. Update `luana-platform/scripts/git-hooks/pre-commit` Sections 4-9 paths (downstream regression gate, voseo, backlog freshness, ruff, PII patterns)
6. Post-move verify: `cd luana-platform && python scripts/generate_backlog.py --check` + `python scripts/reconcile_capabilities.py --check` → both exit 0
7. Test pre-commit hook fires by touching `luana-platform/docs/product/BACKLOG.md` in a dummy commit (rollback)
8. Commit AISALESHT: `chore(pm-ssot): migrate to luana-platform — closure pre-archive`
9. Commit luana-platform: `feat(pm-ssot): receive /pm SSoT from AISALESHT — Phase 4 merge Story 10`

**Hardcoded path discovery (Halt Decisión 4A):** if any script/rule references `/home/chris/AISALESHT/docs/product/...` literal path → halt + report. Pre-move grep audit: `grep -rn "/home/chris/AISALESHT/docs/product" /home/chris/AISALESHT/scripts/ /home/chris/AISALESHT/.claude/`.

**Story 10 archive lands at `luana-platform/docs/archive/2026/stories/luana-nicolify-migration/`** (NOT AISALESHT — Feature 9 enforcement).

### Feature 8 — AISALESHT archive + DB drop closure

**T-14 (final closure ticket):**
1. **Pre-archive verify:** `cd AISALESHT && git status --short` → empty (Scenario 8.3 Halt Trigger #8 if uncommitted)
2. **AISALESHT pre-archive final commits:** closure docs only (impl logs migrated via Feature 7; AISALESHT `backend/src/` + `frontend/` REMOVED via prior commits during waves; final state per architect Phase 0 Q6 — empty repo OR README pointing to luana-platform)
3. **Chris manual step (or `gh api PATCH archived=true`):** GitHub Settings → AISALESHT → Danger Zone → Archive
4. **24h soak verification:** before DB drop, sub-agent checks timestamp delta ≥ 86400s since smoke green Feature 5 + Chris explicit ratification marker
5. **DB drop (Scenario 3.4 + 8.2):** `psql -U postgres -c "DROP DATABASE visionarias_logs;"` + `docker compose down` AISALESHT containers
6. **Audit trail:** T-14-impl-log.md captures all timestamps + Chris ratify markers

### Feature 9 — Story 10 archive at luana-platform location

**Standard `/pm` archival post-merge (per `/pm` skill template):**
```bash
cd /home/chris/luana-platform
git mv docs/product/stories/luana-nicolify-migration/ docs/archive/2026/stories/luana-nicolify-migration/
python scripts/generate_backlog.py  # regen BACKLOG reflects Story 10 done + outcome stories_done 10/14
python scripts/reconcile_capabilities.py
git commit -m "feat(luana-platform-migration): close Story 10 luana-nicolify-migration DONE + archive"
```

**HANDOFF-STORY-10B.md** generated at close (Decisión 10A) — Chris explicit request — captures:
- Scope Story 10b (Streamlit admin + workers ETL)
- Inherited decisions from §7.6 (AISALESHT archived, /pm SSoT in luana-platform, ci-parity root, etc.)
- Open decisions to re-ratify per session (Decisión 1A phased vs big bang, specific worker inclusions)
- Estimated complexity + ticket count
- DEFERRED-FAILURES-STORY-10.md cross-reference (40 sales_agent failures → Story 14 natural home)

## 3. High-level Wave sequence

> **Critical constraint:** cap ≤2 paralelo (Decisión 1A NOT 3). Each Wave's tickets execute sequentially OR in pairs (≤2 simultaneous sub-agents). Opus mayoritario crítico per opus_priority list.

```
T-1  BASELINE (must run FIRST, before any rewrite)
     - Capture pytest --json-report baseline (BE + FE)
     - Commit baseline-{be,fe}-tests.json to story dir
     - Create scripts/test_delta_check.py + new arch fitness tests (4 new)
     - Owner: builder-backend Sonnet
     - Time: ~2h
     - Blocking: ALL subsequent tickets

──────────────────────────────────────────────────────────────────────────

WAVE 1 — BE imports rewrite Wave A (Sonnet/Opus mixed, ≤2 paralelo)
     Goal: Rewrite NON-AGENTIC business modules + their tests.
     
T-2  brand + offer (BE imports rewrite)               [Opus 4.7 — cross-cuts shared]
     - Rewrite from src.modules.{brand,offer} → from luana_core_{brand_studio,offer_studio}
     - Rewrite test mocks
     - Run pytest tests/modules/{brand,offer}/ + arch fitness GREEN
     - Time: ~3h
     
T-3  landing + assets + connections + scheduling + iam + crm + commercial_calendar (sharded BE)  [Sonnet — mechanical, ≤2 paralelo with T-2]
     - Rewrite from src.modules.* → from luana_core_*
     - Rewrite test mocks
     - Time: ~3h
     
T-4  analytics + campaigns + social_proof + tenant_profile + tenant_domains + advertising + social_media (sharded BE)  [Sonnet — mechanical, after T-3]
     - Rewrite from src.modules.* → from luana_core_*
     - Verify make extraction-contract still GREEN (analytics ETL contract)
     - Time: ~3h

──────────────────────────────────────────────────────────────────────────

WAVE 2 — BE imports rewrite Wave B (Opus 4.7 — agentic + shared cross-cutting)
     Goal: Rewrite copilot + sales_agent + shared/* (cross-cutting).
     
T-5  copilot (BE imports rewrite)                     [Opus 4.7 — agentic R23]
     - Rewrite from src.modules.copilot → from luana_core_copilot
     - Preserve 22 frozen ratchet + 36/36 anchors
     - Verify module_registry convention pattern works post rename
     - Run tests/modules/copilot/ + arch fitness GREEN
     - Time: ~4h
     
T-6  sales_agent (BE imports rewrite)                 [Opus 4.7 — agentic R23, parallel with T-5 ≤2 cap]
     - Rewrite from src.modules.sales_agent → from luana_core_sales_agent
     - Preserve §3 NO TOUCH surfaces (Closer Studio, SmartBufferService, OutputManager chunking, enrollment_*)
     - 40 pre-existing failures DEFERRED (delta=0 enforced — these were FAIL in baseline T-1)
     - Time: ~4h
     
T-7  shared/* cross-cutting (sharded by subsystem)    [Opus 4.7 — high cross-coupling risk]
     - Rewrite from src.shared.{agent_observability,events,domain_events,billing,compliance,idempotency,infrastructure.llm,application.extraction,api,application,domain,links,workers} → from luana_core_*
     - Sub-shard by subsystem (one at a time — 11 subsystems, ≤2 paralelo)
     - Cross-check: NO mirror cross-module created (per anti-duplication.md cardinal §0)
     - Time: ~6h total

──────────────────────────────────────────────────────────────────────────

WAVE 3 — FE workspace move + DB consolidation (Opus 4.7 + Sonnet)
     Goal: Frontend lives in luana-platform. Fresh DB.

T-8  FE git mv + workspace registration + imports rewrite  [Opus 4.7 — Vercel reconfig criticality]
     - git mv AISALESHT/frontend/ → luana-platform/nicolify/frontend/
     - Update pnpm-workspace.yaml + package.json deps
     - jscodeshift codemod @/components/ui → @luana/ui-kit (etc.)
     - pnpm install + tsc + eslint + vitest GREEN
     - Time: ~4h
     
T-9  Vercel reconfig + CF tunnel verify           [Opus 4.7 — Halt Triggers #3 + #4]
     - Vercel Settings → switch repo + root dir + build commands
     - Verify env vars preserved
     - Test dev-app.nicolify.com resolves
     - Time: ~2h (mostly Chris/manual UI steps, Claude documents + verifies)

T-10 Fresh nicolify_dev DB + alembic consolidation  [Opus 4.7 — Halt Trigger #5 high risk]
     - pg_dump --schema-only visionarias_logs
     - Phase 0 spike resolution: hybrid pg_dump + alembic autogenerate → consolidated 001_initial_snapshot.py
     - psql CREATE DATABASE nicolify_dev
     - alembic upgrade head + idempotency stress test
     - Run BE pytest on nicolify_dev → delta=0 vs baseline
     - Time: ~4h

──────────────────────────────────────────────────────────────────────────

WAVE 4 — Smoke E2E + CI parity (Sonnet)

T-11 Playwright smoke E2E Chris journey            [Sonnet — playwright-expert SSoT]
     - Create nicolify/frontend/e2e/specs/smoke/chris-journey-e2e.spec.ts
     - 9-step journey + cost regression guard + tenant isolation cross-leak
     - Native WSL execution
     - Time: ~3h
     
T-12 Make ci-parity root migration                  [Sonnet — mechanical]
     - Migrate scripts/ci-parity.sh → luana-platform/scripts/ + --brand= flag
     - Update Makefile root with BRANDS pattern
     - Update .husky/pre-push hook
     - Run make ci-parity from root → GREEN
     - Time: ~2h

──────────────────────────────────────────────────────────────────────────

WAVE 5 — Closure (Opus + Sonnet)

T-13 /pm SSoT atomic git mv Phase 4 merge          [Opus 4.7 — Halt Decisión 4A]
     - Snapshot tar.gz pre-move
     - Verify scripts pre-move
     - git mv docs/product/ across repos
     - Update pre-commit hooks paths
     - Post-move verify scripts + hooks GREEN
     - Time: ~2h
     
T-14 AISALESHT archive + DB drop + Story 10 archive  [Sonnet — mechanical closure]
     - Pre-archive verify clean tree
     - DEFERRED-FAILURES-STORY-10.md generation
     - HANDOFF-STORY-10B.md generation
     - GitHub Settings archive (Chris manual or gh api)
     - 24h soak + DB drop psql
     - Story 10 archive at luana-platform/docs/archive/
     - generate_backlog.py + reconcile_capabilities.py regen
     - Time: ~2h

──────────────────────────────────────────────────────────────────────────

T-N FINAL delta check (gate before review/merge)
     - Full pytest + vitest run from luana-platform
     - scripts/test_delta_check.py --max-new-failures=0
     - If GREEN → state transitions developing → developed (auditor next)
     - If RED + 2 auto-fix iter fail → Halt Trigger #10 escalate Chris
```

**Total estimated time:** ~40-44h sub-agent execution (cap ≤2 paralelo). Wall-clock with parallelization ≈ 20-25h. Cost target: <$5000 sesión (R12 metric soft check-ins at $4000/$4500/$5000).

## 4. Cross-cutting invariants preservation

All preserved post import rewrite (mechanical migration — zero new business logic per Decisión 1A scope clarification):

- **Tenant isolation** — every query `.where(Model.tenant_id == tenant_id)` preserved (`shared/links/ports/` paths rewritten to `luana_core_*.links.ports`). Smoke Scenario 5.4 adversarial verifies. Arch fitness `test_tenant_isolation.py` preserved.
- **Soft deletes** — `deleted_at` patterns preserved. Arch fitness `test_no_hard_deletes.py` preserved.
- **SQLA 2.0 only** — `select(Model).where(...)` preserved. Arch fitness `test_no_sql_alchemy_1x.py` preserved.
- **Pydantic v2** — `ConfigDict(from_attributes=True)` preserved.
- **`response_model=` mandatory** — every route. Arch fitness `test_response_model_required.py` preserved.
- **`FastAPI(redirect_slashes=False)`** — preserved in main.py post rewrite.
- **Currency from data source** — `currency: str | None` DTOs preserved. ETL keeps source currency. FE `formatMoney(amount, currency)` preserved post FE workspace move.
- **Master data** — `DateTime(timezone=True)` + UTC storage + `useTenantLocale()` FE preserved.
- **Spanish neutro LatAm** — UI strings + schemas + prompts preserved. Pre-commit hook Section 5 (voseo) fires on luana-platform post Feature 7. (Exception: sales_agent output respects tenant voice — preserved.)
- **PII sanitization** — `response_model=` allowlist + `sanitize_payload` preserved. Tessl pii-sanitisation rule fires on `luana_core_*` packages.
- **Native-first dev** — lint/tests native WSL (NEVER `docker exec ruff/pytest/tsc/vitest`). `make ci-parity` runs natively.
- **`structlog` only** — no `print`/`logging` introduced.
- **Idempotency on writes** — POST/PUT idempotency keys preserved.

## 5. Risks + mitigations summary

> **Detailed risk register lives in spec §10 (14 risks).** This section abstracts top 5 + new arch-level risks discovered during architect Phase 0 spike.

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| 1 | Import rewrite ~20k LOC silent codemod errors | High | `libcst` AST-based (NOT sed). Test mocks rewrite same step. Arch fitness `test_no_legacy_src_paths.py` + `test_no_legacy_src_mock_paths.py` block regression. Cap ≤2 paralelo. Auditor C2 grep audit cumulative. |
| 2 | Alembic model↔DB drift Scenario 3.2 | Medium-High | Phase 0 hybrid spike (pg_dump + autogenerate diff). Halt Trigger #5. Architect 03-arch-be.md §3 documents exact diff resolution workflow. |
| 3 | Vercel reconfig + CF tunnel surprise | Medium-High | Halt Triggers #3 + #4. Chris executes UI steps. Smoke E2E Feature 5 catches if broken end-to-end. |
| 4 | Test mocks stale paths cause silent test pass | High (silent fail) | New arch fitness `test_no_legacy_src_mock_paths.py`. Halt Trigger #11 distinct from #1. Auditor C5 cross-cutting check. |
| 5 | /pm SSoT migration hardcoded paths Decisión 4A | Medium | Pre-move grep audit `grep -rn "/home/chris/AISALESHT/docs/product"` in scripts + rules. Halt path documented in 03-arch-be.md §5. |
| 6 (NEW arch) | Cross-package re-export drift (legacy `src.shared.X` exported some helper that `luana_core_X` does NOT re-export — Story 14 deferred) | Medium | Halt Trigger #1 (production) + Trigger #11 (test infra). Auditor verifies missing-export count documented + Story 14 ticket queue. |
| 7 (NEW arch) | `module_registry` convention pattern post rename (copilot discovery `src.modules.{name}.copilot_provider:provider` → `luana_core_X.copilot_provider:provider`) | Medium-High | Architect verifies Story 6 luana-core-copilot preserved convention (Phase 0 spike: read `core/luana-core-copilot/src/luana_core_copilot/registry/module_registry.py` line-by-line). If convention changed in Story 6, T-5 rewrites pattern. Halt Trigger #1 if registry breakage. |
| 8 (NEW arch) | `BaseAgentCallbackHandler` subclass `SalesAgentCallbackHandler` import path `from src.shared.agent_observability.recording.base_callback_handler` → `from luana_core_observability.recording.base_callback_handler` + the subclass lives in `luana_core_sales_agent.observability.recording.callback_handler` — verify both packages' tests don't double-mock | Medium | Per `.claude/rules/anti-duplication.md` § "Surfaces compartidas con copilot" — both modules consume shared via subclass. Imports rewrite preserves inheritance chain. Arch fitness `test_no_mirror_*` preserved. |

## 6. Files in scope (high-level — exact line ranges in 03-arch-be.md + 05-guidelines.md)

**MODIFIED (rewrite imports):**
- `backend/src/modules/{brand,offer,landing,assets,connections,scheduling,iam,crm,commercial_calendar,analytics,campaigns,social_proof,tenant_profile,tenant_domains,advertising,social_media,copilot,sales_agent}/**/*.py` (~852 files)
- `backend/src/shared/{agent_observability,events,domain_events,billing,compliance,idempotency,infrastructure,application,api,domain,links,workers}/**/*.py` (~114 files)
- `backend/tests/modules/**/*.py` (test mocks — count via T-1 baseline grep)
- `frontend/src/**/*.{ts,tsx}` (~847 files with `@/...` imports)
- `frontend/package.json` (workspace deps + name)
- `frontend/playwright.config.ts` + `frontend/e2e/` (move paths)
- `Makefile` (root → relocate ci-parity to luana-platform/Makefile)
- `scripts/ci-parity.sh` (move + add `--brand=` flag)
- `scripts/git-hooks/{pre-commit,pre-push}` (move + paths update)

**NEW (architect emits via T-1):**
- `scripts/test_delta_check.py` (Python script — parses pytest --json-report + vitest --reporter=json, computes delta)
- `scripts/codemod_be_imports.py` (libcst AST-based codemod per package)
- `scripts/codemod_fe_imports.ts` (jscodeshift codemod for FE)
- `tests/architecture/test_no_legacy_src_paths.py` (BE arch fitness)
- `tests/architecture/test_no_legacy_src_mock_paths.py` (BE arch fitness)
- `tests/architecture/test_consolidated_migration_idempotent.py` (BE arch fitness)
- `tests/architecture/test_delta_zero_enforcement.py` (BE arch fitness — parses baseline JSON files)
- `frontend/e2e/specs/smoke/chris-journey-e2e.spec.ts` (Playwright spec)
- `docs/product/stories/luana-nicolify-migration/baseline-{be,fe}-tests.json` (audit trail)
- `docs/product/stories/luana-nicolify-migration/DEFERRED-FAILURES-STORY-10.md` (T-N final)
- `docs/product/stories/luana-nicolify-migration/HANDOFF-STORY-10B.md` (T-14 final)

**MOVED (`git mv` Feature 7):**
- `docs/product/` → `luana-platform/docs/product/` (atomic Phase 4)
- `scripts/generate_backlog.py` + `scripts/reconcile_capabilities.py` → `luana-platform/scripts/` (or relative-path strategy per Phase 0 Q7)
- `scripts/emit_process_metric.py` (R12 layer 1) → `luana-platform/scripts/`
- (BE+FE source already moved via Waves 1-3 to `luana-platform/nicolify/{backend,frontend}/`)

**OUT OF SCOPE (DEFERRED Stories 10b/14):**
- `backend/src/admin/` (Streamlit — Story 10b)
- `backend/src/workers/` + per-module `workers/` (Story 10b/14)
- 40 sales_agent pre-existing failures (Story 14 brand-voice-elevation)
- Vitalia/Comunify/Lupulo brand dirs (Stories 11-13)

## 7. Architect Phase 0 spike resolutions (Open Questions spec §11)

| Q# | Question | Architect resolution |
|---|---|---|
| 1 | Codemod tool BE | **libcst** (Python AST-based — preserves nested imports, comments, formatting). Reject sed (regex-prone errors on nested imports, type annotations like `dict[str, "src.shared.X"]`). |
| 2 | Consolidated migration strategy | **Hybrid pg_dump + alembic autogenerate** with diff resolution per Halt Trigger #5. Documented exact diff workflow 03-arch-be.md §3. |
| 3 | FE workspace nesting | **`nicolify/frontend/` nested** (NOT replacing `nicolify/` stub). Preserves `nicolify/backend/` parallel + clean separation. `package.json` `"name": "@luana/nicolify-web"`. |
| 4 | Vercel build command | **Workspace-aware** `pnpm install --filter @luana/nicolify-web... --frozen-lockfile` + `pnpm --filter @luana/nicolify-web build`. Verify in Vercel monorepo support docs at reconfig time. |
| 5 | CF tunnel re-mapping | **Keep existing tunnel** pointing to new Vercel preview URL (re-point not re-create). Chris verifies via `curl -I https://dev-app.nicolify.com/` post-reconfig. |
| 6 | AISALESHT pre-archive final state | **Skeleton README** pointing to luana-platform (NOT empty repo). Preserves `git clone` user discoverability of new home. README contains migration notice + dates + links. |
| 7 | Pre-commit hook migration | Sections 4-9 paths updated: voseo glosario at `luana-platform/.claude/rules/spanish-text.md`, ruff at `luana-platform/nicolify/backend/.venv/`, PII patterns at `luana-platform/nicolify/backend/scripts/_pii_patterns.py` (or shared per anti-duplication §11 inventory if existing in luana-core). Architect verifies _pii_patterns lifted to luana-core or stays nicolify-local during T-13. |
| 8 | Test delta script path | **`luana-platform/scripts/test_delta_check.py`** (cross-brand tool). Stories 11-13 inherit. |
| 9 | Story 10 archive timing | **At end of Session 5** — Story 10 transitions to `done` post T-14 closure. Archive at `luana-platform/docs/archive/2026/stories/luana-nicolify-migration/`. NOT partial close. |
| 10 | Workers tactical inclusion | **NONE** — all workers DEFERRED Story 10b. Architect Phase 0 spike confirms `backend/src/workers/` is 2 files (`__init__.py`, `settings.py`) but per-module workers subdirs vary. Safest: full defer. Sub-agent during T-7 may encounter `from src.workers.X` import in shared/ → halt + escalate per Halt Trigger #1. |

## 8. Phase ratification + next steps

- **Architect emits Part 1 (this doc + 03-arch-be.md + 05-guidelines.md)** — Chris reads/ratifies wording at refined→ready transition.
- **Architect emits Part 2 (04-validators.yaml + 06-tickets.yaml)** — separate spawn after Part 1 ratified.
- Post Part 1 + Part 2 ratification: checkpoint state=refined → ready. `/dev-team` picks up.
- `/dev-team` Session 5 autonomous build picks Story 10 sequential per Decisión 10A + cap ≤2 paralelo Decisión 1A.
- Auditor Story 10 post developed → reviewing → CHECKPOINTS C1-C5 (auditor-{backend,frontend} sub-spawn per surface mapping §0.1).
- /pm merge Story 10 → outcome stories_done = 10/14 → Stories 10b + 11-14 unblocked per cross-story handoff spec §13.

## 9. References

- `01-spec.md` — 9 features × 4 scenarios = 36 Gherkin (BINDING)
- `03-arch-be.md` — BE deep dive (package-by-package codemod map, alembic consolidation, fresh DB, Trigger #11 workflow)
- `05-guidelines.md` — patterns required/forbidden + files in scope + sub-agent skills loading
- `docs/product/outcomes/luana-platform-migration.md` §7.6 (binding) + §7.6.2 (11 triggers) + §7.6.3 (success criteria) + §7.6.1 (cross-story inheritance)
- `/home/chris/luana-platform/docs/migration-from-nicolify.md` §3 (canonical import mapping)
- `docs/archive/2026/stories/luana-v0-1-0-publish/03-arch-be.md` (Story 9 precedent — 26 Python packages + 7 TS workspace member pattern)
- `.claude/rules/{anti-duplication,backend-ddd,backend-migrations,tenant-isolation,tdd-mandatory,parallel-safety,git-safety,e2e-testing,spanish-text}.md`
- `.claude/skills/{backend-expert,frontend-expert,copilot-expert,sales-agent-expert,brand-expert,offer-expert,metrics-expert,playwright-expert,tessl__langgraph,tessl__fastapi,tessl__graceful-degradation}/SKILL.md`

## 10. Research notes (state-of-the-art as of 2026-05-12)

> Knowledge cutoff Jan 2026 (Opus 4.7); arch decisions verified live via local file reads + reference docs on 2026-05-12.

- **`libcst` for Python AST codemods (verified 2026-05-12 via local familiarity):** AST-based, preserves comments + formatting + nested imports. Used by Meta + Instagram for large-scale refactors. Alternative `bowler` (Facebook, older) deprecated. Alternative `rope` (refactoring lib) heavier API. Choice for T-2..T-7 BE codemods: **libcst**. Cite: https://libcst.readthedocs.io/ (accessed 2026-05-12).
- **`jscodeshift` for TS AST codemods (verified 2026-05-12):** Facebook/Meta AST-based for JS/TS. Used by Next.js codemods (`@next/codemod`). Preserves type annotations. Choice for T-8 FE codemod: **jscodeshift** + custom transformer. Cite: https://github.com/facebook/jscodeshift (accessed 2026-05-12).
- **uv workspace + pnpm workspace monorepo patterns (verified via `~/luana-platform/pyproject.toml` + `pnpm-workspace.yaml` local read 2026-05-12):** Story 9 cemented `[tool.uv.workspace] members = [...]` with 26 Python + brand stubs. `pnpm-workspace.yaml packages: [core, core/@luana/*, nicolify, vitalia, ...]` cemented 7 TS packages. Story 10 extends `nicolify/frontend` as nested workspace member.
- **`alembic revision --autogenerate` strategy (verified via local familiarity + `.claude/rules/backend-migrations.md`):** standard pattern is `op.create_table(...)` but project rule MANDATES raw SQL `IF NOT EXISTS` for idempotency. Architect's hybrid approach: autogenerate → manually transform `op.create_table` → `op.execute("CREATE TABLE IF NOT EXISTS ...")`. Tested via Scenario 3.3 idempotency stress (re-run = no-op).
- **Vercel monorepo support (verified 2026-05-12 via Vercel docs — accessed live):** root directory + install command + build command override per project. Workspace-aware pnpm commands via `--filter @scope/pkg... --frozen-lockfile`. Confirmed via Vercel "Monorepos with pnpm" guide. URL: https://vercel.com/docs/monorepos/pnpm (accessed 2026-05-12, anchor at section "Build Command").
- **GitHub repo archive API (verified 2026-05-12):** `gh api repos/{owner}/{repo} --method PATCH -f archived=true` programmatic; UI path Settings → Danger Zone → Archive equivalent. Reversible 1-click. URL: https://docs.github.com/en/repositories/archiving-a-github-repository (accessed 2026-05-12).
- **Playwright + Clerk auth (verified via `playwright-expert` skill SSoT references 2026-05-12):** auth fixture `playwright/.clerk/user.json` storage state file pattern. Freshness gate auto-regens via Clerk testing token. Native WSL execution mandatory (Docker crashes). Cite: `.claude/skills/playwright-expert/SKILL.md` + `references/clerk-auth-deep-dive.md`.

## 11. Open questions for PM (none — Architect Phase 0 spike resolved all 10 spec §11 questions per §7 above)

> All architect-Phase-0 questions resolved in §7. No open questions for PM. Halt-and-ask triggers per §7.6.2 + §0 binding decisions apply at build phase.

If sub-agent during build hits a question NOT covered by §7.6 (10 binding) + §7.6.1 (5 cross-story inheritance defaults) + §7.6.2 (11 halt triggers) + §7 above (10 architect Phase 0 spike resolutions) → escalate Chris per §7.6.2 #1 (coupling oculto no documentado outcome §2 dependencies).
