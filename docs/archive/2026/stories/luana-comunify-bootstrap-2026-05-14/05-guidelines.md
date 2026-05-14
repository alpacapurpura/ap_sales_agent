<!-- voseo-allowed: guidelines cite rules + glossary verbatim for traceability per R25 -->
---
story_id: luana-comunify-bootstrap
guidelines_version: 1
architect_owner: claude-opus-4-7
ratified_by_chris: false
last_modified: 2026-05-14
parent_docs:
  - 01-spec.md
  - 02-design-agentic.md
  - 03-arch.md
  - 03-arch-be.md
  - 03-arch-fe.md
  - 03-arch-agentic.md
purpose: |
  Patterns required/forbidden for sub-agent builders + auditors during Story 12 build phase.
  Files in scope per ticket. Skills/rules to load per sub-agent type. R23 owner_eligibility matrix.
  Working directory: /home/chris/luana-platform/ (NOT AISALESHT — Story 12 code lives in luana-platform subdir, per Story 11 precedent).
---

# 05-guidelines.md — Story 12 luana-comunify-bootstrap

> **Read first:** 01-spec.md § 3 Gherkin scenarios (BINDING — sub-agents implement to pass) + 02-design-agentic.md § 6 tools spec + 03-arch.md § 8 acceptance + this doc.
>
> **Audience:** `builder-{backend,frontend,agentic}` sub-agents during T-1..T-N build phase. Auditors consume to verify compliance.

## 0. Cap parallelization + R23 owner eligibility (Chris ratified Q3=C serial)

**HARD CONSTRAINT Q3=C ratified:** **`parallelization_cap: 1`** for Story 12 (Chris ratified serial mode — safer than Story 11 parallel cap 2; no W9 race risk). `/dev-team` orchestrator enforces.

**Opus 4.7 mandatory tickets (R23 — production AGENTIC code):**
- All 4 tools tickets (T-tools-{1..4})
- 2 extractors tickets (T-extractors-{1,2})
- 2 workflow tickets (T-workflows-{1,2})
- 1 KB pack ingestion ticket (T-kb-1)
- 4 guardrails tickets (T-guards-{1..4})
- Prompt slots + voice integration ticket (T-prompts-1)
- Extension SDK register_all entry (T-extensions-1)
- **Voice cloning pipeline tickets (T-voice-{1..4} — NEW Story 12)**
- Vertical-creator-economy-fidelity rubric MD v1 (T-rubric-1) — Opus by virtue of authoring spec docs

**Sonnet OK tickets (non-agentic OR tests-over-agentic):**
- Comunify subdir scaffolding (T-scaffold-1)
- BrandConfig YAML (T-config-1)
- BE models + repos + migrations (T-be-{1..3})
- BE services non-agentic (Onboarding, Cohort, Subscription, Dunning, etc) (T-be-{4..7})
- BE endpoints + DTOs (T-be-{8,9})
- BE webhooks (T-be-10)
- Payment adapters consume Story 11 lifts (T-payment-1)
- FE routes + components + hooks + schemas (T-fe-{1..6})
- Subscription widget bundle (T-widget-1)
- E2E Playwright specs (T-e2e-1)
- K8s manifests + CF tunnel scripts (T-deploy-1)
- Docs (community-safety.md + widget-embed.md + voice-cloning-guide.md + seed_fixture_creators.py) (T-docs-1)
- Personas YAMLs + rubric MD materialization (T-rubric-1 inputs)

**Sub-agent prompt header for Opus tickets** MUST contain:
```
PRODUCTION CODE: true (R23 — agentic production code mandates Opus 4.7)
PARALLELIZATION CAP: 1 concurrent agent max (Q3=C ratified Story 12)
HALT TRIGGERS: per 04-validators.yaml halt_triggers — escalate Chris, no silent proceed
```

## 1. Required patterns (sub-agent MUST honor)

