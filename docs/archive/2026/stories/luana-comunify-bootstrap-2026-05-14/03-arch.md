<!-- voseo-allowed: arch doc cites sales_agent voice constraints + tenant voice profiles per Slot 5 BRAND_VOICE SSoT (voice cloning compiled v2 distilled per tenant — Anabella AR voseo OK, Trini CL tuteo, Pablo MX neutro). Chrome UI microcopy enforced Spanish neutro tuteo per Q1=B (spec § 17). -->
---
story_id: luana-comunify-bootstrap
arch_version: 1
ratified_by_chris: false
architect_owner: claude-opus-4-7
sub_architects: [architect-be, architect-fe, architect-agentic]
surfaces: [backend, frontend, agentic, infra]
last_modified: 2026-05-14
links:
  spec: "01-spec.md"
  agentic_design: "02-design-agentic.md"
  outcome: "../../outcomes/luana-platform-migration.md"
  sub_arch_be: "03-arch-be.md"
  sub_arch_fe: "03-arch-fe.md"
  sub_arch_agentic: "03-arch-agentic.md"
  validators: "04-validators.yaml"
  guidelines: "05-guidelines.md"
  tickets: "06-tickets.yaml"
  story_11_precedent: "../../../../archive/2026/stories/luana-vitalia-bootstrap-2026-05-14/"
ready_package:
  - 03-arch.md (this file — consolidated)
  - 03-arch-be.md
  - 03-arch-fe.md
  - 03-arch-agentic.md
  - 04-validators.yaml
  - 05-guidelines.md
  - 06-tickets.yaml
---

# 03-arch.md — Story 12 luana-comunify-bootstrap (consolidated)

> **Outcome:** luana-platform-migration · **Sequence:** 12/14 · **State:** refined → ready (Sesion 12 autonomous Phase 2)
> **Strategy:** Full-stack vertical-creator-economy brand bootstrap consumiendo Luana Platform v0.1.0+ (Story 10 cement) + extension SDK validated por Story 11 (Vitalia, APPROVED 2026-05-14). Code lives `luana-platform/comunify/` subdir. Réplica Story 11 pattern adaptado a community + creator-economy domain.

---

## § 1. Resumen ejecutivo

Story 12 entrega Comunify como **vertical-creator-economy brand app** sobre Luana Platform monorepo. Cuatro ejes técnicos:

- **Backend (BE):** módulo nuevo `comunify` con DDD Inside-Out (`domain/infrastructure/application/api/`) consumiendo `@luana/core/*` packages via workspace imports. **13 entidades nuevas** (`Cohort`, `CohortMember`, `CohortBroadcast`, `CommunityPost`, `CommunityModerationEvent`, `Subscription`, `SubscriptionCharge`, `OfferLadder`, `VoiceCloningSamples`, `VoiceDistillationJob`, `AuthorityVaultItem` collection, `LeadQualificationRecord`, `CommunityAuditLog`) + reuse de Story 11 lifts (`MercadoPagoAdapter` + `StripeConnectAdapter` + `TokenizedRecurringAdapter`). Alembic snapshot consolidation pattern Story 10/11 replica. 9 servicios DDD (Onboarding, OfferLadder, Cohort, Community, ContentModeration, Subscription, Dunning, VoiceCloning, AuthorityVault, ComplianceEvent).

- **Frontend (FE):** Next.js 16 App Router en `comunify/frontend/` consumiendo `@luana/ui` + `@luana/shared` (16 Shadcn primitives + 10 shared components). **13 routes** (onboarding wizard 4-step, brand-studio 10 secciones, offer wizard coaching_offers 5-step, ladder visualizer, cohorts list+detail+roster+broadcasts, community feed + moderation inbox, authority vault, subscriptions admin, public landing per creator-handle). **11 NEW comunify-specific components** (CreatorNichePicker, VoiceSamplesUploader, VoiceDistilledPreview, LadderVisualizer drag-drop, AuthorityVaultEditor, CohortRosterTable, CohortBroadcastComposer, CommunityModerationCard, SubscriptionMetricsCards, DunningActiveBanner, CreatorLandingHero) — todos justificados anti-duplication. Embeddable subscription widget bundle (`comunify/frontend/widget/`) postMessage protocol (Q5=B both iframe + canonical).

- **Agentic:** vertical-creator-economy surface en `comunify/backend/src/modules/comunify/agentic/` + `comunify/copilot/` registrando via Extension SDK: **4 tools** (`qualify_for_cohort`, `link_to_community`, `nurture_via_authority_content`, `book_discovery_call`) + **2 extractors** (`OfferLadderAdvisor`, `AuthorityVaultExtractor` — ambos extend `BaseExtractionOrchestrator`) + **2 LangGraph workflows** (`CommunityEngagementWorkflow` + `CohortEnrollmentWorkflow`, ambos con RedisSaver checkpointer) + **1 KB pack Qdrant** (`creator_economy_kb_v1`) + **4 guardrails** (`community_safety_no_spam`, `community_safety_no_nsfw`, `community_safety_no_doxxing`, `prompt_injection_block` reuse Story E) + **voice cloning pipeline NEW** (4-wave distillation 50+ chats → Compiler v2 6-block system_instruction). Prompt slot architecture 10 slots con NEW Slot 4 `COMMUNITY_SAFETY_RAILS`. R23 Opus mandatory para todo production code AGENTIC.

