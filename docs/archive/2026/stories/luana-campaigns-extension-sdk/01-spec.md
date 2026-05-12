---
story_id: luana-campaigns-extension-sdk
type: service-story
module: luana-core-campaigns + luana-core-extension-sdk + @luana/extension-sdk + apps/test-brand
capability: extension-sdk + multi-brand-platform
po_version: 1
last_modified: 2026-05-12
ratified_by_chris: true                          # ★ Session 4 ratification — outcome §7.5 binding decisions cementadas
drafted_by: /po Opus
binding_decisions_ref: docs/product/outcomes/luana-platform-migration.md §7.5
links:
  story_yaml: "../../../../product/stories/luana-campaigns-extension-sdk/checkpoint.md"
  story_md: "00-story.md"
  outcome_md: "../../outcomes/luana-platform-migration.md"
  precedent_story_6: "../../../archive/2026/stories/luana-copilot-engine/07-merge.md"
  precedent_story_7: "../../../archive/2026/stories/luana-sales-agent-engine/07-merge.md"
---

# 01-spec — Story 8: Campaigns Engine Lift + Extension SDK Formalization

## 0. Outcome alignment

Outcome `luana-platform-migration` §1 — establish 4 vertical SaaS brands (Nicolify + Vitalia + Comunify + Lupulo) on shared `luana-core` SSoT with formal extension points so core improvements ripple to all brands and verticals materialize divergence via declarative configuration or registered handlers (zero `if brand == ...` in core).

Outcome §2.1 dependencies — Story 8 (`luana-campaigns-extension-sdk`) blocked_by Story 7 (DONE 2026-05-12) and blocks Story 9 (`luana-v0-1-0-publish`). Story 8 cements EP-1..EP-5 critical executable + EP-6..EP-18 backlog signatures so v0.1.0 publishes with stable public contract.

Outcome §7.5 — 7 business decisions + 13 backlog EP signatures + 5 cross-cutting policies cemented BEFORE refining→refined. This spec consumes §7.5 verbatim. No scope expansion. No scope narrowing.

## 1. Resumen ejecutivo

Lift AISALESHT `backend/src/modules/campaigns/` (80 src files + 42 test files across `domain/infrastructure/application/api/workers/observability`) into `luana-platform/python/luana-core-campaigns/` preserving file names, class names, function signatures, public API surface, and tests verbatim per outcome §7.3 lift mode.

In parallel, define the **Extension SDK** as two new packages (`luana-core-extension-sdk` Python + `@luana/extension-sdk` TypeScript) that formalize 18 extension points: **EP-1..EP-5 critical executable** (field override, offer preset pack, sales agent tool, copilot workflow, scheduling booking policy) wrapping the FROZEN registries from Stories 6+7 byte-stable, plus **EP-6..EP-18 backlog signatures-only** (sidebar routes, extractor, channel adapter, metric, landing template, campaign template, asset template, sales agent guardrail, copilot KB pack, CRM lifecycle stage, IAM signup handler, tenant plan tier, onboarding wizard) with `raise NotImplementedError` semantics until v0.2.x.

Story 8 ships an `apps/test-brand/` smoke pack that registers one handler per critical EP (executable happy path) + one stub per backlog EP (`NotImplementedError` graceful on invocation) via FastAPI lifespan event, plus a `docs/extension-points.md` deliverable containing per-vertical concrete examples (Vitalia + Comunify + Lupulo) and a "Recipe: Build a vertical agent on top of luana-core" section premised on Vitalia treatment-agent (per §7.5.4 — **NO EP-19, pattern doc only**).

Public surface frozen for v0.1.0: 18 extension point signatures + `BrandContext` frozen dataclass (9 fields per §7.5.2 D3) + 5 cross-cutting policies enforced runtime + 2 exception types (`DuplicateRegistrationError`, `NamespaceViolationError`). Bumping after Story 9 publish requires SemVer breaking version.

Why this story matters: enables Stories 9-13. Without SDK formalization, Stories 11-13 brand bootstraps would each invent ad-hoc extension patterns ("lasagna of conditionals" anti-pattern outcome §1 rejects). With SDK, brand-namespaced registration becomes the only path to materialize vertical adaptations, and cross-brand learning happens via /pm core promotion path (§7.5.6), never via cross-namespace consumption.

## 2. User value

| Stakeholder | Value delivered |
|---|---|
| Chris (founder + only dev today) | Story 9 v0.1.0 publish unblocked. Stories 11-13 vertical bootstraps have formal contract — each brand registers handlers, NEVER copy-pastes code or branches on `brand_slug` in core. |
| Future collaborators (Vitalia / Comunify / Lupulo devs) | Path to add vertical features is unambiguous: implement DataClass or Callable per EP signature, register at FastAPI startup, brand-namespace it (`vitalia.medical_consent_request`). Core untouched. CODEOWNERS protects (outcome §3.3 pattern 6). |
| Luana core (architectural integrity) | EP-3 + EP-4 + EP-5 wrap Stories 6+7 frozen registries byte-stable. EP-1..EP-2 + EP-13 + EP-15 + EP-16 surface declarative entry points without core code changes. Cross-brand learning principle (§7.5.6) becomes the only mechanism for promoting features to core. |
| Vitalia treatment-agent (recipe consumer) | Worked example in `docs/extension-points.md` §4 shows how to compose a vertical agent from luana-core packages (observability subclass + scheduling + channels via EP-8 + marketing-kb via EP-14 + prompt-cache + extension-sdk via EP-3/EP-13). Stories 11-13 implementers use as template. |

Negative-space user value (what this spec explicitly does NOT deliver — see §4):
- ❌ No EP-6..EP-18 semantic implementations (signatures-only, raise NotImplementedError on invocation).
- ❌ No brand consumers (Vitalia/Comunify/Lupulo apps = Stories 11-13).
- ❌ No GH Packages publish pipeline (= Story 9).
- ❌ No EP-19 `vertical_agent_register` (per §7.5.4 pattern doc only — vertical agents are brand apps, NOT extension points).

## 3. Scope (IN)

### 3.1 Part A — Lift `modules/campaigns/` (mechanical lift mode per outcome §7.3)

Source: AISALESHT `backend/src/modules/campaigns/`
- 80 Python files across 4 DDD layers + `workers/` + `observability/` + `infrastructure/{channels,repositories,resilience,models,external,links}/`
- 42 test files in `backend/tests/modules/campaigns/`

Target: `luana-platform/python/luana-core-campaigns/`
- `src/luana_core_campaigns/{domain,infrastructure,application,api,workers,observability}/` preserving file names + class names + function signatures + public API surface
- `tests/` mirror of `backend/tests/modules/campaigns/` verbatim
- `pyproject.toml` (uv workspace member, version `0.0.8-alpha`, dependencies declared explicit per outcome §7.3)
- `README.md` stub
- Import path migration: `from src.modules.campaigns.X` → `from luana_core_campaigns.X` (all imports updated within package and within new tests)

Workspace integration:
- `luana-platform/pyproject.toml` workspace members list **append** `python/luana-core-campaigns/` (alphabetical order preserved)
- No publishConfig / .releaserc / release.yml (deferred Story 9 per V-NF-5/6/7 precedent Story 6+7)

Invariants (V-NF):
- AISALESHT `backend/src/modules/campaigns/` source byte-stable (V-NF-4 inviolable — outcome §7.3 MUST NOT)
- Per-package test suite passes with same coverage threshold as AISALESHT campaigns module (BE 43% baseline)
- Downstream regression Stories 2-7 packages: zero new regressions (R3 auditor-downstream-regression scope per `.claude/rules/auditor-downstream-regression.md`)

### 3.2 Part B1 — `luana-core-extension-sdk` Python package (NEW code)

Path: `luana-platform/python/luana-core-extension-sdk/`

```
luana-core-extension-sdk/
├── pyproject.toml                          # uv workspace member, version 0.0.8-alpha
├── README.md                               # SDK overview + link to docs/extension-points.md
├── src/luana_core_extension_sdk/
│   ├── __init__.py                         # public exports
│   ├── extension_points.py                 # ExtensionPointRegistry class with 18 register methods
│   ├── brand_context.py                    # BrandContext frozen dataclass (§7.5.2 D3)
│   ├── models.py                           # DataClass models per EP DataClass-pattern
│   ├── protocols.py                        # Protocol interfaces for Callable-pattern handlers
│   └── exceptions.py                       # DuplicateRegistrationError, NamespaceViolationError, RegistrationClosedError
└── tests/
    ├── unit/                               # registry semantics + namespace enforcement + frozen ctx
    └── architecture/                       # public API surface + frozen contract tests
```

#### 3.2.1 `BrandContext` frozen dataclass (§7.5.2 D3 — verbatim)

```python
# brand_context.py
from dataclasses import dataclass, field
from typing import Literal, Optional
from uuid import UUID

@dataclass(frozen=True)
class BrandContext:
    """Per-tenant context passed to all extension handlers. Future fields opcionales agregables sin breaking bump."""
    tenant_id: UUID
    brand_slug: Literal["nicolify", "vitalia", "comunify", "lupulo", "test-brand"]
    plan_tier: str                                    # tier_id from EP-17 brand-registered
    locale: str                                       # ISO 639-1 + region (es-AR / es-MX / es-CL / en-US)
    feature_flags: dict[str, bool]                    # tenant-level flag map (from feature_flag service)
    tenant_profile_id: UUID
    vertical_kind: Literal["marketing", "medical", "creator-economy", "gastronomy"]
    compliance_flags: dict[str, bool]                 # e.g. {"hipaa_required": True} per Vitalia
    pii_policy: Literal["standard", "medical", "creator", "gastronomy"]
```

