<!-- voseo-allowed: arch doc cites sales_agent voice constraints + tenant voice profiles per Slot 5 BRAND_VOICE SSoT. Chrome UI microcopy enforced Spanish neutro tuteo per Q1=B (spec § 17). -->
---
story_id: luana-vitalia-bootstrap
arch_version: 1
ratified_by_chris: false
architect_owner: claude-opus-4-7
sub_architects: [architect-be, architect-fe, architect-agentic]
surfaces: [backend, frontend, agentic, infra]
last_modified: 2026-05-13
links:
  spec: "01-spec.md"
  agentic_design: "02-design-agentic.md"
  phase0: "00-phase0-ratification.md"
  outcome: "../../outcomes/luana-platform-migration.md"
  sub_arch_be: "03-arch-be.md"
  sub_arch_fe: "03-arch-fe.md"
  sub_arch_agentic: "03-arch-agentic.md"
  validators: "04-validators.yaml"
  guidelines: "05-guidelines.md"
  tickets: "06-tickets.yaml"
  story_10_precedent: "../../../../archive/2026/stories/luana-nicolify-migration/"
ready_package:
  - 03-arch.md (this file — consolidated)
  - 03-arch-be.md
  - 03-arch-fe.md
  - 03-arch-agentic.md
  - 04-validators.yaml
  - 05-guidelines.md
  - 06-tickets.yaml
---

# 03-arch.md — Story 11 luana-vitalia-bootstrap (consolidated)

> **Outcome:** luana-platform-migration · **Sequence:** 11/14 · **State:** refined → ready (Sesion 2 Phase 2)
> **Strategy:** Full-stack vertical-medical brand bootstrap consumiendo Luana Platform v0.1.0+ (Story 10 cement) via Extension SDK EP-1..EP-18. Code lives `luana-platform/vitalia/` subdir.

---

## § 1. Resumen ejecutivo

Story 11 entrega Vitalia como **vertical-medical brand app** sobre Luana Platform monorepo. Tres ejes técnicos:

- **Backend (BE):** módulo nuevo `vitalia` con DDD Inside-Out (`domain/infrastructure/application/api/`) consumiendo `@luana/core/*` packages via workspace imports. Cinco entidades nuevas (`VitaliaBooking`, `VitaliaTreatmentFollowup`, `VitaliaConsentRecord`, `VitaliaMedicalAuditLog`, `VitaliaPlanTierConfig`) + 2 lift-shared adapters (`MercadoPagoAdapter`, `TokenizedRecurringChargeAdapter` if not exists). Alembic snapshot consolidation pattern Story 10 T-10 replica para vitalia migrations. 5 servicios DDD (Onboarding, Booking, PrepaidPayment, Consent, ComplianceEvent, TreatmentFollowup).

- **Frontend (FE):** Next.js 16 App Router en `vitalia/frontend/` consumiendo `@luana/ui` + `@luana/shared` (16 Shadcn primitives + 8 shared components). 9 routes (onboarding wizard 3-step, brand-studio 4 secciones, offer wizard medical_services 5-step, bookings calendar + widget iframe, treatments dashboard, patients CDP medical-flavor, appointments, medical-compliance audit log). 7 NEW vitalia-specific components (clinic-type-picker, consent-signature-modal, treatment-timeline, etc) — todos justificados anti-duplication. Embeddable booking widget bundle (`vitalia/frontend/widget/`) postMessage protocol.

- **Agentic:** vertical-medical surface en `vitalia/backend/src/modules/vitalia/agentic/` registrando via Extension SDK: 4 tools (`prepaid_payment_check`, `treatment_followup_check`, `medical_consent_request`, `appointment_reschedule_with_doctor`) + 2 extractors (`MedicalKBExtractor`, `DentalHistoryExtractor` — ambos extend `BaseExtractionOrchestrator`) + 1 LangGraph workflow (`TreatmentFollowupWorkflow` D0→D5→D14→D90 con RedisSaver checkpointer) + 3 KB packs Qdrant (`medical_kb_dental_v1`, `medical_kb_psychology_v1`, `medical_kb_psychiatry_v1`) + 4 guardrails (`medical_safety_no_diagnosis`, `medical_safety_no_prescription`, `medical_disclaimer_required`, `prompt_injection_block`). Prompt slot architecture 10 slots con NEW Slot 4 `MEDICAL_SAFETY_RAILS`. R23 Opus mandatory para todo production code AGENTIC.

**Cross-repo flow:** Story 11 commits land en `/home/chris/luana-platform/vitalia/` (monorepo subdir Phase 0 Q3=B). Future Story 11.bis extract to `alpacapurpura/vitalia-brand-repo` standalone (rsync + delete pattern Story 10 T-13 precedent).

