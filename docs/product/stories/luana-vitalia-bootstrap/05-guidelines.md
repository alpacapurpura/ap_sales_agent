<!-- voseo-allowed: guidelines cite rules + glossary verbatim for traceability per R25 -->
---
story_id: luana-vitalia-bootstrap
guidelines_version: 1
architect_owner: claude-opus-4-7
ratified_by_chris: false
last_modified: 2026-05-13
parent_docs:
  - 01-spec.md
  - 02-design-agentic.md
  - 03-arch.md
  - 03-arch-be.md
  - 03-arch-fe.md
  - 03-arch-agentic.md
purpose: |
  Patterns required/forbidden for sub-agent builders + auditors during Story 11 build phase.
  Files in scope per ticket. Skills/rules to load per sub-agent type. R23 owner_eligibility matrix.
  Working directory: /home/chris/luana-platform/ (NOT AISALESHT — Story 11 code lives in luana-platform subdir).
---

# 05-guidelines.md — Story 11 luana-vitalia-bootstrap

> **Read first:** 01-spec.md § 3 Gherkin scenarios (BINDING — sub-agents implement to pass) + 02-design-agentic.md § 6 tools spec + 03-arch.md § 8 acceptance + this doc (process discipline).
>
> **Audience:** `builder-{backend,frontend,agentic}` sub-agents during T-1..T-N build phase. Auditors `auditor-{backend,frontend,agentic}` consume this doc to verify compliance.

## 0. Cap parallelization + R23 owner eligibility (binding Chris framing)

**HARD CONSTRAINT:** ≤2 sub-agents simultaneous (Story 10 precedent — Chris stability over speed). `/dev-team` orchestrator enforces via `parallelization_cap: 2` in checkpoint frontmatter.

**Opus 4.7 mandatory tickets (R23 — production AGENTIC code):**
- All 4 tools tickets (T-tools-{1..4})
- 2 extractors tickets (T-extractors-{1,2})
- 1 workflow ticket (T-workflow-1) — TreatmentFollowupWorkflow LangGraph
- 3 KB pack ingestion tickets (T-kb-{1..3})
- 4 guardrails tickets (T-guards-{1..4})
- Prompt slots + voice integration ticket (T-prompts-1)
- Extension SDK register_all entry (T-extensions-1)
- Vertical-medical-fidelity rubric MD v1 (T-rubric-1) — Opus by virtue of authoring spec docs

**Sonnet OK tickets (non-agentic OR tests-over-agentic):**
- Vitalia subdir scaffolding (T-scaffold-1)
- BrandConfig YAML declarative (T-config-1)
- BE models + repos + migrations (T-be-{1..3})
- BE services non-agentic (Onboarding, Booking, PrepaidPayment, Consent, Compliance) (T-be-{4..6})
- BE endpoints + DTOs (T-be-{7,8})
- FE routes + components + hooks + schemas (T-fe-{1..5})
- Booking widget bundle (T-widget-1)
- E2E Playwright specs (T-e2e-1)
- K8s manifests + CF tunnel scripts (T-deploy-1)
- Docs (compliance.md + booking-widget-embed.md) (T-docs-1)

**Sub-agent prompt header for Opus tickets** MUST contain:
```
PRODUCTION CODE: true (R23 — agentic production code mandates Opus 4.7)
PARALLELIZATION CAP: 2 concurrent agents max (Story 10 Decisión 1A precedent)
HALT TRIGGERS: per 04-validators.yaml halt_triggers — escalate Chris, no silent proceed
```

## 1. Required patterns (sub-agent MUST honor)

### 1.1 DDD Inside-Out (BE per `.claude/rules/backend-ddd.md`)

**REQUIRED:**
- Layer order: `domain` → `infrastructure` → `application` → `api`. Domain pure (no framework). Infrastructure implementa interfaces domain. Application = services/use cases. API = FastAPI routes + Pydantic DTOs (thin).
- Every query filter `tenant_id` (incluye `get_by_id`).
- Soft deletes only (`deleted_at` column). Audit log table exception (immutable, no deleted_at).
- SQLA 2.0 `select(Model).where(...)` (no `session.query()`).
- New code `AsyncSession`. NO `Session` legacy.
- `structlog`, NO `print` / `logging`.
- Pydantic v2 `model_config = ConfigDict(...)` (no inner `class Config`).
- FastAPI app `FastAPI(redirect_slashes=False)` mandatory en `main.py` (arch test enforces).
- Repository constructor receives `tenant_id` required param.