Future optional fields (added in future minor versions without breaking handlers that ignore them): may include `currency_code`, `timezone`, `clerk_org_id`, etc. Backward compat covenant: handler that uses only a subset of fields MUST continue working when new optional fields are appended.

#### 3.2.2 `ExtensionPointRegistry` class (18 methods — per §7.5.3 + §7.5.2 D1=B)

EP-1..EP-5 critical — **fully implemented** (registry stores handler + dispatch helpers callable from core).
EP-6..EP-18 backlog — **signature-only** (registry stores registration data + raises `NotImplementedError` if dispatch invoked semantically; the `register_*` call itself succeeds and returns).

| EP | Method signature | Pattern | Mode | Implementation status |
|---|---|---|---|---|
| EP-1 | `field_override(handler: Callable[[FieldDef, BrandContext], Optional[FieldOverride]]) -> None` | Callable | append | EXECUTABLE — core form-runtime resolves override via registry |
| EP-2 | `offer_preset_pack_register(pack: PresetPack) -> None` | DataClass | append | EXECUTABLE — offer wizard reads packs filtered by BrandContext.brand_slug |
| EP-3 | `sales_agent_tool_register(tool: ToolDef) -> None` | DataClass+Callable | append | EXECUTABLE — wraps Story 7 ToolRegistry byte-stable; registry delegates read-only |
| EP-4 | `copilot_workflow_register(workflow: WorkflowDef) -> None` | DataClass+Callable | append | EXECUTABLE — wraps Story 6 WorkflowRegistry byte-stable; registry delegates read-only |
| EP-5 | `scheduling_booking_policy_register(policy: BookingPolicy) -> None` | DataClass+Callable | append | EXECUTABLE — booking flow invokes `policy.can_confirm(booking, ctx) -> Result` |
| EP-6 | `sidebar_routes_register(route: SidebarRouteDef) -> None` | DataClass | append | SIGNATURE-ONLY — registry stores; BE `/api/v1/_sdk/sidebar` returns list; raises NotImplementedError if FE consumer invokes deep semantics |
| EP-7 | `extractor_register(extractor: ExtractorDef) -> None` | DataClass | append | SIGNATURE-ONLY — registry stores; `BaseExtractionOrchestrator` integration deferred v0.2.x |
| EP-8 | `channel_adapter_register(adapter: ChannelAdapterDef) -> None` | DataClass+Callable | append | SIGNATURE-ONLY — covers sales_agent + copilot + vertical brand agents (treatment_agent/kitchen_agent) per §7.5.3 EP-8 extended scope |
| EP-9 | `metric_register(metric: MetricDef) -> None` | DataClass | append | SIGNATURE-ONLY — ETL pipeline integration deferred v0.2.x |
| EP-10 | `landing_template_register(template: LandingTemplateDef) -> None` | DataClass (JSON schema declarativo) | append | SIGNATURE-ONLY — single Landing Engine FE consumes schema; deferred v0.2.x |
| EP-11 | `campaign_template_register(template: CampaignTemplateDef) -> None` | DataClass | append | SIGNATURE-ONLY — drip-pattern templates with steps + trigger_event + conditions |
| EP-12 | `asset_template_register(template: AssetTemplateDef) -> None` | DataClass | append | SIGNATURE-ONLY — static template + placeholder replacement; AI gen NOT scope |
| EP-13 | `sales_agent_guardrail_register(guardrail: GuardrailDef) -> None` | Callable (pre_send + pre_receive) | append | SIGNATURE-ONLY — pre-send + pre-receive both included from v0.1.0 per §7.5.3 EP-13 extended scope |
| EP-14 | `copilot_kb_pack_register(pack: KbPackDef) -> None` | DataClass | append | SIGNATURE-ONLY — `tenant_scope: 'brand' \| 'tenant' \| 'both'` per §7.5.3 EP-14 detail; Qdrant collection lazy-load deferred v0.2.x |
| EP-15 | `crm_lifecycle_stage_register(stage: LifecycleStageDef) -> None` | DataClass | append | SIGNATURE-ONLY — declarative insert-between core stages (no remove) |
| EP-16 | `iam_signup_handler(handler: Callable[[ClerkUser, BrandContext], SignupResult]) -> None` | Callable | append | SIGNATURE-ONLY — async background + pending_review state; requires EP-15 brand registers pending_review stage |
| EP-17 | `tenant_plan_tier_register(tier: PlanTierDef) -> None` | DataClass | **override** | SIGNATURE-ONLY — brand replaces core tiers completamente; `mode='override'` enum permitted |
| EP-18 | `onboarding_wizard_steps_register(step: WizardStepDef) -> None` | DataClass | **override** | SIGNATURE-ONLY — brand replaces wizard completamente; `mode='override'` enum permitted; FE+BE sync (BE expone `/api/v1/_sdk/wizard`, FE Next.js consumes) |

#### 3.2.3 Cross-cutting policy enforcement (§7.5.1 CC-1..CC-5)

| Policy | Runtime enforcement |
|---|---|
| CC-1 per-EP natural pattern | Each EP method signature uses DataClass or Callable as appropriate. No artificial uniformity. |
| CC-2 default append + override case-by-case | `register_*` methods accept `mode: Literal['append', 'override'] = 'append'`. Only EP-17 + EP-18 permit `'override'`; other EPs raise `ValueError` if `mode='override'` passed. |
| CC-3 startup-only registration | After FastAPI lifespan `startup` completes, `registry._closed = True`. Subsequent `register_*` calls raise `RegistrationClosedError`. |
| CC-4 strict raise on duplicate + namespaced obligatorio | All registrations require name with `brand_slug.` prefix (e.g., `vitalia.medical_consent_request`). Bare name (e.g., `medical_consent_request`) raises `NamespaceViolationError`. Re-registering same name raises `DuplicateRegistrationError`. |
| CC-5 inmutable post-startup | Registry exposes NO `unregister_*` method. AttributeError on `getattr(registry, 'unregister_*')`. |

#### 3.2.4 Exception hierarchy

```python
# exceptions.py
class ExtensionSDKError(Exception): """Base exception."""

class NamespaceViolationError(ExtensionSDKError):
    """Raised when registration name lacks brand_slug prefix (CC-4)."""

class DuplicateRegistrationError(ExtensionSDKError):
    """Raised when same name registered twice within same EP (CC-4)."""

class RegistrationClosedError(ExtensionSDKError):
    """Raised when register_* called after FastAPI startup completes (CC-3)."""
```

### 3.3 Part B2 — `@luana/extension-sdk` TypeScript package (NEW code — FE mirror)

Path: `luana-platform/typescript/extension-sdk/`

```
extension-sdk/
├── package.json                            # pnpm workspace member, version 0.0.8-alpha
├── tsconfig.json
├── README.md
└── src/
    ├── index.ts                            # TS interface mirror of ExtensionPointRegistry
    ├── brand-context.ts                    # BrandContext type mirror
    └── models.ts                           # TS type mirror for DataClass-pattern EPs
```

Scope FE-side intentionally narrower than Python: only EPs that materialize FE surface get TS types:
- EP-6 `SidebarRouteDef` (BE+FE sync — FE Next.js renders sidebar from `/api/v1/_sdk/sidebar` response)
- EP-10 `LandingTemplateDef` (JSON schema FE Landing Engine consumes)
- EP-18 `WizardStepDef` (BE+FE sync — FE Next.js renders wizard from `/api/v1/_sdk/wizard` response)

Other EPs (Python-only surface): no TS mirror. The TS `index.ts` exports types only; no runtime registry class on FE side (registration always happens BE at FastAPI startup).

### 3.4 Part C — `apps/test-brand/` smoke test pack (§7.5.2 D6=A)

Path: `luana-platform/apps/test-brand/`

```
test-brand/
├── pyproject.toml                          # uv workspace member, version 0.0.8-alpha
├── README.md                               # "Test brand: SDK smoke validation, NOT a deployable product"
├── python/test_brand/
│   ├── __init__.py
│   ├── extensions.py                       # 5 executable handlers (EP-1..EP-5) + 13 stubs (EP-6..EP-18)
│   └── main.py                             # FastAPI lifespan event invokes register_all(registry)
└── tests/
    └── test_sdk_smoke.py                   # asserts 18 registrations + EP-1..EP-5 happy-path invoke + EP-6..EP-18 NotImplementedError graceful
```

#### 3.4.1 `extensions.py` content shape

```python
# test_brand/extensions.py
from luana_core_extension_sdk import ExtensionPointRegistry, BrandContext
from luana_core_extension_sdk.models import (
    FieldOverride, PresetPack, ToolDef, WorkflowDef, BookingPolicy,
    SidebarRouteDef, ExtractorDef, ChannelAdapterDef, MetricDef,
    LandingTemplateDef, CampaignTemplateDef, AssetTemplateDef,
    GuardrailDef, KbPackDef, LifecycleStageDef, PlanTierDef, WizardStepDef,
)

def register_all(registry: ExtensionPointRegistry) -> None:
    # EP-1 executable: override field "field_x" for test-brand tenants only
    def _override_handler(field, ctx):
        if field.name == "field_x" and ctx.brand_slug == "test-brand":
            return FieldOverride(name="field_x_overridden", default_value="test")
        return None
    registry.field_override(_override_handler, name="test-brand.field_x_override")

    # EP-2 executable
    registry.offer_preset_pack_register(PresetPack(name="test-brand.smoke_pack", ...))

    # EP-3 executable (wraps Story 7 frozen ToolRegistry byte-stable — registry delegates read-only)
    registry.sales_agent_tool_register(ToolDef(name="test-brand.echo_tool", ...))

    # EP-4 executable (wraps Story 6 frozen WorkflowRegistry byte-stable)
    registry.copilot_workflow_register(WorkflowDef(name="test-brand.smoke_workflow", ...))

    # EP-5 executable
    registry.scheduling_booking_policy_register(BookingPolicy(name="test-brand.always_allow_policy", ...))

    # EP-6..EP-18 stubs — registration succeeds; invocation raises NotImplementedError
    registry.sidebar_routes_register(SidebarRouteDef(slug="test-brand.smoke_route", ...))
    registry.extractor_register(ExtractorDef(name="test-brand.smoke_extractor", ...))
    registry.channel_adapter_register(ChannelAdapterDef(channel_slug="test-brand.smoke_channel", ...))
    # ... (one stub per EP-6..EP-18 — 13 total)
```