**Chris UI manual gates (Phase 0 Q4=B):** Clerk app #2 provisioning + K8s cluster + DNS records vitalia.health + MercadoPago production credentials + Stripe Connect onboarding. `/dev-team` autonomous scope = code + manifests + scripts + sandbox; Chris executes irreversible/production-adjacent operations via UI.

---

## § 2. Surface decomposition

### 2.1 Surface inventory por capa

| Surface | Path | Owner sub-architect | Production code | R23 Opus mandatory |
|---|---|---|---|---|
| **Backend** módulo nuevo | `luana-platform/vitalia/backend/src/modules/vitalia/{domain,infrastructure,application,api}/` | `architect-be` | YES (non-agentic) | NO (Sonnet OK) |
| **Backend** agentic (tools + extractors + workflow + guardrails + KB ingest) | `luana-platform/vitalia/backend/src/modules/vitalia/agentic/` + `vitalia/backend/src/modules/vitalia/copilot/{extractors,workflows}/` | `architect-agentic` | YES (AGENTIC) | **YES Opus 4.7** |
| **Backend** payment channel adapters | `vitalia/backend/src/modules/vitalia/payment/` + extends `@luana/core/channels` if MP not present | `architect-be` (lift shared if needed) | YES (non-agentic) | NO |
| **Backend** Alembic migrations | `vitalia/backend/alembic/versions/` (idempotent IF NOT EXISTS) | `architect-be` | YES (data layer) | NO |
| **Backend** tests | `vitalia/backend/tests/{unit,integration,agentic_evals}/` | per ticket | NO (tests) | NO (Sonnet OK incluso para agentic-tests) |
| **Frontend** routes + components + hooks + schemas | `luana-platform/vitalia/frontend/src/{app,features/vitalia}/` | `architect-fe` | YES (non-agentic) | NO |
| **Frontend** booking widget bundle iframe | `luana-platform/vitalia/frontend/widget/` | `architect-fe` | YES (non-agentic) | NO |
| **Frontend** tests Vitest + Playwright | `vitalia/frontend/{tests,e2e}/` | per ticket | NO (tests) | NO |
| **Config** BrandConfig declarative | `vitalia/config/brand.yaml` | shared (BE + agentic owners) | NO (config) | NO |
| **Config** K8s manifests + CF tunnel scripts | `vitalia/deploy/` | `architect-be` (infra) | NO (config) | NO |
| **Docs** compliance + booking widget embed | `vitalia/docs/{compliance,booking-widget-embed}.md` | shared | NO (docs) | NO |
| **Personas YAMLs** archetype-aware vertical-medical | `docs/specs/personas/archetype-aware/patient-*.yaml` (6 NEW) | `architect-agentic` | NO (eval fixtures) | NO (Sonnet OK personas YAML) |
| **Rubric MD v1** vertical-medical-fidelity | `docs/specs/rubrics/vertical-medical-fidelity.md` (NEW) | `architect-agentic` | NO (eval spec) | NO (Sonnet OK rubric MD) |

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
                       └────────────────┬─────────────────┘
                                        │ consume
                                        ▼
       ┌─────────────────────────────────────────────────────────────┐
       │  vitalia/ (Story 11 NEW)                                    │
       │                                                             │
       │  ┌─────────────────────────────────────────────────────┐  │
       │  │  vitalia/backend/src/modules/vitalia/               │  │
       │  │  ├── domain/        (entities + VOs + events)       │  │
       │  │  ├── infrastructure/(repos + ORM models + adapters) │  │
       │  │  ├── application/   (services + event handlers)     │  │
       │  │  ├── api/           (routes + DTOs Pydantic v2)     │  │
       │  │  ├── agentic/       (4 tools — R23 Opus)            │  │
       │  │  ├── copilot/                                        │  │
       │  │  │   ├── extractors/(2 — extend Base shared)        │  │
       │  │  │   └── workflows/ (TreatmentFollowupWorkflow)     │  │
       │  │  ├── payment/       (adapters: MP, Stripe, Tokenize)│  │
       │  │  └── extensions.py  (register_all entry — EP-1..18) │  │
       │  └─────────────────────────────────────────────────────┘  │
       │                                                             │
       │  ┌─────────────────────────────────────────────────────┐  │
       │  │  vitalia/frontend/                                  │  │
       │  │  ├── src/app/[route]/page.tsx (Server Components)   │  │
       │  │  ├── src/features/vitalia/    (FSD-Lite)            │  │
       │  │  │   ├── api/                                       │  │
       │  │  │   ├── components/                                │  │
       │  │  │   ├── hooks/                                     │  │
       │  │  │   ├── schemas/                                   │  │
       │  │  │   └── types/                                     │  │
       │  │  └── widget/        (embeddable iframe bundle)      │  │
       │  └─────────────────────────────────────────────────────┘  │
       │                                                             │
       │  ┌─────────────────────────────────────────────────────┐  │
       │  │  vitalia/config/brand.yaml (declarative)            │  │
       │  │  vitalia/deploy/{k8s,cloudflared}/                  │  │
       │  │  vitalia/docs/{compliance,booking-widget-embed}.md  │  │
       │  └─────────────────────────────────────────────────────┘  │
       └─────────────────────────────────────────────────────────────┘
