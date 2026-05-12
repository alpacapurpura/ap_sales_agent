<!-- voseo-allowed: spec references rules + glossary verbatim for traceability per R25 -->
---
story_id: luana-nicolify-migration
type: service-story
module: luana-platform (cross-package consumer migration — Nicolify is first vertical brand)
capability: luana-core/brand-consumer-migration
po_version: 1
spec_version: 1
drafted_by: /po Opus (claude-opus-4-7-1m)
drafted_at: 2026-05-12
last_modified: 2026-05-12
ratified_by_chris: false                           # ★ Pre-ratified via §7.6 10 binding decisions; spec elaborates only — Chris reads + ratifies wording ★
binding_decisions_ref: docs/product/outcomes/luana-platform-migration.md §7.6 (10 decisions ratified Session 5 Phase 0 2026-05-12)
halt_and_ask_triggers_ref: docs/product/outcomes/luana-platform-migration.md §7.6.2 (10 triggers)
success_criteria_ref: docs/product/outcomes/luana-platform-migration.md §7.6.3 (10 done criteria)
links:
  story_md: "00-story.md"
  checkpoint: "checkpoint.md"
  outcome: "../../outcomes/luana-platform-migration.md"
  story_9_merge: "../../../archive/2026/stories/luana-v0-1-0-publish/07-merge.md"
  story_9_spec: "../../../archive/2026/stories/luana-v0-1-0-publish/01-spec.md"
  migration_guide: "/home/chris/luana-platform/docs/migration-from-nicolify.md"
---

# 01-spec — Story 10: Migrate Nicolify to consume Luana Platform v0.1.0

## 1. Outcome alignment

Story 10 es la **pivot story** del outcome `luana-platform-migration` (posición 10/14 del DAG). Cierra el ciclo entre **Stories 1-9 (Luana Platform v0.1.0 publishable)** y **Stories 11-14 (verticals Vitalia + Comunify + Lupulo + brand-voice-elevation)**. Nicolify se convierte en el **primer consumer real** del Luana v0.1.0 release pipeline — valida end-to-end que la arquitectura monorepo + Extension SDK + 33 packages publicados sirve para producir un brand vertical funcional sin regresión.

Story 10 desbloquea:
- Stories 11-13 (verticals nuevos) — heredan precedente migración (§7.6.1 inheritance matrix)
- Story 14 brand-voice-elevation — toca sales_agent surface natural fix de las 40 PRE-EXISTING failures deferred aquí (Decisión 9B)

**10 business decisions ratificadas Chris Session 5 Phase 0 (binding, no requieren re-ratify mid-spec):**

| # | Decisión | Implicancia spec |
|---|---|---|
| 1 | Full big bang scope (BE+FE+tests+smoke E2E) | Single story cover 9 surfaces (§3). Sub-agent decomposition smart blast radius. Cap ≤2 paralelo. Opus para imports rewrite + schema consolidation + /pm SSoT migration + Vercel reconfig. |
| 2 | Fresh `nicolify` DB + alembic snapshot consolidation | T-N consolida 131 alembic migrations en `001_initial_snapshot.py`. Drop `visionarias_logs` DB al cierre Story 10 post-smoke green + 24h soak. |
| 3 | Archive AISALESHT read-only post-Story-10 | GitHub Settings → Archive UI. Reversible 1-click. History accesible. |
| 4 | /pm SSoT atómico `git mv` durante Fase 4 | `docs/product/` → `luana-platform/docs/product/`. Verify scripts `generate_backlog.py` + `reconcile_capabilities.py` + pre-commit hooks Section 4-6 corren post-move sin path hardcoded breakage. Halt si Claude descubre path hardcoded raro. |
| 5 | Match baseline + fix-on-discovery trivial only (delta=0) | T-1 captura baseline `pytest --json-report` BE + `vitest --reporter=json` FE. T-N final delta=0 new failures enforcement. 40 sales_agent failures DEFERRED-FAILURES-STORY-10.md → Story 14. Fix-on-discovery 5min cap only. |
| 6 | FE workspace member luana-platform monorepo | `git mv AISALESHT/frontend/ → luana-platform/nicolify/frontend/`. `pnpm-workspace.yaml` add member. `package.json` `"@luana/X": "workspace:*"`. Find/replace imports `@/components/ui` → `@luana/ui-kit`. Vercel reconfig root directory → `nicolify/frontend/`. CF tunnel `dev-app.nicolify.com` preserved. |
| 7 | Streamlit admin defer Story 10b | Admin Streamlit (`backend/src/admin/`) NO migra Story 10. Escape hatch architect: si trivial (3-5 archivos clean) puede incluir con halt-and-ask Chris. Default: deferred Story 10b. |
| 8 | CI parity root cross-brand | `make ci-parity` se mueve de `AISALESHT/Makefile` → `luana-platform/Makefile` (root). Stories 11-13 heredan automático. Pre-push hook apunta a root. |
| 9 | Defer 40 sales_agent failures Story 14 | DEFERRED-FAILURES-STORY-10.md generated T-N final con paths exactos. Auditor verifica delta=0 sin tocar estos 40. |
| 10 | Pre-auth scope Sesión 5 = Story 10 solo | Stories 10b/11-14 awaiting per-session ratification. Handoff prompt Story 10b generated at close. |

**Halt-and-ask triggers cardinales** (§7.6.2 — paraliza + escala Chris si reproduce):
1. Coupling oculto cross-module no documentado en outcome §2
2. Builder import rewrite descubre cross-module dependency a módulo en grupo Wave DIFERENTE (sharded disjoint violation)
3. Vercel reconfig surface unexpected issue (custom domain, env vars, secrets, build config)
4. CF tunnel `dev-app.nicolify.com` mapping rompe post-FE-move
5. Alembic snapshot consolidation surface schema inconsistency (model definitions ≠ DB state)
6. Tests pass locally pero ci-parity root falla (env divergence)
7. Pipeline release-please primer execution falla post-migration (orthogonal Story 9)
8. luana-platform monorepo state inesperado (uncommitted changes, branch mismatch)
9. Cumulative cost sesión > $5000 (soft check-in, continuar pero report)
10. Auditor + 2 auto-fix iter all fail → escalate (no 3rd iter sin Chris)

## 2. Resumen ejecutivo

Story 10 ejecuta **migración mecánica big bang** del codebase Nicolify (AISALESHT) para consumir Luana Platform v0.1.0. NO toca business logic — solo:

1. **BE imports rewrite** — 26 packages target. `from src.shared.X` / `from src.modules.X` → `from luana_core_X`. ~20k LOC affected. Mapping completo en `~/luana-platform/docs/migration-from-nicolify.md §3` (Story 9 deliverable, consumer guide).
2. **FE imports rewrite** — `@/components/ui` → `@luana/ui-kit`, `@/lib/format` → `@luana/format`, `@/hooks/...` → `@luana/hooks`, `@/lib/api-client` → `@luana/api-client`, `@/lib/zod-schemas/...` → `@luana/schemas`.
3. **FE workspace member move** — `git mv AISALESHT/frontend/ → luana-platform/nicolify/frontend/`. Add to `pnpm-workspace.yaml`. Update `package.json` deps to `"@luana/X": "workspace:*"`. Vercel reconfig root directory → `nicolify/frontend/`. Preserve CF tunnel `dev-app.nicolify.com`.
4. **Fresh `nicolify` DB + alembic snapshot consolidation** — Create `nicolify_dev` Postgres DB. Consolidate 131 migrations (`AISALESHT/backend/alembic/versions/`) → `001_initial_snapshot.py` reflecting current schema. Update env vars + `docker-compose.dev.yml` `POSTGRES_DB=nicolify`. Drop `visionarias_logs` AISALESHT DB at close post-smoke green + 24h soak.
5. **Test parity baseline + delta=0** — T-1 capture baseline (`pytest --json-report` + `vitest --reporter=json`) BEFORE any rewrite. T-N final delta=0 new failures enforcement.
6. **Playwright smoke E2E** — Chris journey end-to-end through nicolify app (signup → brand setup → offer creation → sales_agent runtime conversation).
7. **CI parity root cross-brand** — `make ci-parity` moves to `luana-platform/Makefile`. Pre-push hook updated.
8. **/pm SSoT atomic migration** — `git mv AISALESHT/docs/product/ → luana-platform/docs/product/` Fase 4 merge. Verify scripts run post-move sin path hardcoded breakage.
9. **AISALESHT archive + DB drop** — GitHub Settings → Archive AISALESHT. Postgres drop `visionarias_logs` post-smoke green + 24h soak verification.
10. **Story 10 archive location** — `luana-platform/docs/archive/2026/stories/luana-nicolify-migration/` (NEW SSoT post-Fase-4 migration).

**Halt criterion cardinal:** si Claude detecta CUALQUIERA de los 10 triggers §7.6.2 — paraliza + escala Chris. No proceed sin ratificación.

## 3. Inventario pre-Story-10 (estado workspace)

### 3.1 AISALESHT backend (`/home/chris/AISALESHT/backend/src/`)

| Path | Contenido | Story 10 action |
|---|---|---|
| `modules/{brand,offer,landing,assets,analytics,advertising,social_media,sales_agent,scheduling,connections,copilot,iam,crm,campaigns,commercial_calendar,social_proof,tenant_domains,tenant_profile}/` | 18 business modules DDD (domain + infrastructure + application + api) | Migration consumer: rewrite imports to luana-core-* equivalents. NO touch business code. |
| `shared/{agent_observability,api,application,billing,compliance,domain,domain_events,idempotency,infrastructure,links,workers}/` | 11 shared subsystems | Same — rewrite imports to luana_core_* equivalents. |
| `admin/` | Streamlit admin panel | **DEFERRED Story 10b** (Decisión 7B). NO touch Story 10 default. |
| `workers/` (root + per-module workers/) | Celery/asyncio workers (ETL scheduler, etc.) | **DEFERRED Story 10b/14** if non-trivial. Architect escape hatch (Decisión 1A clarification — workers + admin diferidos). |
| `alembic/versions/` (131 migrations) | DB schema history | Consolidate → `001_initial_snapshot.py` in new nicolify repo. |

### 3.2 AISALESHT frontend (`/home/chris/AISALESHT/frontend/`)

| Path | Contenido | Story 10 action |
|---|---|---|
| `src/{app,components/{ui,shared},features/{domain},lib,hooks}/` | Next.js 16 App Router + React 19 + FSD-Lite | `git mv` to `luana-platform/nicolify/frontend/`. Find/replace imports. |
| `package.json` | Dependencies `"@/components/ui"` references, deps | Add `"@luana/X": "workspace:*"` deps. Rename `"name": "@luana/nicolify-web"` (or per architect decision). |
| `playwright.config.ts` + `e2e/` | E2E suites + Clerk auth fixture | Move with FE. Update `E2E_BASE_URL` if applicable. |
| `eslint.config.mjs` + `tsconfig.json` | Lint + TS config | Move with FE. Verify boundaries plugin recognizes new luana-platform paths. |