### 1.1 DDD Inside-Out (BE per `.claude/rules/backend-ddd.md`)

**REQUIRED:**
- Layer order: `domain` → `infrastructure` → `application` → `api`.
- Every query filter `tenant_id` (incluye `get_by_id`).
- Soft deletes only (`deleted_at`). Audit log exception (immutable, no deleted_at).
- SQLA 2.0 `select(Model).where(...)` (no `session.query()`).
- New code `AsyncSession`. NO `Session` legacy.
- `structlog`, NO `print` / `logging`.
- Pydantic v2 `model_config = ConfigDict(...)` (no inner `class Config`).
- FastAPI app `FastAPI(redirect_slashes=False)` mandatory (arch test enforces).
- Repository constructor receives `tenant_id` required param.

### 1.2 Anti-duplication (per `.claude/rules/anti-duplication.md`)

**REQUIRED Step 0 GATE before write/edit:**
```bash
find /home/chris/luana-platform/core -name "<ClassName>.py" 2>/dev/null
grep -rn "class <ClassName>" /home/chris/luana-platform/{core,nicolify,vitalia}/ 2>/dev/null
```

If match → ESCALATE to PM.

**Inventory SSoT (EXTEND from `shared/`, NEVER mirror):**

- `BaseExtractionOrchestrator` → comunify `OfferLadderAdvisor` + `AuthorityVaultExtractor` + **`VoiceDistillationOrchestrator`** EXTEND.
- `BaseAgentCallbackHandler` → comunify agentic surface CONSUMES.
- `FXResolver.default()` → comunify payment services CONSUME.
- `sanitize_payload` → comunify observability writes USE.
- `format_for_channel` → comunify channel adapters USE.
- `ExtensionPointRegistry` → comunify.extensions.py CONSUMES via `register_all`.
- `@luana/core/scheduling.calendar` → comunify `book_discovery_call` EXTENDS (Q4=A).
- **`@luana/core/channels/payment/{Stripe,MercadoPago,TokenizedRecurring}Adapter`** → comunify payment adapters EXTEND (Story 11 lifts — Q6=B reuse).
- **`PersonalityCompiler v2`** (existing `@luana/core/sales-agent`) → comunify `voice_cloning/compiler_integration.py` CONSUMES for system_instruction composition.

**Special case Story 12 — payment adapters:** verify Story 11 lifted to `@luana/core/channels/payment/`. Pre-flight at T-payment-1.

### 1.3 TDD mandatory (per `.claude/rules/tdd-mandatory.md`)

**REQUIRED RED → GREEN → REFACTOR per layer.** Forbidden: código sin test. Skip/xfail para pasar CI.

### 1.4 Tenant isolation (per `.claude/rules/tenant-isolation.md`)

**REQUIRED:** `.where(Model.tenant_id == tenant_id)` en TODA query. Middleware Clerk JWT authoritative. FE `fetchClient` auto-injects.

### 1.5 Master data + currency

**REQUIRED:**
- BE store UTC (`utc_now()`, `DateTime(timezone=True)`).
- `TenantLocale` VO + DI.
- FE `useTenantLocale()` + `formatMoney(amount, currency)`.
- DTOs monetary include `currency: str | None`.
- FE fallback `data.currency ?? useTenantLocale().currency`. NEVER hardcode 'USD'.

### 1.6 PII sanitization (Tessl + creator-economy extension)

**REQUIRED:**
- Every endpoint `response_model=` Pydantic.
- `sanitize_payload` before observability/audit writes.
- Member phone/email/national_id mask.
- **Voice cloning chat samples → DELETE raw post-distillation (D15). Only statistics retained.**
- Offer description + testimonial input PII scan PRE-persist.

### 1.7 Migrations idempotent

```python
op.execute("CREATE TABLE IF NOT EXISTS ...")
op.execute("ALTER TABLE x ADD COLUMN IF NOT EXISTS ...")
op.execute("CREATE INDEX IF NOT EXISTS ...")
```