```

### 2.3 Boundary contract

- `vitalia/backend/src/modules/vitalia/*` → **CONSUMES** `@luana/core/*` packages, `shared/agent_observability/*`, `shared/billing/*`, `shared/idempotency/*`, `shared/extraction/base_orchestrator`, `shared/scheduling/calendar` (Q4=A reuse).
- `vitalia/backend/src/modules/vitalia/*` → **NEVER touches** `modules/copilot/` o `modules/sales_agent/` source (consume runtime via extension SDK registry — both copilot + sales_agent runtime live in `@luana/core/{copilot,sales-agent}`).
- `vitalia/frontend/*` → **CONSUMES** `@luana/ui`, `@luana/shared`, `fetchClient` (auto-injects `X-Tenant-ID`).
- Cross-brand isolation: vitalia NEVER imports `nicolify/`, `comunify/`, `lupulo/` (parallel verticals — Stories 12/13).

---

## § 3. Cross-cutting concerns

### 3.1 Tenant isolation (per `.claude/rules/tenant-isolation.md`)

**Mandatory pattern todas las queries:**
```python
# All vitalia repositories MUST filter tenant_id (incluso get_by_id)
async def get_booking_by_id(self, booking_id: UUID, tenant_id: UUID) -> Booking | None:
    stmt = (
        select(VitaliaBookingModel)
        .where(
            VitaliaBookingModel.id == booking_id,
            VitaliaBookingModel.tenant_id == tenant_id,  # MANDATORY
            VitaliaBookingModel.deleted_at.is_(None),    # soft delete
        )
    )
```

**Enforcement layers:**
- Middleware Clerk JWT → injects `X-Tenant-ID` from JWT (authoritative — never client-supplied).
- Repository constructor receives `tenant_id` required param.
- Arch fitness test `test_no_query_without_tenant_filter.py` ratchets vitalia module from Story 10 baseline.
- Cross-tenant attempt audit logged via `medical_audit_log` event `cross_tenant_attempt` (spec § 3.1.D + § 15.4).

### 3.2 Master data + multi-currency (per `.claude/rules/master-data.md` + `.claude/rules/currency-handling.md`)

**Pattern:**
- BE store UTC always (`utc_now()`, `DateTime(timezone=True)`).
- `TenantLocale` VO injects per-tenant currency + timezone via `get_tenant_locale()` DI.
- **Currencies supported Story 11:** USD (Sanaré primary), ARS (Aurora AR), CLP (Mindful CL), MXN (Sanaré MX market), COP, PEN, BRL.
- DTOs monetary fields include `currency: str | None = None` (ISO 4217).
- FE consumes `useTenantLocale()` → `formatMoney(amount, currency)`. **NEVER hardcode 'USD'** — fallback `data.currency ?? useTenantLocale().currency`.
- Cron scheduler `TreatmentFollowupWorkflow` ticks at 8am local TZ (Aurora BA = UTC-3, Mindful Santiago = UTC-3/UTC-4 DST, Sanaré MX City = UTC-6).

### 3.3 PII sanitization (per Tessl `pii-sanitisation.md` + medical extension)

**Pattern:**
- All FastAPI endpoints `response_model=` Pydantic v2 model. Raw dicts / ORM / untyped banned (arch fitness gate).
- `shared.agent_observability.recording.sanitization::sanitize_payload` invoked BEFORE persisting `copilot_trace_event` + `copilot_llm_call` + `medical_audit_log` payloads.
- **Medical PII extension** (vertical-specific):
  - Patient phone → mask `+54***5555` (last 4 visible for support).
  - Patient email → mask `j***@***.com`.
  - National IDs (DNI AR / RUT CL / RFC MX / CURP MX / CC CO) → `[NATIONAL_ID]`.
  - Medication names → kept verbatim (clinically relevant per `_pii_patterns.py::medication_names` category) + log `medication_mentioned` event.
  - Medical conditions → kept verbatim (clinically relevant) + log `medical_pii_detected` event.
  - Consent URLs → `[CONSENT_URL_REDACTED]` post-signing.
- Offer description + testimonial inputs run through `pii_scanner` middleware **BEFORE persist** (spec § 3.2.D + § 3.3.D adversarial scenarios).

### 3.4 Spanish neutro chrome UI + sales_agent voice exception

**Chrome UI (clinic_owner-facing — operator-facing) — spec § 12.1 + Q1=B ratified:**
- Spanish neutro LatAm puro **tuteo** (tú/tu/tienes/eres/puedes/haces).
- NO voseo en buttons / forms / breadcrumbs / toasts / validations / banners.
- Microcopy SSoT = spec § 8.1–8.6 (immutable post-ratification).
- Arch fitness gate `test_vitalia_ui_strings_no_voseo.py` greps `frontend/src/features/vitalia/` for voseo verbs.

**Sales_agent voice (patient-facing) — spec § 12.2 exception per `.claude/rules/sales-agent-brand-voice.md`:**
- Voice viene de `personality_profiles.system_instruction` compiled v2 per tenant (Slot 5 `BRAND_VOICE`).
- Aurora AR puede voseo (preset hipotético `warm_close` con voseo enabled).
- Mindful CL neutro chileno tuteo.
- Sanaré LATAM neutro broad LatAm.
- Voice fidelity grader threshold ≥0.8 + vertical-medical-fidelity ≥0.85 (higher bar for safety).
- `# voseo-allowed: ...` magic comment honored in test fixtures + rule docs + audit reports per R25.

### 3.5 HIPAA-lite compliance

**Pattern (spec § 14):**
- Story 11 = HIPAA-**lite** (LatAm local data protection laws Ley 25.326 AR, LGPD BR, LFPDPPP MX). **NOT HIPAA full** (US healthcare regulation).
- No Stripe Healthcare flag (Q6=B ratified) — `compliance_level: hipaa_lite` declarado en BrandConfig + Stripe payment metadata.
- Consent capture mandatory pre-procedure with `requires_informed_consent=true` (signed name OR signature pad + IP + user_agent + timestamp).
- Compliance audit log (`medical_audit_log` table) tenant-scoped retention 7 years legal record.
- 4 compliance smoke tests (spec § 15.1–15.4):
  - `smoke_prompt_injection.py` — 5 injection patterns (diagnosis / ignore prompt / jailbreak / role swap / data exfil).
  - `smoke_pii_detection.py` — 10 inputs varying PII (AR DNI / CL RUT / MX RFC / email / phone).
  - `smoke_cross_tenant.py` — 3 cross-tenant attack vectors blocked at middleware.
  - `smoke_hipaa_disclaimer.py` — 5 conversation flows triggering medical disclaimer.

---

## § 4. Extension SDK consumption (EP-1..EP-18 register_all surface)

### 4.1 Entry point único `vitalia/backend/src/modules/vitalia/extensions.py`

```python
# Single register_all entry per anti-duplication.md §0 row "luana-platform Extension SDK"
from luana_core_extension_sdk import ExtensionPointRegistry

from .agentic.tools import (
    prepaid_payment_check,
    treatment_followup_check,
    medical_consent_request,
    appointment_reschedule_with_doctor,
)
from .copilot.extractors import MedicalKBExtractor, DentalHistoryExtractor
from .copilot.workflows import TreatmentFollowupWorkflow
from .agentic.guardrails import (
    medical_safety_no_diagnosis,
    medical_safety_no_prescription,
    medical_disclaimer_required,
)
from .payment.adapters import (
    VitaliaStripeConnectAdapter,
    VitaliaMercadoPagoAdapter,
    VitaliaTokenizedRecurringAdapter,
)

ExtensionPointRegistry.register_all(
    brand_slug="vitalia",
    config={
        "tools.agentic": [
            prepaid_payment_check,
            treatment_followup_check,
            medical_consent_request,
            appointment_reschedule_with_doctor,
        ],
        "extractors.copilot": [MedicalKBExtractor, DentalHistoryExtractor],
        "workflows.copilot": [TreatmentFollowupWorkflow],
        "kb_packs": [
            "medical_kb_dental_v1",
            "medical_kb_psychology_v1",
            "medical_kb_psychiatry_v1",
        ],
        "guardrails": [
            medical_safety_no_diagnosis,
            medical_safety_no_prescription,
            medical_disclaimer_required,
            # prompt_injection_block reused from Story E base (canonical)
        ],
        "channels.payment": [
            VitaliaStripeConnectAdapter,
            VitaliaMercadoPagoAdapter,
            VitaliaTokenizedRecurringAdapter,
        ],
        "rubrics": ["vertical-medical-fidelity"],  # NEW MD v1
        "brand_studio.enabled_sections": ["identity", "contact", "team", "testimonials"],
        "offer_studio.preset_pack": "medical_services_v1",
        "compliance_level": "hipaa_lite",  # Q6=B ratified
    },
)
```

### 4.2 Extension SDK contract invariants (per Story 9 cement)

- `ExtensionPointRegistry.register_all()` is the ONLY public API for brand registration.
- `BrandContext` 9-field frozen dataclass — vitalia consumes via `BrandContext(brand_slug="vitalia", country=..., locale=..., timezone=..., currency_default=..., ...)`.
- EP-1..EP-18 immutable per Story 9 cement (`core/luana-core-extension-sdk/src/luana_core_extension_sdk/extension_points.py::ExtensionPointRegistry`).
- TS types mirror Python dataclasses (`apps/test-brand/python/test_brand/tests/` precedent for vitalia).

---

## § 5. Per-brand deploy framework (Phase 0 Q3=B subdir + Chris UI gates Q4=B)

### 5.1 Directory layout per Phase 0 ratified

```
luana-platform/                  (monorepo root)
├── apps/                        (per-brand vertical apps)
├── core/                        (shared @luana/* + luana-core-*)
├── nicolify/                    (Story 10 cement)
├── vitalia/                     (Story 11 NEW — this story)
│   ├── backend/
│   │   ├── src/modules/vitalia/
│   │   ├── alembic/versions/    (vitalia-specific migrations idempotent)
│   │   ├── tests/
│   │   ├── pyproject.toml       (vitalia BE workspace member)
│   │   └── Makefile
│   ├── frontend/
│   │   ├── src/
│   │   ├── widget/              (iframe embed bundle)
│   │   ├── e2e/
│   │   ├── tests/
│   │   ├── package.json         (@luana/vitalia FE workspace member)
│   │   └── next.config.ts
│   ├── config/
│   │   └── brand.yaml           (declarative BrandConfig)
│   ├── deploy/
│   │   ├── k8s/                 (deployment + service + ingress YAML manifests)
│   │   └── cloudflared/         (CF tunnel config + DNS records)
│   ├── docs/
│   │   ├── compliance.md        (HIPAA-lite distinction + LatAm laws)
│   │   └── booking-widget-embed.md  (copy-paste iframe snippet for clinic_owners)
│   ├── scripts/
│   │   └── seed_fixture_clinics.py  (3 LatAm clinics programmatic seed)
│   ├── pyproject.toml           (workspace + dependencies)
│   ├── package.json             (@luana/vitalia)
│   └── README.md
├── comunify/                    (parked — Story 12)
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
    "vitalia/backend",      # NEW Story 11
]
```

**Node.js (pnpm):**
```yaml
# /home/chris/luana-platform/pnpm-workspace.yaml
packages:
  - 'core/@luana/*'
  - 'nicolify/frontend'
  - 'vitalia/frontend'      # NEW Story 11
  - 'apps/*'
```

### 5.3 K8s deploy (Chris UI gate Q4=B)

**`/dev-team` autonomous scope:**
- Generate K8s manifest YAML (`vitalia/deploy/k8s/{deployment,service,ingress}.yaml`).
- Helm chart skeleton (optional) — `vitalia/deploy/k8s/helm/`.
- DigitalOcean / Hetzner / AWS-agnostic (Chris choice).

**Chris UI manual operations:**
- Cluster provision (DigitalOcean / Hetzner / AWS).
- Container registry push (GHCR per-brand namespace future Story 11.bis).
- DNS records `vitalia.health` + `dashboard.vitalia.health` + `landing.vitalia.health` (Cloudflare dashboard).
- Cloudflare Tunnel setup post-cluster (CF dashboard + `vitalia/deploy/cloudflared/config.yml`).

### 5.4 Clerk app #2 provisioning (Chris UI gate Q4=B)

- Chris signup `dashboard.clerk.com` → app `vitalia`.
- Generate publishable_key + secret_key + webhook secret.
- JWT issuer config (single sign-on with Nicolify NOT required per Phase 0 — Vitalia stand-alone Clerk app).
- Webhook endpoint `/api/v1/vitalia/webhooks/clerk` (BE handler signup completion → tenant create).

### 5.5 Payment gateway production keys (Chris UI gate Q4=B)

- MercadoPago production credentials (account per país: AR / MX / BR / CL / CO).
- Stripe Connect onboarding (US/EU clinics secondary market).
- **NO Stripe Healthcare flag** (Q6=B ratified — `compliance_level=hipaa_lite` declared explicit).

---

## § 6. Cross-repo flow (AISALESHT ↔ luana-platform/vitalia/)

### 6.1 Source-of-truth localization Story 11

Per Phase 0 Q3=B ratified:

| Surface | SSoT (Story 11 build) | Mirror destination |
|---|---|---|
| BE code | `/home/chris/luana-platform/vitalia/backend/` | N/A — luana-platform monorepo IS the SSoT |
| FE code | `/home/chris/luana-platform/vitalia/frontend/` | N/A — same |
| Spec + design + arch | `/home/chris/AISALESHT/docs/product/stories/luana-vitalia-bootstrap/` | Hard-copied to `/home/chris/luana-platform/docs/product/stories/luana-vitalia-bootstrap/` at Story 11 merge (T-13 precedent Story 10) |
| Capabilities + outcomes + modules + BACKLOG | `/home/chris/AISALESHT/docs/product/` | luana-platform mirror at Story 11.bis or future PM migration story |

### 6.2 Build phase locality

- **/dev-team builders work in `/home/chris/luana-platform/vitalia/`** (NOT in AISALESHT — AISALESHT is parked post Story 10 T-14 archive).
- Each ticket's `files_in_scope` lists absolute paths under `/home/chris/luana-platform/vitalia/`.
- AISALESHT preserves docs only (Story 11 spec / design / arch ratification artifacts).

