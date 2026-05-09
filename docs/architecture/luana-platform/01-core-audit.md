<!-- voseo-allowed: internal architectural planning doc, Chris-targeted, not user-facing UI -->

# Luana Core — Module Audit

> **Status:** Draft v0.1 — 2026-05-09
> **Owner:** Chris (alpacapurpura@) + Claude Opus 4.7
> **Purpose:** Inventario módulo-por-módulo de qué va a Luana core (transversal, compartido por las 4 marcas) vs qué queda como vertical-specific en cada brand app.
> **Consumers:** este doc es input para `02-extension-points.md`, `03-migration-plan.md`, y la decisión semanal de carve-out Sem 1-3.

## 0. Contexto

4 brand apps consumen Luana core:

| Brand | Vertical | Repo |
|---|---|---|
| **Nicolify** | SaaS marketing/sales generic (caso canónico) | `luana-platform/nicolify` |
| **Vitalia** | Medical/dental/wellness clinics | `luana-platform/vitalia` |
| **Comunify** | Creator/expert economy + community | `luana-platform/comunify` |
| **Lupulo Labs** | Gastronomy (booking + ordering agentic) | `luana-platform/lupulo-labs` |

Luana = `luana-platform/luana-core`. Publica packages versionados a GitHub Packages (private). Brands consumen via `pip install luana-core-*` y `npm install @luana/core-*`.

## 1. Filosofía de partición

| Verdict | Significado | Dónde vive |
|---|---|---|
| **CORE-FULL** | Engine genérico, comportamiento idéntico cross-brand | `luana-core/packages/core-{x}` |
| **CORE-ENGINE + BRAND-CONFIG** | Engine en core, config/data declarativa per-brand | core engine + `apps/{brand}/brand.config` |
| **CORE-ENGINE + BRAND-EXTENSION** | Engine en core, brand registra extensiones código (tools, providers, handlers) | core engine + `apps/{brand}/vertical-{niche}/` |
| **BRAND-SPECIFIC** | Lógica única de un vertical, no compartible | `apps/{brand}/vertical-{niche}/` exclusivo |
| **DROP** | Placeholder/dead — no migra a Luana | descartado o backlog futuro |

Regla: **el core nunca sabe de brand específica**. Cero `if (brand === "vitalia")`. Diferencias se materializan via config declarativa o extension points formales.

## 2. Backend — Módulo por módulo

### 2.1 Tabla resumen BE

| # | Módulo | LOC | Files | Verdict | Razón |
|---|---|---|---|---|---|
| 1 | `iam` | 1900 | 28 | **CORE-FULL** | Auth Clerk, tenant resolution, RBAC. Idéntico cross-brand |
| 2 | `core` | (infra) | — | **CORE-FULL** | Config, DB engine, Sentry, base repository, exceptions |
| 3 | `shared` | 20254 | 100+ | **CORE-FULL** (ya pre-extraído) | Es la pre-Luana. Detalle §2.3 |
| 4 | `copilot` | 33631 | 243 | **CORE-ENGINE + BRAND-EXTENSION** | Engine LangGraph + observability core. Tools/workflows/extractors brand-specific via registry |
| 5 | `sales_agent` | 17483 | 153 | **CORE-ENGINE + BRAND-EXTENSION** | Engine agent + brand voice compiler core. Tools (scheduler/payment/order/booking) brand-specific via registry |
| 6 | `brand` | 11312 | 81 | **CORE-ENGINE + BRAND-CONFIG** | Form-runtime + extraction engine core. `enabled_sections`, `field_overrides` per-brand |
| 7 | `offer` | 18877 | 95 | **CORE-ENGINE + BRAND-CONFIG** | Catalogs DAG + form-runtime + presets registry core. Brand activa preset packs vertical |
| 8 | `landing` | 1783 | 21 | **CORE-ENGINE + BRAND-CONFIG** | Page generator engine core. Templates/sections brand-config |
| 9 | `scheduling` | 1630 | 24 | **CORE-ENGINE + BRAND-EXTENSION** | Booking engine + GCal sync core. `bookingPolicy.canConfirm` extension (Vitalia prepaid, Lupulo table-availability) |
| 10 | `crm` | 5546 | 50 | **CORE-FULL** | CDP genérico, journey events, pipeline. Extensible via custom_fields data, no código |
| 11 | `analytics` | 30263 | 123 | **CORE-ENGINE + BRAND-CONFIG** | ETL framework + metric_catalog + 12 providers core. `enabled_metrics`, `channel_groups` brand-config |
| 12 | `connections` | 10134 | 67 | **CORE-ENGINE + BRAND-EXTENSION** | OAuth + adapter pattern core. Channel adapters brand-extension (Lupulo: POS/kitchen integration; Vitalia: payment gateway prepaid) |
| 13 | `assets` | 1870 | 24 | **CORE-FULL** | AI generation + R2 storage. Templates brand-config si necesario |
| 14 | `commercial_calendar` | 679 | 17 | **CORE-FULL** | Holidays + promotions calendar. Country code brand-config |
| 15 | `tenant_domains` | 1070 | 18 | **CORE-FULL** | Cloudflare Custom Hostnames. Idéntico |
| 16 | `tenant_profile` | 931 | 18 | **CORE-FULL** | Tenant settings, locale, currency, plan |
| 17 | `campaigns` | 10209 | 80 | **CORE-ENGINE + BRAND-CONFIG** | Campaign engine + scheduling. Templates vertical-specific (Vitalia: medical compliance; Lupulo: menú dinámico) |
| 18 | `social_proof` | 2944 | 39 | **CORE-FULL** | Testimonios + casos. Esquema genérico cross-brand |
| 19 | `advertising` | 3075 | 28 | **DROP** (placeholder) | Sin implementación real, ad data en analytics ETL |
| 20 | `social_media` | 5 | 5 | **DROP** (placeholder) | 5 LOC, vacío |