### 1.2 Anti-duplication (per `.claude/rules/anti-duplication.md`)

**REQUIRED Step 0 GATE before write/edit:**
```bash
# For each NEW class/module/file proposed:
find /home/chris/luana-platform/core -name "<ClassName>.py" 2>/dev/null
grep -rn "class <ClassName>" /home/chris/luana-platform/{core,nicolify}/ 2>/dev/null
grep -rn "class <ClassName>" /home/chris/AISALESHT/backend/src/ 2>/dev/null  # legacy ref (Story 10 mirror)
```

If match → ESCALATE to PM with paths + diff conceptual + recomendación (A extend / B lift / C edge new).

**Inventory SSoT (per anti-duplication.md):** EXTEND from `shared/`, NEVER mirror.

- `BaseExtractionOrchestrator` → vitalia MedicalKBExtractor + DentalHistoryExtractor EXTEND
- `BaseAgentCallbackHandler` → vitalia agentic surface CONSUMES (no override)
- `FXResolver.default()` → vitalia payment services CONSUME
- `sanitize_payload` → vitalia observability writes USE (NEVER re-implement)
- `format_for_channel` → vitalia channel adapters USE
- `ExtensionPointRegistry` → vitalia.extensions.py CONSUMES via `register_all`
- `@luana/core/scheduling.calendar` → vitalia appointment_reschedule_with_doctor EXTENDS (Q4=A)

**Special: MercadoPago adapter** — verify @luana/core/channels/payment/MercadoPagoAdapter exists during T-X (FIRST payment ticket). If NOT → LIFT SHARED to core first, EXTEND vitalia second. If yes → EXTEND directly.

### 1.3 TDD mandatory (per `.claude/rules/tdd-mandatory.md`)

**REQUIRED RED → GREEN → REFACTOR per layer:**
- BE (pytest, DDD): domain → infrastructure → application → API. RED por capa antes implementar.
- FE (Vitest): hook → component → store. RED antes.
- E2E (Playwright): ruta nueva → smoke en `e2e/specs/vitalia/` ANTES página.

**Forbidden:** código sin test. Commit con tests rotos. `skip`/`xfail` para pasar CI. Reducir coverage con código nuevo sin tests.

### 1.4 Tenant isolation (per `.claude/rules/tenant-isolation.md`)

**REQUIRED:**
- `.where(Model.tenant_id == tenant_id)` en TODA query (incluye `get_by_id`).
- `tenant_id` from `X-Tenant-ID` header injected by Clerk JWT middleware (authoritative).
- Repos reciben `tenant_id` required param at constructor.
- FE `fetchClient` auto-inyecta `X-Tenant-ID` from Clerk session_claims.public_metadata.active_tenant_id.

### 1.5 Master data + currency (per `.claude/rules/master-data.md` + `currency-handling.md`)

**REQUIRED:**
- BE store UTC (`utc_now()`, `DateTime(timezone=True)`).
- `TenantLocale` VO (shared/domain/locale.py), DI `get_tenant_locale()`.
- FE `useTenantLocale()` → `{ currency, timezone }`. Display: `formatTenantDate*()`, `formatMoneyDual()`.
- DTOs monetary fields include `currency: str | None = None` (ISO 4217).
- FE fallback `data.currency ?? useTenantLocale().currency`. **NEVER hardcode 'USD'.**

### 1.6 PII sanitization (per Tessl `pii-sanitisation.md`)

**REQUIRED:**
- Every FastAPI endpoint `response_model=` Pydantic model.
- `sanitize_payload` invoked BEFORE persist observability/audit data.
- Medical PII extension: patient names → mask "J. P.", DNI/RUT/RFC → `[NATIONAL_ID]`, phone → `+54***5555`, email → `j***@***.com`, signature URLs → `[CONSENT_URL_REDACTED]` post-signing.
- Medication names + medical conditions kept verbatim (clinically relevant) + log `medical_pii_detected` event.
- Offer description + testimonial input scan PRE-persist (spec § 3.2.D + § 3.3.D).