NEVER `op.create_table()` / `sa.Enum(create_type=True)`.

### 1.8 Spanish neutro chrome UI (per `.claude/rules/spanish-text.md` R2 + Q1=B)

**REQUIRED:**
- Chrome UI (creator-facing) Spanish neutro tuteo only.
- NO voseo en buttons/forms/breadcrumbs/toasts/validaciones.
- Microcopy SSoT spec § 8.1-§ 8.8 (immutable).
- Magic comment `// voseo-allowed: <reason>` honored ONLY test fixtures / rule docs / audit reports.

**Exception sales_agent voice:** per `.claude/rules/sales-agent-brand-voice.md` — voice from `personality_profiles.system_instruction` distilled via voice cloning pipeline. Anabella AR voseo OK, Trini CL tuteo chileno, Pablo MX neutro broad.

### 1.9 Anthropic prompt cache

**REQUIRED:**
- Slots 1-6 `cache_control: {"type": "ephemeral"}`.
- Slots 7-10 NOT cached.
- Per-tenant `prompt_cache_key=str(ctx.tenant_id)`.
- Target ≥85% cache hit rate.
- NEVER interpolate `{tenant_name}` / timestamps / PII / raw chat samples mid-block.

### 1.10 Agentic R23 production code

**REQUIRED:**
- Tools wrap `try/except + structlog warning` (best-effort).
- Trace_event + llm_call writes via `try/except`.
- PII redacted via `sanitize_payload` BEFORE persist.
- Tool dispatcher injects `tenant_id` from `ctx`.
- Idempotency keys per tool action.

### 1.11 FSD-Lite

**REQUIRED:**
- Server Components default.
- React Query (data fetch). RHF + Zod (forms). Tailwind + `cn()`.
- NO `any`. NO default exports (excepto Next pages).
- Cross-feature imports forbidden default. Brand isolation per path.

### 1.12 Voice cloning pipeline patterns (NEW Story 12)

**REQUIRED:**
- `VoiceDistillationOrchestrator` MUST inherit `BaseExtractionOrchestrator` (arch test enforces).
- Voice samples raw chats DELETED post-distillation (D15).
- `voice_cloning_ratified` event triggers Slot 5 BRAND_VOICE cache invalidate.
- Compiler integration uses existing `PersonalityCompiler v2` from `@luana/core/sales-agent` — NO re-implementation.
- WhatsApp ZIP parser MUST sanitize personally identifying info pre-distill.
- Voice notes audio → Whisper transcription via LiteLLM proxy (NO direct call).
- Confidence threshold ≥0.65 — below = creator notification "agregá más samples".

## 2. Forbidden patterns (sub-agent MUST NOT do)

### 2.1 Scope expansion (HARD STOP)

**FORBIDDEN:**
- ❌ Touch `modules/copilot/` OR `modules/sales_agent/` runtime source.
  - **Exception per `.claude/rules/backend-ddd.md` §Schema-mirror exception:** if Story 12 introduces shared/ migration referenced by copilot/sales_agent ORM models, comunify tickets MAY touch `modules/{copilot,sales_agent}/persistence/models/` for schema mirror ONLY. Story 12 likely does NOT trigger this — comunify tables isolated `comunify_*` namespace.
- ❌ Touch `nicolify/` brand dir (Story 10 cement).
- ❌ Touch `vitalia/` brand dir (Story 11 cement).
- ❌ Touch `lupulo/` (parked Story 13).
- ❌ Touch `core/luana-core-*` packages without anti-duplication.md Step 0 GATE + PM escalation.
- ❌ Refactor Luana platform foundational architecture.
- ❌ Add new feature flags or flip existing defaults (Story 12 = pure greenfield).
- ❌ Modify Story 10/11 archived artifacts.
- ❌ Modify parallel WIP files in AISALESHT.
- ❌ Touch `01-spec.md` / `02-design-agentic.md` (immutable post-ratification).