- **Voice cloning pipeline NEW (Story 12 first):** Pipeline async ~12 min wave-based (`VoiceDistillationOrchestrator` extends `BaseExtractionOrchestrator`) procesa 50+ chats WhatsApp/voice notes → distilla 6 bloques (identidad/dialecto/vocabulario/registro/anclajes/asíNO) → `personality_profiles.system_instruction` actualizado → Slot 5 BRAND_VOICE cache invalidates. Creator ratifica preview antes deploy. Per-tenant.

**Cross-repo flow:** Story 12 commits land en `/home/chris/luana-platform/comunify/` (monorepo subdir per Phase 0 Q3=B Story 11 precedent). Future Story 12.bis extract to `alpacapurpura/comunify-brand-repo` standalone (rsync + delete pattern Story 10 T-13).

**Chris UI manual gates (Phase 0 Q1=A Story 11 verbatim):** Clerk app #3 provisioning + K8s cluster + DNS records comunify.io + MercadoPago production credentials + Stripe Connect onboarding + Qdrant collection bootstrap. `/dev-team` autonomous scope = code + manifests + scripts + sandbox; Chris executes irreversible/production-adjacent operations via UI.

---

## § 2. Surface decomposition

### 2.1 Surface inventory por capa

| Surface | Path | Owner sub-architect | Production code | R23 Opus mandatory |
|---|---|---|---|---|
| **Backend** módulo nuevo | `luana-platform/comunify/backend/src/modules/comunify/{domain,infrastructure,application,api}/` | `architect-be` | YES (non-agentic) | NO (Sonnet OK) |
| **Backend** agentic (tools + extractors + workflows + guardrails + KB ingest + voice_cloning pipeline) | `comunify/backend/src/modules/comunify/agentic/` + `comunify/backend/src/modules/comunify/copilot/{extractors,workflows}/` + `comunify/backend/src/modules/comunify/brand/voice_cloning/` | `architect-agentic` | YES (AGENTIC) | **YES Opus 4.7** |
| **Backend** payment channel adapters | `comunify/backend/src/modules/comunify/payment/` (consume Story 11 lifts) | `architect-be` | YES (non-agentic) | NO |
| **Backend** Alembic migrations | `comunify/backend/alembic/versions/` (idempotent IF NOT EXISTS) | `architect-be` | YES (data layer) | NO |
| **Backend** tests | `comunify/backend/tests/{unit,integration,e2e,agentic_evals,architecture}/` | per ticket | NO (tests) | NO (Sonnet OK incluso para agentic-tests) |
| **Frontend** routes + components + hooks + schemas | `luana-platform/comunify/frontend/src/{app,features/comunify}/` | `architect-fe` | YES (non-agentic) | NO |
| **Frontend** subscription widget bundle iframe | `luana-platform/comunify/frontend/widget/` | `architect-fe` | YES (non-agentic) | NO |
| **Frontend** tests Vitest + Playwright | `comunify/frontend/{tests,e2e}/` | per ticket | NO (tests) | NO |
| **Config** BrandConfig declarative | `comunify/config/brand.yaml` | shared (BE + agentic owners) | NO (config) | NO |
| **Config** K8s manifests + CF tunnel scripts | `comunify/deploy/` | `architect-be` (infra) | NO (config) | NO |
| **Docs** compliance + widget embed + voice cloning guide | `comunify/docs/{community-safety,widget-embed,voice-cloning-guide}.md` | shared | NO (docs) | NO |
| **Personas YAMLs** archetype-aware vertical-creator-economy | `docs/specs/personas/archetype-aware/lead-*.yaml + member-*.yaml + community-*.yaml` (8 NEW) | `architect-agentic` | NO (eval fixtures) | NO (Sonnet OK personas YAML) |
| **Rubric MD v1** vertical-creator-economy-fidelity | `docs/specs/rubrics/vertical-creator-economy-fidelity.md` (NEW) | `architect-agentic` | NO (eval spec) | NO (Sonnet OK rubric MD) |

### 2.2 Module graph (DAG)