### 3.3 AISALESHT DB current state

| Property | Value |
|---|---|
| Container | `visionarias_postgres_dev` |
| DB name | `visionarias_logs` (per `.env.example` `POSTGRES_DB`) |
| Alembic migrations | 131 versions in `backend/alembic/versions/` |
| Current revision | (architect verifica via `alembic current`) |
| Schema state | Current Story 10 baseline — extracted via `pg_dump --schema-only` |

### 3.4 luana-platform state (post Stories 1-9 merge 2026-05-12)

| Path | Contenido | Story 10 consumer |
|---|---|---|
| `core/luana-core-{26 packages}/` | 26 Python packages at v0.1.0 (Story 9 published) | Replace `src.shared.X` + `src.modules.X` imports in nicolify BE. |
| `core/@luana/{api-client,design-tokens,extension-sdk,format,hooks,schemas,ui-kit}/` | 7 TS packages at v0.1.0 | Replace `@/...` imports in nicolify FE. |
| `nicolify/` (stub) | Placeholder workspace member (`package.json` + `pyproject.toml` + `src/` + `tests/`) | **REPLACE** with full AISALESHT FE + BE migration target. |
| `docs/migration-from-nicolify.md` (§1-§6) | Consumer migration guide (Story 9 deliverable) | Primary reference for import mapping. |
| `pnpm-workspace.yaml` | `packages: [core, core/@luana/*, nicolify, vitalia, comunify, lupulo]` | Verify `nicolify` member exists + expand to include `nicolify/frontend/` workspace path. |
| `pyproject.toml` (root) | `[tool.uv.workspace]` members 26 packages + apps/test-brand | Add nicolify BE workspace member if applicable. |
| `Makefile` (root) | Story 9 placeholder (lint, test, build basics) | Add `make ci-parity` target migrated from AISALESHT/Makefile. |

### 3.5 /pm SSoT current location (`/home/chris/AISALESHT/docs/product/`)

| Subdir | Contenido | Story 10 action |
|---|---|---|
| `BACKLOG.{yaml,md}` + `BACKLOG-TLDR.md` | Auto-generated SSoT via `scripts/generate_backlog.py` (R33) | `git mv` to `luana-platform/docs/product/`. Re-run script post-move verify GREEN. |
| `outcomes/` (4 outcomes) | luana-platform-migration + 3 others | Move atomic. |
| `stories/` (refining + parked + done) | Stories 10b + 11-14 + Story 10 itself + others | Move atomic. Story 10 archive lands at `luana-platform/docs/archive/2026/stories/luana-nicolify-migration/`. |
| `capabilities/{module}/` | Capability YAMLs (R32 reconcile) | Move atomic. Re-run `scripts/reconcile_capabilities.py` post-move verify GREEN. |
| `modules/` | Module narratives | Move atomic. |
| `ideas-pool.yaml` | Ideas pool | Move atomic. |
| `vision.md`, `glossary.md`, `story-map/backbone.md` | Vision docs | Move atomic. |

### 3.6 Pre-commit hooks state (`scripts/git-hooks/pre-commit`)

| Section | Function | Story 10 verify |
|---|---|---|
| Section 4 | Downstream regression freshness gate (R21) | Path references survive `git mv` (relative paths within `docs/`) |
| Section 5 | Voseo enforcement (R25) | Same |
| Section 6 | Backlog freshness (R33) — auto-regen on commit | Re-test after `/pm` SSoT migration |
| Section 7 | Ruff (native, backend venv) | Path to `backend/.venv/` survives — verify |
| Section 8-9 | PII patterns (Story D) | Path to `_pii_patterns.py` — verify |

## 4. Scope (in + out)

### 4.1 IN SCOPE Story 10 (9 surfaces — features 1-9 §5 below)

1. ✅ BE imports rewrite (26 packages target)
2. ✅ FE imports rewrite + workspace member move
3. ✅ Fresh `nicolify_dev` DB + alembic snapshot consolidation
4. ✅ Test parity baseline + delta=0 enforcement
5. ✅ Playwright smoke E2E (Chris journey end-to-end)
6. ✅ CI parity root cross-brand (`make ci-parity` migrates)
7. ✅ /pm SSoT atomic migration Fase 4
8. ✅ AISALESHT archive + DB drop closure
9. ✅ Story 10 archive at new SSoT location

### 4.2 OUT OF SCOPE (deferred Stories 10b/14)

10. ❌ **Streamlit admin panel migration** (`backend/src/admin/`) — Decisión 7B. Story 10b dedicated. Escape hatch: architect puede incluir si trivial 3-5 archivos con halt-and-ask Chris. Default deferred.
11. ❌ **Workers/ETL scheduler migration** — `backend/src/workers/` + per-module `workers/` subdirs. Story 10b OR Story 14 (sales_agent workers natural fit Story 14). Architect decide per-worker if trivial inclusion vs defer.
12. ❌ **40 sales_agent pre-existing failures fix** — Decisión 9B. Story 14 brand-voice-elevation natural home. DEFERRED-FAILURES-STORY-10.md genera T-N final con paths exactos.
13. ❌ **Vertical brand bootstraps Vitalia/Comunify/Lupulo** — Stories 11-13. Story 10 NO touches `vitalia/`, `comunify/`, `lupulo/` brand directories in luana-platform.
14. ❌ **Brand voice elevation refactor** — Story 14. Story 10 preserves PersonalityProfile.system_instruction byte-stable.
15. ❌ **New business logic / feature additions** — Story 10 es **migration mechanical only**. NO new endpoints, NO new DTOs, NO refactor module boundaries.
16. ❌ **Re-platforming to K8s / new infra** — preserve existing dev infra. Production deploy isolated per-brand later (outcome §7.5.5).
17. ❌ **Stable release v1.0.0** — Story 10 consumes v0.1.0. Future stories cement v1.0.0 post-stabilization.

### 4.3 Architect escape hatches (halt-and-ask Chris if invoked)

- Admin inclusion si trivial (3-5 archivos clean imports). Default deferred Story 10b.
- Worker inclusion per-module si trivial. Default deferred.

## 5. Acceptance Criteria (Gherkin AI-resistant)

Mínimo 4 scenarios obligatorios por feature (happy + negative + edge + adversarial). 9 features → ~36 scenarios mínimo. Cada scenario cita §7.6.2 halt triggers donde aplique.

---

### Feature 1 — BE imports rewrite to luana-core packages

#### Scenario 1.1 — `be-imports-rewrite-mass-codemod-module-brand` (`type: happy`)

**Given:**
- AISALESHT `backend/src/modules/brand/` contiene ~47 archivos con imports `from src.modules.brand.X`, `from src.shared.X import Y` (verificable via `grep -rn "from src\." backend/src/modules/brand/ | wc -l`).
- `~/luana-platform/core/luana-core-brand-studio/src/luana_core_brand_studio/` contiene módulos equivalentes (Story 5 deliverable, v0.1.0).
- `~/luana-platform/docs/migration-from-nicolify.md §3` documenta mapping exacto (Story 9 consumer guide).

**When:**
- Sub-agent ejecuta codemod mecánico (e.g., `libcst` codemod o `sed` script) que:
  - Reemplaza `from src.modules.brand.` → `from luana_core_brand_studio.`
  - Reemplaza `from src.shared.agent_observability.recording.` → `from luana_core_observability.recording.`
  - (... mapping completo per §3 migration guide)
- Sub-agent también actualiza test mocks (`tests/modules/brand/`) que importan paths legacy.

**Then:**
- Todos los 47 archivos en `backend/src/modules/brand/` rewritten — `grep -rn "from src\." backend/src/modules/brand/` → empty.
- Tests `pytest tests/modules/brand/ -v` pasan con delta=0 new failures vs baseline T-1 snapshot.
- Test mocks NO apuntan a paths legacy `src.modules.brand.X` (verificable via grep).
- Pyright/ruff lint pasan (imports resolvables a packages instalados via `uv add luana-core-brand-studio==0.1.0`).

**Graders:**
- shell `grep -rn "from src\." /home/chris/AISALESHT/backend/src/modules/brand/ | wc -l` → 0 (post rewrite)
- shell `cd /home/chris/AISALESHT/backend && .venv/bin/pytest tests/modules/brand/ -v --tb=short` → exit 0
- shell `grep -rn "src.modules.brand\|src.shared.agent_observability" /home/chris/AISALESHT/backend/tests/modules/brand/` → 0
- pytest arch fitness `test_imports_no_legacy_src_paths_module_brand.py` — itera archivos + assert no `from src\.` o `import src\.` remanente

---

#### Scenario 1.2 — `be-imports-rewrite-missing-luana-core-export` (`type: negative`)

**Given:**
- AISALESHT `backend/src/modules/X/Y.py` importa `from src.modules.X.Z import some_function`.
- Luana-core/luana_core_X/ NO exporta `some_function` (e.g., función legacy específica de Nicolify, NO migrated a Story 5/6/7).

**When:**
- Sub-agent ejecuta codemod rewrite `from src.modules.X.Z` → `from luana_core_X.Z`.
- Sub-agent corre `pytest tests/modules/X/test_Y.py` post-rewrite.

**Then:**
- Halt-and-ask triggered per §7.6.2 trigger #1 (coupling oculto no documentado outcome §2 dependencies).
- Sub-agent NO proceed con commit del rewrite.
- Report Chris con:
  - Path exacto del symbol missing (e.g., `luana_core_X.Z.some_function`)
  - Stack trace `ImportError: cannot import name 'some_function' from 'luana_core_X.Z'`
  - Proposed mitigation (e.g., (A) lift symbol al luana-core package, (B) recrear como helper local en nicolify BE si pure-Nicolify-specific, (C) remove if dead code)
- Chris ratifica mitigation → sub-agent resume.

**Graders:**
- shell agent log contains string `halt_and_ask_trigger_1` (or equivalent observable marker)
- shell `git log -1 --pretty=%s` NO contains commit del rewrite hasta Chris ratify
- pytest `tests/modules/X/test_Y.py` collected → 0 (collection error since import missing)
- audit trail `T-N-impl-log.md` documenta diagnosis + mitigation + Chris ratify timestamp

---

#### Scenario 1.3 — `be-imports-cross-module-port-still-resolvable` (`type: edge`)

**Given:**
- AISALESHT cross-module imports via `shared/links/ports/` (per `backend-ddd.md` rule — único cross-module permitido).
- Por ejemplo `backend/src/modules/sales_agent/X.py` importa `from src.shared.links.ports.brand_data_port import BrandDataPort`.

**When:**
- Sub-agent rewrite `from src.shared.links.ports.` → `from luana_core_<package>.links.ports.` (per §3 migration guide).
- Tests cross-module fixtures `tests/modules/sales_agent/test_X.py` que mockean `BrandDataPort` corren.