### 2.2 BE anti-patterns

**FORBIDDEN:**
- ❌ `session.query()` (SQLA 1.x banned).
- ❌ `datetime.utcnow()` (use `utc_now()`).
- ❌ `DateTime()` without `timezone=True`.
- ❌ Hardcode `'USD'`.
- ❌ Pydantic default `= "USD"` outside allowed files.
- ❌ `print()` / `logging.*` (use `structlog`).
- ❌ Endpoint without `response_model=`.
- ❌ Raw dicts / ORM / untyped returned from endpoints.
- ❌ Cross-module import without port.
- ❌ Mirror `shared/agent_observability` patterns en `modules/comunify/`.

### 2.3 FE anti-patterns

**FORBIDDEN:**
- ❌ `any` types.
- ❌ Default exports.
- ❌ Cross-feature imports (NO `from "@/features/vitalia/..."` from comunify).
- ❌ Voseo verbs in user-facing chrome UI strings.
- ❌ Hardcode `'USD'`.
- ❌ `toLocaleDateString()`.
- ❌ Member PII in URL params / localStorage / sessionStorage.
- ❌ `// eslint-disable-next-line` without justification.
- ❌ `make e2e*` Docker E2E (crashes WSL2).

### 2.4 AGENTIC anti-patterns

**FORBIDDEN:**
- ❌ Tool input schema includes `tenant_id` (inject via ctx).
- ❌ LLM call without `response_model=` Pydantic schema (where applicable).
- ❌ Interpolate `{tenant_name}` / timestamps / PII in cacheable slots 1-4 + 6.
- ❌ Spam / NSFW / doxxing in LLM response (adversarial pass^5 ≥0.95 safety bar).
- ❌ Skip guardrail chain (input + output pipeline order enforced).
- ❌ Skip RAG citation in `copilot_trace_event.context_used`.
- ❌ Write to `copilot_llm_call` from eval runs (cost bucket separation).
- ❌ Re-implement `sanitize_payload`.
- ❌ Spawn AGENTIC ticket with Sonnet (R23 hard rule).
- ❌ **Persist raw chat samples post-distillation (D15 — DELETE raw).**
- ❌ **Re-implement PersonalityCompiler v2 — bridge to existing @luana/core/sales-agent.**

### 2.5 Process anti-patterns

**FORBIDDEN:**
- ❌ `git pull` / `git fetch && merge`.
- ❌ `git push --force` / `--force-with-lease`.
- ❌ `git revert` without explicit Chris approval.
- ❌ `git add .` / `-A` / `-u`.
- ❌ `git commit --no-verify`.
- ❌ Feature branches / worktrees / release branches.
- ❌ Skip Step 0 GATE anti-duplication grep.
- ❌ Skip TDD RED → GREEN.

## 3. Files in scope

### 3.1 Working directory

**Builders work primarily in `/home/chris/luana-platform/comunify/`** (NOT AISALESHT).

### 3.2 IN SCOPE Story 12