#### 3.4.2 `main.py` FastAPI lifespan integration (§7.5.2 D2=B explicit register pattern)

```python
# test_brand/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from luana_core_extension_sdk import ExtensionPointRegistry
from test_brand.extensions import register_all

@asynccontextmanager
async def lifespan(app: FastAPI):
    registry = ExtensionPointRegistry()
    register_all(registry)
    registry.close()                          # CC-3: subsequent register_* raises RegistrationClosedError
    app.state.registry = registry
    yield

app = FastAPI(lifespan=lifespan)
```

#### 3.4.3 `test_sdk_smoke.py` — smoke validation contract

Asserts in this exact order:
1. Lifespan event completes without error (18 registrations succeed)
2. `registry._closed is True` post-startup
3. `len(registry.get_all('EP-1')) == 1`, ... `len(registry.get_all('EP-18')) == 1` — 18 EPs each hold 1 registration
4. EP-1 through EP-5 happy-path invocations return expected typed results
5. EP-6 through EP-18 invocation raises `NotImplementedError` with message indicating signature-only status
6. Bare-name registration attempt raises `NamespaceViolationError`
7. Duplicate-name registration attempt raises `DuplicateRegistrationError`
8. Post-startup `register_*` attempt raises `RegistrationClosedError`
9. `registry.unregister_*` does not exist (AttributeError)
10. `mode='override'` on EP-1..EP-16 raises `ValueError`; `mode='override'` on EP-17 + EP-18 succeeds

### 3.5 Part D — `docs/extension-points.md` documentation deliverable (§7.5.2 D5=B + §7.5.4)

Path: `luana-platform/docs/extension-points.md`

Required sections:

**§1 SDK overview + design principles** — narrative cement of CC-1..CC-5 verbatim from §7.5.1 + rationale paragraphs.

**§2 EP-1..EP-5 critical with per-vertical examples** — for each critical EP, provide:
- Method signature (Python)
- Method signature (TypeScript mirror if applicable)
- Vitalia example (medical vertical) — e.g., EP-3 `vitalia.medical_consent_request` tool definition
- Comunify example (creator-economy vertical) — e.g., EP-2 `comunify.creator_offer_pack` preset pack
- Lupulo example (gastronomy vertical) — e.g., EP-5 `lupulo.table_capacity_policy` booking policy
- Code snippet showing registration in FastAPI lifespan

**§3 EP-6..EP-18 backlog signatures with per-vertical examples** — for each backlog EP, provide:
- Method signature
- Per-vertical example showing intended use (signature-only — note "this signature is frozen v0.1.0; implementation deferred v0.2.x")
- Reference to outcome §7.5.3 row

**§4 Recipe: Build a vertical agent on top of luana-core** — Vitalia treatment-agent worked example per §7.5.4 verbatim:
- Pattern statement: "Vertical agent ES un APP del brand, NO un EP del core. NO EP-19."
- Code skeleton: `apps/vitalia/agents/treatment_agent/` consumes:
  - `luana-core-observability` — `VitaliaTreatmentCallbackHandler(BaseAgentCallbackHandler)` + `VitaliaTreatmentObservabilityContext(BaseObservabilityContext)` subclass pattern from Story 6+7
  - `luana-core-scheduling` — job queue + reminders pre/post-session
  - `luana-core-channels` via EP-8 — `vitalia.treatment_whatsapp_adapter` registered
  - `luana-core-marketing-kb` via EP-14 — `vitalia.medical-protocols-kb-pack-v1` brand-scope + `vitalia.{tenant_id}.internal-kb` tenant-scope
  - `luana-core-prompt-cache` — slot composer with slot 5 BRAND_VOICE via Story 7 D-T3 BrandVoicePort
  - `luana-core-extension-sdk` — `vitalia.medical_consent_request` tool via EP-3 + `vitalia.no_medical_recommendations_guardrail` via EP-13

**§5 Cross-brand learning principle — how features graduate to core** — §7.5.6 verbatim guideline:
- Brand A invents feature → /pm evaluates if generalizable → if yes, lift to core → brands B/C/D consume via SDK
- NEVER cross-brand direct import
- Example: Vitalia treatment agent learnings (pre/post engagement reminders) → /pm promotes to `luana-core-engagement-scheduler` → Comunify cohort retention + Lupulo dietary follow-up consume same primitive

## 4. Scope (OUT — explicit out-of-scope list)

Architect MUST emit validators that REJECT any of the following as scope creep:

- ❌ **EP-6..EP-18 semantic implementations** — signatures-only per §7.5.2 D1=B. Registry stores registration; invocation raises `NotImplementedError`. ETL pipeline integration (EP-7/EP-9), Landing Engine integration (EP-10), CRM lifecycle integration (EP-15), IAM signup integration (EP-16) all DEFERRED v0.2.x.
- ❌ **Brand consumer apps** (Vitalia/Comunify/Lupulo bootstraps = Stories 11-13). Story 8 ships `apps/test-brand/` ONLY.
- ❌ **GH Packages publish pipeline** = Story 9 (`luana-v0-1-0-publish`). Story 8 keeps workspace-internal uv + pnpm. No publishConfig / .releaserc / release.yml.
- ❌ **CF tunnel multi-domain dev setup** (`dev-app.vitalialat.com`, `dev-comunify.alpacapurpura.lat`, `dev-lupulo.alpacapurpura.lat`) = Stories 11-13 scope per outcome §7.5.5.
- ❌ **Production deployment isolation per brand** (GCP/AWS independent + Clerk apps + Stripe + Sentry + Postgres + Qdrant per brand) = Stories 11-13 scope per outcome §7.5.5.
- ❌ **Treatment agent implementation** = Story 11.5+ Vitalia bootstrap scope. Story 8 ships only the recipe doc in §4 of `docs/extension-points.md`.
- ❌ **Multi-session offer model changes for Vitalia** = Story 11+ Vitalia-specific. `VariantStructure` already supports packs per Story 5 lifted (verified). Story 8 does not modify offer model.
- ❌ **Streamlit admin pages** (sales-routing, sales-agent-quality, costo-agentes, llm-virtual-keys, llm-models) = Story 10 nicolify migration scope per Story 7 DEFERRED-FILES.
- ❌ **Scheduling concrete provider runtime** — sales_agent `application/tools/scheduling/providers.py` was lifted in Story 7 with deferred-import pattern preserved inside method bodies. Story 8 does NOT promote scheduling concrete providers to top-level imports. Per Story 7 §9.2 deferral, this is **Story 8 deferred ON PURPOSE** — full scheduling lift happens when Story 8 lifts `modules/scheduling/`. **OPEN QUESTION for architect: is `modules/scheduling/` lift part of Story 8 OR a separate post-Story-8 effort?** Spec assumes **NOT in Story 8** — scope is campaigns + SDK + test-brand + docs only. Architect MUST confirm or escalate.
- ❌ **AppointmentModel stub cement** = Story 8 cements OR re-allowlists post-Story-8. Currently allowlisted per Story 7 audit-fix carry-over (`tests/architecture/test_no_residual_test_stubs_post_story_6.py` Story 7 references). Architect MUST decide: cement now (if scheduling territory enters Story 8 scope) OR re-allowlist with explicit "deferred to scheduling lift" reason. Spec defaults to **re-allowlist** since scheduling lift NOT in scope.
- ❌ **ProductModel stub cement** = same disposition as AppointmentModel. Re-allowlist with "deferred to catalog/product lift" reason. Catalog/product module lift NOT in Story 8 scope.
- ❌ **EP-19 `vertical_agent_register`** = §7.5.4 explicitly forbids. Vertical agents are brand apps, NOT extension points. Pattern doc only in §4 of `docs/extension-points.md`.
- ❌ **Refactor or modification of Stories 6+7 frozen registries** (ToolRegistry / WorkflowRegistry / ExtractorRegistry / ModuleRegistry / SuggestionRegistry — copilot; ToolRegistry — sales_agent). EP-3 + EP-4 wrap byte-stable read-only delegation. Story 6 V-AG-3 golden snapshot continues GREEN post Story 8.
- ❌ **Eval framework / agentic_evals** — EXCLUDED Luana v0.2.0 per Story 7 §V-AG-5 + outcome §2 OQ1.
- ❌ **Voice cloning per-tenant** — Stories 11-13 scope per Story 5 §9.5.
- ❌ **BrandContext shape redefinition** — §7.5.2 D3 verbatim is FROZEN. Future optional fields permitted; required fields immutable for v0.1.0.

## 5. Gherkin scenarios (AI-resistant)