Total CORE: ~131k LOC BE. Total DROP: ~3k LOC. **96% del BE migra a Luana** (engine + config-points).

### 2.2 Detalle por módulo BE

#### `iam` — CORE-FULL
- **Goes to:** `luana-core/packages/core-iam`
- **Sub-packages:** Clerk integration, tenant resolution middleware, role/permission RBAC, onboarding flows, X-Tenant-ID header injection
- **Brand divergence:** ninguna. Todos usan Clerk + multitenant `X-Tenant-ID`.
- **Cleanup pre-extract:** ninguno. Puro core ya.

#### `core` (infra) — CORE-FULL
- **Goes to:** `luana-core/packages/core-platform`
- **Sub-packages:** Pydantic settings, DB engine factory, Sentry init, security middleware, base repository, exception hierarchy, FastAPI app factory (`redirect_slashes=False` mandatory)
- **Brand divergence:** brand-config carga env propio (DB URL, Sentry DSN, Clerk keys), pero la factory es shared.
- **Cleanup pre-extract:** revisar `Settings` class — campos brand-specific deben moverse a `BrandConfig` separado en cada app.

#### `shared` — CORE-FULL (ya pre-extraído)
**Este módulo es la mitad de Luana ya hoy.** Detalle dedicado §2.3.

#### `copilot` (33k LOC, el grande) — CORE-ENGINE + BRAND-EXTENSION
**Engine al core:**
- LangGraph state machine + `CopilotOrchestrator`
- DeepAgents subagent harness + `SubAgentMiddleware` isolation
- Anthropic prompt cache slot architecture (5min/1h TTL)
- Observability completa (`copilot_trace_event`, `copilot_llm_call`, cost recorder, retention workers)
- Tool registry pattern + base classes
- Workflow registry pattern + base classes
- Extractor registry pattern + base classes
- Module registry (`module_registry.py`) — descriptors
- LLM routing via shared LiteLLM Proxy
- Suggestion engine + provider registry
- Mutation journal + persistence
- Doc extraction pipeline (LLM-powered, route-based)
- Voice transcription endpoint
- Streamlit admin (LLM virtual keys, conversaciones, costo, etc.)

**Brand extension (vertical packages):**
- `vertical-medical` (Vitalia) → registra `MedicalKBExtractor`, `PrepaidPaymentChecker` tool, `TreatmentFollowupWorkflow`
- `vertical-creator-economy` (Comunify) → registra `OfferLadderAdvisor`, `AuthorityVaultExtractor`, `CommunityEngagementWorkflow`
- `vertical-gastronomy` (Lupulo) → registra `MenuExtractor`, `KitchenStatusTool`, `ReservationOrderWorkflow`

**Cleanup pre-extract:**
- ⚠️ Allowlist `KNOWN_LEGACY_LLM_FILES` ya en 0 (S3 PR-1 PI-2). ✅
- ⚠️ Capa duplicada `copilot/infrastructure/llm/` ya DELETED (S3 PR-1). ✅
- ⚠️ ModuleDescriptor entries dependen de cada módulo presente — al partir, registry necesita lazy-load (brand registra sus modules)
- ⚠️ Tools registrados en código (no en registry) — mapear cuáles son genéricos vs brand-specific antes de cortar
- ⚠️ Hardcoded prompts en algunos extractors deben moverse a templates configurables

#### `sales_agent` (17k LOC, el otro grande) — CORE-ENGINE + BRAND-EXTENSION
**Engine al core:**
- LangGraph orchestrator + state machine
- Agent identity prompt + brand voice compiler v2 (`personality_profiles.system_instruction`)
- Slot architecture (5 slots, prompt cache prefix)
- Tool registry (scheduler, payment, knowledge, qualification, follow-up base)
- Specialist routing semantic (NANO/FAST/REASONING/AGENT)
- Closer Studio API + WS (conversación humana en cargo)
- Buffer service + output manager
- Follow-up engine + scheduler
- Observability (traces, cost, evals)
- Eval framework (simulator dual-LLM, MAJ-EVAL grader, personas catalog, goldens dataset)
- Channel format registry (`format_for_channel`)
- Intent detector
- Semantic router
- PII sanitization