### 1.7 Migrations idempotent (per `.claude/rules/backend-migrations.md`)

**REQUIRED:**
```python
op.execute("CREATE TABLE IF NOT EXISTS ...")
op.execute("ALTER TABLE x ADD COLUMN IF NOT EXISTS ...")
op.execute("CREATE INDEX IF NOT EXISTS ...")
```

- NEVER `op.create_table()` / `op.add_column()` / `op.create_index()` (not idempotent).
- NEVER `sa.Enum(..., create_type=True)` (broken SA 2.0.27 — use raw SQL `DO $$ BEGIN CREATE TYPE ...; EXCEPTION WHEN duplicate_object THEN NULL; END $$;`).
- Single consolidated snapshot Story 10 T-10 pattern: `001_vitalia_initial_snapshot.py`.

### 1.8 Spanish neutro chrome UI (per `.claude/rules/spanish-text.md` R2 + Q1=B ratified)

**REQUIRED:**
- Chrome UI (clinic_owner-facing) Spanish neutro tuteo only: tú/tu/tienes/eres/puedes/haces.
- NO voseo en buttons/forms/breadcrumbs/toasts/validaciones.
- Microcopy SSoT spec § 8.1-§ 8.6 (immutable post-ratification).
- Magic comment `// voseo-allowed: <reason>` honored ONLY in test fixtures / rule docs / audit reports (NEVER user-facing strings).

**Exception sales_agent voice:** Per `.claude/rules/sales-agent-brand-voice.md` — voice respects `personality_profiles.system_instruction` per tenant. Aurora AR voseo OK, Mindful CL neutro chileno, Sanaré LATAM neutro broad.

### 1.9 Anthropic prompt cache (per `claude-api` skill)

**REQUIRED:**
- Slots 1-6 `cache_control: {"type": "ephemeral"}` markers.
- Slots 7-10 NOT cached.
- Per-tenant cache_key `prompt_cache_key=str(ctx.tenant_id)` for Slot 5 BRAND_VOICE isolation.
- Target ≥85% cache hit rate on slots 1-6.
- NEVER interpolate `{tenant_name}` / timestamps / patient PII mid-block in cacheable slots.

### 1.10 Agentic R23 production code (per `.claude/rules/copilot-resilience.md` + `copilot-observability.md`)

**REQUIRED:**
- All tools wrap `try/except + structlog warning` (best-effort, no break turn).
- All trace_event + llm_call writes via `try/except + structlog.warning("...persist_failed", exc=str(e))`.
- PII redacted via `sanitize_payload(...)` BEFORE persist.
- Tool dispatcher injects `tenant_id` from `ctx` (NOT from input schema — security boundary).
- Idempotency keys per tool action.

### 1.11 FSD-Lite (FE per `.claude/rules/frontend-fsd.md`)

**REQUIRED:**
- Server Components default. `"use client"` solo cuando necesario (interactive forms, useState, event handlers, Clerk hooks, React Query).
- React Query (data fetch). RHF + Zod (forms). Tailwind + `cn()`.
- NO `any` (`unknown` + type guards). NO default exports (excepto Next pages).
- Cross-feature imports forbidden default. Brand isolation per path (NO `from "@/features/nicolify/..."` in vitalia code).

## 2. Forbidden patterns (sub-agent MUST NOT do)

### 2.1 Scope expansion (HARD STOP)

**FORBIDDEN:**
- ❌ Touch `modules/copilot/` OR `modules/sales_agent/` runtime source (vitalia CONSUMES via Extension SDK, never modifies core).
  - **Exception per `.claude/rules/backend-ddd.md` §Schema-mirror exception:** if Story 11 introduces shared/ migration with new columns referenced by copilot/sales_agent ORM models, vitalia tickets MAY touch `modules/{copilot,sales_agent}/persistence/models/` for schema mirror ONLY (no domain/application/api/observability changes). Story 11 likely does NOT trigger this — vitalia tables are isolated `vitalia_*` namespace.