```
                       ┌──────────────────────────────────┐
                       │  @luana/core/* shared packages   │
                       │  (Story 10 cement — read only)   │
                       │  - extension-sdk (EP-1..EP-18)   │
                       │  - brand-studio                   │
                       │  - offer-studio                   │
                       │  - sales-agent (runtime)          │
                       │  - copilot (runtime)              │
                       │  - llm + observability + iam     │
                       │  - billing + idempotency         │
                       │  - channels (format_for_channel) │
                       │  - extraction (BaseOrchestrator) │
                       │  - scheduling (calendar)          │
                       │                                   │
                       │  Story 11 LIFTS (consume):        │
                       │  - @luana/core/channels/payment/  │
                       │    MercadoPagoAdapter             │
                       │  - @luana/core/channels/payment/  │
                       │    StripeConnectAdapter           │
                       │  - @luana/core/channels/payment/  │
                       │    TokenizedRecurringAdapter      │
                       └────────────────┬─────────────────┘
                                        │ consume
                                        ▼
       ┌─────────────────────────────────────────────────────────────┐
       │  comunify/ (Story 12 NEW)                                   │
       │                                                             │
       │  ┌─────────────────────────────────────────────────────┐  │
       │  │  comunify/backend/src/modules/comunify/             │  │
       │  │  ├── domain/        (entities + VOs + events)       │  │
       │  │  ├── infrastructure/(repos + ORM models + adapters) │  │
       │  │  ├── application/   (services + event handlers)     │  │
       │  │  ├── api/           (routes + DTOs Pydantic v2)     │  │
       │  │  ├── agentic/       (4 tools — R23 Opus)            │  │
       │  │  ├── copilot/                                        │  │
       │  │  │   ├── extractors/(2 — extend Base shared)        │  │
       │  │  │   ├── workflows/ (CommunityEngagement +          │  │
       │  │  │   │              CohortEnrollment)               │  │
       │  │  │   └── kb/        (creator_economy_kb_v1 chunks) │  │
       │  │  ├── brand/                                          │  │
       │  │  │   └── voice_cloning/ (distillation pipeline)     │  │
       │  │  ├── payment/       (extends @luana/core/channels)  │  │
       │  │  └── extensions.py  (register_all entry — EP-1..18) │  │
       │  └─────────────────────────────────────────────────────┘  │
       │                                                             │
       │  ┌─────────────────────────────────────────────────────┐  │
       │  │  comunify/frontend/                                 │  │
       │  │  ├── src/app/[route]/page.tsx (Server Components)   │  │
       │  │  ├── src/features/comunify/   (FSD-Lite)            │  │
       │  │  │   ├── api/                                       │  │
       │  │  │   ├── components/                                │  │
       │  │  │   ├── hooks/                                     │  │
       │  │  │   ├── schemas/                                   │  │
       │  │  │   └── types/                                     │  │
       │  │  └── widget/        (embeddable iframe subscription) │  │
       │  └─────────────────────────────────────────────────────┘  │
       │                                                             │
       │  ┌─────────────────────────────────────────────────────┐  │
       │  │  comunify/config/brand.yaml (declarative)           │  │
       │  │  comunify/deploy/{k8s,cloudflared}/                 │  │
       │  │  comunify/docs/{community-safety,widget-embed,...}  │  │
       │  └─────────────────────────────────────────────────────┘  │
       └─────────────────────────────────────────────────────────────┘
```

### 2.3 Boundary contract

- `comunify/backend/src/modules/comunify/*` → **CONSUMES** `@luana/core/*` packages, `shared/agent_observability/*`, `shared/billing/*`, `shared/idempotency/*`, `shared/extraction/base_orchestrator`, `shared/scheduling/calendar` (Q4=A reuse + Story 11 cement).
- `comunify/backend/src/modules/comunify/*` → **NEVER touches** `modules/copilot/` o `modules/sales_agent/` source (consume runtime via extension SDK registry).
- `comunify/frontend/*` → **CONSUMES** `@luana/ui`, `@luana/shared`, `fetchClient` (auto-injects `X-Tenant-ID`).
- Cross-brand isolation: comunify NEVER imports `nicolify/`, `vitalia/`, `lupulo/` (parallel verticals — Stories 10/11/13).

---

## § 3. Cross-cutting concerns

### 3.1 Tenant isolation (per `.claude/rules/tenant-isolation.md`)

**Mandatory pattern todas las queries:**
```python
async def get_cohort_by_id(self, cohort_id: UUID, tenant_id: UUID) -> Cohort | None:
    stmt = (
        select(CohortModel)
        .where(
            CohortModel.id == cohort_id,
            CohortModel.tenant_id == tenant_id,    # MANDATORY
            CohortModel.deleted_at.is_(None),     # soft delete
        )
    )
```

**Enforcement layers:**
- Middleware Clerk JWT → injects `X-Tenant-ID` from JWT (authoritative — never client-supplied).
- Repository constructor receives `tenant_id` required param.
- Arch fitness test `test_no_query_without_tenant_filter.py` ratchets comunify module from Story 10/11 baseline.
- Cross-tenant attempt audit logged via `community_audit_log` event `cross_tenant_attempt` (spec § 3.1.D + § 15.5).

### 3.2 Master data + multi-currency (per `.claude/rules/master-data.md` + `.claude/rules/currency-handling.md`)

**Pattern:**
- BE store UTC always (`utc_now()`, `DateTime(timezone=True)`).
- `TenantLocale` VO injects per-tenant currency + timezone via `get_tenant_locale()` DI.
- **Currencies supported Story 12:** USD (Anabella + Pablo primary), ARS (Anabella AR option), CLP (Trini CL), MXN (Pablo MX option), COP, PEN, BRL.
- DTOs monetary fields include `currency: str | None = None` (ISO 4217).
- FE consumes `useTenantLocale()` → `formatMoney(amount, currency)`. **NEVER hardcode 'USD'** — fallback `data.currency ?? useTenantLocale().currency`.
- Cron scheduler `CommunityEngagementWorkflow` + `CohortEnrollmentWorkflow` ticks at 9am local TZ per tenant (Anabella BA = UTC-3, Trini Santiago = UTC-3/UTC-4 DST, Pablo CDMX = UTC-6).
- Recurring subscription billing schedules respect tenant TZ for due_date computation.

### 3.3 PII sanitization (per Tessl `pii-sanitisation.md` + creator-economy extension)