**Then:**
- Cross-module imports resuelven post-rewrite (luana-core packages preservan ports en mismo subpath).
- Mock-patches en tests usan path nuevo (`mocker.patch("luana_core_sales_agent.X.BrandDataPort")`).
- Tests pasan con delta=0 vs baseline.

**Graders:**
- shell `grep -rn "from src.shared.links" /home/chris/AISALESHT/backend/src/` → 0
- shell `grep -rn "luana_core.*\.links\.ports" /home/chris/AISALESHT/backend/src/` → ≥ 1 (port consumers preservados)
- shell `cd backend && .venv/bin/pytest tests/modules/sales_agent/test_X.py -v` → pasa

---

#### Scenario 1.4 — `be-imports-test-mocks-stale-path-detection` (`type: adversarial`)

**Given:**
- Test `tests/modules/copilot/test_callback_handler.py` mockea path legacy: `mocker.patch("src.shared.agent_observability.cost.cost_recorder.record")`.
- Codemod rewrites production imports `src.shared.agent_observability` → `luana_core_observability`.
- Test mock path NO rewritten (sub-agent fallo en step 2 — common slip).

**When:**
- T-N final corre full test suite post all rewrites.

**Then:**
- Test `test_callback_handler.py` FAILS silenciosamente (mock no patches real symbol → test pasa pero NO prueba nothing real) o explicitly (mock target not found → AttributeError).
- T-N final scan grep tests audit detects stale mock paths.
- Halt-and-ask triggered per §7.6.2 trigger #10 (auditor escalate) si auto-fix 2 iter fails.

**Graders:**
- shell `grep -rn 'mocker\.patch.*"src\.\|patch("src\.' /home/chris/AISALESHT/backend/tests/` → 0 (post-cleanup)
- shell `grep -rn 'mocker\.patch.*"src\.\|patch("src\.' /home/chris/AISALESHT/backend/tests/ | wc -l` baseline-T1 captures ≥ N → final = 0
- pytest arch fitness `test_no_legacy_src_mock_paths.py` — fail si encuentra `patch("src.")` o `mocker.patch("src.")` post-migration
- Auditor C5 cross-cutting check verifies mock paths align con production imports

---

### Feature 2 — FE imports rewrite + workspace member move

#### Scenario 2.1 — `fe-workspace-member-move-and-rewrite-happy` (`type: happy`)

**Given:**
- AISALESHT `frontend/` directory contiene Next.js 16 App Router + React 19 + FSD-Lite + `package.json` con deps tipo `"react": "^19.0.0"`.
- `~/luana-platform/pnpm-workspace.yaml` declara `packages: [core, core/@luana/*, nicolify, vitalia, comunify, lupulo]`.
- `~/luana-platform/nicolify/` actualmente stub (`package.json` `"name": "@luana/nicolify"` `"version": "0.1.0"` + minimal `src/` + `tests/`).

**When:**
- Sub-agent ejecuta:
  1. `git mv AISALESHT/frontend/ → luana-platform/nicolify/frontend/` (preserve git history via `--follow` o equivalent — architect verifica strategy)
  2. Update `pnpm-workspace.yaml` add `nicolify/frontend` member (o keep `nicolify` y FE nested per architect decision)
  3. Update `luana-platform/nicolify/frontend/package.json`:
     - `"name": "@luana/nicolify-web"` (o per architect)
     - Reemplaza deps `"react": "^19.0.0"` → workspace local; add `"@luana/api-client": "workspace:*"`, `"@luana/ui-kit": "workspace:*"`, `"@luana/format": "workspace:*"`, `"@luana/hooks": "workspace:*"`, `"@luana/schemas": "workspace:*"`, `"@luana/design-tokens": "workspace:*"`
  4. Find/replace imports en `nicolify/frontend/src/**/*.{ts,tsx}`:
     - `from "@/components/ui/X"` → `from "@luana/ui-kit/X"`
     - `from "@/lib/api/fetchClient"` → `from "@luana/api-client"`
     - `from "@/lib/format"` → `from "@luana/format"`
     - `from "@/hooks/useTenantLocale"` → `from "@luana/hooks"`
     - `from "@/lib/zod-schemas/X"` → `from "@luana/schemas"`
  5. `cd luana-platform && pnpm install` (workspace link)
  6. `cd luana-platform/nicolify/frontend && npx tsc --noEmit && npm run lint && npm run test:unit`

**Then:**
- `git log --follow nicolify/frontend/src/app/page.tsx` muestra historia AISALESHT preservada.
- TypeScript compile GREEN (`tsc --noEmit` exit 0).
- ESLint GREEN (0 errors).
- Vitest unit tests pasan delta=0 vs baseline T-1 snapshot.
- `grep -rn "from \"@/" nicolify/frontend/src/` → 0 (no legacy aliases remanentes — todos rewritten)
- `pnpm list -r @luana/ui-kit` muestra resolve a workspace link.

**Graders:**
- shell `cd /home/chris/luana-platform/nicolify/frontend && npx tsc --noEmit` → exit 0
- shell `cd /home/chris/luana-platform/nicolify/frontend && npx eslint src/ --cache --max-warnings=0` → exit 0
- shell `cd /home/chris/luana-platform/nicolify/frontend && npx vitest run --reporter=default` → exit 0 + delta=0 vs baseline
- shell `grep -rn 'from "@/' /home/chris/luana-platform/nicolify/frontend/src/ | wc -l` → 0
- shell `cd /home/chris/luana-platform && pnpm list -r @luana/ui-kit --json | jq '.[] | .dependencies."@luana/ui-kit".version'` → matches workspace pattern (e.g., `"link:../@luana/ui-kit"`)

---

#### Scenario 2.2 — `fe-import-path-missing-luana-package` (`type: negative`)

**Given:**
- AISALESHT FE `frontend/src/lib/legacy-helper.ts` exporta helper único Nicolify-specific (no migrated to luana-core).
- Importer `frontend/src/features/X/component.tsx` usa `from "@/lib/legacy-helper"`.
- Sub-agent ejecuta find/replace `from "@/` → `from "@luana/` mechanically.

**When:**
- Sub-agent corre `tsc --noEmit` post-rewrite.

**Then:**
- TypeScript error: `Cannot find module '@luana/lib/legacy-helper' or its corresponding type declarations`.
- Halt-and-ask triggered per §7.6.2 trigger #1.
- Sub-agent NO commit del rewrite.
- Report Chris con:
  - Path del importer (`features/X/component.tsx`)
  - Path del helper original (`lib/legacy-helper.ts`)
  - Proposed mitigation: (A) move helper to `nicolify/frontend/src/lib/legacy-helper.ts` (Nicolify-local, no shared), (B) lift to `@luana/format` if generic, (C) inline if simple
- Chris ratifica → sub-agent resume con strategy ratificada.

**Graders:**
- shell `cd /home/chris/luana-platform/nicolify/frontend && npx tsc --noEmit 2>&1 | grep "Cannot find module"` → ≥ 1 línea (pre-fix)
- audit trail T-N-impl-log.md documenta halt + Chris ratify timestamp
- shell post-fix: `npx tsc --noEmit` → exit 0

---

#### Scenario 2.3 — `fe-vercel-reconfig-custom-domain-preserved` (`type: edge`)

**Given:**
- Vercel project actual Nicolify configurado:
  - Root directory: `frontend/` (AISALESHT repo)
  - Custom domain `dev-app.nicolify.com` mapped via CF tunnel (cloudflared local → Vercel preview)
  - Env vars (Clerk keys, DB URL preview, etc.)
- Post FE workspace member move, Vercel debe re-config root → `nicolify/frontend/` y debe seguir building from `luana-platform` repo.

**When:**
- Sub-agent (o Chris manual per architect decision) ejecuta:
  1. Vercel Settings → Git → Connected repo: switch from `AISALESHT` to `alpacapurpura/luana-platform`
  2. Vercel Settings → Build & Development → Root directory: `nicolify/frontend`
  3. Vercel Settings → Build & Development → Install command: `cd ../.. && pnpm install --filter @luana/nicolify-web... --frozen-lockfile`
  4. Vercel Settings → Build & Development → Build command: `pnpm --filter @luana/nicolify-web build`
  5. Vercel Settings → Environment Variables: verify all preserved (Clerk, DB, etc.)
  6. CF tunnel `dev-app.nicolify.com` → verify mapping points to new Vercel deployment URL

**Then:**
- Vercel deployment from `luana-platform` repo GREEN (build succeeds with workspace deps resolved).
- `dev-app.nicolify.com` resolves to new deployment.
- Chris can navigate signup page locally via `dev-app.nicolify.com`.
- Smoke pre-E2E: `curl -I https://dev-app.nicolify.com/` → `HTTP 200`.

**Then (halt path — Vercel surprise):**
- Si Vercel reconfig surface unexpected issue (e.g., monorepo build fails, env vars lost, CF tunnel mapping rompe) → halt-and-ask trigger #3 + #4 (§7.6.2).
- Sub-agent documents exact error.
- Escalate Chris.

**Graders:**
- shell `curl -I https://dev-app.nicolify.com/` → returns `HTTP/2 200` (or 3xx redirect to signed page)
- Vercel deployment log shows successful build + workspace resolution
- audit trail T-N-impl-log.md captures reconfig steps + verification

---

#### Scenario 2.4 — `fe-shadcn-component-version-skew` (`type: adversarial`)

**Given:**
- AISALESHT FE usa `Button` shadcn component customizado en `components/ui/button.tsx` con prop adicional `customSize` Nicolify-specific.
- `@luana/ui-kit/button` (Story 5 deliverable) exporta `Button` SIN ese prop (luana-core preserva sólo shadcn standard surface).
- Sub-agent rewrite `from "@/components/ui/button"` → `from "@luana/ui-kit/button"`.

**When:**
- TypeScript compile.

**Then:**
- TS error: `Property 'customSize' does not exist on type 'ButtonProps'` en archivos consumer del prop.
- Halt-and-ask triggered §7.6.2 trigger #1.
- Sub-agent reports proposed mitigations:
  - (A) Lift `customSize` to `@luana/ui-kit/button` (lift shared if multi-brand use case viable)
  - (B) Wrap `Button` localmente en `nicolify/frontend/src/components/ui/button-nicolify.tsx` extending `@luana/ui-kit/button` (composition)
  - (C) Remove customSize usage (refactor consumers to use standard size prop)
- Chris ratifica strategy → sub-agent resume.

**Graders:**
- shell `cd /home/chris/luana-platform/nicolify/frontend && npx tsc --noEmit 2>&1 | grep "customSize"` → ≥ 1 (pre-fix)
- post-fix TS compile GREEN
- audit trail records strategy chosen + rationale

---

### Feature 3 — Fresh `nicolify_dev` DB + alembic snapshot consolidation

#### Scenario 3.1 — `db-fresh-nicolify-with-consolidated-snapshot` (`type: happy`)