- ❌ Touch `nicolify/` brand dir. NICOLIFY is Story 10 cement.
- ❌ Touch `comunify/` or `lupulo/` (parked Stories 12/13).
- ❌ Touch `core/luana-core-*` packages without anti-duplication.md Step 0 GATE + PM escalation.
- ❌ Refactor Luana platform foundational architecture. Story 11 = vertical brand bootstrap, NOT platform refactor.
- ❌ Add new feature flags or flip existing flag defaults (Story 11 = pure greenfield).
- ❌ Modify Story 10 archived artifacts (`docs/archive/2026/stories/luana-nicolify-migration/`).
- ❌ Modify parallel WIP AISALESHT files (`buyer-persona-ai-flow-verified.png`, `qa-extract-clean.png`, `docs/etl/extraction-contract.md`).
- ❌ Modify parallel WIP luana-platform files (`core/DEFERRED-FILES.md`, `core/luana-core-platform/src/luana_core_platform/{infrastructure/model_registry.py,links/ports/calendar.py}`, 8 arch tests `core/tests/architecture/test_*.py`, `pyproject.toml`).
- ❌ Touch `01-spec.md` / `02-design-agentic.md` / `00-phase0-ratification.md` (immutable post-ratification — Sesion 1 closed).

### 2.2 BE anti-patterns

**FORBIDDEN:**
- ❌ `session.query()` (SQLA 1.x banned).
- ❌ `datetime.utcnow()` (use `utc_now()`).
- ❌ `DateTime()` without `timezone=True`.
- ❌ Hardcode `'USD'` (consume `data.currency`).
- ❌ Pydantic default `= "USD"` outside allowed files.
- ❌ `print()` / `logging.*` (use `structlog`).
- ❌ Endpoint without `response_model=` Pydantic.
- ❌ Raw dicts / ORM / untyped returned from endpoints (arch fitness gate).
- ❌ Cross-module import without port (excepción copilot infra-like).
- ❌ Mirror `shared/agent_observability` patterns in `modules/vitalia/agentic/observability/` — extend shared base.

### 2.3 FE anti-patterns

**FORBIDDEN:**
- ❌ `any` types (use `unknown` + type guards).
- ❌ Default exports (excepto Next.js pages).
- ❌ Cross-feature imports (NO `from "@/features/nicolify/..."` from vitalia).
- ❌ Voseo verbs in user-facing chrome UI strings (per spec § 8 microcopy SSoT + arch fitness gate).
- ❌ Hardcode currency `'USD'` (consume `useTenantLocale().currency` or `data.currency`).
- ❌ `toLocaleDateString()` (use `formatTenantDate*()`).
- ❌ Patient PII in URL params / localStorage / sessionStorage (use POST body + signed JWT tokens).
- ❌ `// eslint-disable-next-line` without justification comment.
- ❌ `make e2e*` Docker E2E (crashes WSL2 — per playwright-expert SSoT, use native `npx playwright test`).

### 2.4 AGENTIC anti-patterns

**FORBIDDEN:**
- ❌ Tool input schema includes `tenant_id` (must be injected via ctx, security boundary).
- ❌ LLM call without `response_model=` Pydantic schema (where applicable).
- ❌ Interpolate `{tenant_name}` / timestamps / patient PII in cacheable slots 1-4 + 6.
- ❌ Diagnose / prescribe in LLM response (production-critical safety bar adversarial pass^5 ≥0.95).
- ❌ Skip guardrail chain (input + output pipeline order enforced).
- ❌ Skip RAG citation in `copilot_trace_event.context_used`.
- ❌ Write to `copilot_llm_call` from eval runs (cost bucket separation Story B/E cement — write to `eval_simulator_llm_call`).
- ❌ Re-implement `sanitize_payload` (consume shared).
- ❌ Spawn AGENTIC production code ticket with Sonnet owner_eligibility (R23 hard rule).

### 2.5 Process anti-patterns

**FORBIDDEN:**
- ❌ `git pull` / `git fetch && merge` (per `.claude/rules/parallel-safety.md` cardinal).
- ❌ `git push --force` / `--force-with-lease`.
- ❌ `git revert` without explicit Chris approval.
- ❌ `git add .` / `-A` / `-u` (parallel sessions WIP — stage by exact filename).
- ❌ `git commit --no-verify` (pre-commit hook mandatory).
- ❌ Feature branches / worktrees / release branches.
- ❌ Skip Step 0 GATE anti-duplication grep before write.
- ❌ Skip TDD RED → GREEN.