**Pattern:**
- All FastAPI endpoints `response_model=` Pydantic v2 model. Raw dicts / ORM / untyped banned (arch fitness gate).
- `shared.agent_observability.recording.sanitization::sanitize_payload` invoked BEFORE persisting `copilot_trace_event` + `copilot_llm_call` + `community_audit_log` payloads.
- **Creator-economy PII extension** (vertical-specific):
  - Member phone → mask `+54***5555` (last 4 visible for support).
  - Member email → mask `j***@***.com`.
  - National IDs (DNI AR / RUT CL / RFC MX / CURP MX / CC CO) → `[NATIONAL_ID]`.
  - **Voice cloning chat samples → distilled, raw text deleted post-distillation. Only statistics retained (sample_count, dialect_detected, vocabulary_anchors_extracted).**
  - Stripe customer_id → `[STRIPE_CUSTOMER_REDACTED]`.
  - Other-member private contact info in posts → caught by `community_safety_no_doxxing` guardrail BEFORE persist.
- Offer description + testimonial inputs run through `pii_scanner` middleware **BEFORE persist** (spec § 3.2.D + § 3.3.D adversarial scenarios).

### 3.4 Spanish neutro chrome UI + sales_agent voice exception

**Chrome UI (creator-facing — operator-facing) — spec § 12.1 + Q1=B ratified:**
- Spanish neutro LatAm puro **tuteo** (tú/tu/tienes/eres/puedes/haces).
- NO voseo en buttons / forms / breadcrumbs / toasts / validations / banners.
- Microcopy SSoT = spec § 8.1–8.8 (immutable post-ratification).
- Arch fitness gate `test_comunify_ui_strings_no_voseo.py` greps `frontend/src/features/comunify/` for voseo verbs.

**Sales_agent voice (lead/member-facing) — spec § 12.2 exception per `.claude/rules/sales-agent-brand-voice.md`:**
- Voice viene de `personality_profiles.system_instruction` compiled v2 per tenant (Slot 5 `BRAND_VOICE`).
- **Voice cloning compiled v2 distilled de 50+ chats reales del creator** (NEW Story 12 — vs Story 11 OFF).
- Anabella Conexión AR: es-AR voseo natural distilled de chats reales.
- Trini Nutrición CL: es-CL neutro chileno tuteo distilled.
- Pablo Productividad MX: es-MX neutro broad LatAm tuteo distilled.
- Voice fidelity grader threshold ≥0.8 + vertical-creator-economy-fidelity ≥0.85.
- `# voseo-allowed: ...` magic comment honored in test fixtures + rule docs + audit reports per R25.

### 3.5 Community safety + recurring billing compliance

**Community safety pattern (spec § 14):**
- 4 guardrails registered: `community_safety_no_spam` + `community_safety_no_nsfw` + `community_safety_no_doxxing` + `prompt_injection_block` (reuse Story E).
- Pre-moderation new members default ON for first 3 posts (skip if from waitlist OR engagement_score > 80).
- 5 compliance smoke tests (spec § 15.1–15.5):
  - `smoke_prompt_injection.py` — 5 injection patterns.
  - `smoke_spam_detection.py` — 10 spam vectors.
  - `smoke_nsfw_upload.py` — 5 image upload severity levels.
  - `smoke_doxxing.py` — 4 doxxing attempts.
  - `smoke_cross_tenant.py` — 3 cross-tenant attack vectors.
- `community_audit_log` table tenant-scoped retention 5 years (vs Vitalia 7-year HIPAA — creator-economy lighter requirement).

**Recurring billing pattern:**
- Subscription pricing per plan tier (creator $29 / pro $99 / agency $299 USD/mo) — Comunify SaaS.
- Subscriber-side recurring (cohort installments + monthly memberships) — DunningWorkflow handles failures (retry_1 → retry_2 → suspended → cancelled).
- Idempotency `(subscriber_id, billing_period, installment_n)` composite.

---

## § 4. Extension SDK consumption (EP-1..EP-18 register_all surface)

### 4.1 Entry point único `comunify/backend/src/modules/comunify/extensions.py`

```python
# Single register_all entry per anti-duplication.md §0 row "luana-platform Extension SDK"
from luana_core_extension_sdk import ExtensionPointRegistry

from .agentic.tools import (
    qualify_for_cohort,
    link_to_community,
    nurture_via_authority_content,
    book_discovery_call,
)
from .copilot.extractors import OfferLadderAdvisor, AuthorityVaultExtractor
from .copilot.workflows import CommunityEngagementWorkflow, CohortEnrollmentWorkflow
from .brand.voice_cloning import VoiceDistillationOrchestrator
from .agentic.guardrails import (
    community_safety_no_spam,
    community_safety_no_nsfw,
    community_safety_no_doxxing,
)
from .payment.adapters import (
    ComunifyStripeConnectAdapter,
    ComunifyMercadoPagoAdapter,
    ComunifyTokenizedRecurringAdapter,
)

ExtensionPointRegistry.register_all(
    brand_slug="comunify",
    config={
        "tools.agentic": [
            qualify_for_cohort,
            link_to_community,
            nurture_via_authority_content,
            book_discovery_call,
        ],
        "extractors.copilot": [OfferLadderAdvisor, AuthorityVaultExtractor],
        "workflows.copilot": [CommunityEngagementWorkflow, CohortEnrollmentWorkflow],
        "kb_packs": ["creator_economy_kb_v1"],
        "guardrails": [
            community_safety_no_spam,
            community_safety_no_nsfw,
            community_safety_no_doxxing,
            # prompt_injection_block reused from Story E base (canonical)
        ],
        "channels.payment": [
            ComunifyStripeConnectAdapter,
            ComunifyMercadoPagoAdapter,
            ComunifyTokenizedRecurringAdapter,
        ],
        "rubrics": ["vertical-creator-economy-fidelity"],   # NEW MD v1
        "brand_studio.enabled_sections": [
            "identity", "story", "narrative", "voice",
            "buyer_persona", "authority_vault", "team",
            "testimonials", "communication_assets", "contact",
        ],
        "brand_studio.sections.required": ["authority_vault"],   # ★ NEW Story 12
        "brand_studio.field_overrides": {
            "buyer_persona": {"min_count": 3},   # ★ NEW Story 12
        },
        "brand_studio.features": ["voice_cloning_pipeline"],   # ★ NEW Story 12
        "offer.entities": ["OfferLadder"],   # ★ NEW Story 12
        "offer_studio.preset_pack": "coaching_offers_v1",
        "compliance_level": "creator_economy",   # vs Vitalia hipaa_lite
        "subscriptions.enabled": True,   # NEW Story 12 recurring
        "subscriptions.plan_tiers": ["creator", "pro", "agency"],
        "voice_cloning_orchestrators": [VoiceDistillationOrchestrator],   # ★ NEW Story 12
    },
)
```