### 6.3 Future Story 11.bis extraction

Per Phase 0 Q3=B + Q1=A: Story 11.bis post-Story-11-merge extracts `luana-platform/vitalia/` to standalone `alpacapurpura/vitalia-brand-repo` via rsync + delete pattern (Story 10 T-13 precedent):

```bash
# Pseudo-precedent Story 11.bis (NOT executed in Story 11 itself)
rsync -av --delete /home/chris/luana-platform/vitalia/ /home/chris/vitalia-brand-repo/
cd /home/chris/vitalia-brand-repo && git init && git add -A && git commit -m "feat: extract vitalia brand from luana-platform monorepo"
gh repo create alpacapurpura/vitalia-brand-repo --private
git push -u origin main
# Then in luana-platform: rm -rf vitalia/ && commit
```

---

## § 7. Migration consolidation (Alembic per Story 10 T-10 cement pattern)

### 7.1 Migration strategy per Story 10 precedent

- Single consolidated snapshot `001_vitalia_initial_snapshot.py` containing ALL vitalia tables.
- All DDL idempotent: `CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`.
- **NEVER `sa.Enum(..., create_type=True)`** in `op.create_table()` — use raw SQL `DO $$ BEGIN CREATE TYPE ... ; EXCEPTION WHEN duplicate_object THEN NULL; END $$;`.
- Test pre-prod: clone DB workflow per `.claude/rules/backend-migrations.md` (clone migration_test DB → pg_dump schema → stamp current rev → upgrade head → drop).
- Arch fitness test `test_vitalia_migrations_idempotent.py` ratchets parsing for raw SQL `IF NOT EXISTS` pattern.