**Brand extension:**
- **Vitalia tools:** `prepaid_payment_check`, `treatment_followup_check`, `medical_consent_request`, `appointment_reschedule_with_doctor`
- **Comunify tools:** `qualify_for_cohort`, `link_to_community`, `nurture_via_authority_content`, `book_discovery_call`
- **Lupulo tools:** `book_table`, `place_order`, `query_menu`, `kitchen_eta`, `loyalty_check`
- **Personas catalog:** core ships archetype-aware base, brand registra personas verticales adicionales
- **Goldens curation:** core ships test framework, brand cura sus propios goldens (15-cell matrix)

**Cleanup pre-extract:**
- ⚠️ §3 protected surfaces (Closer Studio API/WS, BufferService, OutputManager, FollowUp, PromptVersionModel, agent_state_checkpoint) — extracción quirúrgica, marcar boundaries
- ⚠️ Eval simulator + grader recientemente shipped (Stories B-E, mayo 2026) — todavía en developed/reviewing. **Esperar a que esté `done` antes de carve-out** o migrar in-flight con coordinación.
- ⚠️ `LLM_ROLE_BY_SITE` en `domain/model_tier.py` — config por env vars, OK.
- ⚠️ `litellm_config.yaml` SSoT — vive en `core-shared`. ✅

#### `brand` — CORE-ENGINE + BRAND-CONFIG
**Engine al core:**
- Field-contract-platform + form-runtime engine
- Extraction orchestrator (subclass `BaseExtractionOrchestrator`)
- Web scraping pipeline
- Doc extraction pipeline
- PersonalityProfile (3-pillar engine: dimensions/patterns/exchanges)
- BuyerPersona (multi-persona)
- StoryBrand narrative
- Authority vault
- Communication assets
- Schema definitions (10 secciones)

**Brand-config (declarativo en cada app):**
```python
# apps/vitalia/brand.config.py
LUANA_BRAND_CONFIG = {
    "enabled_sections": ["identity", "contact", "team", "testimonials"],
    "field_overrides": {
        "voice_archetype": {"required": False},
        "buyer_persona": {"max_count": 1},  # paciente único arquetipo
    },
    "preset_pack": "medical_clinic_v1",
}

# apps/comunify/brand.config.py
LUANA_BRAND_CONFIG = {
    "enabled_sections": ["identity", "story", "narrative", "voice", "buyer_persona", "authority_vault", "team", "testimonials", "communication_assets", "contact"],  # all 10
    "field_overrides": {
        "buyer_persona": {"min_count": 3},  # múltiples avatares mandatory
        "authority_vault": {"required": True},
    },
    "preset_pack": "creator_economy_v1",
}
```

**Cleanup pre-extract:** ninguno crítico. Refactor field-contract-platform ya post 2026-04, esquema estable.

#### `offer` — CORE-ENGINE + BRAND-CONFIG
**Engine al core:**
- 7 catalogs DAG (ExpertBusinessType, OfferValueLevel, SectionCatalog, VariantStructure, OfferArchetype, OfferFormat, OfferLadderHints, OfferTypePreset)
- Form-runtime engine
- 76 presets catalog
- Conditional questions engine
- Cards/Split mode automático
- Multi-currency (TenantLocale-driven)
- Wizard flow + value-level step

**Brand-config:**
- Vitalia activa preset pack `medical_services` (consulta, paquete tratamiento, plan continuo)
- Comunify activa `coaching_offers` (cohort course, mastermind, 1:1, productized service, lead magnet, mid-ticket community)
- Lupulo activa `gastronomy_offers` (menú prix-fixe, evento, catering, delivery)
- Nicolify activa todos (caso genérico)

**Cleanup pre-extract:**
- ⚠️ Confirmar `_CATALOG_VERSION` bump cuando cortes — arch test enforce both stacks
- ⚠️ Algunos presets tienen referencias hardcodeadas a Visionarias-style coaching — migrar a `coaching_offers` preset pack vertical-creator-economy

#### `landing` — CORE-ENGINE + BRAND-CONFIG
**Engine:** page generator, slug routing, preview, publish, sections engine
**Brand-config:** Vitalia template `medical_appointment_booking`, Lupulo template `restaurant_menu_booking`, etc.
**Cleanup:** templates hoy hardcoded — extraer a templates/{vertical}_{template}.json registry

#### `scheduling` — CORE-ENGINE + BRAND-EXTENSION
**Engine:** Google Calendar sync + booking engine + multi-timezone + watch channel + recordatorios + booking page
**Brand-extension:**
- Vitalia: `bookingPolicy.canConfirm` returns `false` if `payment_status != paid`
- Lupulo: `bookingPolicy.canConfirm` checks `table_capacity`, `kitchen_load`
- Vitalia: `bookingPolicy.beforeBook` sends prepaid checkout link
- Comunify: default (no extension, libre)
- Nicolify: default

**Cleanup pre-extract:** definir extension points formales (`bookingPolicy.{canConfirm, beforeBook, afterCancel, reminderTemplate}`)

#### `crm` — CORE-FULL
- Contacts, journey events, sales pipeline, lifecycle scoring
- Custom fields ya soportados — no hace falta extension code, brands extienden via custom_fields data
- Pipeline stages configurables per-tenant