## 3. Files in scope

### 3.1 Working directory

**Builders work primarily in `/home/chris/luana-platform/vitalia/`** (NOT AISALESHT — Story 11 code lives in monorepo subdir).

### 3.2 IN SCOPE Story 11 (exhaustive paths)

```
/home/chris/luana-platform/vitalia/
├── backend/
│   ├── src/modules/vitalia/
│   │   ├── domain/
│   │   ├── infrastructure/
│   │   ├── application/
│   │   ├── api/
│   │   ├── agentic/                # R23 Opus mandatory
│   │   ├── copilot/                # R23 Opus mandatory (extractors + workflows + KB)
│   │   ├── payment/                # Adapters (Stripe + MP + Tokenized)
│   │   └── extensions.py
│   ├── alembic/versions/001_vitalia_initial_snapshot.py
│   ├── tests/unit/
│   ├── tests/integration/
│   ├── tests/e2e/
│   ├── tests/agentic_evals/
│   ├── tests/architecture/
│   └── scripts/
│       ├── seed_fixture_clinics.py
│       └── seed_medical_kb.py
├── frontend/
│   ├── src/
│   │   ├── app/                    # Next.js 16 App Router routes
│   │   └── features/vitalia/       # FSD-Lite
│   ├── widget/                     # Embeddable iframe bundle
│   ├── e2e/specs/vitalia/          # Playwright E2E
│   ├── tests/                      # Vitest
│   ├── package.json
│   └── next.config.ts
├── config/
│   └── brand.yaml                  # Declarative BrandConfig
├── deploy/
│   ├── k8s/                        # K8s manifests
│   └── cloudflared/                # CF tunnel config
├── docs/
│   ├── compliance.md
│   └── booking-widget-embed.md
├── pyproject.toml
├── package.json
└── README.md

/home/chris/AISALESHT/docs/   (docs only — code lives in luana-platform)
├── product/stories/luana-vitalia-bootstrap/
│   ├── 01-spec.md (immutable post-ratification)
│   ├── 02-design-agentic.md (immutable post-ratification)
│   ├── 00-phase0-ratification.md (immutable)
│   ├── 03-arch.md
│   ├── 03-arch-be.md
│   ├── 03-arch-fe.md
│   ├── 03-arch-agentic.md
│   ├── 04-validators.yaml
│   ├── 05-guidelines.md (this file)
│   ├── 06-tickets.yaml
│   ├── checkpoint.md
│   └── T-{n}-impl-log.md (per ticket)
└── specs/
    ├── personas/archetype-aware/
    │   ├── patient-anxious-dental-ar.yaml (NEW)
    │   ├── patient-depressed-psych-cl.yaml (NEW)
    │   ├── patient-unresponsive-followup-mx.yaml (NEW)
    │   ├── patient-adversarial-diagnosis-mx.yaml (NEW)
    │   ├── patient-prompt-injection-attempt.yaml (NEW)
    │   └── patient-medication-recommendation-mx.yaml (NEW)
    └── rubrics/
        └── vertical-medical-fidelity.md (NEW MD v1)
```

### 3.3 OUT-OF-SCOPE (anti-creep)

- `/home/chris/luana-platform/nicolify/**` (Story 10 cement, immutable)
- `/home/chris/luana-platform/comunify/**` (Story 12 parked)
- `/home/chris/luana-platform/lupulo/**` (Story 13 parked)
- `/home/chris/luana-platform/core/**` (consume only — exception: lift MercadoPagoAdapter to `core/luana-core-channels/payment/` first ticket if needed, with PM escalation)
- `/home/chris/luana-platform/apps/test-brand/**` (Story 9 cement)
- `/home/chris/AISALESHT/backend/**` (parked post Story 10 T-14)
- `/home/chris/AISALESHT/frontend/**` (parked post Story 10)
- Story 11.bis deferred items: real piloto clínica, multi-site UI federation, insurance integration, voice cloning, Stripe Healthcare flag, wellness deep coverage, telemedicine native, doctor mobile app.

## 4. Skills + rules per ticket type

### 4.1 Skills/rules per surface