### 7.2 Tables introduced Story 11

| Table | Purpose | Tenant isolated |
|---|---|---|
| `vitalia_bookings` | Patient bookings with offer + doctor + slot + payment status | YES (tenant_id NOT NULL) |
| `vitalia_treatment_followups` | TreatmentFollowupWorkflow state per patient | YES |
| `vitalia_adherence_records` | Per-step adherence + sentiment from sales_agent classification | YES |
| `vitalia_consent_records` | Informed consent capture (signature + IP + user_agent + template version) | YES |
| `vitalia_medical_audit_log` | HIPAA-lite audit log all compliance events | YES (7-year retention) |
| `vitalia_plan_tier_configs` | Plan tier configs (features_enabled JSONB + price_usd_monthly) | NO (cross-tenant catalog) |
| `vitalia_payment_intents` | Payment intent records (Stripe / MercadoPago) | YES |
| `vitalia_payment_schedules` | Recurring tokenized payment schedules (paquetes + treatment installments) | YES |
| `vitalia_patient_medical_histories` | Extracted historia médica from MedicalKBExtractor (JSONB) | YES |
| `vitalia_patient_dental_histories` | Extracted historia dental from DentalHistoryExtractor (JSONB) | YES |
| `vitalia_doctor_extensions` | Vertical-medical extensions to doctor profile (specialty + treatment_room + max_concurrent) | YES |