```
/home/chris/luana-platform/comunify/
├── backend/
│   ├── src/modules/comunify/
│   │   ├── domain/
│   │   ├── infrastructure/
│   │   ├── application/
│   │   ├── api/
│   │   ├── agentic/                  # R23 Opus mandatory
│   │   ├── copilot/                  # R23 Opus mandatory
│   │   ├── brand/voice_cloning/      # R23 Opus mandatory (NEW Story 12)
│   │   ├── payment/                  # consume Story 11 lifts
│   │   └── extensions.py
│   ├── alembic/versions/001_comunify_initial_snapshot.py
│   ├── tests/unit/
│   ├── tests/integration/
│   ├── tests/e2e/
│   ├── tests/agentic_evals/
│   ├── tests/architecture/
│   └── scripts/
│       ├── seed_fixture_creators.py
│       └── seed_creator_economy_kb.py
├── frontend/
│   ├── src/
│   │   ├── app/                      # Next.js 16 App Router routes
│   │   └── features/comunify/        # FSD-Lite
│   ├── widget/                       # Embeddable iframe bundle subscription
│   ├── e2e/specs/comunify/
│   ├── tests/
│   ├── package.json
│   └── next.config.ts
├── config/
│   └── brand.yaml
├── deploy/
│   ├── k8s/
│   └── cloudflared/
├── docs/
│   ├── community-safety.md
│   ├── widget-embed.md
│   └── voice-cloning-guide.md
├── pyproject.toml
├── package.json
└── README.md

/home/chris/AISALESHT/docs/   (docs only)
├── product/stories/luana-comunify-bootstrap/
│   ├── 01-spec.md (immutable)
│   ├── 02-design-agentic.md (immutable)
│   ├── 03-arch.md
│   ├── 03-arch-be.md
│   ├── 03-arch-fe.md
│   ├── 03-arch-agentic.md
│   ├── 04-validators.yaml
│   ├── 05-guidelines.md (this file)
│   ├── 06-tickets.yaml
│   ├── checkpoint.md
│   └── T-{n}-impl-log.md
└── specs/
    ├── personas/archetype-aware/
    │   ├── lead-pricing-guilt-coach-ar.yaml (NEW)
    │   ├── member-drift-nutrition-cl.yaml (NEW)
    │   ├── lead-skeptical-productivity-mx.yaml (NEW)
    │   ├── member-tier-upgrade-coach-ar.yaml (NEW)
    │   ├── lead-prompt-injection-attempt.yaml (NEW)
    │   ├── community-spammer-mx.yaml (NEW)
    │   ├── community-doxxing-attempt-cl.yaml (NEW)
    │   └── member-vulnerable-disclosure-cl.yaml (NEW)
    └── rubrics/
        └── vertical-creator-economy-fidelity.md (NEW MD v1)
```

### 3.3 OUT-OF-SCOPE (anti-creep)

- `/home/chris/luana-platform/nicolify/**` (Story 10 cement)
- `/home/chris/luana-platform/vitalia/**` (Story 11 cement)
- `/home/chris/luana-platform/lupulo/**` (Story 13 parked)
- `/home/chris/luana-platform/core/**` (consume only — exception lift if needed with escalation)
- `/home/chris/luana-platform/apps/test-brand/**` (Story 9 cement)
- `/home/chris/AISALESHT/backend/**` (parked)
- `/home/chris/AISALESHT/frontend/**` (parked)
- Story 12.bis deferred items: Discord/Circle bridge, multi-account creator switcher UI, live streaming, gamification deep, affiliate program, mobile app, LMS course delivery, NFT/Web3, English localization.

## 4. Skills + rules per ticket type

### 4.1 Skills/rules per surface