**Given:**
- AISALESHT DB actual `visionarias_logs` en container `visionarias_postgres_dev`.
- 131 alembic migrations en `AISALESHT/backend/alembic/versions/`.
- AISALESHT BE models actuales reflejan schema state post all 131 migrations applied.

**When:**
- Sub-agent ejecuta:
  1. `pg_dump --schema-only -U postgres visionarias_logs > /tmp/aisaleshT_schema_snapshot.sql` (capture current schema)
  2. Create new DB: `psql -U postgres -c "CREATE DATABASE nicolify_dev;"`
  3. Generate consolidated migration `001_initial_snapshot.py` reflecting current schema (raw SQL `CREATE TABLE IF NOT EXISTS ...` per `.claude/rules/backend-migrations.md` idempotent pattern). Architect decide tool: handcraft from pg_dump OR `alembic revision --autogenerate` desde models on empty DB OR script per-table.
  4. Place consolidated migration in `luana-platform/nicolify/backend/alembic/versions/001_initial_snapshot.py` (or per architect — could live in luana-core-platform package + nicolify imports). Architect verifies pattern.
  5. Update env vars + `docker-compose.dev.yml` `POSTGRES_DB=nicolify` (or per dev environment migration strategy).
  6. `docker exec <postgres-container> alembic upgrade head` (apply consolidated migration on fresh DB)
  7. Verify schema: `pg_dump --schema-only nicolify_dev > /tmp/nicolify_schema.sql` + `diff /tmp/aisaleshT_schema_snapshot.sql /tmp/nicolify_schema.sql` → minimal diff (tolerable: column order, comments; intolerable: missing tables/columns/FKs/indexes).