> 22 scenarios across 7 categories. Each scenario is testeable + has grader explicit. Auditor verifies 1:1 mapping to validators (architect emits `04-validators.yaml`).

### 5.1 Part A — Campaigns lift scenarios

#### Scenario A1 — `campaigns-workspace-registered` (`type: happy`)

**Given:**
- `luana-platform/pyproject.toml` workspace members list before Story 8 contains 23 packages (Story 7 cumulative)
- AISALESHT `backend/src/modules/campaigns/` contains 80 src files

**When:**
- Story 8 build completes lifting campaigns module

**Then:**
- `luana-platform/pyproject.toml` workspace members list contains 24 packages (alphabetical order preserved)
- New entry `python/luana-core-campaigns/` appears between alphabetical neighbors
- `luana-platform/python/luana-core-campaigns/pyproject.toml` declares `version = "0.0.8-alpha"`
- `luana-platform/python/luana-core-campaigns/src/luana_core_campaigns/__init__.py` exports public API

**Graders:**
- Arch fitness — `tests/architecture/test_workspace_members_alphabetical.py`
- File-presence — gate-runner verifies `pyproject.toml` version + structure

#### Scenario A2 — `campaigns-tests-pass-verbatim` (`type: happy`)

**Given:**
- AISALESHT `backend/tests/modules/campaigns/` contains 42 test files passing GREEN on AISALESHT development branch

**When:**
- Story 8 lifts tests verbatim to `luana-platform/python/luana-core-campaigns/tests/`
- Per-package pytest invocation runs

**Then:**
- All 42 test files discoverable
- Pass count matches AISALESHT baseline (or differs only by deferred-import skip markers explicitly tagged)
- Coverage threshold ≥ 43% per AISALESHT baseline
- Zero new test failures introduced by import path migration

**Graders:**
- Pytest — `cd luana-platform/python/luana-core-campaigns && uv run pytest --cov=src/luana_core_campaigns`
- Coverage gate — fails build if < 43%

#### Scenario A3 — `aisalesht-campaigns-untouched` (`type: adversarial`)

> Cardinal invariant V-NF-4 outcome §7.3 MUST NOT.

**Given:**
- AISALESHT `backend/src/modules/campaigns/` git status clean at start of Story 8 build
- `git rev-parse HEAD` recorded as baseline

**When:**
- 18-22 ticket Story 8 build completes (per checkpoint estimate)

**Then:**
- `git diff baseline..HEAD -- backend/src/modules/campaigns/` returns empty diff
- `git diff baseline..HEAD -- backend/tests/modules/campaigns/` returns empty diff
- No AISALESHT campaigns file modified, added, or deleted by Story 8 commits

**Graders:**
- Pre-commit hook — auditor C5 verifies via `git log --name-only` per Story 7 V-NF-4 pattern
- Arch fitness — `tests/architecture/test_aisalesht_campaigns_untouched.py` (if architect emits)

#### Scenario A4 — `campaigns-import-paths-migrated` (`type: happy`)

**Given:**
- AISALESHT campaigns files use `from src.modules.campaigns.X import Y` pattern

**When:**
- Story 8 lifts files to luana-core-campaigns

**Then:**
- Zero occurrences of `from src.modules.campaigns` in lifted files (`grep -rn 'from src\.modules\.campaigns' python/luana-core-campaigns/`)
- All imports rewritten to `from luana_core_campaigns.X import Y`
- Cross-module imports from campaigns to other lifted packages use `from luana_core_X.Y import Z` (e.g., `from luana_core_shared.events import DomainEvent`)
- Test imports follow same pattern

**Graders:**
- Grep — `grep -rn 'from src\.modules' luana-platform/python/luana-core-campaigns/` returns zero matches
- Arch fitness — `tests/architecture/test_no_legacy_import_paths.py`

### 5.2 Part B — Extension SDK EP-1..EP-5 critical (executable)

#### Scenario B1 — `EP-1-field-override-executable` (`type: happy`)

**Given:**
- `ExtensionPointRegistry` instantiated
- `BrandContext(brand_slug='vitalia', ...)` created
- Vitalia registers handler `vitalia.medical_consent_override` that overrides field `consent_form` for `brand_slug == 'vitalia'` with medical-compliance HTML

**When:**
- Core form-runtime invokes `registry.resolve_field_override(field=FieldDef(name='consent_form'), ctx=BrandContext(brand_slug='vitalia', ...))`

**Then:**
- Registry returns `FieldOverride` from Vitalia handler
- For `BrandContext(brand_slug='nicolify', ...)`, handler returns None → registry returns None → default field rendered

**Graders:**
- Unit test — `tests/unit/test_ep1_field_override.py`
- Smoke test — `apps/test-brand/tests/test_sdk_smoke.py::test_ep1_executable`

#### Scenario B2 — `EP-2-offer-preset-pack-comunify` (`type: happy`)

**Given:**
- Comunify registers `PresetPack(name='comunify.creator_offer_pack', presets=[...], applies_to_brand='comunify')`

**When:**
- Offer wizard invokes `registry.list_offer_preset_packs(ctx=BrandContext(brand_slug='comunify', ...))`

**Then:**
- Returns list containing `comunify.creator_offer_pack`
- For `BrandContext(brand_slug='vitalia', ...)`, returns list NOT containing `comunify.creator_offer_pack` (brand-filter applied)

**Graders:**
- Unit test — `tests/unit/test_ep2_offer_preset_pack.py`

#### Scenario B3 — `EP-3-sales-agent-tool-frozen-registry-wrap` (`type: happy`)

> CRITICAL: EP-3 wraps Story 7 ToolRegistry byte-stable. Story 7 V-AG-3 golden snapshot continues GREEN post Story 8.

**Given:**
- Story 7 frozen `ToolRegistry` in `luana-core-sales-agent` lifted from AISALESHT (V-AG-3 golden snapshot byte-stable)
- Vitalia registers `ToolDef(name='vitalia.medical_consent_request', ...)` via `registry.sales_agent_tool_register(tool)`

**When:**
- Sales agent specialist `closer` invokes `tool_registry.get_tool('vitalia.medical_consent_request')` (via existing Story 7 ToolRegistry dispatch path)

**Then:**
- Tool resolves to Vitalia handler
- Story 7 ToolRegistry public API surface UNCHANGED — same method names, same signatures (V-AG-3 golden snapshot continues GREEN)
- EP-3 dispatch is read-only delegation; ToolRegistry mutation surface NOT exposed via EP-3

**Graders:**
- Arch fitness — `tests/architecture/test_story_7_tool_registry_golden_snapshot.py` (continues GREEN from Story 7)
- Unit test — `tests/unit/test_ep3_sales_agent_tool.py`
- Downstream regression — Story 7 sales-agent 429+ own tests GREEN post Story 8

#### Scenario B4 — `EP-4-copilot-workflow-frozen-registry-wrap` (`type: happy`)

> CRITICAL: EP-4 wraps Story 6 WorkflowRegistry byte-stable. Story 6 V-AG-3 golden snapshot continues GREEN.

**Given:**
- Story 6 frozen 5 copilot registries (`ToolRegistry`, `WorkflowRegistry`, `ExtractorRegistry`, `ModuleRegistry`, `SuggestionRegistry`) byte-stable per V-AG-3 golden snapshot
- Lupulo registers `WorkflowDef(name='lupulo.menu_seasonal_refresh', ...)` via `registry.copilot_workflow_register(workflow)`

**When:**
- Copilot orchestrator dispatches workflow via existing Story 6 WorkflowRegistry path

**Then:**
- Workflow resolves to Lupulo handler
- Story 6 WorkflowRegistry public API surface UNCHANGED (V-AG-3 golden snapshot continues GREEN)
- EP-4 dispatch is read-only delegation

**Graders:**
- Arch fitness — Story 6 V-AG-3 golden snapshot test continues GREEN
- Unit test — `tests/unit/test_ep4_copilot_workflow.py`
- Downstream regression — Story 6 copilot 1640 tests GREEN post Story 8

#### Scenario B5 — `EP-5-scheduling-booking-policy-executable` (`type: happy`)

**Given:**
- Lupulo registers `BookingPolicy(name='lupulo.table_capacity_policy', can_confirm=lambda booking, ctx: Result(allowed=True if booking.party_size <= 8 else False))`

**When:**
- Booking flow invokes `registry.get_booking_policy('lupulo.table_capacity_policy').can_confirm(booking, ctx)`

**Then:**
- Returns `Result(allowed=False)` for `booking.party_size = 12`
- Returns `Result(allowed=True)` for `booking.party_size = 4`
- For `BrandContext(brand_slug='nicolify', ...)`, policy NOT applied (brand-namespaced)

**Graders:**
- Unit test — `tests/unit/test_ep5_scheduling_booking_policy.py`

### 5.3 Part B — Extension SDK EP-6..EP-18 backlog (signatures-only)

> One scenario per backlog EP. Registration succeeds, invocation raises `NotImplementedError` graceful. Smoke pack `apps/test-brand/` verifies all 13.

#### Scenario B6 — `EP-6-sidebar-routes-signature-only` (`type: happy`)

**Given:** `registry.sidebar_routes_register(SidebarRouteDef(slug='test-brand.smoke_route', label='Smoke', icon='zap', order=99))` succeeds.

**When:** Core invokes `registry.get_sidebar_routes(ctx)` (semantic dispatch).

**Then:** Raises `NotImplementedError("EP-6 sidebar_routes_register is signature-only in v0.1.0; semantic dispatch deferred v0.2.x")`. BE `/api/v1/_sdk/sidebar` returns 501 Not Implemented.