Detail (column types + indexes + foreign keys) → `03-arch-be.md` § 3-§ 4.

### 7.3 Schema-mirror exception (per `.claude/rules/backend-ddd.md`)

Story 11 does NOT trigger schema-mirror exception (no shared/ migrations introducing tables to copilot/sales_agent modules). All vitalia tables live in `vitalia_*` namespace — fully isolated, NO mirror to `modules/copilot/persistence/models/` o `modules/sales_agent/persistence/models/`.

---

## § 8. Acceptance criteria architecture-level

Per spec § 18 + 02-design § 20.2:

- ✅ Vitalia subdir bootstrap: `luana-platform/vitalia/{backend,frontend,config,deploy,docs}/` populated with workspace integration verified (`uv sync` + `pnpm install`).
- ✅ BrandConfig declarative `vitalia/config/brand.yaml` complete + EP-1..EP-18 register_all surface enforced.
- ✅ 5 BE entities + repositories + services + endpoints implemented with tenant isolation enforced.
- ✅ Alembic migrations idempotent + arch fitness test passing.
- ✅ 4 agentic tools registered (Opus 4.7 mandatory R23).
- ✅ 2 extractors extend BaseExtractionOrchestrator (anti-duplication compliant).
- ✅ TreatmentFollowupWorkflow LangGraph + RedisSaver checkpointer functional.
- ✅ 3 KB packs ingested into Qdrant tenant-isolated collections.
- ✅ 4 guardrails registered in copilot/sales_agent middleware chain.
- ✅ 9 FE routes operational with reuse @luana/ui + @luana/shared.
- ✅ 7 NEW vitalia-specific components implemented (justified anti-duplication).
- ✅ Booking widget iframe embeddable bundle (`vitalia/frontend/widget/`).
- ✅ 18 E2E specs (3 fixtures × 6 flows) Playwright smoke green.
- ✅ 4 compliance smoke tests (prompt injection / PII detection / cross-tenant / HIPAA disclaimer).
- ✅ Vertical-medical-fidelity rubric MD v1 ratified + 7 personas YAMLs materialized.
- ✅ pass^k thresholds: happy ≥0.75 / nurture ≥0.75 / adversarial ≥0.95 (safety bar).
- ✅ Cost budgets honored: booking conversation ≤$0.08, followup turn ≤$0.025, PDF extract ≤$0.18.
- ✅ K8s manifest YAML generated (Chris UI gate for cluster provision).
- ✅ Validators GREEN per 04-validators.yaml.