| Surface | Skills MUST load | Rules MUST load |
|---|---|---|
| Tools tickets (R23 Opus AGENTIC) | `sales-agent-expert` + `copilot-expert` + `tessl__langgraph` + `claude-api` | `sales-agent-brand-voice` + `copilot-resilience` + `copilot-observability` + `anti-duplication` + `tenant-isolation` |
| Extractors tickets (R23 Opus AGENTIC) | `copilot-expert` + `sales-agent-expert` + `tessl__langgraph` + `claude-api` | `anti-duplication` (extends BaseExtractionOrchestrator) + `tenant-isolation` |
| Workflow ticket (R23 Opus AGENTIC) | `copilot-expert` + `tessl__langgraph` + `claude-api` + `tessl__graceful-degradation` | `copilot-resilience` + `copilot-observability` + `tenant-isolation` + `master-data` |
| KB pack tickets (R23 Opus AGENTIC) | `copilot-expert` | `tenant-isolation` + `anti-duplication` |
| Guardrails tickets (R23 Opus AGENTIC) | `sales-agent-expert` + `copilot-expert` + `claude-api` | `sales-agent-brand-voice` + `copilot-observability` |
| Prompt slot architecture (R23 Opus AGENTIC) | `sales-agent-expert` + `claude-api` | `sales-agent-brand-voice` |
| BE tickets (Sonnet OK) | `backend-expert` | `backend-ddd` + `tenant-isolation` + `master-data` + `currency-handling` + `architectural-fitness` + `anti-duplication` + `backend-migrations` + `backend-quality` |
| FE tickets (Sonnet OK) | `frontend-expert` + `tessl__shadcn-ui` + `tessl__tailwind` + `tessl__react-patterns` + `tessl__zod` | `frontend-fsd` + `frontend-quality` + `spanish-text` + `form-runtime-array` + `tenant-isolation` |
| E2E tickets (Sonnet OK) | `playwright-expert` | `e2e-testing` + `tdd-mandatory` |
| Booking widget bundle (Sonnet OK) | `frontend-expert` + `tessl__tailwind` | `frontend-fsd` + `frontend-quality` |
| K8s manifests + deploy scripts (Sonnet OK) | `backend-expert` (infra docs) | (general infrastructure — no specific rule SSoT) |
| Docs tickets (Sonnet OK) | (none — markdown docs) | `spanish-text` (if user-facing copy) |
| Scaffolding ticket (Sonnet OK) | `backend-expert` + `frontend-expert` | `backend-ddd` + `frontend-fsd` |
| Personas YAML + Rubric MD (Sonnet OK for materialization; surface authored by /architect-agentic) | `sales-agent-expert` + `copilot-expert` | `sales-agent-brand-voice` + `auditor-downstream-regression` |

### 4.2 ALL tickets baseline rules

- `.claude/rules/git-safety.md` (no `git pull`, no `--force`, no `--no-verify`)
- `.claude/rules/parallel-safety.md` (cap ≤2 paralelo, no `git add .`)
- `.claude/rules/tdd-mandatory.md` (RED tests before GREEN)
- `.claude/rules/anti-duplication.md` (shared abstractions inventory — NEVER mirror)
- `.claude/rules/anti-default-flip-audit.md` (NO flag flips Story 11 — pure greenfield)
- `.claude/rules/auditor-downstream-regression.md` (R3 scope cumulative)
- `.claude/rules/spanish-text.md` (UI strings neutro tuteo Q1=B; sales_agent voice exception)
- `.claude/rules/hotfix-repro-mandatory.md` (R26 — N/A Story 11 greenfield, but baseline)
- `.claude/rules/debugging.md` (regression test FIRST, root cause only)

## 5. Owner eligibility matrix per ticket type (R23 enforcement)