**Graders:** `tests/unit/test_ep6_sidebar_routes.py::test_signature_only`

#### Scenario B7 — `EP-7-extractor-signature-only` (`type: happy`)

**Given:** `registry.extractor_register(ExtractorDef(name='test-brand.smoke_extractor', target_module='offer', wave_position=99, ...))` succeeds.

**When:** `BaseExtractionOrchestrator` integration attempts dispatch.

**Then:** Raises `NotImplementedError`. **Graders:** `tests/unit/test_ep7_extractor.py::test_signature_only`

#### Scenario B8 — `EP-8-channel-adapter-signature-only` (`type: happy`)

**Given:** `registry.channel_adapter_register(ChannelAdapterDef(channel_slug='test-brand.smoke_channel', send=..., receive=..., format_for_channel=..., ))` succeeds. EP-8 scope per §7.5.3 extended covers sales_agent + copilot + vertical brand agents (treatment_agent/kitchen_agent).

**When:** Semantic dispatch attempted (e.g., `treatment_agent` consumes adapter).

**Then:** Raises `NotImplementedError`. **Graders:** `tests/unit/test_ep8_channel_adapter.py::test_signature_only`

#### Scenario B9 — `EP-9-metric-signature-only` (`type: happy`)

**Given:** `registry.metric_register(MetricDef(name='test-brand.smoke_metric', module='analytics', aggregation='sum', unit='count', currency_aware=False, stage_assignment='attraction', refresh_freq='daily', python_compute=...))` succeeds.

**When:** ETL pipeline integration attempts dispatch.

**Then:** Raises `NotImplementedError`. **Graders:** `tests/unit/test_ep9_metric.py::test_signature_only`

#### Scenario B10 — `EP-10-landing-template-signature-only` (`type: happy`)

**Given:** `registry.landing_template_register(LandingTemplateDef(template_id='test-brand.smoke_landing', vertical_hint='test', sections_schema={...}, preview_url=None))` succeeds. JSON schema declarative per §7.5.3 EP-10.

**When:** Landing Engine FE attempts to consume schema via semantic dispatch.

**Then:** Raises `NotImplementedError`. **Graders:** `tests/unit/test_ep10_landing_template.py::test_signature_only`

#### Scenario B11 — `EP-11-campaign-template-signature-only` (`type: happy`)

**Given:** `registry.campaign_template_register(CampaignTemplateDef(template_id='test-brand.smoke_drip', channel='email', steps=[CampaignStepDef(...), ...], trigger_event='user.signup', conditions={...}))` succeeds. Drip pattern.

**When:** Campaigns engine attempts to consume template via semantic dispatch.

**Then:** Raises `NotImplementedError`. **Graders:** `tests/unit/test_ep11_campaign_template.py::test_signature_only`

#### Scenario B12 — `EP-12-asset-template-signature-only` (`type: happy`)

**Given:** `registry.asset_template_register(AssetTemplateDef(template_id='test-brand.smoke_asset', asset_type='image', placeholders={'logo_url': str, 'tagline': str}, source_path='templates/smoke.png'))` succeeds. Static template + placeholder replacement.

**When:** Asset engine attempts to render via semantic dispatch.

**Then:** Raises `NotImplementedError`. **Graders:** `tests/unit/test_ep12_asset_template.py::test_signature_only`

#### Scenario B13 — `EP-13-sales-agent-guardrail-pre-send-and-pre-receive` (`type: happy`)

**Given:** `registry.sales_agent_guardrail_register(GuardrailDef(name='test-brand.smoke_guardrail', pre_send_check=..., pre_receive_check=..., priority=10, mode='warn'))` succeeds. Per §7.5.3 EP-13 extended scope: pre-send + pre-receive BOTH included from v0.1.0.

**When:** Sales agent attempts to invoke guardrail.

**Then:** Raises `NotImplementedError`. **Graders:** `tests/unit/test_ep13_sales_agent_guardrail.py::test_signature_only` + `test_pre_send_and_pre_receive_both_present_in_signature`

#### Scenario B14 — `EP-14-copilot-kb-pack-tenant-scope` (`type: happy`)

**Given:** `registry.copilot_kb_pack_register(KbPackDef(pack_id='test-brand.smoke_kb', documents_path='./kb/', embedding_model_ref='text-embedding-3-small', qdrant_collection_name='test-brand-smoke', tenant_scope='both', metadata={...}))` succeeds. Per §7.5.3 EP-14: `tenant_scope: 'brand' | 'tenant' | 'both'`.

**When:** Copilot RAG attempts to consume pack via semantic dispatch.

**Then:** Raises `NotImplementedError`. **Graders:** `tests/unit/test_ep14_copilot_kb_pack.py::test_signature_only` + `test_tenant_scope_field_present_and_accepts_three_values`

#### Scenario B15 — `EP-15-crm-lifecycle-stage-insert-between` (`type: happy`)

**Given:** `registry.crm_lifecycle_stage_register(LifecycleStageDef(stage_id='test-brand.pending_review', label='Pending Review', after_stage='signup', before_stage='active', transition_rules=[...]))` succeeds. Declarative insert-between core stages (no remove).

**When:** CRM engine attempts to apply lifecycle change via semantic dispatch.

**Then:** Raises `NotImplementedError`. **Graders:** `tests/unit/test_ep15_crm_lifecycle_stage.py::test_signature_only`

#### Scenario B16 — `EP-16-iam-signup-handler-pending-review` (`type: happy`)

**Given:** `registry.iam_signup_handler(handler=lambda clerk_user, ctx: SignupResult(status='pending_review', metadata={'reason': 'medical_compliance_check'}))` succeeds. Async background + pending_review state.

**When:** Clerk webhook attempts to invoke handler via semantic dispatch.

**Then:** Raises `NotImplementedError`. **Graders:** `tests/unit/test_ep16_iam_signup_handler.py::test_signature_only`

#### Scenario B17 — `EP-17-tenant-plan-tier-override-mode` (`type: happy`)

**Given:** `registry.tenant_plan_tier_register(PlanTierDef(tier_id='vitalia.starter', label='Vitalia Starter', price_monthly=99.0, currency='USD', features=['medical_kb_pack', 'consent_management'], limits={'max_tenants': 1}, stripe_price_id='price_xxx'), mode='override')` succeeds. Brand replaces core tiers completely per §7.5.3 EP-17.

**When:** Tenant tier engine attempts to read tiers via semantic dispatch.

**Then:** Raises `NotImplementedError`. **Graders:** `tests/unit/test_ep17_tenant_plan_tier.py::test_override_mode_permitted` + `test_signature_only`

#### Scenario B18 — `EP-18-onboarding-wizard-steps-override-mode-and-fe-be-sync` (`type: happy`)

**Given:** `registry.onboarding_wizard_steps_register(WizardStepDef(step_id='vitalia.medical_intake', title='Medical Intake', component_ref='VitaliaMedicalIntakeStep', prereqs=[], skippable=False, post_action_event='medical_intake_complete'), mode='override')` succeeds. Brand replaces wizard completely.

**When:** BE `/api/v1/_sdk/wizard` attempts to serve wizard config to FE Next.js.

**Then:** Raises `NotImplementedError` (BE returns 501). FE TypeScript types from `@luana/extension-sdk` available for compile-time validation but no runtime FE consumption in v0.1.0.

**Graders:** `tests/unit/test_ep18_wizard_steps.py::test_override_mode_permitted` + `test_signature_only` + `tests/architecture/test_ts_types_mirror_python_dataclasses.py`

### 5.4 Cross-cutting policy enforcement

#### Scenario C1 — `cc4-duplicate-registration-raises` (`type: negative`)

**Given:**
- Registry instantiated, lifespan startup NOT yet complete (`registry._closed is False`)
- First registration: `registry.field_override(handler1, name='vitalia.medical_consent_override')` succeeds

**When:**
- Second registration with same name: `registry.field_override(handler2, name='vitalia.medical_consent_override')`

**Then:**
- Raises `DuplicateRegistrationError("Name 'vitalia.medical_consent_override' already registered for EP-1 field_override")`
- Registry state unchanged (handler1 remains registered)
- Audit log entry written (if audit infra wired) recording duplicate attempt

**Graders:** `tests/unit/test_cc4_duplicate_registration.py`

#### Scenario C2 — `cc4-bare-name-violation` (`type: adversarial`)

> Anti-island enforcement: prevents accidental cross-brand consumption.

**Given:** Registry instantiated, startup NOT complete.

**When:** Registration with bare (non-namespaced) name: `registry.sales_agent_tool_register(ToolDef(name='medical_consent_request', ...))` (note: bare `medical_consent_request` instead of `vitalia.medical_consent_request`).

**Then:**
- Raises `NamespaceViolationError("Name 'medical_consent_request' must be namespaced with brand_slug prefix (e.g., 'vitalia.medical_consent_request')")`
- Registry state unchanged
- Error message includes accepted brand_slugs list from `BrandContext.brand_slug` Literal type

**Graders:** `tests/unit/test_cc4_namespace_violation.py`

#### Scenario C3 — `cc3-registration-closed-after-startup` (`type: negative`)

**Given:**
- FastAPI lifespan completes successfully
- `registry.close()` called → `registry._closed is True`

**When:** Attempted runtime registration: `registry.field_override(handler, name='vitalia.late_override')`.

**Then:**
- Raises `RegistrationClosedError("Registry closed after FastAPI startup; runtime registration prohibited per CC-3")`
- Registry state unchanged