---

## § 9. Cross-arch sub-docs cite

Detail per surface lives in sub-architectures:

- **`03-arch-be.md`** — endpoints + DTOs + ORM models + migrations + repositories + services + tests (BE production code non-agentic).
- **`03-arch-fe.md`** — routes + components FSD-Lite + hooks React Query + Zod schemas + types + tests Vitest + Playwright E2E + booking widget bundle.
- **`03-arch-agentic.md`** — tools defs (Pydantic schemas + register decorator) + extractors (wave composition) + workflow (LangGraph StateGraph + RedisSaver) + KB packs registration (Qdrant) + prompt slot architecture (10 slots + cache_control) + voice constraints integration + guardrails middleware chain + channel adapters + observability writes + eval policy (vertical-medical-fidelity rubric + 7 personas + pass^k + sandbox markers).

---

## § 10. Risks + mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Cross-repo navigation confusion (AISALESHT docs vs luana-platform code) | medium | 06-tickets.yaml `files_in_scope` uses absolute paths under `/home/chris/luana-platform/vitalia/`; CLAUDE.md update post-Story-11 docs builders work in luana-platform |
| Anti-duplication violation lifting MercadoPago adapter mid-build | high | Pre-flight grep + § 3 BE arch confirms during ticket T-X authoring; if @luana/core has MP base → EXTEND. If not → LIFT SHARED to `@luana/core/channels/payment/` first ticket | 
| AGENTIC R23 owner_eligibility drift (Sonnet picked up Opus-only ticket) | high | 06-tickets.yaml `owner_eligibility: [opus]` exclusive on all production AGENTIC tickets; /dev-team Step 0.5 refuses spawn if mismatch |
| Migration drift (alembic models ≠ DB) | high | Story 10 T-10 pattern replica: consolidated snapshot + arch fitness `test_vitalia_migrations_idempotent.py` + pg_dump diff sanity at architecture phase close |
| Vision multimodal LiteLLM router model availability | medium | /architect-agentic verifies `claude-sonnet-4-6-vision` available pre-ticket; fallback `claude-opus-4-7-vision` (higher cost) |
| Cron worker capacity (3 vitalia workflows + Nicolify cycles + ETL) | medium | /architect-be load assessment ticket T-X; if saturate → split worker pool per brand |
| Slot race in booking_confirm (double-booking) | high | Advisory lock per `(doctor_id, slot_iso)` enforced at `propose_and_book` action; idempotency key `(patient_id, doctor_id, target_slot)` window 60s |
| Prompt injection diagnosis attempt | high (safety) | Sandbox markers DQ2 Slot 4 + guardrail `medical_safety_no_diagnosis` (input+output layers) + audit_log + adversarial persona test pass^5 ≥0.95 |
| Patient PII leaked in offer description / testimonial | medium | PII scanner middleware BEFORE persist + arch fitness `test_no_pii_in_offer_table.py` |
| HIPAA-lite vs HIPAA confusion clinic onboarding | medium | `vitalia/docs/compliance.md` clear distinction + Stripe metadata `compliance_level=hipaa_lite` + BrandConfig flag |
| Clerk webhook race (signup → tenant create idempotency) | medium | Idempotency key on `clerk_user_id` in `shared.idempotency` table; second webhook within 1s → no-op |