| Surface | Skills MUST load | Rules MUST load |
|---|---|---|
| Tools tickets (R23 Opus AGENTIC) | `sales-agent-expert` + `copilot-expert` + `tessl__langgraph` + `claude-api` | `sales-agent-brand-voice` + `copilot-resilience` + `copilot-observability` + `anti-duplication` + `tenant-isolation` |
| Extractors tickets (R23 Opus AGENTIC) | `copilot-expert` + `sales-agent-expert` + `tessl__langgraph` + `claude-api` | `anti-duplication` + `tenant-isolation` |
| Workflow tickets (R23 Opus AGENTIC) | `copilot-expert` + `tessl__langgraph` + `claude-api` + `tessl__graceful-degradation` | `copilot-resilience` + `copilot-observability` + `tenant-isolation` + `master-data` |
| KB pack ticket (R23 Opus AGENTIC) | `copilot-expert` | `tenant-isolation` + `anti-duplication` |
| Guardrails tickets (R23 Opus AGENTIC) | `sales-agent-expert` + `copilot-expert` + `claude-api` | `sales-agent-brand-voice` + `copilot-observability` |
| Prompt slot architecture (R23 Opus AGENTIC) | `sales-agent-expert` + `claude-api` | `sales-agent-brand-voice` |
| **Voice cloning pipeline (R23 Opus AGENTIC)** | **`sales-agent-expert` + `copilot-expert` + `brand-expert` + `tessl__langgraph` + `claude-api`** | **`sales-agent-brand-voice` + `anti-duplication` + `tenant-isolation`** |
| BE tickets (Sonnet OK) | `backend-expert` | `backend-ddd` + `tenant-isolation` + `master-data` + `currency-handling` + `architectural-fitness` + `anti-duplication` + `backend-migrations` + `backend-quality` |
| FE tickets (Sonnet OK) | `frontend-expert` + `tessl__shadcn-ui` + `tessl__tailwind` + `tessl__react-patterns` + `tessl__zod` | `frontend-fsd` + `frontend-quality` + `spanish-text` + `form-runtime-array` + `tenant-isolation` |
| E2E tickets (Sonnet OK) | `playwright-expert` | `e2e-testing` + `tdd-mandatory` |
| Subscribe widget bundle (Sonnet OK) | `frontend-expert` + `tessl__tailwind` | `frontend-fsd` + `frontend-quality` |
| K8s manifests + deploy (Sonnet OK) | `backend-expert` (infra docs) | (no specific rule SSoT) |
| Docs tickets (Sonnet OK) | (markdown) | `spanish-text` if user-facing copy |
| Scaffolding ticket (Sonnet OK) | `backend-expert` + `frontend-expert` | `backend-ddd` + `frontend-fsd` |
| Personas YAML + Rubric MD (Sonnet OK) | `sales-agent-expert` + `copilot-expert` | `sales-agent-brand-voice` + `auditor-downstream-regression` |
| Brand-related Story 12 tickets (authority vault, ladder visualizer, voice cloning UX) | `brand-expert` + `offer-expert` | `form-runtime-array` |

### 4.2 ALL tickets baseline rules

- `.claude/rules/git-safety.md`
- `.claude/rules/parallel-safety.md` (cap ≤1 paralelo Q3=C ratified)
- `.claude/rules/tdd-mandatory.md`
- `.claude/rules/anti-duplication.md`
- `.claude/rules/anti-default-flip-audit.md` (N/A Story 12 — pure greenfield)
- `.claude/rules/auditor-downstream-regression.md`
- `.claude/rules/spanish-text.md`
- `.claude/rules/hotfix-repro-mandatory.md` (N/A Story 12 — baseline)
- `.claude/rules/debugging.md`

## 5. Owner eligibility matrix per ticket type (R23 enforcement)