**Graders:** `tests/unit/test_cc3_registration_closed.py` + `apps/test-brand/tests/test_sdk_smoke.py::test_post_startup_registration_raises`

#### Scenario C4 — `cc5-no-unregister-method-exists` (`type: negative`)

**Given:** Registry instantiated, any state.

**When:** Attempted attribute access: `registry.unregister_field_override` or `registry.unregister_sales_agent_tool`.

**Then:**
- Raises `AttributeError("'ExtensionPointRegistry' object has no attribute 'unregister_field_override'")`
- Registry exposes NO unregister method for any EP (CC-5 enforcement)

**Graders:** `tests/architecture/test_no_unregister_api.py` (verifies registry class has zero methods starting with `unregister_`)

#### Scenario C5 — `cc2-override-mode-restricted-to-ep17-ep18` (`type: edge`)

**Given:** Registry instantiated, startup NOT complete.

**When:**
- Attempted EP-1 override mode: `registry.field_override(handler, name='vitalia.override_test', mode='override')`

**Then:**
- Raises `ValueError("EP-1 field_override does not support mode='override'; only EP-17 + EP-18 permit override")`
- Registry state unchanged

**When (companion):** EP-17 override mode: `registry.tenant_plan_tier_register(PlanTierDef(...), mode='override')`.

**Then:** Succeeds. Registration replaces any prior tier registration for that brand.

**Graders:** `tests/unit/test_cc2_override_mode.py` (parametrized — verifies all 18 EPs accept/reject mode='override' per §7.5.3 table)

### 5.5 Smoke test pack apps/test-brand/

#### Scenario D1 — `smoke-pack-lifespan-registers-all-18-eps` (`type: happy`)

**Given:** `apps/test-brand/python/test_brand/main.py` FastAPI app with lifespan event configured.

**When:** App startup invokes lifespan handler → `register_all(registry)` executes.

**Then:**
- 18 registrations succeed (5 executable + 13 signature-only stubs)
- `registry.close()` invoked
- `registry._closed is True`
- `len(registry.get_all('EP-1')) == 1`, ..., `len(registry.get_all('EP-18')) == 1`

**Graders:** `apps/test-brand/tests/test_sdk_smoke.py::test_lifespan_registers_all_18_eps`

#### Scenario D2 — `smoke-pack-ep1-to-ep5-happy-invocation` (`type: happy`)

**Given:** Registry post-startup with 18 registrations.

**When:** Invocation of each of EP-1..EP-5 happy paths via registry dispatch helpers.

**Then:** All 5 invocations return typed results without exception.

**Graders:** `apps/test-brand/tests/test_sdk_smoke.py::test_ep1_to_ep5_executable`

#### Scenario D3 — `smoke-pack-ep6-to-ep18-not-implemented-graceful` (`type: edge`)

**Given:** Registry post-startup with 18 registrations.

**When:** Semantic dispatch attempted on each of EP-6..EP-18.

**Then:** Each raises `NotImplementedError` with descriptive message indicating signature-only status + reference to v0.2.x deferral. No crash. No silent failure.

**Graders:** `apps/test-brand/tests/test_sdk_smoke.py::test_ep6_to_ep18_not_implemented_graceful`

#### Scenario D4 — `docs-extension-points-md-ships-with-recipe-and-examples` (`type: happy`)

**Given:** Story 8 build completes.

**When:** File-presence check executes.

**Then:**
- `luana-platform/docs/extension-points.md` exists
- §1 contains CC-1..CC-5 verbatim from §7.5.1
- §2 contains Vitalia + Comunify + Lupulo examples for EP-1..EP-5 (per §7.5.2 D5=B)
- §3 contains per-vertical examples for EP-6..EP-18 (signature-only notes)
- §4 contains "Recipe: Build a vertical agent on top of luana-core" with Vitalia treatment-agent worked example (per §7.5.4)
- §4 explicitly states "NO EP-19 — vertical agents are brand apps, not core extension points"
- §5 contains cross-brand learning principle from §7.5.6

**Graders:** `tests/architecture/test_docs_extension_points_completeness.py` (parses MD headers, checks required sections exist + required strings appear)

### 5.6 BrandContext shape verification

#### Scenario E1 — `brandcontext-frozen-dataclass-9-fields` (`type: happy`)

**Given:** `luana-core-extension-sdk` package.

**When:** Import `BrandContext` and inspect dataclass.

**Then:**
- `BrandContext.__dataclass_params__.frozen is True`
- All 9 fields per §7.5.2 D3 present with correct types: `tenant_id: UUID`, `brand_slug: Literal[...]`, `plan_tier: str`, `locale: str`, `feature_flags: dict[str, bool]`, `tenant_profile_id: UUID`, `vertical_kind: Literal[...]`, `compliance_flags: dict[str, bool]`, `pii_policy: Literal[...]`
- Attempted mutation of instance raises `dataclasses.FrozenInstanceError`

**Graders:** `tests/unit/test_brand_context.py::test_frozen_9_fields`

#### Scenario E2 — `brandcontext-future-optional-fields-backward-compat` (`type: edge`)

**Given:** Handler implemented against BrandContext v0.1.0 (9 fields).

**When:** Hypothetical future v0.2.x adds optional field (e.g., `currency_code: Optional[str] = None`).

**Then:**
- Handler that uses only original 9 fields continues working (does not crash on instantiation)
- New field defaults to None — handler ignoring it sees no change in behavior
- Backward compat covenant documented in `brand_context.py` docstring

**Graders:** `tests/unit/test_brand_context.py::test_optional_field_addition_does_not_break_existing_handlers` (uses subclass / mock to simulate future addition)

### 5.7 Vertical-agent-recipe doc deliverable

#### Scenario F1 — `recipe-vitalia-treatment-agent-worked-example` (`type: happy`)

**Given:** `docs/extension-points.md` §4.

**When:** Doc consumer reads §4.

**Then:** Section contains:
- Statement "Vertical agent ES un APP del brand, NO un EP del core. NO EP-19."
- Code skeleton `apps/vitalia/agents/treatment_agent/` consuming:
  - `luana-core-observability` subclass pattern (VitaliaTreatmentCallbackHandler + VitaliaTreatmentObservabilityContext) — Story 6+7 cement
  - `luana-core-scheduling` for pre/post-session reminders
  - `luana-core-channels` via EP-8 (vitalia.treatment_whatsapp_adapter registration example)
  - `luana-core-marketing-kb` via EP-14 with `tenant_scope='both'` example (medical-protocols brand-scope + clínica internal-KB tenant-scope)
  - `luana-core-prompt-cache` slot composer with slot 5 BRAND_VOICE via D-T3 BrandVoicePort (Story 7)
  - `luana-core-extension-sdk` for tool (EP-3) + guardrail (EP-13) registration

**Graders:** `tests/architecture/test_docs_extension_points_completeness.py::test_recipe_section_content` (regex match on required strings)

#### Scenario F2 — `recipe-explicitly-forbids-ep19` (`type: adversarial`)

> Prevents future contributors from proposing EP-19 vertical_agent_register.

**Given:** `docs/extension-points.md` §4.

**When:** Doc consumer reads §4.

**Then:**
- Section contains literal string "NO EP-19" or "no EP-19" (case-insensitive)
- Section contains rationale: "Vertical agents are brand apps composing core packages, not core extension points"

**Graders:** `tests/architecture/test_docs_extension_points_completeness.py::test_no_ep19_explicit`

## 6. Acceptance criteria (mappable 1:1 to validators)

Architect Story 8 emits `04-validators.yaml` covering exactly these acceptance criteria — each as a `must_pass: true` validator.

### 6.1 Non-functional (V-NF-*)
- [ ] **V-NF-1**: `luana-platform/pyproject.toml` workspace members alphabetical, 24 packages (Story 7 baseline 23 + Story 8 luana-core-campaigns + luana-core-extension-sdk + apps/test-brand + typescript/extension-sdk = 27 total **OR confirm count via architect**)
- [ ] **V-NF-2**: All new packages declare `version = "0.0.8-alpha"`
- [ ] **V-NF-3**: Per-package `pyproject.toml` declares dependencies explicit
- [ ] **V-NF-4**: AISALESHT `backend/src/modules/campaigns/` byte-stable (cardinal invariant)
- [ ] **V-NF-5**: No publishConfig in any new pyproject.toml (deferred Story 9)
- [ ] **V-NF-6**: No .releaserc / release.yml (deferred Story 9)
- [ ] **V-NF-7**: Spanish neutro LatAm in any user-facing string (zero voseo) — N/A this story (infra only, no UI strings)

### 6.2 Functional (V-F-*)
- [ ] **V-F-campaigns-1**: luana-core-campaigns per-package pytest passes, coverage ≥ 43%
- [ ] **V-F-campaigns-2**: Import paths migrated (`from src.modules.campaigns` zero matches)
- [ ] **V-F-sdk-1**: ExtensionPointRegistry exposes exactly 18 register methods (EP-1..EP-18)
- [ ] **V-F-sdk-2**: EP-1..EP-5 happy path invocations succeed
- [ ] **V-F-sdk-3**: EP-6..EP-18 semantic dispatch raises NotImplementedError
- [ ] **V-F-sdk-4**: CC-1..CC-5 runtime enforcement (5 cross-cutting scenarios C1-C5 pass)
- [ ] **V-F-sdk-5**: BrandContext frozen dataclass with 9 fields per §7.5.2 D3
- [ ] **V-F-ts-1**: `@luana/extension-sdk` TS types mirror Python DataClasses (EP-6 + EP-10 + EP-18)
- [ ] **V-F-test-brand-1**: apps/test-brand smoke test passes 18 registrations + 5 executable + 13 NotImplementedError graceful
- [ ] **V-F-docs-1**: docs/extension-points.md ships with §1..§5 (CC verbatim + per-vertical examples + recipe + cross-brand learning principle)