### 4.2 Extension SDK contract invariants (per Story 9 + Story 11 cement)

- `ExtensionPointRegistry.register_all()` is the ONLY public API for brand registration.
- `BrandContext` 9-field frozen dataclass — comunify consumes via `BrandContext(brand_slug="comunify", country=..., locale=..., timezone=..., currency_default=..., ...)`.
- EP-1..EP-18 immutable per Story 9 cement.
- TS types mirror Python dataclasses (Story 9 arch gate).

---

## § 5. Per-brand deploy framework (Phase 0 Story 11 verbatim subdir + Chris UI gates)

### 5.1 Directory layout

```
luana-platform/                  (monorepo root)
├── apps/                        (per-brand vertical apps)
├── core/                        (shared @luana/* + luana-core-*)
├── nicolify/                    (Story 10 cement)
├── vitalia/                     (Story 11 cement)
├── comunify/                    (Story 12 NEW — this story)
│   ├── backend/
│   │   ├── src/modules/comunify/
│   │   ├── alembic/versions/    (comunify-specific migrations idempotent)
│   │   ├── tests/
│   │   ├── pyproject.toml       (comunify BE workspace member)
│   │   └── Makefile
│   ├── frontend/
│   │   ├── src/
│   │   ├── widget/              (iframe embed bundle subscription)
│   │   ├── e2e/
│   │   ├── tests/
│   │   ├── package.json         (@luana/comunify FE workspace member)
│   │   └── next.config.ts
│   ├── config/
│   │   └── brand.yaml           (declarative BrandConfig)
│   ├── deploy/
│   │   ├── k8s/                 (deployment + service + ingress YAML manifests)
│   │   └── cloudflared/         (CF tunnel config + DNS records)
│   ├── docs/
│   │   ├── community-safety.md  (community safety pattern + 4 guardrails distintos vs Vitalia HIPAA)
│   │   ├── widget-embed.md      (copy-paste iframe snippet for creator-own landing pages)
│   │   └── voice-cloning-guide.md  (50+ chats requirements + distillation flow + ratify)
│   ├── scripts/
│   │   └── seed_fixture_creators.py  (3 LATAM creators programmatic seed)
│   ├── pyproject.toml           (workspace + dependencies)
│   ├── package.json             (@luana/comunify)
│   └── README.md
└── lupulo/                      (parked — Story 13)
```

### 5.2 Workspace integration

**Python (uv):**
```toml
# /home/chris/luana-platform/pyproject.toml
[tool.uv.workspace]
members = [
    "core/*",
    "nicolify/backend",
    "vitalia/backend",
    "comunify/backend",      # NEW Story 12
]
```

**Node.js (pnpm):**
```yaml
# /home/chris/luana-platform/pnpm-workspace.yaml
packages:
  - 'core/@luana/*'
  - 'nicolify/frontend'
  - 'vitalia/frontend'
  - 'comunify/frontend'      # NEW Story 12
  - 'apps/*'
```

### 5.3 K8s deploy (Chris UI gate)

**`/dev-team` autonomous scope:**
- Generate K8s manifest YAML (`comunify/deploy/k8s/{deployment,service,ingress}.yaml`).
- Helm chart skeleton (optional) — `comunify/deploy/k8s/helm/`.
- DigitalOcean / Hetzner / AWS-agnostic (Chris choice).

**Chris UI manual operations:**
- Cluster provision.
- Container registry push (GHCR per-brand namespace future Story 12.bis).
- DNS records `comunify.io` + `dashboard.comunify.io` + `landing.comunify.io` + `landing.comunify.io/{handle}` (Cloudflare dashboard).
- Cloudflare Tunnel setup post-cluster.

### 5.4 Clerk app #3 provisioning (Chris UI gate)

- Chris signup `dashboard.clerk.com` → app `comunify`.
- Generate publishable_key + secret_key + webhook secret.
- JWT issuer config (single sign-on across Luana brands NOT required per Phase 0 — Comunify stand-alone Clerk app, like Vitalia).
- Webhook endpoint `/api/v1/comunify/webhooks/clerk` (BE handler signup completion → tenant create).

### 5.5 Payment gateway production keys (Chris UI gate Q6=B)