**Then:**
- `nicolify_dev` DB exists con all tables + indexes + FKs equivalentes a `visionarias_logs`.
- `alembic current` reports `001_initial_snapshot` (or composite head per architect's branching strategy).
- BE tests `pytest -x -q` corren contra `nicolify_dev` con delta=0 new failures.

**Graders:**
- shell `psql -U postgres -lqt | cut -d \| -f 1 | grep -qw nicolify_dev` → exit 0
- shell `diff <(pg_dump --schema-only visionarias_logs | grep -E "^CREATE TABLE|^ALTER TABLE.*FOREIGN KEY" | sort) <(pg_dump --schema-only nicolify_dev | grep -E "^CREATE TABLE|^ALTER TABLE.*FOREIGN KEY" | sort)` → empty (or only acceptable cosmetic diffs)
- shell `docker exec <postgres-container> alembic current` → outputs `001_initial_snapshot (head)` or equivalent
- shell `cd backend && DATABASE_URL=postgresql://...@postgres:5432/nicolify_dev .venv/bin/pytest -x -q` → exit 0 + delta=0 vs baseline T-1

---

#### Scenario 3.2 — `db-schema-drift-models-vs-snapshot` (`type: negative`)

**Given:**
- AISALESHT BE model `User` declara campo `created_at` con `default=utc_now()`.
- AISALESHT DB `visionarias_logs` tiene tabla `users` con column `created_at` PERO sin default (drift histórico: model was updated, migration to add default was never created).
- Sub-agent ejecuta consolidation per Scenario 3.1.

**When:**
- Sub-agent compara schema generated from models (`alembic revision --autogenerate` on empty DB) vs actual `visionarias_logs` schema.

**Then:**
- Drift detected — schemas no match.
- Halt-and-ask triggered per §7.6.2 trigger #5 (alembic snapshot consolidation surface schema inconsistency).
- Sub-agent reports exact tables/columns con drift + proposed resolution:
  - (A) Update models to match prod state (NO default — current behavior)
  - (B) Add default + include migration in consolidation snapshot (changes runtime behavior — Chris must ratify)
  - (C) Defer drift to follow-up ticket Story 10b (snapshot reflects current prod state, models stay aligned with old behavior)
- Chris ratifica → sub-agent resume.

**Graders:**
- audit trail T-N-impl-log.md documenta drift table + resolution strategy + Chris ratify
- shell pre-fix: `diff /tmp/models_inferred_schema.sql /tmp/aisaleshT_schema_snapshot.sql | wc -l` → > 0
- post-resolution: `diff` minimal (matches strategy chosen)

---

#### Scenario 3.3 — `db-idempotent-migration-survives-reapply` (`type: edge`)

**Given:**
- Consolidated migration `001_initial_snapshot.py` follows `.claude/rules/backend-migrations.md` pattern (raw SQL `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`, etc.).
- DB `nicolify_dev` already at head revision post initial upgrade.

**When:**
- Sub-agent re-runs `alembic upgrade head` (idempotency stress test).

**Then:**
- Migration succeeds with NO errors (idempotent — `IF NOT EXISTS` clauses prevent duplicate-create errors).
- `alembic current` still reports same head revision.
- Schema unchanged.

**Graders:**
- shell `docker exec <postgres-container> alembic upgrade head` (second run) → exit 0
- shell `pg_dump --schema-only nicolify_dev | sha256sum` (before+after) → equal hashes
- pytest `tests/architecture/test_consolidated_migration_idempotent.py` corre raw SQL parser + assert all DDL uses `IF NOT EXISTS` / `IF EXISTS` patterns

---

#### Scenario 3.4 — `db-aisalesht-drop-prematuro-blocks` (`type: adversarial`)

**Given:**
- Sub-agent tentado a `DROP DATABASE visionarias_logs` para reclaim space ANTES smoke E2E pasa.
- Decisión 2B: drop SOLO al cierre Story 10 después tests green + 24h soak.

**When:**
- Sub-agent prompt llega a step "drop AISALESHT DB".

**Then:**
- Sub-agent verifica preconditions:
  - Smoke E2E (Feature 5) ya pasó GREEN
  - 24h soak completed (timestamp delta ≥ 24h since smoke green)
  - Chris explicit go (could be ratification at merge time)
- Si preconditions NOT met → defer drop, document in checkpoint `next_action: pending_24h_soak`.
- Si all met → execute `psql -U postgres -c "DROP DATABASE visionarias_logs;"` + record in T-N-impl-log.

**Graders:**
- shell pre-soak: `psql -U postgres -lqt | grep -qw visionarias_logs` → exit 0 (DB still exists)
- shell post-cierre Story 10: same query → exit 1 (DB dropped)
- audit trail records soak verification timestamps

---

### Feature 4 — Test parity baseline + delta=0 enforcement

#### Scenario 4.1 — `test-baseline-captured-T1` (`type: happy`)

**Given:**
- AISALESHT en estado pre-Story-10 (no rewrite yet).
- T-1 ticket es FIRST ticket Story 10 — captures baseline antes any change.

**When:**
- Sub-agent T-1 ejecuta:
  ```bash
  cd /home/chris/AISALESHT/backend
  .venv/bin/pytest --json-report --json-report-file=/home/chris/AISALESHT/docs/product/stories/luana-nicolify-migration/baseline-be-tests.json --tb=short 2>&1 | tee baseline-be.log
  cd /home/chris/AISALESHT/frontend
  npx vitest run --reporter=json --outputFile=/home/chris/AISALESHT/docs/product/stories/luana-nicolify-migration/baseline-fe-tests.json 2>&1 | tee baseline-fe.log
  ```

**Then:**
- `baseline-be-tests.json` + `baseline-fe-tests.json` committed at T-1 (audit trail).
- Files contain JSON con `passed: N`, `failed: M`, `skipped: K` counters per-test detailed.
- M (failures) captured — incluye 40 pre-existing sales_agent failures (Decisión 9B baseline).
- Sub-agent T-1 outputs summary: "Baseline captured: BE N pass / M fail / K skip; FE N pass / M fail / K skip"

**Graders:**
- file exists `docs/product/stories/luana-nicolify-migration/baseline-be-tests.json` (committed)
- file exists `docs/product/stories/luana-nicolify-migration/baseline-fe-tests.json` (committed)
- shell `jq '.summary.failed' baseline-be-tests.json` → integer ≥ 0 (matches 40 sales_agent if all baseline state captured)
- T-1-impl-log.md documents exact counts + which tests failed pre-rewrite

---

#### Scenario 4.2 — `test-delta-zero-final-enforcement` (`type: happy`)

**Given:**
- Baseline captured T-1 per Scenario 4.1.
- All rewrites Features 1-3 completed.
- T-N final ticket runs full suite post-rewrite.

**When:**
- Sub-agent T-N runs full suite + delta calculation:
  ```bash
  cd /home/chris/luana-platform/nicolify/backend  # or wherever BE lives post-move
  uv run pytest --json-report --json-report-file=/tmp/final-be-tests.json --tb=short
  python scripts/test_delta_check.py baseline-be-tests.json /tmp/final-be-tests.json --max-new-failures=0
  ```

**Then:**
- Delta script outputs:
  ```
  Baseline BE: N pass / M fail / K skip
  Final BE:    N' pass / M' fail / K' skip
  New failures (in final, not in baseline): []
  Delta: 0 new failures ✓
  ```
- Same for FE.
- If new failures detected, list paths exactly (test file + test name) → halt-and-ask trigger #10 if 2 auto-fix iter fail.

**Graders:**
- pytest `test_delta_zero_enforcement.py` — parses baseline + final + asserts new_failures = []
- shell script `scripts/test_delta_check.py` exit 0
- shell `jq '.tests[] | select(.outcome == "failed") | .nodeid' /tmp/final-be-tests.json | sort > /tmp/final-failed.txt && jq '.tests[] | select(.outcome == "failed") | .nodeid' baseline-be-tests.json | sort > /tmp/baseline-failed.txt && diff /tmp/baseline-failed.txt /tmp/final-failed.txt` → empty (no new failures introduced) OR only entries in baseline_failed but not final (improvements OK)

---

#### Scenario 4.3 — `test-fix-on-discovery-trivial-only` (`type: edge`)

**Given:**
- During rewrite Feature 1, sub-agent encounters test failure in `tests/modules/X/test_Y.py`.
- Failure root cause: import path stale in test mock (`patch("src.modules.X.Z")` → should be `patch("luana_core_X.Z")`).
- Fix time estimate: < 5 min (mechanical replace).

**When:**
- Sub-agent applies trivial fix in same commit as rewrite.

**Then:**
- Fix committed inline.
- T-N-impl-log.md documents fix-on-discovery with rationale (delta=0 reduce + within 5min cap per Decisión 5B).
- Fix does NOT expand scope (no refactor, no new tests, no logic change).

**Graders:**
- audit trail records fix-on-discovery list with timestamps + lines changed
- shell `git log --grep="fix-on-discovery" --oneline | wc -l` ≥ 1 (if any fixes applied)
- post-fix `pytest tests/modules/X/test_Y.py` → exit 0

---

#### Scenario 4.4 — `test-new-failure-introduced-blocks-merge` (`type: adversarial`)

**Given:**
- Sub-agent rewrite introduces subtle regression (e.g., wrong mapping `from src.modules.brand.events` → `from luana_core_brand_studio.events` but missing re-export in luana-core).
- Test `tests/modules/brand/test_events.py::test_brand_created_event_emission` FAILS post-rewrite (was passing in baseline).

**When:**
- T-N final delta check.

**Then:**
- Delta check outputs `NEW FAILURE: tests/modules/brand/test_events.py::test_brand_created_event_emission`.
- Sub-agent auto-fix iter 1 attempts diagnose + fix.
- If iter 1 fails → auto-fix iter 2.
- If iter 2 also fails → halt-and-ask trigger #10 (auditor escalate, no 3rd iter sin Chris).
- Story 10 NO merge until new failure resolved (delta=0 hard gate).

**Graders:**
- shell delta script `--max-new-failures=0` → exit 1 (with new failure detected)
- audit trail records auto-fix attempts + outcomes
- merge blocked: checkpoint state stays `developed` (not transitions to `reviewing` if auditor pre-check catches)

---

### Feature 5 — Playwright smoke E2E (Chris journey end-to-end)

#### Scenario 5.1 — `smoke-e2e-chris-journey-happy` (`type: happy`)

**Given:**
- Post all rewrites (Features 1-4 GREEN), nicolify app runs on `dev-app.nicolify.com` (CF tunnel) via Vercel from `luana-platform` repo.
- BE runs locally (`docker compose -f docker-compose.dev.yml up` from `luana-platform` root).
- DB `nicolify_dev` populated with consolidated snapshot.
- Clerk auth fixture configured (testing token per `playwright-expert` skill).

**When:**
- Smoke E2E spec `nicolify/frontend/e2e/specs/smoke/chris-journey-e2e.spec.ts` runs:
  1. Navigate to `dev-app.nicolify.com`
  2. Signup new tenant (Clerk testing token)
  3. Land on dashboard
  4. Brand Studio → fill basics (name, voice tone)
  5. Offer Studio → create offer (basic preset)
  6. Sales Agent → start conversation runtime
  7. Verify conversation responds (LLM call succeeds via luana-core-sales-agent path)
  8. Verify cards rendered (copilot via luana-core-copilot path)
  9. Sign out

**Then:**
- All 9 steps complete with `expect()` assertions GREEN.
- Smoke exit 0.
- No console errors (`page.on('pageerror', ...)` captures empty).
- Network requests resolve (no 5xx errors).

**Graders:**
- shell `cd /home/chris/luana-platform/nicolify/frontend && E2E_BASE_URL=https://dev-app.nicolify.com npx playwright test --project=smoke chris-journey-e2e.spec.ts` → exit 0
- playwright HTML report (`playwright-report/index.html`) shows all 9 steps GREEN
- artifact `test-results/` directory has 0 failure trace files

---

#### Scenario 5.2 — `smoke-e2e-clerk-auth-fixture-rebuild` (`type: edge`)

**Given:**
- Post FE workspace move, `playwright/.clerk/user.json` storage state file path may have changed location (e.g., `frontend/playwright/.clerk/` → `nicolify/frontend/playwright/.clerk/`).
- Smoke test fixture references new path.

**When:**
- First smoke run post-migration.

**Then:**
- If fixture freshness gate detects stale (e.g., > 24h) → auto-regenerate via Clerk testing token (per `playwright-expert` skill).
- If fixture path missing entirely → halt-and-ask trigger #4 (CF tunnel/auth surface issue).
- Smoke proceeds GREEN after fixture refreshed.

**Graders:**
- file exists `luana-platform/nicolify/frontend/playwright/.clerk/user.json` (post fixture regen)
- shell `cd /home/chris/luana-platform/nicolify/frontend && npm run test:e2e:smoke` → exit 0

---

#### Scenario 5.3 — `smoke-e2e-sales-agent-conversation-via-luana-core` (`type: edge`)

**Given:**
- Sales agent conversation step (Scenario 5.1 step 6-7) requires:
  - LiteLLM proxy responding (or graceful fallback per `tessl__graceful-degradation`)
  - Trace event written via `luana_core_observability.recording.callback_handler`
  - Cost recorder via `luana_core_observability.cost.cost_recorder`
- Imports rewritten Feature 1 to luana-core paths.

**When:**
- Smoke step "Sales Agent → conversation".

**Then:**
- LLM response received (within 30s timeout).
- DB query `select trace_event from sales_agent_trace_event where tenant_id = <test_tenant>` → ≥ 1 row.
- DB query `select cost_usd from copilot_llm_call where tenant_id = <test_tenant>` → cost_usd > 0 (no NULL — per anti-default-flip-audit and Story PI-12 S1 T-1.bis lessons).

**Graders:**
- playwright test step assertion: `await expect(page.getByText('Hola')).toBeVisible({ timeout: 30000 })`
- post-test DB query via test helper script: `tenant trace events ≥ 1 AND cost_usd > 0`
- copilot module trace audit shows successful tool calls path via luana_core_copilot

---

#### Scenario 5.4 — `smoke-e2e-tenant-cross-leak-blocked` (`type: adversarial`)

**Given:**
- Smoke creates 2 tenants (T1, T2).
- T1 creates offer "Offer A". T2 creates offer "Offer B".
- Migration imports rewrite preserves `.where(Model.tenant_id == tenant_id)` filters (per `tenant-isolation.md` rule).

**When:**
- T2 navigates to Offer Studio → list offers.

**Then:**
- T2 sees ONLY "Offer B" (their own).
- T2 does NOT see "Offer A" (T1's).
- API request inspected (network panel): response payload contains only `offer_id=<T2's offer>`.
- Audit log shows `X-Tenant-ID: <T2>` header on request (auto-injected by `@luana/api-client`).

**Graders:**
- playwright `await expect(page.getByText('Offer B')).toBeVisible()` AND `await expect(page.getByText('Offer A')).not.toBeVisible()`
- network response payload inspection: `expect(response.url).toContain('tenant_id=<T2>') OR header X-Tenant-ID = T2`
- DB query verification: `select tenant_id from offers where id = <T2_offer_id>` → matches T2

---

### Feature 6 — CI parity root cross-brand migration

#### Scenario 6.1 — `ci-parity-root-makefile-target-migrated` (`type: happy`)

**Given:**
- AISALESHT `Makefile` contains target `ci-parity` (lint + arch tests + pytest + frontend tsc/eslint/vitest + e2e preflight).
- luana-platform root `Makefile` has placeholder + Story 9 release targets but NO `ci-parity` yet.

**When:**
- Sub-agent ejecuta:
  1. Read `AISALESHT/Makefile` `ci-parity` target definition.
  2. Adapt paths to luana-platform monorepo:
     - `cd backend && ...` → `cd nicolify/backend && uv run ...` (or workspace-aware command)
     - `cd frontend && ...` → `cd nicolify/frontend && pnpm ...`
     - Add cross-brand support placeholders for Stories 11-13 future (e.g., `for brand in nicolify vitalia comunify lupulo; do ...; done`)
  3. Write to `luana-platform/Makefile`.
  4. Update pre-push hook in `luana-platform/.git/hooks/pre-push` (or `husky/.husky/pre-push`) to invoke `make ci-parity` from luana-platform root.

**Then:**
- `cd luana-platform && make ci-parity` exit 0.
- Pre-push hook intercepts `git push` from luana-platform → invokes ci-parity.
- AISALESHT `Makefile` `ci-parity` target marked deprecated (comment) or removed if AISALESHT will archive.

**Graders:**
- shell `cd /home/chris/luana-platform && make ci-parity` → exit 0
- shell `cat luana-platform/.git/hooks/pre-push | grep -q ci-parity` → exit 0
- file `luana-platform/Makefile` contains `ci-parity:` target

---

#### Scenario 6.2 — `ci-parity-env-divergence-detected` (`type: negative`)

**Given:**
- Tests pass locally (`pytest -x -q` GREEN).
- `make ci-parity` (which runs in cleaner env, simulates GitHub Actions) fails on env-specific assertion (e.g., timezone difference, locale, env var presence).

**When:**
- Sub-agent ejecuta `make ci-parity` post-migration.

**Then:**
- Failure detected with clear error message identifying env divergence (e.g., "TZ env var not set; tests expect UTC").
- Halt-and-ask trigger #6 (§7.6.2 — tests pass local pero ci-parity falla).
- Sub-agent diagnoses + reports Chris.
- Resolution: fix env config in Makefile (`export TZ=UTC`) OR fix test (parametrize tz).
- Chris ratifies → resume.

**Graders:**
- audit trail T-N-impl-log.md documents env divergence + fix
- pre-fix `make ci-parity` → exit ≠ 0
- post-fix `make ci-parity` → exit 0

---

#### Scenario 6.3 — `ci-parity-cross-brand-future-stories-extensible` (`type: edge`)

**Given:**
- Makefile `ci-parity` target is currently Nicolify-specific.
- Stories 11-13 (Vitalia/Comunify/Lupulo) will need same gate per their brand directories.

**When:**
- Architect designs Makefile structure to be brand-agnostic.

**Then:**
- Makefile uses iteration pattern (e.g., `BRANDS := nicolify` Story 10, future Stories 11-13 append `BRANDS := nicolify vitalia comunify lupulo`).
- Each brand target callable individually (`make ci-parity-nicolify`).
- Aggregated target runs all (`make ci-parity-all`).
- Documentation in `luana-platform/Makefile` header comments + RELEASES.md note.

**Graders:**
- shell `cd luana-platform && make -n ci-parity-nicolify` (dry-run) → exit 0 + shows commands per brand
- file `luana-platform/Makefile` contains `BRANDS :=` variable or equivalent pattern
- ADR or comment in Makefile documents extension pattern

---

#### Scenario 6.4 — `ci-parity-pre-push-bypass-attempt-blocked` (`type: adversarial`)

**Given:**
- Developer attempts `git push origin development --no-verify` to bypass pre-push hook (forbidden per `.claude/rules/git-safety.md`).

**When:**
- Pre-push hook execution.

**Then:**
- Hook detects `--no-verify` flag (via env `HUSKY_SKIP_HOOKS` or similar) → if detected, block or log warning.
- If hook bypassed somehow + ci-parity not run → CI server-side gate (GitHub Actions) catches failure.

**Graders:**
- attempt `git push --no-verify` from clean state with broken ci-parity → server-side CI fails OR hook blocks
- file `luana-platform/.husky/pre-push` (or `.git/hooks/pre-push`) does NOT exit early on `HUSKY_SKIP_HOOKS` for ci-parity step

---

### Feature 7 — /pm SSoT atomic migration Fase 4

#### Scenario 7.1 — `pm-ssot-atomic-git-mv-and-script-verify` (`type: happy`)

**Given:**
- AISALESHT `docs/product/` contains (post Story 10 build phase complete):
  - `BACKLOG.{yaml,md}` + `BACKLOG-TLDR.md` (auto-gen)
  - `outcomes/` (4+ outcomes)
  - `stories/` including `luana-nicolify-migration/` (current story)
  - `capabilities/{module}/` (per-module YAMLs)
  - `modules/`, `ideas-pool.yaml`, `vision.md`, `glossary.md`, `story-map/backbone.md`
- `scripts/generate_backlog.py` (R33) + `scripts/reconcile_capabilities.py` (R32) live in AISALESHT.
- Pre-commit hooks Section 4-6 reference paths.
- Fase 4 = merge time, all earlier features complete.

**When:**
- Sub-agent (Opus per checkpoint frontmatter opus_priority) ejecuta atomic migration:
  1. Snapshot pre-move: `tar czf /tmp/pre-move-snapshot.tar.gz docs/product/` (audit trail)
  2. Verify scripts pre-move work: `cd AISALESHT && python scripts/generate_backlog.py --dry-run` exit 0 + `python scripts/reconcile_capabilities.py --check` exit 0
  3. `git mv AISALESHT/docs/product/ → AISALESHT/<discard>` AND `git mv` content to `luana-platform/docs/product/` (architect verifies exact `git mv` strategy across repos — likely 2-step: `mv` filesystem + commit deletion in AISALESHT + commit addition in luana-platform)
  4. Also migrate `scripts/generate_backlog.py` + `scripts/reconcile_capabilities.py` to `luana-platform/scripts/` (or per architect — could remain at root with relative paths)
  5. Update pre-commit hooks in luana-platform (`scripts/git-hooks/pre-commit`) Section 4-6 paths
  6. Post-move verify: `cd luana-platform && python scripts/generate_backlog.py --dry-run` exit 0 + `python scripts/reconcile_capabilities.py --check` exit 0
  7. Commit in AISALESHT: `chore(pm-ssot): migrate to luana-platform — closure pre-archive`
  8. Commit in luana-platform: `feat(pm-ssot): receive /pm SSoT from AISALESHT — Fase 4 merge Story 10`

**Then:**
- AISALESHT `docs/product/` directory empty or removed (only audit-trail snapshot retained as archived tarball if architect chooses).
- luana-platform `docs/product/` contains full SSoT mirror.
- Scripts run GREEN in new location with same output (BACKLOG.md regenerates byte-stable except for paths).
- Pre-commit hooks fire on new location (test via dummy commit in luana-platform that touches `docs/product/BACKLOG.md`).
- Story 10 archive lands at `luana-platform/docs/archive/2026/stories/luana-nicolify-migration/` (NOT AISALESHT — Story 10 transitions to done in new SSoT).

**Graders:**
- shell `ls /home/chris/AISALESHT/docs/product/ 2>/dev/null | wc -l` → 0 (empty)
- shell `ls /home/chris/luana-platform/docs/product/BACKLOG.md` → exit 0
- shell `cd /home/chris/luana-platform && python scripts/generate_backlog.py --check` → exit 0
- shell `cd /home/chris/luana-platform && python scripts/reconcile_capabilities.py --check` → exit 0
- pytest `tests/scripts/test_backlog_generator.py` (migrated) → GREEN
- pytest `tests/scripts/test_reconcile_capabilities.py` (migrated) → GREEN

---

#### Scenario 7.2 — `pm-ssot-hardcoded-path-discovered-halt` (`type: negative`)

**Given:**
- Sub-agent ejecuta SSoT move per Scenario 7.1.
- Mid-move, sub-agent encounters script `scripts/X.py` or `.claude/rules/Y.md` that hardcodes `/home/chris/AISALESHT/docs/product/...` path (instead of relative or dynamic).

**When:**
- Sub-agent attempts to run scripts post-move.

**Then:**
- Script fails with `FileNotFoundError: /home/chris/AISALESHT/docs/product/...`.
- Halt-and-ask triggered per Decisión 4A "Halt-and-ask si Claude descubre path hardcoded raro".
- Sub-agent reports:
  - Exact file with hardcoded path + line number
  - Proposed mitigation (replace with relative path, env var, or `pathlib.Path(__file__).parents[N]` pattern)
- Chris ratifies fix → resume.

**Graders:**
- audit trail T-N-impl-log.md records hardcoded path discovery + fix + Chris ratify
- shell `grep -rn "/home/chris/AISALESHT/docs/product" /home/chris/luana-platform/scripts/ /home/chris/luana-platform/.claude/` → 0 (post-fix)

---

#### Scenario 7.3 — `pm-ssot-rollback-if-scripts-fail-post-move` (`type: edge`)

**Given:**
- Sub-agent completes git mv but post-move scripts fail (per Scenario 7.2 not yet caught).
- Atomic rollback strategy: revert commits.

**When:**
- Auto-fix iter 1+2 fail to resolve script breakage.

**Then:**
- Halt-and-ask trigger #10 (auditor escalate, no 3rd iter).
- Rollback option presented: `cd AISALESHT && git reset --soft HEAD~1` + restore `docs/product/` from snapshot tarball (NO `git revert` per parallel-safety rules — manual restore via Chris approval).
- OR forward-fix if scope narrow (script path patches).

**Graders:**
- audit trail records rollback decision + Chris ratification
- pre-fix scripts FAIL; post-fix or rollback scripts GREEN
- git log shows clean rollback OR forward-fix commits

---

#### Scenario 7.4 — `pm-ssot-no-content-leak-during-move` (`type: adversarial`)

**Given:**
- Sub-agent ejecuta git mv.
- Risk: mid-move state could expose secrets, sensitive Chris context to wrong repo visibility.

**When:**
- During move, sub-agent verifies destination repo (luana-platform) has appropriate visibility (private monorepo).

**Then:**
- luana-platform is PRIVATE repo (verified via `gh repo view alpacapurpura/luana-platform --json visibility --jq .visibility` → `"PRIVATE"`).
- No `docs/product/` content leaked to public repos.
- Snapshot tarball stored only in `/tmp/` or `docs/archive/` private location.

**Graders:**
- shell `gh repo view alpacapurpura/luana-platform --json visibility --jq .visibility` → `"PRIVATE"`
- audit trail verifies repo visibility check pre-move
- no `docs/product/` commits to public repo

---

### Feature 8 — AISALESHT archive + DB drop closure

#### Scenario 8.1 — `aisalesht-archive-via-github-ui` (`type: happy`)

**Given:**
- Story 10 all earlier features complete + smoke green + 24h soak passed.
- AISALESHT `development` and `main` branches clean (final commits = Story 10 closure docs only).
- AISALESHT repo at `github.com/alpacapurpura/AISALESHT` (or owner).

**When:**
- Chris (manual, post Claude reports ready) ejecuta:
  1. Navigate to GitHub Settings → AISALESHT → Danger Zone → Archive
  2. Confirm archive
- (Alternative: Claude could attempt `gh api repos/alpacapurpura/AISALESHT --method PATCH -f archived=true` but Chris ratifies)

**Then:**
- AISALESHT GitHub Settings shows "This repository is archived" banner.
- No new pushes accepted (read-only state).
- Issues/PRs locked.
- Reversible via Settings → Unarchive (1-click).

**Graders:**
- shell `gh api repos/alpacapurpura/AISALESHT --jq .archived` → `true`
- audit trail T-N-impl-log.md records archive timestamp + UI screenshot reference

---

#### Scenario 8.2 — `aisalesht-db-drop-post-soak` (`type: happy`)

**Given:**
- Smoke green Feature 5 complete + 24h soak elapsed (timestamp delta ≥ 86400s).
- New nicolify DB `nicolify_dev` healthy (queries respond, no data loss).
- Chris explicit ratification to drop AISALESHT DB.

**When:**
- Sub-agent (with Chris approval marker) ejecuta:
  ```bash
  psql -U postgres -c "DROP DATABASE visionarias_logs;"
  docker compose -f docker-compose.dev.yml down  # if AISALESHT compose still up
  ```

**Then:**
- `visionarias_logs` DB no longer exists.
- AISALESHT container stopped.
- Nicolify dev environment fully on `nicolify_dev` + luana-platform containers only.

**Graders:**
- shell `psql -U postgres -lqt | grep -qw visionarias_logs` → exit 1
- shell `docker ps | grep visionarias_postgres_dev` → empty
- audit trail records Chris ratify + soak verification timestamps

---

#### Scenario 8.3 — `aisalesht-archive-blocked-if-uncommitted-changes` (`type: edge`)

**Given:**
- AISALESHT working tree has uncommitted changes (e.g., parallel session WIP) at archive time.

**When:**
- Sub-agent attempts archive.

**Then:**
- Pre-archive check: `cd AISALESHT && git status --short` outputs ≥ 1 line.
- Halt-and-ask trigger #8 (luana-platform monorepo state inesperado — analog rule applies to AISALESHT closure).
- Report Chris: "Uncommitted changes detected. Resolve via commit/stash/discard before archive."
- Chris resolves → archive proceeds.

**Graders:**
- shell `cd AISALESHT && git status --short` exit 0 + empty output (pre-archive verify)
- audit trail records check + resolution if needed

---

#### Scenario 8.4 — `aisalesht-archive-history-still-readable` (`type: adversarial`)

**Given:**
- AISALESHT archived per Scenario 8.1.
- Future developer needs to read history (audit trail, legacy code reference).

**When:**
- Developer attempts `git clone github.com/alpacapurpura/AISALESHT.git` + `git log`.

**Then:**
- Clone succeeds (read-only).
- `git log` returns full history including Stories 1-10.
- File reads work (`git show HEAD:backend/src/modules/brand/X.py`).
- No push permitted (archived state).

**Graders:**
- shell `git clone https://github.com/alpacapurpura/AISALESHT.git /tmp/archived-test` → exit 0
- shell `cd /tmp/archived-test && git log --oneline | wc -l` → ≥ 100 (full history preserved)
- shell `cd /tmp/archived-test && git push origin development 2>&1 | grep -q "archived"` → exit 0 (push blocked with archive message)

---

### Feature 9 — Story 10 archive location at new SSoT

#### Scenario 9.1 — `story-10-archives-at-luana-platform-location` (`type: happy`)

**Given:**
- Story 10 reaches `done` state post all features 1-8 + auditor APPROVED + /pm merge.
- /pm SSoT migration Feature 7 complete (docs/product/ lives in luana-platform now).

**When:**
- /pm executes archival:
  ```bash
  cd /home/chris/luana-platform
  git mv docs/product/stories/luana-nicolify-migration/ docs/archive/2026/stories/luana-nicolify-migration/
  python scripts/generate_backlog.py  # regen BACKLOG to reflect Story 10 done
  python scripts/reconcile_capabilities.py
  git commit -m "feat(luana-platform-migration): close Story 10 luana-nicolify-migration DONE + archive"
  ```

**Then:**
- Story 10 archive accessible at `luana-platform/docs/archive/2026/stories/luana-nicolify-migration/`.
- BACKLOG.md updated: Story 10 status `done`, outcome counter `stories_done = 10/14`.
- Story 11-14 unblocked (DAG-wise) — their checkpoint `blocked_by` references updated.

**Graders:**
- file exists `luana-platform/docs/archive/2026/stories/luana-nicolify-migration/checkpoint.md` with `state: done`
- shell `grep "stories_done.*10/14" luana-platform/docs/product/outcomes/luana-platform-migration.md` → exit 0
- pytest BACKLOG freshness gate fires + passes post-regen

---

#### Scenario 9.2 — `story-10-archive-not-accessible-aisalesht-post-archive` (`type: edge`)

**Given:**
- AISALESHT archived per Feature 8.
- AISALESHT NO contains `docs/product/stories/luana-nicolify-migration/` (moved Feature 7).

**When:**
- Someone tries to find Story 10 archive.

**Then:**
- Path `AISALESHT/docs/product/stories/luana-nicolify-migration/` does NOT exist.
- Path `AISALESHT/docs/archive/2026/stories/luana-nicolify-migration/` does NOT exist (never written here).
- Only valid path: `luana-platform/docs/archive/2026/stories/luana-nicolify-migration/`.

**Graders:**
- shell `ls /home/chris/AISALESHT/docs/product/stories/luana-nicolify-migration/ 2>/dev/null` → exit ≠ 0 OR empty
- shell `ls /home/chris/AISALESHT/docs/archive/2026/stories/luana-nicolify-migration/ 2>/dev/null` → exit ≠ 0 OR empty
- shell `ls /home/chris/luana-platform/docs/archive/2026/stories/luana-nicolify-migration/checkpoint.md` → exit 0

---

#### Scenario 9.3 — `story-10-handoff-prompt-story-10b-emitted` (`type: edge`)

**Given:**
- Decisión 10A: Handoff prompt Story 10b generated at close (Chris explicit request).

**When:**
- /pm merge Story 10.

**Then:**
- File `luana-platform/docs/product/stories/luana-nicolify-migration/HANDOFF-STORY-10B.md` (or per `/pm` template) emitted with:
  - Scope Story 10b (Streamlit admin migration + workers/ETL deferred)
  - Decisions inherited from §7.6 (most apply: archive AISALESHT done, /pm SSoT in luana-platform, etc.)
  - Decisions to re-ratify per session (Decisión 10A scope-per-session)
  - Estimated complexity + ticket count
  - DEFERRED-FAILURES-STORY-10.md cross-reference

**Graders:**
- file exists `luana-platform/docs/archive/2026/stories/luana-nicolify-migration/HANDOFF-STORY-10B.md` (or active path during Story 10 transition)
- file contains sections: Scope, Inherited decisions, Open decisions per session, Estimated work
- audit trail records handoff prompt emission

---

#### Scenario 9.4 — `story-10-aisalesht-development-branch-final-state` (`type: adversarial`)

**Given:**
- Pre-archive AISALESHT, the `development` branch has Story 10 in-flight commits (impl logs, checkpoints, etc.).
- During Feature 7 (/pm SSoT migration), AISALESHT `docs/product/` removed. AISALESHT story content NO migrated to luana-platform (the new home is `luana-platform/docs/archive/...`).

**When:**
- Final state of AISALESHT pre-archive.

**Then:**
- AISALESHT `development` branch contains:
  - Story 10 impl-logs T-1..T-N (impl audit trail) — moved to luana-platform via SSoT migration
  - Final closure commits referencing migration completion
  - `docs/process/learnings.md` Session 5 entry (R12 process metric)
- AISALESHT `backend/src/` + `frontend/` REMOVED (FE moved to luana-platform/nicolify/frontend/; BE imports cleaned in nicolify location).
  - Architect verifies cleanup strategy: keep skeleton + readme pointing to luana-platform OR remove entirely (AISALESHT becomes empty repo archive marker).
- Final pre-archive commit: `chore: closure pre-archive — Story 10 complete, see luana-platform`.

**Graders:**
- shell `cd /home/chris/AISALESHT && git status --short` → empty (clean tree)
- shell `cd /home/chris/AISALESHT && git log --oneline -5` shows closure commits
- audit trail captures final AISALESHT state before archive UI action

---

## 6. Non-functional requirements

| Categoría | Requisito | Verificador |
|---|---|---|
| Test parity | Delta=0 new failures BE + FE vs baseline T-1 snapshot | Feature 4 scenarios + scripts/test_delta_check.py |
| AISALESHT closure | History preserved + read-only post-archive | Feature 8 Scenario 8.4 |
| /pm SSoT integrity | Scripts (generate_backlog + reconcile_capabilities) green post-move | Feature 7 Scenario 7.1 graders |
| Smoke E2E | Chris journey end-to-end GREEN | Feature 5 graders |
| ci-parity migration | Root Makefile target + pre-push hook | Feature 6 graders |
| Tenant isolation cumulative | All luana-core packages preserve `.where(tenant_id == ...)` filters post import rewrite | Feature 5 Scenario 5.4 + arch fitness existing |
| Soft deletes preserved | Migration preserves `deleted_at` patterns | Existing arch fitness backend tests (no regression) |
| SQLA 2.0 only | No `session.query()` introduced (per backend-ddd.md) | Existing arch fitness backend tests (no regression) |
| Spanish neutro | User-facing strings preserved (no voseo introduced) | Pre-commit hook Section 5 (voseo enforcement) — verify post-move it still fires |
| R3 downstream regression | Stories 1-9 luana-core packages tests preserved GREEN | Feature 4 cumulative + Story 9 baseline 149 arch fitness GREEN |
| Cost ceiling | Session 5 cumulative ≤ $5000 (soft check-in markers @ $4000 + $4500 + $5000) | R12 process metric emission |
| PII sanitization | Migration preserves all `response_model=` Pydantic patterns | Existing arch fitness (no regression — verify still GREEN) |
| Cap paralelización | ≤2 sub-agents concurrent (Decisión 1A NOT 3) | /dev-team orchestration enforcement |
| Opus priority | Critical tickets (imports rewrite, schema consolidation, /pm SSoT migration, Vercel reconfig) → Opus | Checkpoint frontmatter opus_priority + /dev-team router |
| Halt-and-ask compliance | All 10 §7.6.2 triggers honored — no silent proceed | Audit trail T-N-impl-log.md records triggers + Chris ratify |

## 7. Constraints técnicos heredados

- `.claude/rules/git-safety.md` — single branch `development` AISALESHT + `main` luana-platform. No feature branches. No `--force` push.
- `.claude/rules/parallel-safety.md` — Session 5 single sequential autonomous (Decisión 10A scope). Cap ≤2 paralelo Decisión 1A is for sub-agents within Story 10, NOT cross-session.
- `.claude/rules/backend-migrations.md` — alembic consolidated migration MUST use raw SQL `IF NOT EXISTS` / `IF EXISTS` patterns.
- `.claude/rules/backend-ddd.md` — preserve DDD layers post import rewrite. Imports rewrite ONLY — no boundary refactors.
- `.claude/rules/tenant-isolation.md` — `.where(Model.tenant_id == tenant_id)` filters preserved cumulative.
- `.claude/rules/frontend-fsd.md` — FSD-Lite preserved post FE workspace move. Boundaries plugin verifies.
- `.claude/rules/anti-duplication.md` — Imports rewrite uses luana-core packages (already lifted Stories 1-8) — NO mirror local copies in nicolify.
- `.claude/rules/anti-default-flip-audit.md` — Story 10 NO flips feature flag defaults. Pure migration.
- `.claude/rules/auditor-downstream-regression.md` — R3 scope applies. Auditor verifies downstream regression Stories 1-9 packages.
- `.claude/rules/tdd-mandatory.md` — Migration is mechanical, but ANY new code (test_delta_check.py, codemod scripts) requires tests.
- `.claude/rules/spanish-text.md` — preserved user-facing strings. Migration is mechanical — no string changes expected.
- `.claude/rules/e2e-testing.md` — Smoke E2E Feature 5 follows playwright-expert skill patterns. NEVER `make e2e*` Docker.
- `.claude/rules/hotfix-repro-mandatory.md` — N/A (Story 10 is not hot-fix, is planned migration).
- Outcome §7.6 binding decisions — all 10 binding pre-spec.
- Outcome §7.6.2 halt-and-ask triggers — paraliza + escala Chris.
- Outcome §7.6.3 success criteria — Story 10 done definition (matches §9 below verbatim).

## 8. Cross-module impact

- **Lee de:** todos los 26 luana-core packages + 7 @luana TS packages (Story 9 published v0.1.0 consumer)
- **Es leído por:** Stories 10b (admin/workers cleanup), Stories 11-13 (vertical brand bootstraps inherit pattern), Story 14 (sales_agent brand voice elevation natural home for 40 failures fix)
- **Eventos emitidos:** ninguno runtime. GitHub event `repository.archived` (AISALESHT) si Chris archives via API vs UI.
- **Eventos consumidos:** ninguno runtime.
- **Side-effects externos:**
  - GitHub repo AISALESHT marked archived (read-only)
  - GitHub repo luana-platform receives /pm SSoT atomically
  - Postgres DB visionarias_logs dropped post-soak
  - Postgres DB nicolify_dev created with consolidated snapshot
  - Vercel project reconfig (root directory + build commands + linked repo)
  - CF tunnel `dev-app.nicolify.com` mapping preserved (or re-mapped post-Vercel reconfig)

## 9. Done definition (matches outcome §7.6.3 verbatim)

Story 10 reaches `done` state when ALL true:

- ✅ BE: imports rewritten `from src.modules.X` → `from luana_core_X` en 26 packages target
- ✅ FE: imports rewritten `@/...` → `@luana/...` + FE workspace member luana-platform
- ✅ Fresh `nicolify_dev` DB + alembic snapshot consolidated + AISALESHT DB dropped
- ✅ Tests BE: same coverage threshold 43% + delta=0 new failures vs baseline
- ✅ Tests FE: same coverage threshold 20% + delta=0 new failures vs baseline
- ✅ Playwright smoke E2E green (Chris journey end-to-end through nicolify app)
- ✅ ci-parity root green (luana-platform/Makefile orchestrates)
- ✅ /pm SSoT migrated to luana-platform/docs/product/ + scripts verified
- ✅ AISALESHT repo archived GitHub UI
- ✅ 07-merge.md + capability promoted + outcome §1 stories_done 10/14 appended
- ✅ Handoff prompt Story 10b generated for Chris next session

## 10. Risks

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| 1 | Import rewrite surface massive (~20k LOC) cross 18 modules + 11 shared subsystems — codemod errors cascade silently | High | Codemod uses libcst (AST-based) per package, not sed regex. Test mocks pivoted in same step. Auditor C2 verifies cumulative via grep. Cap ≤2 paralelo (Decisión 1A) reduces blast radius. |
| 2 | Alembic snapshot consolidation surface model↔schema drift | Medium-High | Feature 3 Scenario 3.2 halt trigger #5. Architect Phase 0 spike: extract schema from prod via pg_dump + autogenerate from models → diff → resolve before T-N. |
| 3 | Vercel reconfig surprise (custom domain, env vars, monorepo build) | Medium-High | Feature 2 Scenario 2.3 halt trigger #3. Chris may need to execute Vercel UI steps manually. Architect provides exact step list. |
| 4 | CF tunnel `dev-app.nicolify.com` mapping rompe post-FE-move | Medium | Halt trigger #4. Mitigation: re-establish tunnel pointing to new Vercel URL. Chris verifies. |
| 5 | Test mocks stale paths cause silent test pass (no real coverage) | High (silent failure) | Feature 1 Scenario 1.4 arch fitness test_no_legacy_src_mock_paths.py. Auditor C5 cross-cutting check. |
| 6 | /pm SSoT migration hardcoded paths discovered mid-move | Medium | Feature 7 Scenario 7.2 halt trigger via Decisión 4A. Architect Phase 0 grep audit pre-move. |
| 7 | 24h soak elapses but issue surfaces post-archive | Low-Medium | Archive reversible 1-click via GitHub Settings. Chris can unarchive if needed. |
| 8 | Cap paralelización ≤2 violated by /dev-team orchestrator | Low | /dev-team explicit cap_paralelization=2 setting per checkpoint frontmatter parallelization_cap field. |
| 9 | Cost > $5000 cap | Low (soft check-in) | R12 process metric emission @ $4000/$4500/$5000. Chris reports. |
| 10 | Auditor + 2 auto-fix iter all fail → no 3rd iter sin Chris | Procedural | Halt trigger #10. Escalate Chris per outcome §7.6.2. |
| 11 | Story 10 archive lands at wrong location (AISALESHT vs luana-platform post SSoT migration) | Low | Feature 9 explicit scenario. /pm enforces archive lands at luana-platform location post Feature 7. |
| 12 | 40 sales_agent pre-existing failures accidentally addressed (scope expansion) | Medium | Decisión 9B + DEFERRED-FAILURES-STORY-10.md cross-reference. Auditor verifies fix-on-discovery limited to 5min cap. Story 14 natural home. |
| 13 | Workers/ETL scheduler regression silent (not in scope but might break post-import-rewrite) | Medium | Architect escape hatch: include workers if trivial. Otherwise tests for workers run but failures DEFERRED Story 10b. Document explicitly. |
| 14 | luana-platform git history pollution from large `git mv` of `frontend/` (FE workspace move) | Low | Architect verifies `git mv` strategy preserves history (use `--follow` aware). May result in repo size growth — accept. |

## 11. Open questions (for architect Story 10 Phase 0 resolution — NOT for Chris)

> Architect Story 10 resuelve estas en Phase 0 sin escalate Chris (within outcome §7.6 binding decisions). Si surface uno NUEVO no cubierto, escalate per halt criteria.

1. **Codemod tool choice:** libcst (Python AST-based) preferred per safety; vs sed scripts (faster but error-prone); vs jscodeshift (TS). Architect commits choice + writes codemod scripts.
2. **Consolidated migration strategy:** handcraft from pg_dump (precise) vs `alembic revision --autogenerate` from models (model-driven). Architect Phase 0 spike: which yields fewer drift surprises Scenario 3.2.
3. **FE workspace nesting:** `nicolify/` flat with FE replacing stub vs `nicolify/frontend/` nested. Architect commits choice + pnpm-workspace.yaml update.
4. **Vercel build command:** `pnpm --filter @luana/nicolify-web build` (workspace-aware) vs `cd nicolify/frontend && pnpm build` (CWD-based). Architect verifies which works with Vercel monorepo support.
5. **CF tunnel re-mapping:** keep existing tunnel pointing to new Vercel URL vs new tunnel. Architect decides + Chris verifies post-reconfig.
6. **AISALESHT pre-archive final state:** keep skeleton + README pointing to luana-platform vs empty repo (just .git + LICENSE). Architect commits choice.
7. **Pre-commit hook migration:** scripts/git-hooks/pre-commit moves to luana-platform/ — does it still detect AISALESHT-specific paths? Architect rewrites Sections 4-9 paths.
8. **Test delta script path:** new script `scripts/test_delta_check.py` lives in luana-platform (cross-brand tool) vs nicolify-specific. Architect decides + writes script.
9. **Story 10 archive timing:** archive Story 10 at end of Session 5 (with Story 10 docs in luana-platform/docs/archive/) vs partial close (archive after Story 10b ratification). Architect aligns with /pm orchestrator.
10. **Workers tactical inclusion:** which workers (if any) qualify "trivial" per Decisión 7B escape hatch — architect lists candidates in Phase 0 spike.

## 12. Validators preview (for architect 04-validators.yaml)

Architect Story 10 emits `04-validators.yaml` con minimum 25 validators across 4 categories. Preview list:

### Non-functional (V-NF-*)
- **V-NF-1:** AISALESHT `backend/src/` + `frontend/` cleanup state (per architect — empty or skeleton).
- **V-NF-2:** AISALESHT archived state (GitHub `archived: true`).
- **V-NF-3:** visionarias_logs DB dropped post-soak.
- **V-NF-4:** nicolify_dev DB exists + alembic head reports consolidated.
- **V-NF-5:** No `from src\.` imports remanentes in luana-platform/nicolify/backend (grep audit).
- **V-NF-6:** No `from "@/` imports remanentes in luana-platform/nicolify/frontend (grep audit).
- **V-NF-7:** Tests delta=0 BE + FE vs baseline.
- **V-NF-8:** Cap paralelización ≤2 honored (audit /dev-team orchestrator log).

### Functional (V-F-*)
- **V-F-1:** Smoke E2E Chris journey GREEN.
- **V-F-2:** ci-parity root Makefile target exists + GREEN.
- **V-F-3:** Pre-push hook luana-platform invokes ci-parity.
- **V-F-4:** /pm SSoT scripts (generate_backlog + reconcile_capabilities) GREEN post-move.
- **V-F-5:** Pre-commit hooks fire post-/pm-SSoT-move on luana-platform.
- **V-F-6:** Vercel deployment successful + CF tunnel resolves dev-app.nicolify.com.
- **V-F-7:** Story 10 archive at luana-platform/docs/archive/.
- **V-F-8:** HANDOFF-STORY-10B.md generated.
- **V-F-9:** DEFERRED-FAILURES-STORY-10.md generated with 40 sales_agent paths.

### Agentic / Integration (V-AG-*)
- **V-AG-1:** Sales agent conversation via luana_core_sales_agent path GREEN (smoke step 6-7).
- **V-AG-2:** Trace event + cost_usd recorded via luana_core_observability path (no NULL cost regression — Story PI-12 S1 T-1.bis lesson).
- **V-AG-3:** Tenant isolation cross-leak blocked smoke Scenario 5.4.
- **V-AG-4:** R3 downstream regression Stories 1-9 luana-core packages cumulative GREEN.

### Documentation + cross-cutting (V-D-*)
- **V-D-1:** /pm SSoT BACKLOG.md regenerated post-move + reflects Story 10 done.
- **V-D-2:** Capability promoted to luana-core/brand-consumer-migration (or per architect).
- **V-D-3:** Outcome §1 stories_done 10/14 appended.
- **V-D-4:** Learnings.md Session 5 entry recorded (R12 process metric).

## 13. Cross-story handoff (Stories 10b + 11-14 enablement)

Story 10 merge unblocks:

**Story 10b (immediate next session per Decisión 10A):**
- Receives: HANDOFF-STORY-10B.md
- Scope: Streamlit admin migration + workers/ETL scheduler cleanup
- Inherited decisions: most §7.6 (AISALESHT archived, /pm SSoT in luana-platform, ci-parity root pattern, etc.)
- Open re-ratify: Decisión 1A (full big bang vs phased), specific worker inclusions

**Stories 11-13 (vertical brand bootstraps):**
- Receives: Nicolify-as-canonical-case proven pattern
- Inherited decisions per §7.6.1 inheritance matrix
- Each brand bootstraps using same FE workspace member + Vercel reconfig + brand-specific config

**Story 14 (brand-voice-elevation):**
- Receives: DEFERRED-FAILURES-STORY-10.md with 40 sales_agent failure paths
- Scope: fix 40 failures + PersonalityProfile + voice cloning refactor

## 14. Próximo paso

- **Pre-ratification check:** Chris reads spec, verifies §7.6 binding decisions correctly elaborated + scenarios cover §7.6.3 success criteria. Ratifica wording.
- **Post-ratification:** /pm transitions state=refining → refined. /architect picks up.
- /architect Story 10 lee este 01-spec.md + outcome §7.6 + §7.6.1 + §7.6.2 + §7.6.3 + Story 9 07-merge.md + migration-from-nicolify.md → produces 03-arch.md + 04-validators.yaml + 05-guidelines.md + 06-tickets.yaml = ready package.
- /dev-team Session 5 autonomous build picks Story 10 sequential per Decisión 10A + cap ≤2 paralelo Decisión 1A.
- /auditor Story 10 post developed → reviewing → CHECKPOINTS C1-C5.
- /pm merge → outcome stories_done = [Stories 1-10] → Stories 10b + 11-14 unblocked (per cross-story handoff §13).

## 15. Open question for Chris (NEW halt trigger candidate — flag at end of spec per /po skill mandate)

> /po skill instruction: "Si durante spec drafting identifico un NEW halt trigger no en §7.6.2 → flag at end of spec for Chris review (don't fabricate, just surface)."

**Candidate NEW halt trigger #11 (proposed):**

- **Trigger:** Sub-agent rewrite encuentra un test mock que apunta a un path en `src.shared.X` que NO tiene equivalent claro en luana-core packages (e.g., legacy mock para internal helper que nunca fue lifted Stories 1-8). Different from trigger #1 (production imports missing) — this is test infra only.
- **Why propose:** test mocks can be drift-prone (silent fail Scenario 1.4) and may surface non-trivially during rewrite. Trigger #1 covers production missing exports; this covers test-only missing patches.
- **Mitigation if accepted:** sub-agent halt + ask Chris whether to (A) inline mock value into test (no patch), (B) lift symbol via Story 14 deferred, (C) skip test temporarily with magic comment `# luana-migration-defer` + Story 14 ticket.

**Chris decides:** accept as Trigger #11 OR fold into existing Trigger #1 (broader interpretation) OR reject as non-issue.

**Ratified Chris 2026-05-12 Session 5 Phase 1:** ✅ Accept as Trigger #11 distinct. Outcome §7.6.2 updated. Sub-agents during Phase 2 build MUST honor Trigger #11 halt rule.

## Changelog

- v1 2026-05-12 — /po Opus draft inicial post Phase 0 ratification §7.6 10 decisions. 9 features (40 scenarios total covering happy + negative + edge + adversarial each). Halt triggers cited per §7.6.2 in scenarios where apply. NEW trigger candidate #11 flagged §15. Ready for Chris ratification.