| Ticket type | production_code | owner_eligibility | R23 Opus mandatory |
|---|---|---|---|
| scaffolding | false | `[opus, sonnet]` | NO |
| config | false | `[opus, sonnet]` | NO |
| migration | true (data layer) | `[opus, sonnet]` | NO |
| model (SQLAlchemy ORM) | true (non-agentic) | `[opus, sonnet]` | NO |
| repository (BE infra) | true (non-agentic) | `[opus, sonnet]` | NO |
| service (BE application) | true (non-agentic) | `[opus, sonnet]` | NO |
| endpoint (BE API) | true (non-agentic) | `[opus, sonnet]` | NO |
| webhook | true (non-agentic) | `[opus, sonnet]` | NO |
| payment_adapter (consume lifts) | true (non-agentic) | `[opus, sonnet]` | NO |
| component (FE non-agentic) | true (non-agentic) | `[opus, sonnet]` | NO |
| hook (FE non-agentic) | true (non-agentic) | `[opus, sonnet]` | NO |
| widget bundle (FE non-agentic) | true (non-agentic) | `[opus, sonnet]` | NO |
| **tool (AGENTIC production)** | **true (AGENTIC)** | **`[opus]` EXCLUSIVE** | **YES** |
| **extractor (AGENTIC production)** | **true (AGENTIC)** | **`[opus]` EXCLUSIVE** | **YES** |
| **workflow (AGENTIC production)** | **true (AGENTIC)** | **`[opus]` EXCLUSIVE** | **YES** |
| **guardrail (AGENTIC production)** | **true (AGENTIC)** | **`[opus]` EXCLUSIVE** | **YES** |
| **prompts/slot architecture (AGENTIC)** | **true (AGENTIC)** | **`[opus]` EXCLUSIVE** | **YES** |
| **KB pack ingestion (AGENTIC)** | **true (AGENTIC)** | **`[opus]` EXCLUSIVE** | **YES** |
| **voice_cloning pipeline (AGENTIC)** | **true (AGENTIC)** | **`[opus]` EXCLUSIVE** | **YES** |
| **extensions.py register_all (AGENTIC mounting)** | **true (AGENTIC)** | **`[opus]` EXCLUSIVE** | **YES** |
| e2e (Playwright over UI) | false (tests) | `[opus, sonnet]` | NO |
| smoke (agentic_eval tests over AGENTIC) | false (tests) | `[opus, sonnet]` | NO (R23 exempts tests over agentic) |
| docs (markdown) | false | `[opus, sonnet]` | NO |
| k8s (manifests + deploy scripts) | false (config) | `[opus, sonnet]` | NO |
| personas YAML (eval fixtures) | false | `[opus, sonnet]` | NO |
| rubric MD (eval spec) | false | `[opus, sonnet]` | NO |

## 6. Decisions applicable (cite SSoT)

| Decision | Source | Description |
|---|---|---|
| D1 | 03-arch.md § 11 | Comunify subdir at `luana-platform/comunify/` (Q3=B Story 11 verbatim) |
| D2 | 03-arch.md § 11 + spec Q4=A | Reuse `@luana/core/scheduling` + appointment_type=discovery_call |
| D3 | 03-arch.md § 11 + 02-design § 8.1 | Workflows inherit `StateGraph` directly (no shared base) |
| D4 | 03-arch.md § 11 | Payment adapters CONSUME Story 11 lifts |
| D5 | 03-arch.md § 11 + 02-design § 10.1 | Slot 4 `COMMUNITY_SAFETY_RAILS` NEW prompt slot |
| D6 | 03-arch.md § 11 + 02-design § 13.3 | pass^k adversarial bar ≥0.95 |
| D7 | 03-arch.md § 11 | `compliance_level=creator_economy` (NOT hipaa_lite) |
| D8 | 03-arch.md § 11 + 00-story.md | **`features.voice_cloning=True` (NEW Story 12)** |
| D9 | 03-arch.md § 11 + spec Q1=B | Chrome UI Spanish neutro pure tuteo |
| D10 | 03-arch.md § 11 | RedisSaver checkpointer cross-brand |
| D11 | 03-arch.md § 11 + spec Q5=B | Subscription widget BOTH iframe + canonical |
| D12 | 03-arch.md § 11 + spec Q2=B | Multi-account creator switcher UI DEFER Story 12.bis |
| D13 | 03-arch.md § 11 + spec Q3=B | Third-party community bridge DEFER Story 12.bis |
| D14 | 03-arch.md § 11 | `OfferLadder` entity comunify-local initially, lift-shared candidate Story 13+ |
| D15 | 03-arch.md § 11 | **Voice cloning samples raw chats DELETED post-distillation (only statistics retained)** |
| D16 | 03-arch.md § 11 | Community moderation classifier Haiku 4.5 default |
| D17 | 03-arch.md § 11 | KB Qdrant collection name `comunify_creator_economy_kb_v1` |
| D18 | 03-arch.md § 11 | `community_audit_log` retention 5 years |
| D19 | 03-arch.md § 11 | Subscription dunning state: active → past_due → suspended → cancelled |
| D20 | 03-arch.md § 11 | `coaching_offers_v1` preset pack registered Story 12, lift-shared candidate Story 13+ |