#### `analytics` — CORE-ENGINE + BRAND-CONFIG
**Engine:** ETL framework, scheduler, workers, metric_catalog, extraction_contract, channel_registry, stage_services, progressive loading tiers, 12+ providers (Meta, GA4, Shopify, etc.)
**Brand-config:**
- Vitalia: `enabled_metrics: [appointments_booked, treatment_completion_rate, no_show_rate]` + custom medical KPIs
- Comunify: `enabled_metrics: [community_members, cohort_completion, ladder_velocity]`
- Lupulo: `enabled_metrics: [reservation_rate, table_turnover, avg_ticket, kitchen_efficiency]`
- Nicolify: full (todos los metrics)

**Cleanup pre-extract:** crítico — `make extraction-contract` workflow debe regenerar SSoT en luana-core post-cambios. Confirmar `extraction_contract.py` + `metric_catalog.py` son source of truth única.

#### `connections` — CORE-ENGINE + BRAND-EXTENSION
**Engine:** OAuth flows, webhook handler, channel adapter pattern, credentials vault
**Brand-extension:**
- Lupulo: `vertical-gastronomy/connections/` adds POS systems (Square, Toast), kitchen display systems
- Vitalia: `vertical-medical/connections/` adds payment gateways (Stripe Healthcare-flagged, MercadoPago)
- ManyChat, Meta, Shopify, Google = en core (genéricos)

**Cleanup:** revisar si hay channel adapters hoy en `connections/` que solo aplican a vertical específico — mover a vertical-{niche}/connections/

#### `assets` — CORE-FULL
- AI generation (LLM + image), R2 storage, MIME, templates
- Templates pueden ser brand-config en backlog (cada vertical sus templates default), pero motor es shared

#### `commercial_calendar` — CORE-FULL
- Holidays + promotions, country-code config

#### `tenant_domains` — CORE-FULL
- Cloudflare Custom Hostnames API. Idéntico.

#### `tenant_profile` — CORE-FULL
- Tenant settings, locale, currency, plan

#### `campaigns` — CORE-ENGINE + BRAND-CONFIG
**Engine:** campaign engine + scheduling + templates
**Brand-config:** templates per-vertical (Vitalia: medical compliance disclaimers; Lupulo: menú dinámico)
**Cleanup:** revisar separación entre `campaigns` (engine) y `campaigns-lite` FE — definir contract estable

#### `social_proof` — CORE-FULL
- Testimonios + casos, esquema genérico

#### `advertising` — DROP
- Placeholder, sin implementación. Decisión: no migra a Luana ahora. Backlog futuro si emerge necesidad.

#### `social_media` — DROP
- 5 LOC vacío. No migra.

### 2.3 `shared/` deep-dive — la pre-Luana ya extraída

**Esta carpeta es ~50% de Luana ya hoy.** Migración mecánica.

| Sub-package | Contenido | Goes to |
|---|---|---|
| `agent_observability/recording` | TurnEnvelope base, callback handler base, sanitization | `core-observability` |
| `agent_observability/persistence` | trace_event repo base, llm_call repo base, billing_config repo | `core-observability` |
| `agent_observability/cost` | calculator, pricing resolver, FX resolver, cost recorder | `core-observability` |
| `agent_observability/pricing` | model pricing snapshot table mgmt | `core-observability` |
| `agent_observability/channels` | format_for_channel, intent_detector | `core-channels` |
| `agent_observability/application` | services + use cases | `core-observability` |
| `agent_observability/workers` | retention, MV refresh | `core-observability` |
| `agent_observability/reporting` | aggregations, reports | `core-observability` |
| `domain_events/outbox` | DomainEventOutboxModel + adapter_bus | `core-events` |
| `billing` | BudgetGuard + RateLimiter | `core-billing` |
| `compliance` | ComplianceService | `core-compliance` |
| `idempotency` | idempotency keys infra | `core-idempotency` |
| `infrastructure/llm` | router, providers (litellm), config | `core-llm` |
| `infrastructure/channels` | channel ABCs | `core-channels` |
| `infrastructure/files` | file handling | `core-platform` |
| `infrastructure/prompts` | prompt templates infra | `core-platform` |
| `infrastructure/database` | DB infra | `core-platform` |
| `infrastructure/external` | external clients | `core-platform` |
| `infrastructure/web` | web utils | `core-platform` |
| `infrastructure/models` | shared SQLA models | `core-platform` |
| `links/ports` | cross-module ports (DTOs) | `core-platform` |
| `domain` | locale (TenantLocale VO), schemas | `core-platform` |
| `application/extraction` | BaseExtractionOrchestrator | `core-extraction` |
| `workers` | shared workers infra | `core-platform` |
| `api` | shared API utils | `core-platform` |

**Conclusión:** `shared/` se rompe en ~10 packages versionados de Luana. Mapeo 1:1 con limpieza mínima.

## 3. Frontend — Feature por feature

### 3.1 Tabla resumen FE