| Ticket type | production_code | owner_eligibility | R23 Opus mandatory |
|---|---|---|---|
| scaffolding (subdir bootstrap) | false | `[opus, sonnet, qwen-opencode]` | NO |
| config (BrandConfig YAML) | false | `[opus, sonnet, qwen-opencode]` | NO |
| migration (alembic) | true (data layer non-agentic) | `[opus, sonnet, qwen-opencode]` | NO |
| model (SQLAlchemy ORM) | true (non-agentic) | `[opus, sonnet, qwen-opencode]` | NO |
| repository (BE infra non-agentic) | true (non-agentic) | `[opus, sonnet, qwen-opencode]` | NO |
| service (BE application non-agentic) | true (non-agentic) | `[opus, sonnet, qwen-opencode]` | NO |
| endpoint (BE API non-agentic) | true (non-agentic) | `[opus, sonnet, qwen-opencode]` | NO |
| component (FE non-agentic) | true (non-agentic) | `[opus, sonnet, qwen-opencode]` | NO |
| hook (FE non-agentic) | true (non-agentic) | `[opus, sonnet, qwen-opencode]` | NO |
| widget bundle (FE non-agentic) | true (non-agentic) | `[opus, sonnet, qwen-opencode]` | NO |
| **tool (AGENTIC production)** | **true (AGENTIC)** | **`[opus]` EXCLUSIVE** | **YES** |
| **extractor (AGENTIC production)** | **true (AGENTIC)** | **`[opus]` EXCLUSIVE** | **YES** |
| **workflow (AGENTIC production)** | **true (AGENTIC)** | **`[opus]` EXCLUSIVE** | **YES** |
| **guardrail (AGENTIC production)** | **true (AGENTIC)** | **`[opus]` EXCLUSIVE** | **YES** |
| **prompts/slot architecture (AGENTIC)** | **true (AGENTIC)** | **`[opus]` EXCLUSIVE** | **YES** |
| **KB pack ingestion (AGENTIC)** | **true (AGENTIC)** | **`[opus]` EXCLUSIVE** | **YES** |
| **extensions.py register_all (AGENTIC mounting)** | **true (AGENTIC)** | **`[opus]` EXCLUSIVE** | **YES** |
| e2e (Playwright specs over UI) | false (tests) | `[opus, sonnet, qwen-opencode]` | NO |
| smoke (agentic_eval tests over AGENTIC) | false (tests) | `[opus, sonnet]` | NO (R23 exempts tests over agentic) |
| docs (markdown) | false | `[opus, sonnet]` | NO |
| k8s (manifests + deploy scripts) | false (config) | `[opus, sonnet, qwen-opencode]` | NO |
| personas YAML (eval fixtures) | false | `[opus, sonnet]` | NO (Sonnet OK personas YAML) |
| rubric MD (eval spec) | false | `[opus, sonnet]` | NO (Sonnet OK rubric MD) |

## 6. Decisions applicable (cite SSoT)

Each ticket `decisions_applicable` field cites decisions ratified upstream:

| Decision | Source | Description |
|---|---|---|
| D1 | 03-arch.md § 11 | Vitalia subdir at `luana-platform/vitalia/` (Q3=B) |
| D2 | 03-arch.md § 11 + spec Q4=A | Reuse `@luana/core/scheduling` calendar base + vertical extensions |
| D3 | 03-arch.md § 11 + 02-design § 8.1 | TreatmentFollowupWorkflow inherits `StateGraph` directly (no shared base) |
| D4 | 03-arch.md § 11 | MercadoPago adapter LIFT SHARED to `@luana/core/channels/payment/` if not exists |
| D5 | 03-arch.md § 11 + 02-design § 10.1 | Slot 4 `MEDICAL_SAFETY_RAILS` NEW prompt slot |
| D6 | 03-arch.md § 11 + 02-design § 13.3 | pass^k adversarial bar ≥0.95 |
| D7 | 03-arch.md § 11 + spec Q6=B | compliance_level=hipaa_lite (NOT hipaa_full) |
| D8 | 03-arch.md § 11 + 00-story.md | features.voice_cloning=False |
| D9 | 03-arch.md § 11 + spec Q1=B | Chrome UI Spanish neutro pure tuteo |
| D10 | 03-arch.md § 11 | RedisSaver checkpointer cross-brand (NOT per-brand Redis) |
| D11 | 03-arch.md § 11 + spec Q5=B | Booking widget BOTH iframe + canonical |
| D12 | 03-arch.md § 11 + spec Q7=B | Wellness vertical UI enabled, deep coverage defer Story 11.bis |
| D13 | 03-arch.md § 11 + spec Q2=B | Multi-site UI federation DEFER Story 11.bis |
| D14 | 03-arch.md § 11 + spec Q3=B | Insurance integration LatAm DEFER Story 11.bis |