- MercadoPago production credentials (account per país: AR / MX / CL / CO / PE primary).
- Stripe Connect onboarding (US/EU subscribers secondary market).
- Tokenized recurring schedules per subscription month + cohort installments.

---

## § 6. Cross-repo flow (AISALESHT ↔ luana-platform/comunify/)

### 6.1 Source-of-truth localization Story 12

Per Phase 0 Q3=B (Story 11 verbatim):

| Surface | SSoT (Story 12 build) | Mirror destination |
|---|---|---|
| BE code | `/home/chris/luana-platform/comunify/backend/` | N/A — luana-platform monorepo IS the SSoT |
| FE code | `/home/chris/luana-platform/comunify/frontend/` | N/A — same |
| Spec + design + arch | `/home/chris/AISALESHT/docs/product/stories/luana-comunify-bootstrap/` | Hard-copied to `/home/chris/luana-platform/docs/product/stories/luana-comunify-bootstrap/` at Story 12 merge (T-13 precedent Story 10) |
| Capabilities + outcomes + modules + BACKLOG | `/home/chris/AISALESHT/docs/product/` | luana-platform mirror at Story 12.bis or future PM migration story |

### 6.2 Build phase locality

- **/dev-team builders work in `/home/chris/luana-platform/comunify/`** (NOT in AISALESHT).
- Each ticket's `files_in_scope` lists absolute paths under `/home/chris/luana-platform/comunify/`.
- AISALESHT preserves docs only (Story 12 spec / design / arch ratification artifacts).

### 6.3 Future Story 12.bis extraction

Per Phase 0 Q1=A + Q3=B: Story 12.bis post-Story-12-merge extracts `luana-platform/comunify/` to standalone `alpacapurpura/comunify-brand-repo` via rsync + delete pattern (Story 10 T-13 / Story 11 precedent).

---

## § 7. Migration consolidation (Alembic per Story 10/11 cement pattern)

### 7.1 Migration strategy per Story 10/11 precedent

- Single consolidated snapshot `001_comunify_initial_snapshot.py` containing ALL comunify tables.
- All DDL idempotent: `CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`.
- **NEVER `sa.Enum(..., create_type=True)`** in `op.create_table()` — use raw SQL `DO $$ BEGIN CREATE TYPE ... ; EXCEPTION WHEN duplicate_object THEN NULL; END $$;`.
- Test pre-prod: clone DB workflow per `.claude/rules/backend-migrations.md`.
- Arch fitness test `test_comunify_migrations_idempotent.py` ratchets parsing for raw SQL `IF NOT EXISTS` pattern.

### 7.2 Tables introduced Story 12

| Table | Purpose | Tenant isolated |
|---|---|---|
| `comunify_cohorts` | Creator cohort definitions (name + capacity + start/end + criteria) | YES |
| `comunify_cohort_members` | Members enrolled per cohort (subscriber_id + tier + engagement_score + last_active) | YES |
| `comunify_cohort_broadcasts` | Broadcast messages to cohort with audience filter + delivery status | YES |
| `comunify_cohort_broadcast_recipients` | Per-recipient delivery + open/reply tracking | YES |
| `comunify_community_posts` | Member posts (text + media + status + moderation_result) | YES |
| `comunify_community_post_attachments` | Image/video attachments (NSFW score + tenant isolated) | YES |
| `comunify_community_moderation_events` | Moderation classifier results + creator actions audit | YES |
| `comunify_subscriptions` | Recurring subscription per subscriber (plan_tier + status + access_until + dunning_state) | YES |
| `comunify_subscription_charges` | Per-charge tokenized recurring records (installment_n + amount + status) | YES |
| `comunify_offer_ladders` | 4-level offer ladder relations per tenant (level_1_id → level_4_id) | YES |
| `comunify_voice_cloning_samples` | Uploaded chats + voice notes metadata (count + dialect + sanitized post-distill) | YES |
| `comunify_voice_distillation_jobs` | Async distillation job tracking (status + samples_count + confidence + compiled_blocks) | YES |
| `comunify_lead_qualification_records` | qualify_for_cohort tool snapshot results | YES |
| `comunify_community_audit_log` | Community safety + compliance event log (5-year retention) | YES |
| `comunify_plan_tier_configs` | Plan tier configs (creator/pro/agency features_enabled JSONB + price_usd_monthly) | NO (cross-tenant catalog) |

Detail (column types + indexes + foreign keys) → `03-arch-be.md` § 3-§ 4.

### 7.3 Schema-mirror exception (per `.claude/rules/backend-ddd.md`)

Story 12 does NOT trigger schema-mirror exception (no shared/ migrations introducing tables to copilot/sales_agent modules). All comunify tables live in `comunify_*` namespace — fully isolated.

---

## § 8. Acceptance criteria architecture-level

Per spec § 18 + 02-design § 20.2:

- ✅ Comunify subdir bootstrap: `luana-platform/comunify/{backend,frontend,config,deploy,docs}/` populated with workspace integration verified (`uv sync` + `pnpm install`).
- ✅ BrandConfig declarative `comunify/config/brand.yaml` complete + EP-1..EP-18 register_all surface enforced.
- ✅ 13 BE entities + repositories + services + endpoints implemented with tenant isolation enforced.
- ✅ Alembic migrations idempotent + arch fitness test passing.
- ✅ 4 agentic tools registered (Opus 4.7 mandatory R23).
- ✅ 2 extractors extend BaseExtractionOrchestrator (anti-duplication compliant).
- ✅ CommunityEngagementWorkflow + CohortEnrollmentWorkflow LangGraph + RedisSaver checkpointer functional.
- ✅ 1 KB pack ingested into Qdrant tenant-isolated collection.
- ✅ 4 guardrails registered in copilot/sales_agent middleware chain.
- ✅ **Voice cloning pipeline functional (50+ samples → distilled compiled v2 6-block → ratified) — NEW Story 12.**
- ✅ 13 FE routes operational with reuse @luana/ui + @luana/shared.
- ✅ 11 NEW comunify-specific components implemented (justified anti-duplication).
- ✅ Subscription widget iframe embeddable bundle (`comunify/frontend/widget/`).
- ✅ 24 E2E specs (3 fixtures × 8 flows) Playwright smoke green.
- ✅ 5 compliance smoke tests (prompt injection / spam / NSFW / doxxing / cross-tenant).
- ✅ Vertical-creator-economy-fidelity rubric MD v1 ratified + 8 personas YAMLs materialized.
- ✅ pass^k thresholds: happy ≥0.75 / nurture ≥0.75 / adversarial-light ≥0.85 / adversarial ≥0.95 (safety bar).
- ✅ Cost budgets honored: lead qualification conversation ≤$0.06, drift re-engagement ≤$0.025, voice cloning distillation ≤$0.18.
- ✅ K8s manifest YAML generated (Chris UI gate for cluster provision).
- ✅ Validators GREEN per 04-validators.yaml.

---

## § 9. Cross-arch sub-docs cite

Detail per surface lives in sub-architectures:

- **`03-arch-be.md`** — endpoints + DTOs + ORM models + migrations + repositories + services + tests (BE production code non-agentic + subscription/recurring billing infra + community + cohort domain).
- **`03-arch-fe.md`** — routes + components FSD-Lite + hooks React Query + Zod schemas + types + tests Vitest + Playwright E2E + subscription widget bundle + ladder visualizer.
- **`03-arch-agentic.md`** — tools defs (Pydantic schemas + register decorator) + extractors (wave composition) + workflows (LangGraph StateGraph + RedisSaver × 2) + KB pack registration (Qdrant) + voice cloning pipeline (4-wave distillation NEW) + prompt slot architecture (10 slots + cache_control) + voice constraints integration + guardrails middleware chain + channel adapters + observability writes + eval policy (vertical-creator-economy-fidelity rubric + 8 personas + pass^k + sandbox markers).

---