| # | Feature | LOC | Files | Verdict | Razón |
|---|---|---|---|---|---|
| 1 | `growth-studio` | 49846 | 313 | **CORE-ENGINE + BRAND-CONFIG** | Dashboard analytics framework + components. Brand activa metric panels |
| 2 | `offer-studio` | 28214 | 259 | **CORE-ENGINE + BRAND-CONFIG** | Offer wizard + form-runtime FE. Brand activa preset pack |
| 3 | `copilot` | 18708 | 145 | **CORE-FULL** | UI chat + composer + cards + smart-chips. Genérico. |
| 4 | `brand-studio` | 11968 | 115 | **CORE-ENGINE + BRAND-CONFIG** | Form-runtime FE + sections renderer. Brand habilita secciones |
| 5 | `connections` | 6551 | 26 | **CORE-FULL** | OAuth flows UI, channel cards genéricos |
| 6 | `sales` | 3095 | 28 | **CORE-FULL** | Sales agent FE config UI |
| 7 | `closer-studio` | 2934 | 30 | **CORE-FULL** | Conversación humana UI, idéntico cross-brand |
| 8 | `crm-hub` | 2687 | 26 | **CORE-FULL** | Contacts + pipeline UI |
| 9 | `settings` | 2209 | 22 | **CORE-FULL** | Tenant settings UI |
| 10 | `audit` | 1497 | 11 | **CORE-FULL** | Audit log viewer |
| 11 | `tenant-domains` | 1182 | 13 | **CORE-FULL** | Custom domain config UI |
| 12 | `campaigns-lite` | 1056 | 14 | **CORE-FULL** | Campaign builder lite |
| 13 | `tenant-profile` | 1038 | 15 | **CORE-FULL** | Tenant profile UI |
| 14 | `notifications` | 319 | 7 | **CORE-FULL** | Notification toaster genérico |
| 15 | `admin` | 134 | 1 | **CORE-FULL** | Admin entry stub |
| 16 | `tenant` | 100 | 2 | **CORE-FULL** | Tenant switcher |

Total FE CORE: ~131k LOC. **100% del FE va a Luana** (engine + config-points). Cero feature 100% brand-specific en FE actual.

### 3.2 Componentes/UI shared

- `frontend/src/components/ui/` — Shadcn primitives → `@luana/ui-kit`
- `frontend/src/components/shared/` — sidebar, tenant-switcher, layouts → `@luana/ui-shared`
- `frontend/src/lib/tokens/` — design tokens (colors, typography, spacing) → `@luana/design-tokens`
- `frontend/src/lib/format/` — formatMoney, formatTenantDate → `@luana/format`
- `frontend/src/hooks/` — useTenantLocale, useFetch → `@luana/hooks`
- `frontend/src/lib/api/` — fetchClient (X-Tenant-ID injection) → `@luana/api-client`
- `frontend/src/lib/zod-schemas/` → `@luana/schemas`

### 3.3 Brand divergence en FE

**Theme overlay** (no código) gestionado via:
- Tailwind v4 `@theme` directive con tokens brand-specific
- CSS variables override per-brand (`--color-primary`, `--color-accent`)
- Logo + favicon assets per-brand
- Copy/i18n bundle per-brand (Spanish neutro core + brand-specific overrides)

**Routes brand-specific** (no van a core):
- `apps/vitalia/app/(dashboard)/treatments/` — Vitalia exclusive
- `apps/comunify/app/(dashboard)/cohorts/` — Comunify exclusive
- `apps/lupulo/app/(dashboard)/kitchen/` — Lupulo exclusive
- `apps/lupulo/app/(dashboard)/menu/` — Lupulo exclusive