### 6.3 Agentic invariants (V-AG-*) — from Stories 6+7 continue GREEN
- [ ] **V-AG-3-story-6**: Story 6 copilot 5 registries golden snapshot continues GREEN (frozen contract preservation)
- [ ] **V-AG-3-story-7**: Story 7 sales-agent ToolRegistry golden snapshot continues GREEN
- [ ] **V-AG-new-story-8**: EP-3 + EP-4 wrappers do NOT mutate frozen registries (read-only delegation verified by arch fitness)

### 6.4 Downstream regression (R3 auditor-downstream-regression scope)
- [ ] **V-D-1**: Stories 1-7 packages per-package pytest GREEN post Story 8 (zero new regressions)
- [ ] **V-D-2**: Story 6 copilot 1640 tests + Story 7 sales-agent 429+ tests continue GREEN
- [ ] **V-D-3**: AISALESHT BE/FE test suite GREEN (campaigns module still loads in AISALESHT via `src.modules.campaigns` — Story 10 nicolify migration is separate)

## 7. Edge cases

### 7.1 Stories 6+7 frozen registries breakage detection

**Risk:** EP-3 / EP-4 wrappers accidentally mutate registry state (e.g., add validation hook that changes registration order).

**Mitigation:** Arch fitness `test_ep3_ep4_wrappers_read_only.py` — inspects registry class methods, ensures EP-3 + EP-4 dispatch helpers do NOT call any mutation method on underlying ToolRegistry / WorkflowRegistry. Cross-references Story 6 V-AG-3 + Story 7 V-AG-3 golden snapshots.

### 7.2 BrandContext serialization safety

**Risk:** BrandContext logged or serialized to traces could leak PII if mutated to include sensitive fields.

**Mitigation:** `pii_policy: Literal['standard', 'medical', 'creator', 'gastronomy']` is metadata only (NOT actual PII). All 9 fields are IDs + slugs + flag maps + locale strings — none are PII. Logging BrandContext is safe by construction. Documented in `brand_context.py` docstring + tested via `tests/unit/test_brand_context.py::test_json_serializable_no_pii`.

### 7.3 Workspace pyproject.toml ordering (alphabetical)

**Risk:** New package additions break alphabetical ordering invariant from Stories 1-7.

**Mitigation:** Arch fitness `test_workspace_members_alphabetical.py` (continues from prior stories) verifies sorted order post-Story-8. Builder MUST insert new packages in correct alphabetical position.

### 7.4 Tests downstream R3 — Stories 1-7 packages must not regress

**Risk:** Lifting campaigns + introducing new packages (luana-core-extension-sdk + apps/test-brand + typescript/extension-sdk) triggers `pyproject.toml` / workspace config changes that ripple to Stories 1-7 packages.

**Mitigation:** Per-package pytest run for each of Stories 1-7 packages post Story 8 build. Per R3 `auditor-downstream-regression.md` SSoT table — luana-platform workspace root pyproject.toml change is a cross-package change requiring downstream verification. Gate-runner scope: all packages.

### 7.5 EP-3 wraps Story 7 ToolRegistry — provider routing

**Risk:** Story 7 ToolRegistry uses internal provider routing (qualifier/product_expert/closer/supervisor/tool_executor/safety/escalate specialists per Story 7 §3 protected surfaces). EP-3 must preserve byte-stable provider routing.

**Mitigation:** EP-3 dispatch helper invokes Story 7 ToolRegistry public API only. No reach-into private dispatch methods. Arch fitness verifies EP-3 imports only from `luana_core_sales_agent.application.tools.registry` public exports.

### 7.6 EP-13 pre-receive expansion ripple (sales-agent runtime)

**Risk:** §7.5.3 EP-13 extended to include pre-receive checks from v0.1.0 (Chris "pagar precio hoy"). Story 7 sales-agent runtime currently has NO pre-receive hook. EP-13 signature includes `pre_receive_check: Optional[Callable]` but invocation NotImplementedError v0.1.0.

**Mitigation:** EP-13 is signature-only in Story 8. NO sales-agent runtime changes. When v0.2.x implements EP-13 semantics, separate ticket adds pre-receive hook to sales-agent runtime. Story 8 spec explicitly NOT in scope.

### 7.7 EP-8 extended scope (sales_agent + copilot + vertical agents)

**Risk:** §7.5.3 EP-8 extended from sales_agent-only to cover sales_agent + copilot + vertical brand agents (treatment_agent/kitchen_agent). Signature must be flexible enough to support all three without breaking.

**Mitigation:** `ChannelAdapterDef` includes `target_agent_runtime: Literal['sales_agent', 'copilot', 'vertical_brand']` field. Documented in `models.py` + per-vertical examples in `docs/extension-points.md` §3 EP-8.

### 7.8 EP-14 tenant_scope tri-modal

**Risk:** `tenant_scope: 'brand' | 'tenant' | 'both'` per §7.5.3 EP-14 detail. Three modes increase implementation complexity. Story 8 only signature, but signature must enumerate all 3.

**Mitigation:** `KbPackDef.tenant_scope: Literal['brand', 'tenant', 'both']` enforced via Pydantic Literal type. Per-vertical examples in docs show usage (Vitalia: brand-scope medical-protocols + tenant-scope clínica internal-KB).

### 7.9 EP-17 + EP-18 override-mode semantics

**Risk:** `mode='override'` permitted only for EP-17 + EP-18. Other EPs raise `ValueError`. Override semantics not yet implemented (signature-only). Future implementation must define what "override" means (replace entire core list? replace per-key?).

**Mitigation:** Spec defers implementation semantics to v0.2.x. Story 8 only enforces signature acceptance for EP-17 + EP-18 + rejection for EP-1..EP-16. Documented as known deferred decision.

### 7.10 Workspace member count drift

**Risk:** Story 8 introduces 3 new packages (luana-core-campaigns + luana-core-extension-sdk + apps/test-brand + typescript/extension-sdk = 4 actually) but exact count depends on whether `apps/test-brand` counts as workspace member or standalone app, and whether `typescript/extension-sdk` is pnpm-only.

**Mitigation:** Architect Story 8 confirms exact count in 03-arch.md. Validator V-NF-1 uses exact count post-architect-confirm.

## 8. Non-functional requirements

| Categoría | Requisito | Verificador |
|---|---|---|
| Latencia | Registry register_* < 1ms (in-memory dict insert) | Microbenchmark unit test |
| Latencia | Registry dispatch lookup < 1ms | Microbenchmark unit test |
| Memory | Registry holds ~18 registrations × small DataClass each — < 100KB total | N/A (trivial) |
| Cost | Story 8 NOT agentic production code (R23 NOT triggered per checkpoint frontmatter) — Sonnet eligible | /dev-team owner_eligibility per checkpoint |
| PII | BrandContext fields are NOT PII (IDs + slugs + flag maps) — safe to log | `tests/unit/test_brand_context.py::test_json_serializable_no_pii` |
| Tenant isolation | EP namespacing enforces brand isolation (CC-4 strict raise on bare names) | Scenario C2 + C5 |
| i18n | Spanish neutro LatAm — N/A this story (infra only, no user-facing strings) | N/A |
| Backward compat | BrandContext future optional fields permitted without breaking handlers | Scenario E2 |
| Frozen contract | EP-1..EP-18 signatures FROZEN for v0.1.0; bump after Story 9 publish requires SemVer breaking | Story 9 V-NF gate (this story emits frozen contracts) |

## 9. Constraints técnicos heredados

### 9.1 Rules `.claude/rules/` aplicables
- `backend-ddd.md` — Inside-Out DDD layers preserved in luana-core-campaigns lift (domain → infrastructure → application → api)
- `anti-duplication.md` — Story 8 introduces NEW shared abstraction (`luana-core-extension-sdk`) cross-consumer. Inventario SSoT in anti-duplication.md MUST be updated post Story 8 with row "Extension SDK / ExtensionPointRegistry / consumed by all brand apps".
- `auditor-downstream-regression.md` — R3 scope: Story 8 touches workspace pyproject.toml + introduces new shared abstraction. Downstream test targets: ALL Stories 1-7 packages per-package pytest + Story 6 + Story 7 frozen registry golden snapshots.
- `git-safety.md` + `parallel-safety.md` — Single Claude sub session 4, single branch (development on AISALESHT side + main on luana-platform side per Story 6+7 precedent), no force push, no revert without Chris approval.
- `tdd-mandatory.md` — Tests FIRST for SDK (register/lookup/exceptions before implementation). Tests verbatim lift for campaigns.
- `hotfix-repro-mandatory.md` — Story 8 is NOT a hotfix (greenfield SDK + lift). N/A.
- `anti-default-flip-audit.md` — Story 8 does NOT flip any feature flag defaults. N/A.

### 9.2 Tessl skills relevantes
- `tessl__fastapi` — apps/test-brand main.py FastAPI lifespan pattern
- `tessl__pytest-api-testing` — pytest patterns for SDK unit tests + smoke pack
- `tessl__zod` — N/A (TypeScript types are mirror only, no runtime validation in v0.1.0)

### 9.3 Outcome §7.3 lift mode constraints (campaigns Part A)
- MUST DO: lift file names + class names + function signatures + public API surface + tests verbatim + version 0.0.8-alpha
- MUST NOT DO: scope expansion, refactor module boundaries, rename modules, change tech stack defaults, introduce new patterns not in AISALESHT, schema migration changes, cross-brand architecture decisions, drop/deprecate code