## § 10. Risks + mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Cross-repo navigation confusion (AISALESHT docs vs luana-platform code) | medium | 06-tickets.yaml `files_in_scope` uses absolute paths under `/home/chris/luana-platform/comunify/`; CLAUDE.md update post-Story-12 |
| Anti-duplication violation lifting MercadoPago adapter (already lifted Story 11) | medium | Pre-flight grep at T-payment-1 verifies Story 11 lift complete; EXTEND vs re-LIFT decision in CONTRACT |
| AGENTIC R23 owner_eligibility drift (Sonnet picked up Opus-only ticket) | high | 06-tickets.yaml `owner_eligibility: [opus]` exclusive on all production AGENTIC tickets; /dev-team Step 0.5 refuses spawn if mismatch |
| Migration drift (alembic models ≠ DB) | high | Story 10/11 T-10 pattern replica: consolidated snapshot + arch fitness `test_comunify_migrations_idempotent.py` + pg_dump diff sanity at architecture phase close |
| **Voice cloning pipeline failure (low confidence distillation)** | **high** | Wave-based confidence scoring + creator notification "re-distilar con más samples" + arch test `test_voice_cloning_distillation_quality_threshold.py` |
| **Voice cloning PII leak in chat samples persisted** | **high** | Sanitize samples post-distill (delete raw chats, retain only statistics) + audit_log `voice_cloning_pii_sanitized` |
| Vision multimodal LiteLLM router model availability (voice notes audio→text) | medium | /architect-agentic verifies Whisper model available; fallback `claude-opus-4-7` for audio transcription if Whisper unavailable |
| Cron worker capacity (Comunify 2 workflows + Vitalia 1 + Nicolify cycles + ETL) | medium | /architect-be load assessment ticket; if saturate → split worker pool per brand |
| Cohort capacity race (double-enrollment) | high | Advisory lock per `(cohort_id, enrollment_slot)` + idempotency key + integration test |
| Subscription dunning state machine race (concurrent webhook retries) | medium | Idempotency key `(subscriber_id, billing_period, installment_n)` + LangGraph atomicity |
| Cross-tenant cohort access (member of tenant_A accessing tenant_B cohort) | high | Middleware authoritative tenant_id + smoke test `smoke_cross_tenant.py` + audit log |
| Community spam attack at scale | medium | LLM classifier + heuristic combo + rate-limit per-author + pre-moderation new members default ON |
| Doxxing detection false positive (legitimate sharing creator's own email) | medium | Cross-reference cohort_members.phone/email — only block if matches OTHER member's contact, not creator's own |
| **NSFW image classifier latency (block upload pre-persistence)** | medium | Async classification with optimistic pre-upload + retroactive delete if NSFW>0.85; UX shows "verificando" |

---

## § 11. Decisiones arquitectónicas registradas

- **D1 (2026-05-14)** — Comunify subdir at `luana-platform/comunify/` (Phase 0 Q3=B Story 11 verbatim). Rationale: pattern Story 11 dual-state — full big-bang en subdir, future Story 12.bis extracts.
- **D2 (2026-05-14)** — Reuse `@luana/core/scheduling` calendar base + creator-economy `discovery_call` appointment type (Q4=A reuse). Rationale: anti-duplication.md; cross-brand benefit.
- **D3 (2026-05-14)** — `CommunityEngagementWorkflow` + `CohortEnrollmentWorkflow` inherit from `langgraph.graph.StateGraph` directly. NO `BaseWorkflowOrchestrator` shared abstraction Story 12 (defer Story 14+ YAGNI — total 3 workflows post-Story-12). Rationale: 02-design § 8 + Story 11 D3 precedent.
- **D4 (2026-05-14)** — MercadoPago + Stripe Connect + Tokenized recurring adapters CONSUME `@luana/core/channels/payment/*` lifted Story 11 (post-verify). Rationale: anti-duplication.md; Story 11 cement.
- **D5 (2026-05-14)** — Slot 4 `COMMUNITY_SAFETY_RAILS` NEW prompt slot (vertical-creator-economy overlay). Rationale: 02-design § 10.1; cache prefix layer.
- **D6 (2026-05-14)** — pass^k adversarial bar ≥0.95 (single safety leak across 5 trials = fail). Rationale: 02-design § 13.3; production-critical alignment Story G CI gate + Story 11 precedent.
- **D7 (2026-05-14)** — `compliance_level=creator_economy` (NOT hipaa_lite). Rationale: vertical-creator-economy non-medical → lighter compliance bar (community safety + GDPR/LGPD/Ley 25.326 local).
- **D8 (2026-05-14)** — `features.voice_cloning=True` (NEW Story 12 — vs Vitalia OFF). Rationale: 00-story.md ratificación; differentiator vs Story 11; pipeline 4-wave distillation BaseExtractionOrchestrator pattern.
- **D9 (2026-05-14)** — Chrome UI Spanish neutro pure tuteo (Q1=B). Sales_agent voice per-tenant exception (voice cloning compiled v2). Rationale: spec § 17.
- **D10 (2026-05-14)** — RedisSaver checkpointer cross-brand (NOT per-brand Redis). Rationale: shared infra, tenant_id en checkpoint state key always (Story 11 D10 precedent).
- **D11 (2026-05-14)** — Subscription widget BOTH iframe + canonical (Q5=B). Rationale: spec § 17 Q5; Anabella fixture demo iframe, Trini + Pablo demo canonical.
- **D12 (2026-05-14)** — Multi-account creator switcher UI DEFER Story 12.bis (Q2=B). Single tenant per Clerk user_id. Rationale: spec § 17 Q2.
- **D13 (2026-05-14)** — Third-party community bridge (Discord/Circle/Slack) DEFER Story 12.bis (Q3=B). Native community feed in-app Story 12. Rationale: spec § 17 Q3.
- **D14 (2026-05-14)** — `OfferLadder` entity initially comunify-local; LIFT-SHARED candidate Story 13+ when 2nd vertical needs ladder (TBD). Rationale: YAGNI Story 12; arch decision documented for future evaluation.
- **D15 (2026-05-14)** — Voice cloning samples raw chats DELETED post-distillation (only statistics retained — sample_count, dialect_detected, vocabulary_anchors_extracted, confidence_score). Rationale: PII compliance + storage cost; if creator re-distills with new samples, uploads fresh.
- **D16 (2026-05-14)** — Community moderation classifier: Haiku 4.5 default (~$0.005 per post target). Sonnet 4.6 fallback only if Haiku accuracy <80%. Rationale: cost target + 02-design § 14.6.
- **D17 (2026-05-14)** — `creator_economy_kb_v1` Qdrant collection name `comunify_creator_economy_kb_v1` (per-brand prefix consistent with Vitalia `vitalia_medical_kb_*` Story 11). Rationale: namespace consistency.
- **D18 (2026-05-14)** — `community_audit_log` retention 5 years (vs Vitalia 7-year HIPAA). Rationale: creator-economy lighter compliance bar (no medical regulatory requirement).
- **D19 (2026-05-14)** — Subscription dunning state machine: active → past_due (3d) → suspended (7d, lose write access) → cancelled (14d, lose read access). Rationale: industry standard recurring billing UX; grace period preserves goodwill.
- **D20 (2026-05-14)** — `coaching_offers_v1` preset pack registered Story 12 in `@luana/core/offer-studio/presets/`. Lift-shared candidate Story 13+ (Lupulo may consume). Rationale: anti-duplication.md.

---

## § 12. Próximo paso (/architect orchestrator)

Reúno los 03-arch-{be,fe,agentic}.md (este file IS el consolidated). Produzco:
- `04-validators.yaml` (4 categories — non_functional / functional / visual / agentic_eval)
- `05-guidelines.md` (patterns required/forbidden + files in scope + skills/rules per ticket type)
- `06-tickets.yaml` (~38 atomic tickets ≤4h each con `decisions_applicable` + `production_code` + `owner_eligibility` per R23)

Cierra Sesion 12 Phase 2: state `refined → ready` post Chris ratification (autonomous self-ratify Sesion 12 per Q4=A).

---

**03-arch.md consolidated draft v1 — Sesion 12 autonomous Phase 2.**

done -> docs/product/stories/luana-comunify-bootstrap/03-arch.md