Sub-agent commit body MUST include section "Decisions honored" citing each D# from `decisions_applicable`.

## 7. Halt triggers (per 04-validators.yaml halt_triggers)

| # | Trigger | Sub-agent action |
|---|---|---|
| H1 | Cost variance >100% vs budget (V-AE-14/15/16 fail) | STOP + document in T-N-impl-log.md + escalate Chris |
| H2 | Validators blocked >max_iterations (10) | STOP + document last error trace + escalate |
| H3 | Arch fitness violation introduced (V-NF-5/6 fail) | STOP + fix or revert + escalate if persists |
| H4 | Spec drift detected (impl != spec ratified) | STOP + write delta-spec.md → /po ratifies (NOT this Sesion) |
| H5 | Tenant isolation regression (V-F-9 fail) | STOP + immediate fix (security-critical) + escalate |
| H6 | PII leak detected (V-AE-2 fail) | STOP + immediate fix (compliance-critical) + escalate |
| H7 | Spanish neutro violation user-facing (V-NF-6 fail) | STOP + fix microcopy per spec § 8 SSoT |
| H8 | Alembic consolidation conflict (V-NF-9/10 fail) | STOP + investigate drift + propose mitigation (Story 10 T-10 pattern) |
| H9 | Cross-module import boundary violation | STOP + fix per FSD-Lite / DDD boundaries |
| H10 | Anti-duplication detection (shared abstraction needed) | STOP + lift shared first OR EXTEND base (per anti-duplication.md workflow) |
| H11 | Anti-default-flip-audit violation | N/A Story 11 (no flag flips planned) — but if encountered → STOP + escalate |
| H12 | Hotfix repro_verified false | N/A Story 11 (greenfield, NOT hotfix) — but if encountered → STOP + run repro |
| H13 | Builder spawn refusal (Sonnet picked Opus-only ticket per R23) | /dev-team Step 0.5 refuses spawn — orchestrator reassigns to Opus |

## 8. Sub-agent return contract (anti-telephone-game)

Each sub-agent MUST return UNA línea final:

```
<verdict> -> <path-to-artifact>
```

Examples:
- `done -> docs/product/stories/luana-vitalia-bootstrap/T-1-result.md`
- `blocked -> docs/product/stories/luana-vitalia-bootstrap/checkpoint.md`
- `failed -> luana-platform/vitalia/backend/tests/agentic_evals/grader/test_vertical_medical_fidelity_adversarial.py:42`

NEVER inline >500 tokens of artifact body. Caller reads file on demand.

## 9. Cross-repo flow reminder

- **Code commits land in `/home/chris/luana-platform/vitalia/`** (NOT AISALESHT).
- **Docs (spec + design + arch + validators + guidelines + tickets) land in `/home/chris/AISALESHT/docs/product/stories/luana-vitalia-bootstrap/`**.
- At Story 11 merge (post `/auditor` APPROVED), /pm hard-copies docs to `/home/chris/luana-platform/docs/product/stories/luana-vitalia-bootstrap/` (T-13 Story 10 precedent).
- Future Story 11.bis (post-merge) extracts `luana-platform/vitalia/` to standalone `alpacapurpura/vitalia-brand-repo` via rsync + delete pattern.

## 10. R3 downstream regression scope (per `.claude/rules/auditor-downstream-regression.md`)

Architecture phase ticket T-X appends to SSoT table per surface modified. Pre-commit hook Section 4 detects new files under `backend/src/shared/.+\.py$` requiring SSoT row or `# downstream-regression-na: <reason>` magic comment.

Vitalia surfaces add rows (per 03-arch-be.md § 15 + 03-arch-agentic.md § 17). Auditor verifies post-build.

## 11. Pre-commit hook conformance

- Pre-commit hook native (backend venv) — runs Ruff on staged `.py` files.
- Voseo magic comment honored (R25): `# voseo-allowed: <reason>` Python; `<!-- voseo-allowed: <reason> -->` Markdown.
- Story 11 NEVER bypasses hook (`--no-verify` BANNED).

---

**05-guidelines.md draft v1 ratified at Sesion 2 close → state refined→ready.**

done -> docs/product/stories/luana-vitalia-bootstrap/05-guidelines.md