### 9.4 Outcome §7.5 binding decisions (SDK Part B + C + D)
- §7.5.1 CC-1..CC-5 verbatim runtime enforcement
- §7.5.2 D1..D7 — scope + discovery + brand_context + versioning + examples + stub-brand + pre-auth
- §7.5.3 EP-6..EP-18 backlog signature decisions verbatim
- §7.5.4 vertical-agent-recipe doctrine (NO EP-19)
- §7.5.5 dev infra dummy domains (NOT Story 8 scope)
- §7.5.6 cross-brand learning principle (docs deliverable)

## 10. Cross-module impact

**Lifted from AISALESHT:**
- `backend/src/modules/campaigns/` → `luana-platform/python/luana-core-campaigns/`
- `backend/tests/modules/campaigns/` → `luana-platform/python/luana-core-campaigns/tests/`

**New packages introduced (no AISALESHT counterpart):**
- `luana-platform/python/luana-core-extension-sdk/` (NEW Python SDK)
- `luana-platform/typescript/extension-sdk/` (NEW TS SDK mirror)
- `luana-platform/apps/test-brand/` (NEW smoke test pack)

**Wraps (read-only delegation, byte-stable):**
- Story 6 `luana-core-copilot` ToolRegistry + WorkflowRegistry + ExtractorRegistry + ModuleRegistry + SuggestionRegistry (V-AG-3 golden snapshot — continues GREEN post Story 8)
- Story 7 `luana-core-sales-agent` ToolRegistry (V-AG-3 golden snapshot — continues GREEN post Story 8)

**Eventos emitidos:** none (Story 8 is infra + signatures, no runtime semantic dispatch for EP-6..EP-18)

**Eventos consumidos:** none (registry is passive store + dispatch helper, not event-driven)

**Documentation deliverable:** `luana-platform/docs/extension-points.md` (NEW)

## 11. Validators preview (architect Story 8 formalize in 04-validators.yaml)

> Brief enumeration only. Architect emits `must_pass: true` per validator with exact command + expected output.

| Category | Validator ID | Scope |
|---|---|---|
| **non_functional** | V-NF-1 workspace alphabetical | `tests/architecture/test_workspace_members_alphabetical.py` |
| | V-NF-2 version 0.0.8-alpha | gate-runner grep `version = "0.0.8-alpha"` per pyproject.toml |
| | V-NF-3 dependencies explicit | per-package pyproject.toml verification |
| | V-NF-4 AISALESHT untouched (cardinal) | `git diff baseline..HEAD -- backend/src/modules/campaigns/` empty |
| | V-NF-5/6/7 no publish artifacts | grep zero matches for publishConfig + .releaserc + release.yml |
| **functional (campaigns)** | V-F-campaigns-1 per-package pytest pass + coverage | `cd luana-platform/python/luana-core-campaigns && uv run pytest --cov` |
| | V-F-campaigns-2 import paths migrated | `grep -rn 'from src\.modules\.campaigns' luana-platform/python/luana-core-campaigns/` returns 0 |
| **functional (SDK)** | V-F-sdk-1 18 EP methods exposed | `tests/unit/test_registry_surface.py` |
| | V-F-sdk-2 EP-1..EP-5 executable | `tests/unit/test_ep1_through_ep5.py` |
| | V-F-sdk-3 EP-6..EP-18 NotImplementedError | `tests/unit/test_ep6_through_ep18_signature_only.py` |
| | V-F-sdk-4 CC-1..CC-5 enforcement | `tests/unit/test_cross_cutting_policies.py` |
| | V-F-sdk-5 BrandContext frozen 9 fields | `tests/unit/test_brand_context.py` |
| **functional (TS mirror)** | V-F-ts-1 TS types mirror Python | `tests/architecture/test_ts_types_mirror_python_dataclasses.py` |
| **functional (test-brand)** | V-F-test-brand-1 smoke pack | `apps/test-brand/tests/test_sdk_smoke.py` |
| **functional (docs)** | V-F-docs-1 extension-points.md sections | `tests/architecture/test_docs_extension_points_completeness.py` |
| **agentic (frozen contracts)** | V-AG-3-story-6 5 copilot registries golden snapshot | Story 6 arch fitness continues GREEN |
| | V-AG-3-story-7 sales-agent ToolRegistry golden snapshot | Story 7 arch fitness continues GREEN |
| | V-AG-new-story-8 EP-3+EP-4 wrappers read-only | `tests/architecture/test_ep3_ep4_wrappers_read_only.py` |
| **downstream regression (R3)** | V-D-1 Stories 1-7 packages pytest GREEN | gate-runner scope: all 23 prior packages per-package |
| | V-D-2 Story 6 copilot 1640 tests + Story 7 sales-agent 429+ tests GREEN | gate-runner scope: 2 packages |
| | V-D-3 AISALESHT BE/FE GREEN | gate-runner scope: AISALESHT root |
| **visual** | N/A this story (infra only, no FE rendered surface) | — |
| **agentic_eval** | N/A this story (no agentic runtime changes) | — |

## 12. Risks

Per outcome §7.5 halt criteria + checkpoint frontmatter halt_criteria_session_4:

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| 1 | Scope expansion needed (campaigns module refactor) | High | Halt + escalate Chris. Lift mode constraint outcome §7.3. |
| 2 | EP signature decision surfaces during build NOT covered by §7.5 | High | Halt + escalate Chris. /po MUST emit delta-spec.md if discovered. |
| 3 | Stories 6+7 frozen registries breakage (EP-3/EP-4 wrappers mutate) | High | V-AG-3 golden snapshots continue GREEN — auto-detect. `tests/architecture/test_ep3_ep4_wrappers_read_only.py` enforces. |
| 4 | AISALESHT campaigns touched by accident (V-NF-4 violated) | Critical | V-NF-4 git diff check + Story 7 precedent enforcement pattern. |
| 5 | Cumulative session 4 cost crosses $2500 soft check-in | Medium | Soft check-in per outcome §7.2; Chris confirms continue. |
| 6 | Auditor REJECTED + 3 auto-fix Opus iter all fail | High | Halt + escalate Chris per outcome §7.2. |
| 7 | Builder cap_reached 10 iter on same ticket | High | Halt + escalate Chris. |
| 8 | Workspace member count miscount (V-NF-1 fails) | Low | Architect 03-arch.md confirms exact count post-design. |
| 9 | TypeScript mirror drift (TS types not matching Python DataClasses) | Medium | V-F-ts-1 arch fitness test enforces mirror parity. |
| 10 | docs/extension-points.md missing required sections | Medium | V-F-docs-1 arch fitness test enforces section presence via regex match. |

## 13. Open questions for architect (resolve in 03-arch.md)

- [ ] **OQ-1 Workspace member exact count**: Story 7 baseline = 23 packages. Story 8 introduces luana-core-campaigns (+1) + luana-core-extension-sdk (+1) + apps/test-brand (+1) + typescript/extension-sdk (+1) = 27 total OR is typescript/extension-sdk co-located with python SDK as same workspace member? Architect confirm + V-NF-1 uses exact count.
- [ ] **OQ-2 Scheduling lift in Story 8 scope or not**: Spec §4 OUT explicitly excludes scheduling concrete provider runtime. AppointmentModel + ProductModel stubs allowlisted post-Story-7. Architect MUST confirm scope decision: (A) Story 8 cements scheduling lift now, OR (B) scheduling deferred to separate post-Story-8 lift effort. Spec defaults to **(B) deferred** since outcome §7.5 does NOT mention scheduling module lift.
- [ ] **OQ-3 EP-3 + EP-4 dispatch helper API surface**: How exactly do EP-3 + EP-4 wrappers expose Story 6+7 frozen registries to brand handlers? Read-only proxy class? Pass-through method? Architect defines exact dispatch API ensuring V-AG-3 golden snapshots stay GREEN.
- [ ] **OQ-4 BrandContext `feature_flags` dict shape**: Outcome §7.5.2 D3 defines field as `feature_flags: dict[str, bool]`. Source of truth for flag map — Story 4 connections module or other? Architect confirm + how is BrandContext populated at request boundary (FastAPI dependency)?
- [ ] **OQ-5 ts-types mirror automation**: Are TS types hand-maintained or auto-generated from Python DataClasses? If hand-maintained, V-F-ts-1 must compare structures programmatically. Architect decides.

## 14. Próximo paso

- /pm ratifica spec via state transition `refining → refined` (post Chris ratify checkpoint frontmatter — already `ratified_by_chris: true` per Session 4 §7.5 pre-auth)
- /architect spawned with this spec + checkpoint frontmatter binding_decisions + outcome §7.5 verbatim → emits 03-arch.md + 04-validators.yaml + 05-guidelines.md + 06-tickets.yaml
- /dev-team Session 4 autonomous build per outcome §7.2 + §7.4 cap extended to 3 stories Tier 3 sequencial
- /auditor Session 4 post-developed → CHECKPOINTS C1-C5
- /pm merge → capability promoted (luana-core-campaigns + luana-core-extension-sdk + @luana/extension-sdk) → Story 9 unblocked

## 15. Changelog

- v1 2026-05-12 — /po Opus draft inicial consuming outcome §7.5 binding decisions verbatim. ratified_by_chris pre-auth per Session 4 §7.5.2 D7=B (Stories 8+9 secuencial autonomous, Chris delegated `toma tú todas las decisiones`).