---

## § 11. Decisiones arquitectónicas registradas

- **D1 (2026-05-13)** — Vitalia subdir at `luana-platform/vitalia/` (Phase 0 Q3=B). Rationale: pattern Story 10 dual-state — full big-bang en subdir, future Story 11.bis extracts to standalone repo.
- **D2 (2026-05-13)** — Reuse `@luana/core/scheduling` calendar base + vertical-medical extensions (Q4=A ratified). Rationale: anti-duplication.md; cross-brand benefit (Comunify/Lupulo also need scheduling).
- **D3 (2026-05-13)** — TreatmentFollowupWorkflow inherits from `langgraph.graph.StateGraph` directly. NO `BaseWorkflowOrchestrator` shared abstraction Story 11 (defer Story 14+ YAGNI). Rationale: 02-design § 8.1.
- **D4 (2026-05-13)** — MercadoPago adapter LIFT SHARED to `@luana/core/channels/payment/MercadoPagoAdapter` IF NOT exists. Rationale: anti-duplication.md (Comunify+Lupulo also LatAm). /architect-be verifies during 03-arch-be.md authoring.
- **D5 (2026-05-13)** — Slot 4 `MEDICAL_SAFETY_RAILS` NEW prompt slot (vertical-medical overlay). Rationale: 02-design § 10.1; cache prefix layer.
- **D6 (2026-05-13)** — pass^k adversarial bar ≥0.95 (single safety leak across 5 trials = fail). Rationale: 02-design § 13.3; production-critical alignment Story G CI gate.
- **D7 (2026-05-13)** — `compliance_level=hipaa_lite` (NOT hipaa_full). Q6=B ratified. Rationale: LatAm market primary, US HIPAA real requires Stripe Healthcare flag + extra audit (defer Story 11.bis).
- **D8 (2026-05-13)** — `features.voice_cloning=False` BrandConfig declarative (00-story.md). Rationale: Story 14 luana-brand-voice-elevation owns voice cloning future.
- **D9 (2026-05-13)** — Chrome UI Spanish neutro pure tuteo (Q1=B). Sales_agent voice per-tenant exception. Rationale: spec § 17.
- **D10 (2026-05-13)** — RedisSaver checkpointer cross-brand (NOT per-brand Redis). Rationale: shared infra, tenant_id en checkpoint state key always.
- **D11 (2026-05-13)** — Booking widget BOTH iframe + canonical (Q5=B). Rationale: spec § 17 Q5.
- **D12 (2026-05-13)** — Wellness vertical UI selector enabled but deep coverage DEFER Story 11.bis (Q7=B). Rationale: spec § 17 Q7.
- **D13 (2026-05-13)** — Multi-site UI federation DEFER Story 11.bis (Q2=B). Sanaré LATAM fixture uses single-country view MX primary. Rationale: spec § 17 Q2.
- **D14 (2026-05-13)** — Insurance integration LatAm DEFER Story 11.bis (Q3=B). Story 11 prepaid-only flow. Rationale: spec § 17 Q3.

---

## § 12. Próximo paso (/architect orchestrator)

Reúno los 03-arch-{be,fe,agentic}.md (este file IS el consolidated). Produzco:
- `04-validators.yaml` (4 categories — non_functional / functional / visual / agentic_eval)
- `05-guidelines.md` (patterns required/forbidden + files in scope + skills/rules per ticket type)
- `06-tickets.yaml` (25-30 atomic tickets ≤4h each con `decisions_applicable` + `production_code` + `owner_eligibility` per R23)

Cierra Sesion 2 Phase 2: state `refined → ready` post Chris ratification.

---

**03-arch.md consolidated draft v1 awaiting Chris ratification.**

done -> docs/product/stories/luana-vitalia-bootstrap/03-arch.md