**Sidebar entries** registrables via `BrandConfig.sidebarRoutes` (extension point #6, ver §5).

## 4. Transversales (cross-cutting concerns)

Estos atraviesan TODOS los módulos y son non-negotiable shared. Viven en `core-platform` o cores dedicados.

| # | Concern | Goes to | Detalle |
|---|---|---|---|
| 1 | **Tenant isolation** | `core-iam` + `core-platform` | `X-Tenant-ID` middleware, todas las queries filter `tenant_id`, soft-deletes |
| 2 | **Multitenancy DB** | `core-platform` | DB engine async, session factory, base repository |
| 3 | **Auth (Clerk)** | `core-iam` | JWT verification, user/tenant resolution, RBAC |
| 4 | **PII sanitization** | `core-observability` | `sanitize_payload`, allowed-list response models |
| 5 | **Locale + Currency** | `core-platform` | `TenantLocale` VO, UTC storage, `formatMoney(amount, currency)` |
| 6 | **Spanish neutro** | `core-platform` | Glossary + glossary-aware lint hook (heritable a brand repos via shared `.claude-shared/`) |
| 7 | **Observability agentic** | `core-observability` | trace_event, llm_call, cost recorder, FX, MV refresh |
| 8 | **LLM routing** | `core-llm` | LiteLLM Proxy + ModelRole semantic + provider config |
| 9 | **Domain events + outbox** | `core-events` | DomainEvent base, outbox pattern, adapter_bus |
| 10 | **Billing guards** | `core-billing` | BudgetGuard, RateLimiter — gating cross-cutting |
| 11 | **Compliance gates** | `core-compliance` | ComplianceService — campaigns/sales_agent gating |
| 12 | **Idempotency** | `core-idempotency` | Idempotency keys infra |
| 13 | **Cross-module ports** | `core-platform/links` | DTOs PII-stripped, port pattern |
| 14 | **Outbox pattern** | `core-events` | DomainEventOutboxModel, USE_OUTBOX_PATTERN_* flags (todos True post 2026-04-29) |
| 15 | **Extraction orchestrator** | `core-extraction` | BaseExtractionOrchestrator, wave-based LLM extraction |
| 16 | **Field-contract-platform** | `core-brand-studio` + `core-offer-studio` | Form-runtime engine compartido brand+offer |
| 17 | **Channel format dispatch** | `core-channels` | format_for_channel registry, intent_detector |
| 18 | **Prompt cache architecture** | `core-llm` + `core-copilot` + `core-sales-agent` | Anthropic 5min/1h TTL slot-based, per-tenant key |
| 19 | **Eval framework** | `core-evals` | Simulator dual-LLM, MAJ-EVAL grader, personas catalog, goldens schema (NEW para Luana — extracción in-flight) |
| 20 | **Migration framework** | `core-platform` | Alembic idempotent migrations base + IF NOT EXISTS conventions |
| 21 | **Architectural fitness** | `core-platform/tests` | Arch fitness tests base + ratchet pattern infra (heritable a brand apps) |
| 22 | **CI/CD baseline** | `.github/workflows/` shared subtree | Lint/test/build/publish Actions reusable |

## 5. Extension Points (5 críticos primero, resto backlog)

Los **5 extension points formales que arrancamos Sem 1** (los que rompen primero si no están):

### EP-1: `BrandStudio.fieldOverride(field, context) → FieldOverride`
**Owner:** `core-brand-studio`
**Use case:** Vitalia oculta `voice_archetype.required`, simplifica a 4 secciones. Comunify hace `buyer_persona` mandatory min 3. Brand registra overrides declarativos.
**Signature TS:** `(field: FieldDef, ctx: { tenantId, brand }) => Partial<FieldDef> | null`
**Signature Python:** `def field_override(field: FieldDef, ctx: BrandContext) -> Optional[FieldOverride]`

### EP-2: `Offer.presetPackRegister(pack: PresetPack) → void`
**Owner:** `core-offer-studio`
**Use case:** Cada brand registra su preset pack vertical (`medical_services`, `coaching_offers`, `gastronomy_offers`). Core ofrece base, brand activa subset.
**Signature:** brand declarativo en `BrandConfig.offerPresetPack` o programmatic via SDK.

### EP-3: `SalesAgent.toolRegister(tool: ToolDef) → void`
**Owner:** `core-sales-agent`
**Use case:** Cada brand registra tools verticales (Vitalia: `prepaid_payment_check`; Lupulo: `book_table`, `place_order`; Comunify: `qualify_for_cohort`). Core ofrece tools genéricos (scheduler, payment, knowledge), brand extiende.
**Signature:** `tool_def: ToolDef` con Pydantic schema args + handler async.
**Voice:** brand voice compiler v2 NO se toca por brand — esa es contract estable. Solo tools.

### EP-4: `Copilot.workflowRegister(workflow: WorkflowDef) → void`
**Owner:** `core-copilot`
**Use case:** Cada brand registra workflows verticales (Vitalia: `treatment_followup_workflow`; Lupulo: `reservation_to_order_workflow`). Core ofrece workflows genéricos (extraction, suggestion, mutation_journal), brand extiende.
**Signature:** `workflow_def: WorkflowDef` con LangGraph StateGraph + nodes + edges.

### EP-5: `Scheduling.bookingPolicy.canConfirm(booking) → bool | string`
**Owner:** `core-scheduling`
**Use case:** Vitalia retorna `false`/`"prepaid_required"` si `payment_status != paid`. Lupulo chequea `table_capacity`, `kitchen_load`. Default core retorna `true`. Brand registra handler.
**Signature TS:** `(booking: Booking, ctx: BrandContext) => boolean | string`
**Signature Python:** `def can_confirm(booking: Booking, ctx: BrandContext) -> Union[bool, str]` (string = denial reason for UX).

### Backlog extension points (Sem 4+)

| EP | Module | Use case |
|---|---|---|
| EP-6 | `BrandConfig.sidebarRoutes` | Routes brand-specific (Vitalia treatments, Lupulo kitchen) en sidebar |
| EP-7 | `Copilot.extractorRegister` | Field extractors verticales (Vitalia medical_history, Lupulo menu_extractor) |
| EP-8 | `Connections.adapterRegister` | Channel adapters verticales (Lupulo POS, Vitalia payment gateway) |
| EP-9 | `Analytics.metricRegister` | Custom metrics verticales (Vitalia treatment_completion, Lupulo table_turnover) |
| EP-10 | `Landing.templateRegister` | Templates page verticales |
| EP-11 | `Campaigns.templateRegister` | Templates campaign verticales |
| EP-12 | `Assets.templateRegister` | Templates assets verticales |
| EP-13 | `SalesAgent.guardrailRegister` | Guardrails verticales (Vitalia HIPAA-lite legal disclaimers) |
| EP-14 | `Copilot.kbPackRegister` | Knowledge base packs verticales (Vitalia medical, Lupulo menu) |
| EP-15 | `CRM.lifecycleStageRegister` | Custom pipeline stages verticales |

## 6. Riesgos + cleanup pre carve-out

### 6.1 Cleanup obligatorio antes Sem 1

| # | Item | Owner | ETA | Bloqueante? |
|---|---|---|---|---|
| 1 | Esperar Story E (`sales-agent-voice-fidelity-grader-runtime`) → state `done` | `/auditor` | 1-2 sem | **Sí** — eval runtime in-flight |
| 2 | Confirmar `_CATALOG_VERSION` mecánica funciona post split | `offer-expert` | 1 día | Sí (offer carve-out) |
| 3 | Mapear tools sales_agent generic vs brand-specific (audit list) | Claude | 2 días | Sí (sales_agent carve-out) |
| 4 | Mapear extractors copilot generic vs brand-specific | Claude | 2 días | Sí (copilot carve-out) |
| 5 | ETL extraction-contract regenera correctamente desde core-analytics | Claude | 1 día | Sí (analytics carve-out) |
| 6 | Definir ModuleDescriptor lazy-load (registry per-brand) | Claude + arquitectura | 3 días | Sí (copilot carve-out) |
| 7 | Migrate 16 references hardcoded a "Visionarias-style coaching" → preset pack `creator_economy_v1` | Claude | 1 día | No (puede ir Sem 2) |
| 8 | Auditar imports cross-module reales para detectar coupling oculto | Claude | 2 días | Sí (todos los carve-outs) |
| 9 | Confirmar `.claude/rules/` + skills pueden vivir en `.claude-shared/` subtree cross-repo | Claude + Chris | 2 días | Sí (DX cross-repo) |
| 10 | Inventario de `if "tenant_..." in ...` o branch-y-condicionales que se vuelven brand-config | Claude | 2 días | No (puede ir Sem 2) |

### 6.2 Riesgos arquitectónicos

| # | Riesgo | Severidad | Mitigación |
|---|---|---|---|
| 1 | Coupling oculto entre módulos no documentado | Alta | Audit dependency graph cross-module antes Sem 1 (item 8 arriba) |
| 2 | Eval framework sales_agent in-flight (Stories B-E) — extracción mid-build | Alta | Postergar extracción de eval hasta Story E `done`. Mientras tanto, eval queda en `nicolify` y se promueve a Luana en v0.2.0 |
| 3 | Migration data Nicolify → split (DB schema acoplado entre módulos) | Media | Dual-write 2 sem ventana cutover, scripts idempotentes |
| 4 | Brand voice contract estable — si se rompe, 4 brands rompen | Alta | Semver enforcement + tests downstream R3 obligatorios en Luana CI |
| 5 | Prompt cache arquitectura + slot 5 BRAND_VOICE — hash invariante per tenant | Alta | Mantener contract `personality_profiles.system_instruction` cementado, NO interpolar `{tenant_name}` mid-block |
| 6 | LiteLLM Proxy SSoT shared cross-brand (única instancia o per-brand?) | Media | **Decisión: per-brand instance**. Cada brand cluster K8s incluye su `visionarias_litellm` svc. Centralizada inviable cross-cluster. Pricing snapshot SSoT en core (immutable ledger). |
| 7 | Anthropic prompt cache TTL 5min/1h — cache miss cross-brand inevitable | Baja | Por design — cache es per-tenant per-brand, esperado. |
| 8 | Stories en `developing`/`reviewing` durante carve-out | Alta | **Freeze Stories durante Sem 1-3**. PI-12 sub-stories no toman nuevos tickets hasta Luana v0.1.0 |
| 9 | Test fixtures + conftest.py acoplados cross-module | Media | Audit conftest.py + fixtures para identificar shared vs module-specific antes split |
| 10 | Migrations Alembic versionadas — split desafía orden histórico | Media | Cada repo arranca su propia history Alembic. Schema baseline = snapshot post-cutover. **NO migrar history Alembic cross-repo** |

### 6.3 Costos no contemplados antes

| Costo | $/mes inicial | Notas |
|---|---|---|
| LiteLLM proxy per-brand (4 instancias) | ~0 (incluido en cluster) | Si self-hosted en cluster |
| Sentry per-brand (4 projects) | $26/mo × 4 = $104 | Free tier 5k errores/mo limita rápido |
| GitHub Actions minutes (5 repos privados) | $0 free 2000min, después $0.008/min | Probable upgrade Pro $4/user/mo |
| Qdrant Cloud per-brand (4 instancias) | $0 free tier × 4 ó self-hosted | Self-hosted en cluster es opción |
| Backup managed Postgres × 4 | ~$10-20/mo cada | Daily snapshots |
| **Total adicional ~** | **$150-200/mo** | Sumar a estimación previa $950-1200 |

Total real revisado: **~$1100-1400/mo** infra + AI dev.

## 7. Roadmap detallado Sem 1-3 (Luana v0.1.0)

### Sem 1 (2026-05-12 → 2026-05-18) — Foundation

**Day 1-2 (Lun-Mar):**
- Chris: crear GitHub Org `luana-platform` + 5 repos vacíos
- Chris: comprar 4 Claude Code Max subs adicionales (5 totales)
- Claude: dependency graph cross-module (item 8 cleanup) + reporte coupling oculto

**Day 3-4 (Mié-Jue):**
- Claude: setup `luana-core` repo skeleton — pyproject + package.json + turbo.json + workspaces config
- Claude: lift `shared/agent_observability/` → `core-observability` (10 sub-packages mapped §2.3)
- Claude: lift `shared/billing` → `core-billing`, `shared/compliance` → `core-compliance`, `shared/idempotency` → `core-idempotency`

**Day 5 (Vie):**
- Claude: lift `shared/domain_events/outbox` → `core-events`
- Claude: lift `shared/infrastructure/llm` → `core-llm`
- Claude: lift `shared/links/ports` + `shared/domain` + `shared/application/extraction` → `core-platform`
- Publish Luana v0.0.1-alpha to GH Packages (smoke test)

### Sem 2 (2026-05-19 → 2026-05-25) — Engine cores

**Day 1-2:**
- Claude: lift `iam` → `core-iam`
- Claude: lift `tenant_profile` + `tenant_domains` + `commercial_calendar` + `social_proof` + `assets` → `core-tenancy` + `core-content`

**Day 3-4:**
- Claude: lift `crm` → `core-crm`
- Claude: lift `analytics` → `core-analytics-engine` (con cleanup ETL contract)

**Day 5:**
- Claude: lift `landing` → `core-landing`
- Claude: lift `connections` engine → `core-connections` (channel adapters base, brand-specific quedan en vertical packages)

### Sem 3 (2026-05-26 → 2026-06-01) — Studios + Agents

**Day 1-2:**
- Claude: lift `brand` → `core-brand-studio` (form-runtime engine + extraction)
- Claude: lift `offer` → `core-offer-studio` (catalogs + presets registry)

**Day 3-4:**
- Claude: lift `copilot` (engine only) → `core-copilot`
- Claude: lift `sales_agent` (engine only, EXCLUYENDO eval framework in-flight) → `core-sales-agent`

**Day 5:**
- Claude: lift `campaigns` engine → `core-campaigns`
- Claude: define EP-1 a EP-5 formal en `core-extension-sdk`
- Publish **Luana v0.1.0** to GH Packages (production-grade alpha)
- Tests + CI completos
- Docs: API reference auto-gen + extension points docs

### Sem 4 (2026-06-02 → 2026-06-08) — Nicolify migration

- Rename AISALESHT → nicolify
- Swap imports internos por `@luana/core-*` y `luana-core-*`
- Verificar zero regresión funcional (all tests pass)
- Deploy Nicolify v2.0.0 (consumer #1 de Luana)

### Sem 5-8 — Brand bootstrap paralelo (4 Claude Codes paralelos)

Detalle en `02-brand-bootstrap-plan.md` (próximo doc).

## 8. Próximos documentos a generar

Este audit es input para:

1. **`02-extension-points.md`** — Especificación formal EP-1..EP-15 con signatures Python + TS, ejemplos de uso por brand, tests required
2. **`03-migration-plan.md`** — Detalle día-a-día Sem 1-3 con scripts concretos, comandos, rollback plan
3. **`04-brand-config-spec.md`** — Schema completo de `BrandConfig` (Python + TS), ejemplos por brand
4. **`05-cross-repo-tooling.md`** — `.claude-shared/` subtree strategy, GitHub Project v2, cross-repo PR review, semver enforcement
5. **`ADR-001-luana-platform.md`** — Architecture Decision Record firmable

## 9. Open questions (a ratificar con Chris)

1. **Eval framework (Story B-E)** — ¿esperamos a `done` (estimado 1-2 sem) o lo extraemos en flight con coordinación? Recomiendo esperar.
2. **Streamlit admin** — ¿core compartido (`core-admin-streamlit`) o copia per-brand? Recomiendo core porque la mayoría de tools (LLM virtual keys, costo, traces) son transversales.
3. **`tenant_profile` vs `iam`** — ¿se fusionan en `core-tenancy` o quedan separados? Recomiendo separados (iam = auth, tenant_profile = settings).
4. **Brand voice compiler v2** — ¿sigue cementado en `core-sales-agent` o se eleva a `core-brand-studio` (porque la voz es brand)? Recomiendo `core-brand-studio` con consumer en `core-sales-agent` via port — más limpio DDD.
5. **Frontend monorepo interno** — ¿`luana-core/packages/web/` separado por estudios (offer-studio, brand-studio, copilot-ui) o unificado en `@luana/ui`? Recomiendo separado — releases independientes por estudio.
6. **`.claude-shared/` subtree o submodule** — Recomiendo subtree (más simple cross-repo, no hay submodule pain).
7. **Migrations Alembic baseline** — ¿cada brand parte de schema snapshot o desde history clean? Recomiendo snapshot frozen v1 + history clean per-repo.
8. **`development` branch** — el patrón `development` en parallel-safety era mitigation single-repo multi-session. **Con 5 repos separados, eliminamos `development` branch**. Cada repo trunk-based en `main` con PR mandatory.

---

**Próximo paso:** ratificar este audit con Chris (vos) → escribir `02-extension-points.md` con signatures formales → empezar Sem 1 lunes 2026-05-12.