Sub-agent commit body MUST include "Decisions honored" citing each D# from `decisions_applicable`.

## 7. Halt triggers (per 04-validators.yaml halt_triggers)

| # | Trigger | Sub-agent action |
|---|---|---|
| H1 | Cost variance >100% vs budget | STOP + document in T-N-impl-log.md + escalate Chris |
| H2 | Validators blocked >max_iterations | STOP + document last error trace + escalate |
| H3 | Arch fitness violation introduced | STOP + fix or revert + escalate |
| H4 | Spec drift detected | STOP + write delta-spec.md → /po ratifies |
| H5 | Tenant isolation regression | STOP + immediate fix (security-critical) + escalate |
| H6 | PII leak detected | STOP + immediate fix (compliance-critical) + escalate |
| H7 | Spanish neutro violation user-facing | STOP + fix microcopy per spec § 8 SSoT |
| H8 | Alembic consolidation conflict | STOP + investigate drift + propose mitigation |
| H9 | Cross-module import boundary violation | STOP + fix per FSD-Lite / DDD boundaries |
| H10 | Anti-duplication detection (shared abstraction needed) | STOP + lift shared first OR EXTEND base |
| H11 | Anti-default-flip-audit violation | N/A Story 12 (no flips) — STOP + escalate if encountered |
| H12 | Hotfix repro_verified false | N/A Story 12 (greenfield) — STOP + run repro if encountered |
| H13 | Builder spawn refusal (Sonnet picked Opus-only) | /dev-team Step 0.5 refuses spawn — reassign to Opus |

**Story 12 additional halt (per checkpoint frontmatter HC1-HC8 INMEDIATE):**

- HC4 R10 anti-duplication mirror detected → STOP write SESSION-HALT.md
- HC5 R23 violation AGENTIC routed Sonnet → STOP
- HC6 Secret detected staged → STOP escalate Chris immediately

## 8. Sub-agent return contract (anti-telephone-game)

Each sub-agent MUST return UNA línea final:

```
<verdict> -> <path-to-artifact>
```

Examples:
- `done -> docs/product/stories/luana-comunify-bootstrap/T-1-result.md`
- `blocked -> docs/product/stories/luana-comunify-bootstrap/checkpoint.md`
- `failed -> luana-platform/comunify/backend/tests/agentic_evals/grader/test_vertical_creator_economy_fidelity_adversarial.py:42`

NEVER inline >500 tokens of artifact body.

## 9. Cross-repo flow reminder

- **Code commits land in `/home/chris/luana-platform/comunify/`** (NOT AISALESHT).
- **Docs land in `/home/chris/AISALESHT/docs/product/stories/luana-comunify-bootstrap/`**.
- At Story 12 merge, /pm hard-copies docs to `/home/chris/luana-platform/docs/product/stories/luana-comunify-bootstrap/`.
- Future Story 12.bis extracts `luana-platform/comunify/` to standalone `alpacapurpura/comunify-brand-repo`.

## 10. R3 downstream regression scope

Architecture phase ticket T-X appends to SSoT table per surface modified. Comunify surfaces add rows (per 03-arch-be.md § 15 + 03-arch-agentic.md § 16).

## 11. Pre-commit hook conformance

- Pre-commit hook native (backend venv) — runs Ruff on staged `.py` files.
- Voseo magic comment honored (R25).
- Story 12 NEVER bypasses hook (`--no-verify` BANNED).

---

**05-guidelines.md draft v1 — Sesion 12 autonomous Phase 2.**

done -> docs/product/stories/luana-comunify-bootstrap/05-guidelines.md
