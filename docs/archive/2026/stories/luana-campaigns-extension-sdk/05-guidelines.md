---
story_id: luana-campaigns-extension-sdk
guidelines_version: 1
last_modified: 2026-05-12
drafted_by: /architect-orchestrator (claude-opus-4-7)
authority: 03-arch.md + 03-arch-be.md + 01-spec.md + outcome §7.5 + checkpoint binding_decisions + Story 6+7 05-guidelines.md precedent
---

# 05-guidelines.md — luana-campaigns-extension-sdk

> **/dev-team reads this BEFORE picking ANY ticket.** R23 nuance: Story 8 `production_code=false` at story level BUT T-5 + T-6 individual tickets touch agentic-adjacent surface (Stories 6+7 frozen registries) → architect promotes to `builder-agentic` Opus eligibility per 03-arch.md §2.2. Other tickets `builder-backend`/`builder-frontend` Sonnet eligible.

## §1. Patterns Required

### §1.1 Lift mode (outcome §7.3 — campaigns Part A)

Same as Stories 5/6/7 §1.1 — verbatim file names + class names + function signatures + public API surface + tests verbatim, preserve DDD layers (domain → infrastructure → application → api), version 0.0.8-alpha.

**Tests verbatim:** 42 test files from `backend/tests/modules/campaigns/` lift to `core/luana-core-campaigns/tests/` — NO test rewrites, NO test skips beyond what AISALESHT already has.

**Coverage threshold:** AISALESHT 43% baseline preserved (V-F-campaigns-1).

### §1.2 Workspace registration (T-1)

Add 3 entries to `~/luana-platform/pyproject.toml`:

```toml
[tool.uv.workspace]
members = [
    "core",
    # (Stories 2-7 — 23 packages already registered)
    # ...
    "core/luana-core-sales-agent",
    # Story 8 (NEW — 3 packages)
    "core/luana-core-campaigns",            # ← INSERT alphabetical (before sales-agent)
    "core/luana-core-extension-sdk",        # ← INSERT alphabetical (after sales-agent)
    "apps/test-brand",                      # ← INSERT after core/ block
    # Brand apps
    "nicolify", "vitalia", "comunify", "lupulo",
]

[tool.uv.sources]
# (Stories 2-7 — 23 entries)
# Story 8 (NEW — 3 entries)
luana-core-campaigns = { workspace = true }
luana-core-extension-sdk = { workspace = true }
test-brand = { workspace = true }
```

**Alphabetical order MUST hold** (V-NF-1 + arch fitness `test_workspace_members_alphabetical_story8.py`).

### §1.3 Extension SDK package skeleton (T-2)

```python
# core/luana-core-extension-sdk/pyproject.toml
[project]
name = "luana-core-extension-sdk"
version = "0.0.8-alpha"
requires-python = ">=3.12"
description = "Luana extension SDK — 18 extension points formalized contract"
dependencies = []       # ★ ZERO workspace deps — pure contract layer ★

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/luana_core_extension_sdk"]

[tool.pytest.ini_options]
pythonpath = ["."]
asyncio_mode = "auto"
```

```
core/luana-core-extension-sdk/
├── pyproject.toml
├── README.md                               # "Luana Extension SDK v0.0.8-alpha — 18 EP signatures (5 EXECUTABLE + 13 SIGNATURE-ONLY)"
├── src/luana_core_extension_sdk/__init__.py
└── tests/__init__.py + tests/unit/__init__.py + tests/architecture/__init__.py
```

Public `__init__.py` exports:

```python
# core/luana-core-extension-sdk/src/luana_core_extension_sdk/__init__.py
from luana_core_extension_sdk.brand_context import BrandContext
from luana_core_extension_sdk.exceptions import (
    DuplicateRegistrationError,
    ExtensionSDKError,
    NamespaceViolationError,
    RegistrationClosedError,
)
from luana_core_extension_sdk.extension_points import ExtensionPointRegistry
from luana_core_extension_sdk.models import (
    AssetTemplateDef, BookingPolicy, BookingResult,
    CampaignStepDef, CampaignTemplateDef, ChannelAdapterDef,
    ExtractorDef, FieldDef, FieldOverride, GuardrailDef, GuardrailResult,
    KbPackDef, LandingTemplateDef, LifecycleStageDef, MetricDef,
    PlanTierDef, PresetPack, SidebarRouteDef, SignupResult, ToolDef,
    WizardStepDef, WorkflowDef,
)
from luana_core_extension_sdk.protocols import (
    FieldOverrideHandler, GuardrailCheck, SignupHandler,
)

__version__ = "0.0.8-alpha"

__all__ = [
    "ExtensionPointRegistry", "BrandContext",
    "ExtensionSDKError", "DuplicateRegistrationError",
    "NamespaceViolationError", "RegistrationClosedError",
    # 18 DataClass models
    "FieldOverride", "FieldDef", "PresetPack", "ToolDef", "WorkflowDef",
    "BookingPolicy", "BookingResult", "SidebarRouteDef", "ExtractorDef",
    "ChannelAdapterDef", "MetricDef", "LandingTemplateDef",
    "CampaignTemplateDef", "CampaignStepDef", "AssetTemplateDef",
    "GuardrailDef", "GuardrailResult", "KbPackDef", "LifecycleStageDef",
    "PlanTierDef", "WizardStepDef", "SignupResult",
    # Protocols
    "FieldOverrideHandler", "GuardrailCheck", "SignupHandler",
]
```

### §1.4 BrandContext + exceptions + models pattern (T-3, T-4)

Per 03-arch-be.md §1.3 verbatim. Use modern 2026 canonical pattern:

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class FooDef:
    ...
```

**Why all three flags:**
- `frozen=True` — CC-5 inmutable cement (raises FrozenInstanceError on mutation)
- `slots=True` — memory efficiency + faster attribute access (Python 3.10+ compatible with frozen; 2026 canonical pattern)
- `kw_only=True` — explicit construction, survives field reordering (Python 3.10+)

Per [Python Dataclasses 2026 guide](https://www.pyblog.in/programming/python-dataclasses-the-complete-2026-guide-from-dataclass-to-slots-frozen-and-__post_init__/) accessed 2026-05-12. Knowledge cutoff Opus 4.7 = Jan 2026; researched live for current state-of-the-art.

### §1.5 ExtensionPointRegistry critical EP-1..EP-5 (T-5 — Opus REQUIRED)

Per 03-arch-be.md §1.3 verbatim. Key invariants:

1. **CC-3 startup-only** — `_closed: bool = False` instance attribute. `close()` sets True. All `register_*` methods call `_enforce_open(ep_id, name)` first → raises RegistrationClosedError if `_closed`.
2. **CC-4 namespace allowlist** — `_ALLOWED_BRAND_SLUGS = frozenset({"nicolify", "vitalia", "comunify", "lupulo", "test-brand"})`. `_enforce_namespace(name, ep_id)` parses `name.split(".", 1)` → first part MUST be in allowlist + non-empty second part. Else raises NamespaceViolationError with accepted list.
3. **CC-4 duplicate** — `_enforce_unique(ep_id, name, mode)` — scans `self._registrations[ep_id]` for matching name; if `mode='append'` and found → DuplicateRegistrationError. If `mode='override'` → bypasses uniqueness, replaces existing record by name.
4. **CC-2 mode** — `_enforce_mode(ep_id, mode)` — ValueError if `mode='override'` on EP-1..EP-16 (only EP-17 + EP-18 permit override).
5. **EP-1 dispatch helper `resolve_field_override`** — invoke all handlers; FIRST non-None wins (deterministic by registration order).
6. **EP-2 dispatch helper `list_offer_preset_packs`** — filter by `pack.applies_to_brand == ctx.brand_slug`.
7. **EP-3 + EP-4** — record DataClass in registry + delegate to injected adapter IF adapter is not None. Adapter wiring is OPTIONAL (test-brand passes None for both).
8. **EP-5 dispatch helper `get_booking_policy`** — lookup by name (exact match).

### §1.6 EP-3 + EP-4 read-only adapter wrappers (T-6 — Opus REQUIRED)

Per 03-arch-be.md §1.4 verbatim. Critical invariants:

1. **Read-only delegation** — adapter calls ONLY `register_*_from_extension` public method on inner registry. If not available → graceful `NotImplementedError`.
2. **Zero private surface access** — V-AG-new-story-8 arch fitness AST parse forbids any attribute access starting with `_dispatch`, `_mutate`, `_internal_`, `_private_`.
3. **Stories 6+7 V-AG-3 golden snapshots continue GREEN** — adapter pattern must NOT introduce new public methods on inner registry, must NOT mutate existing public signature. T-17 verifies via Stories 6+7 arch fitness re-run.
4. **Wiring DEFERRED** — test-brand passes `None` for both adapter args. Stories 11-13 brand bootstraps wire real adapter instances. Story 8 ships ONLY the adapter classes — actual integration with Story 6/7 registries deferred (graceful NotImplementedError path tested).

### §1.7 EP-6..EP-18 backlog signature-only (T-7)

Per 03-arch-be.md §1.3 verbatim. Each `register_*` method:
1. Accepts DataClass / Callable per signature
2. Calls `self._register(ep_id, name, payload, mode)` — registry stores record (CC-3 + CC-4 enforced)
3. Returns None — semantic dispatch deferred v0.2.x

Each `dispatch_*` / `get_*_dispatch` method:
```python
def dispatch_FOO(self, *args, **kwargs) -> Any:
    raise NotImplementedError(
        f"EP-X foo_register is signature-only in v0.1.0; "
        f"semantic dispatch deferred v0.2.x"
    )
```

### §1.8 @luana/extension-sdk TS mirror (T-8 — Sonnet FE)

Per 03-arch-be.md §3.4 + §3.8. **3 TS interfaces only** — EP-6 + EP-10 + EP-18:

```typescript
// core/@luana/extension-sdk/src/brand-context.ts
export interface BrandContext {
  tenantId: string;             // UUID
  brandSlug: 'nicolify' | 'vitalia' | 'comunify' | 'lupulo' | 'test-brand';
  planTier: string;
  locale: string;
  featureFlags: Record<string, boolean>;
  tenantProfileId: string;      // UUID
  verticalKind: 'marketing' | 'medical' | 'creator-economy' | 'gastronomy';
  complianceFlags: Record<string, boolean>;
  piiPolicy: 'standard' | 'medical' | 'creator' | 'gastronomy';
}
```

```typescript
// core/@luana/extension-sdk/src/models.ts
export interface SidebarRouteDef {
  slug: string;                 // `{brandSlug}.{slug}` per CC-4
  label: string;
  icon: string;
  order?: number;
  parentSlug?: string;
  roleRequired?: string;
}

export interface LandingTemplateDef {
  templateId: string;           // `{brandSlug}.{templateId}` per CC-4
  verticalHint: string;
  sectionsSchema: Record<string, unknown>;     // JSON schema
  previewUrl?: string;
}

export interface WizardStepDef {
  stepId: string;               // `{brandSlug}.{stepId}` per CC-4
  title: string;
  componentRef: string;
  prereqs?: string[];
  skippable?: boolean;
  postActionEvent?: string;
}
```

```typescript
// core/@luana/extension-sdk/src/index.ts
export type { BrandContext } from './brand-context';
export type { SidebarRouteDef, LandingTemplateDef, WizardStepDef } from './models';
```

```json
// core/@luana/extension-sdk/package.json
{
  "name": "@luana/extension-sdk",
  "version": "0.0.8-alpha",
  "description": "Luana extension SDK — TypeScript type mirror (EP-6/EP-10/EP-18 FE surface)",
  "main": "src/index.ts",
  "types": "src/index.ts",
  "license": "UNLICENSED",
  "private": true,
  "dependencies": {}
}
```

```json
// core/@luana/extension-sdk/tsconfig.json
{
  "extends": "../tsconfig.json",
  "compilerOptions": {
    "outDir": "./dist",
    "rootDir": "./src",
    "declaration": true,
    "declarationMap": true
  },
  "include": ["src/**/*.ts"]
}
```

**Field naming convention:** Python `snake_case` → TS `camelCase` (per existing pattern in `@luana/api-client` + `@luana/schemas`). V-F-ts-1 arch test handles snake↔camel conversion when comparing field names.

### §1.9 Campaigns lift import path rewrite (sed — T-9..T-13)

```bash
cd ~/luana-platform/core/luana-core-campaigns

# Self-imports
find src tests -name "*.py" -exec sed -i 's|from src\.modules\.campaigns\.|from luana_core_campaigns.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|import src\.modules\.campaigns\.|import luana_core_campaigns.|g' {} \;

# Cross-module Stories 2-7
find src tests -name "*.py" -exec sed -i 's|from src\.modules\.iam\.|from luana_core_iam.|g' {} \;

# Shared → luana-core-platform / observability / events / channels / idempotency
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.agent_observability\.channels\.|from luana_core_channels.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.agent_observability\.|from luana_core_observability.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.domain_events\.|from luana_core_events.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.idempotency\.|from luana_core_idempotency.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.domain\.|from luana_core_platform.domain.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.links\.|from luana_core_platform.links.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.infrastructure\.|from luana_core_platform.infrastructure.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.application\.|from luana_core_platform.application.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.core\.|from luana_core_platform.core.|g' {} \;
```

Verify post-sed:
```bash
grep -rn 'from src\.modules\|from src\.shared\|from src\.core' core/luana-core-campaigns/
# → expected: empty
```

### §1.10 apps/test-brand FastAPI lifespan pattern (T-14)

```python
# apps/test-brand/src/test_brand/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI

from luana_core_extension_sdk import ExtensionPointRegistry
from test_brand.extensions import register_all


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan event — Story 8 §7.5.2 D2=B explicit register pattern.

    1. Construct ExtensionPointRegistry (adapter wiring None for Story 8 — Stories 11-13 wire real)
    2. register_all(registry) — 18 registrations (5 executable + 13 stubs)
    3. registry.close() — CC-3 lock; subsequent register raises RegistrationClosedError
    4. app.state.registry — make available for request handlers (Stories 11-13 retrieve via FastAPI dependency)
    """
    registry = ExtensionPointRegistry(
        sales_agent_tool_registry_adapter=None,         # Story 8 — Stories 11-13 wire real
        copilot_workflow_registry_adapter=None,
    )
    register_all(registry)
    registry.close()
    app.state.registry = registry
    yield
    # No teardown — registry held until process exit


app = FastAPI(lifespan=lifespan, redirect_slashes=False)


@app.get("/health")
async def health():
    return {"status": "ok", "registry_closed": True}
```

```python
# apps/test-brand/src/test_brand/extensions.py
"""Test brand extensions — 5 executable + 13 signature-only stubs per §7.5.2 D6=A."""
from luana_core_extension_sdk import (
    BrandContext, ExtensionPointRegistry,
    # DataClass models
    AssetTemplateDef, BookingPolicy, BookingResult,
    CampaignStepDef, CampaignTemplateDef, ChannelAdapterDef,
    ExtractorDef, FieldDef, FieldOverride, GuardrailDef, GuardrailResult,
    KbPackDef, LandingTemplateDef, LifecycleStageDef, MetricDef,
    PlanTierDef, PresetPack, SidebarRouteDef, SignupResult, ToolDef,
    WizardStepDef, WorkflowDef,
)
from typing import Optional


def register_all(registry: ExtensionPointRegistry) -> None:
    """Register 18 extensions — 5 executable (EP-1..EP-5) + 13 stubs (EP-6..EP-18).

    All names MUST start with 'test-brand.' prefix per CC-4.
    """
    # ── EP-1 executable: field_override ─────────────────────────────────
    def _override_handler(field: FieldDef, ctx: BrandContext) -> Optional[FieldOverride]:
        if field.name == "field_x" and ctx.brand_slug == "test-brand":
            return FieldOverride(name="field_x_overridden", default_value="test")
        return None
    registry.field_override(_override_handler, name="test-brand.field_x_override")

    # ── EP-2 executable: offer_preset_pack_register ─────────────────────
    registry.offer_preset_pack_register(
        PresetPack(
            name="test-brand.smoke_pack",
            presets=(),
            applies_to_brand="test-brand",
            description="Smoke test preset pack",
        )
    )

    # ── EP-3 executable: sales_agent_tool_register (adapter is None — record only) ─
    def _echo_handler(message: str) -> str:
        return f"echo: {message}"
    registry.sales_agent_tool_register(
        ToolDef(
            name="test-brand.echo_tool",
            description="Echo tool for smoke testing",
            input_schema={"type": "object", "properties": {"message": {"type": "string"}}},
            handler=_echo_handler,
            tool_groups=("smoke",),
        )
    )

    # ── EP-4 executable: copilot_workflow_register (adapter is None — record only) ─
    registry.copilot_workflow_register(
        WorkflowDef(
            name="test-brand.smoke_workflow",
            description="Smoke workflow",
            steps=(),
            trigger_event=None,
        )
    )

    # ── EP-5 executable: scheduling_booking_policy_register ─────────────
    def _always_allow_policy(booking: object, ctx: BrandContext) -> BookingResult:
        return BookingResult(allowed=True, reason="smoke test always allows")
    registry.scheduling_booking_policy_register(
        BookingPolicy(
            name="test-brand.always_allow_policy",
            can_confirm=_always_allow_policy,
            priority=0,
        )
    )

    # ── EP-6..EP-18 stubs: register succeeds; dispatch raises NotImplementedError ─

    # EP-6
    registry.sidebar_routes_register(
        SidebarRouteDef(slug="test-brand.smoke_route", label="Smoke", icon="zap", order=99)
    )

    # EP-7
    registry.extractor_register(
        ExtractorDef(
            name="test-brand.smoke_extractor",
            target_module="offer",
            wave_position=99,
            prompt_template_ref="smoke.j2",
            output_schema_ref="SmokeSchema",
        )
    )

    # EP-8
    def _smoke_send(*args, **kwargs): return None
    def _smoke_receive(*args, **kwargs): return None
    def _smoke_format(*args, **kwargs): return None
    registry.channel_adapter_register(
        ChannelAdapterDef(
            channel_slug="test-brand.smoke_channel",
            send=_smoke_send,
            receive=_smoke_receive,
            format_for_channel=_smoke_format,
            target_agent_runtime="sales_agent",
        )
    )

    # EP-9
    registry.metric_register(
        MetricDef(
            name="test-brand.smoke_metric",
            module="analytics",
            aggregation="sum",
            unit="count",
            currency_aware=False,
            stage_assignment="attraction",
            refresh_freq="daily",
            python_compute=lambda: 0,
        )
    )

    # EP-10
    registry.landing_template_register(
        LandingTemplateDef(
            template_id="test-brand.smoke_landing",
            vertical_hint="test",
            sections_schema={"sections": []},
        )
    )

    # EP-11
    registry.campaign_template_register(
        CampaignTemplateDef(
            template_id="test-brand.smoke_drip",
            channel="email",
            steps=(CampaignStepDef(step_id="s1", delay_seconds=0, template_ref="t1"),),
            trigger_event="user.signup",
        )
    )

    # EP-12
    registry.asset_template_register(
        AssetTemplateDef(
            template_id="test-brand.smoke_asset",
            asset_type="image",
            placeholders={"logo_url": "str", "tagline": "str"},
            source_path="templates/smoke.png",
        )
    )

    # EP-13 (pre_send + pre_receive both)
    def _pre_send_check(msg: str, ctx: BrandContext) -> GuardrailResult:
        return GuardrailResult(blocked=False)
    def _pre_receive_check(msg: str, ctx: BrandContext) -> GuardrailResult:
        return GuardrailResult(blocked=False)
    registry.sales_agent_guardrail_register(
        GuardrailDef(
            name="test-brand.smoke_guardrail",
            pre_send_check=_pre_send_check,
            pre_receive_check=_pre_receive_check,
            priority=10,
            mode="warn",
        )
    )

    # EP-14
    registry.copilot_kb_pack_register(
        KbPackDef(
            pack_id="test-brand.smoke_kb",
            documents_path="./kb/",
            embedding_model_ref="text-embedding-3-small",
            qdrant_collection_name="test-brand-smoke",
            tenant_scope="both",
        )
    )

    # EP-15
    registry.crm_lifecycle_stage_register(
        LifecycleStageDef(
            stage_id="test-brand.pending_review",
            label="Pending Review",
            after_stage="signup",
            before_stage="active",
        )
    )

    # EP-16
    def _smoke_signup_handler(clerk_user, ctx: BrandContext) -> SignupResult:
        return SignupResult(status="pending_review", metadata={"reason": "smoke"})
    registry.iam_signup_handler(_smoke_signup_handler, name="test-brand.smoke_signup")

    # EP-17 (override permitted)
    registry.tenant_plan_tier_register(
        PlanTierDef(
            tier_id="test-brand.smoke_tier",
            label="Smoke Tier",
            price_monthly=0.0,
            currency="USD",
            features=(),
            limits={},
        ),
        mode="override",
    )

    # EP-18 (override permitted)
    registry.onboarding_wizard_steps_register(
        WizardStepDef(
            step_id="test-brand.smoke_step",
            title="Smoke",
            component_ref="SmokeStep",
        ),
        mode="override",
    )
```

### §1.11 docs/extension-points.md content (T-16 — Spanish neutro)

Per 01-spec §3.5 + §7.5.4 verbatim. Required sections:

**§1 SDK overview + design principles** — narrative cement of CC-1..CC-5 verbatim from §7.5.1. Each policy gets ~1 paragraph rationale.

**§2 EP-1..EP-5 critical with per-vertical examples** — for each EP:
- Method signature (Python)
- Method signature (TypeScript if applicable for EP-6/EP-10/EP-18)
- **Vitalia example** (medical) — e.g., EP-3 `vitalia.medical_consent_request` tool
- **Comunify example** (creator-economy) — e.g., EP-2 `comunify.creator_offer_pack` preset
- **Lupulo example** (gastronomy) — e.g., EP-5 `lupulo.table_capacity_policy` booking
- Code snippet showing FastAPI lifespan registration

**§3 EP-6..EP-18 backlog signatures** — per-vertical examples + "signature-only v0.1.0, semantic dispatch deferred v0.2.x" note.

**§4 Recipe: Build a vertical agent on top of luana-core** — Vitalia treatment-agent worked example per §7.5.4 verbatim:
- Statement: **"Vertical agent ES un APP del brand, NO un EP del core. NO EP-19."**
- Rationale: vertical agents are brand apps composing core packages, not core extension points.
- Code skeleton `apps/vitalia/agents/treatment_agent/` consuming:
  - luana-core-observability subclass pattern (VitaliaTreatmentCallbackHandler + VitaliaTreatmentObservabilityContext)
  - luana-core-scheduling (job queue + reminders)
  - luana-core-channels via EP-8 (`vitalia.treatment_whatsapp_adapter` registration)
  - luana-core-marketing-kb via EP-14 (`tenant_scope='both'` — medical-protocols brand-scope + clínica internal-KB tenant-scope)
  - luana-core-prompt-cache slot composer (slot 5 BRAND_VOICE via D-T3 BrandVoicePort Story 7)
  - luana-core-extension-sdk for tool (EP-3) + guardrail (EP-13) registration

**§5 Cross-brand learning principle** — §7.5.6 verbatim:
- Brand A invents feature → /pm evaluates if generalizable → if yes, lift to core → brands B/C/D consume via SDK
- NEVER cross-brand direct import
- Example: Vitalia treatment-agent learnings → /pm promotes to `luana-core-engagement-scheduler` → Comunify + Lupulo consume

**Spanish neutro LatAm** applies (per `.claude/rules/spanish-text.md`). NO voseo (tuteo `tú` only). Pre-commit hook validates.

### §1.12 Arch fitness tests (T-17)

12 NEW arch fitness tests per 03-arch-be.md §7. Template same as Story 6+7 — `core/tests/architecture/test_story8_*.py`. AST + path-based + dataclasses-introspection patterns.

### §1.13 Test execution per package + aggregate

After each lift ticket, run isolated:
```bash
cd ~/luana-platform && uv run pytest <path> -x -q --tb=short
```

Final aggregate per V-F-x-2:
```bash
cd ~/luana-platform && uv run pytest core/ apps/ -x -q --tb=short --ignore=core/src \
    --ignore=core/luana-core-copilot/tests/test_streaming_integration.py \
    --ignore=core/luana-core-sales-agent/tests/eval_simulator/ \
    --ignore=core/luana-core-sales-agent/tests/agentic_evals/
```

### §1.14 AISALESHT untouched verification (T-18)

```bash
cd /home/chris/AISALESHT
git diff $BASE_SHA HEAD --name-only -- \
    backend/src/modules/campaigns/ \
    backend/tests/modules/campaigns/
# Expected: empty
```

`$BASE_SHA` = git rev-parse HEAD at Story 8 build start. Capture in checkpoint frontmatter `base_sha` field at state transition refined→ready (T-1 first activity).

## §2. Patterns Forbidden

### §2.1 Lift mode violations (auto-FAIL)

- ❌ Modifying campaigns module file names, class names, function signatures
- ❌ Refactoring DDD layer boundaries during lift
- ❌ Renaming entities, repositories, services
- ❌ Adding new functionality to campaigns engine
- ❌ Modifying coverage threshold (43% baseline preserved)
- ❌ Skipping tests beyond AISALESHT baseline skip pattern

### §2.2 Mutating AISALESHT (auto-FAIL — V-NF-4 cardinal)

- ❌ Any file under `backend/src/modules/campaigns/` READ-ONLY
- ❌ Any file under `backend/tests/modules/campaigns/` READ-ONLY
- ❌ Workspace pyproject.toml additions on AISALESHT side (Story 8 only modifies `~/luana-platform/pyproject.toml`)

### §2.3 SDK design violations (auto-FAIL)

- ❌ Adding methods to `ExtensionPointRegistry` beyond 18 specified (EP-1..EP-18 only). NO EP-19 or higher per §7.5.4.
- ❌ Adding `unregister_*` method (CC-5 inmutable violation)
- ❌ Allowing `mode='override'` on EP-1..EP-16 (only EP-17 + EP-18 permitted per §7.5.3)
- ❌ Allowing bare names (without brand_slug prefix) — CC-4 violation
- ❌ Allowing duplicate name registration within same EP and `mode='append'` — CC-4 violation
- ❌ Allowing register_* call after registry.close() — CC-3 violation
- ❌ Adding workspace dependency to luana-core-extension-sdk (must stay zero-dep contract layer)
- ❌ Modifying BrandContext 9-field shape (§7.5.2 D3 verbatim FROZEN at v0.1.0)
- ❌ BrandContext mutable (must remain `@dataclass(frozen=True, slots=True, kw_only=True)`)

### §2.4 Stories 6+7 frozen registry violations (auto-FAIL — D-T1 cardinal)

- ❌ EP-3 + EP-4 adapter accessing private surface of Stories 6+7 registries (`_dispatch`, `_mutate`, `_internal_*`)
- ❌ Adding new public methods to Story 6 WorkflowRegistry / Story 7 ToolRegistry (must use existing OR raise NotImplementedError gracefully — Stories 11-13 add public surfaces if needed)
- ❌ Mutating Stories 6+7 V-AG-3 golden snapshots (these are byte-stable cement)

### §2.5 Forward-Story coupling (auto-FAIL)

- ❌ luana-core-extension-sdk depending on luana-core-campaigns, luana-core-copilot, luana-core-sales-agent (must stay zero-dep)
- ❌ luana-core-campaigns importing from luana_core_advertising / luana_core_social_media (Story 11+)
- ❌ apps/test-brand depending on anything other than luana-core-extension-sdk + fastapi
- ❌ Anything importing from `src.modules.*` post-sed (lift incomplete)

### §2.6 Anti-mirror discipline (per `.claude/rules/anti-duplication.md`)

- ❌ Mirror ExtensionPointRegistry / BrandContext / 18 DataClass models in any other package (canonical in luana-core-extension-sdk only)
- ❌ Implementing CC enforcement (CC-3 close + CC-4 namespace + CC-5 inmutable) outside ExtensionPointRegistry (single source of truth)

### §2.7 Spanish text violations

- ❌ Voseo in docs/extension-points.md user-facing strings (tuteo only)
- ❌ Voseo in commit messages, code comments visible in API responses, README

### §2.8 EP-19 violations (per §7.5.4)

- ❌ Adding `vertical_agent_register` method to ExtensionPointRegistry
- ❌ Documenting EP-19 as future scope in docs/extension-points.md (explicit forbidden)
- ❌ Treating vertical agents as extension points (they are brand apps composing core packages)

### §2.9 Scope expansion forbidden

Per 01-spec §4 OUT list:
- ❌ EP-6..EP-18 semantic implementations
- ❌ Brand consumer apps (Vitalia/Comunify/Lupulo bootstraps)
- ❌ GH Packages publish pipeline (Story 9)
- ❌ Streamlit admin pages
- ❌ Scheduling concrete provider runtime lift
- ❌ Voice cloning per-tenant
- ❌ AppointmentModel + ProductModel stub cement (RE-ALLOWLIST only)

## §3. Files in Scope

### §3.1 AISALESHT (READ-ONLY source)

**Lift these (campaigns):**
```
backend/src/modules/campaigns/
├── __init__.py
├── domain/                  (12 files)
├── infrastructure/          (29 files: channels + repositories + resilience + models + links + external)
├── application/             (21 files: dtos + ports + services + segment_filter_evaluator)
├── api/                     (8 files: routers + _async_session + _dependencies + _service_factories)
├── observability/           (4 files: persistence/models/llm_call_model)
└── workers/                 (5 files: audit_retention + execution + scheduler_tick + segment_refresh_tick)

backend/tests/modules/campaigns/  (42 test files — verbatim)
```

**NOT lifted (per §4 OUT):**
```
backend/src/modules/scheduling/  ★ scheduling lift deferred ★
backend/src/modules/advertising/  ★ advertising lift deferred ★
backend/src/modules/social_media/  ★ social_media lift deferred ★
backend/src/admin/pages/  ★ Streamlit admin Story 10 nicolify migration ★
```

### §3.2 luana-platform (CREATE)

**NEW Story 8 files:**
- `~/luana-platform/core/luana-core-extension-sdk/{pyproject.toml,README.md,src/luana_core_extension_sdk/**,tests/**}`
- `~/luana-platform/core/luana-core-campaigns/{pyproject.toml,README.md,src/luana_core_campaigns/**,tests/**}`
- `~/luana-platform/apps/test-brand/{pyproject.toml,README.md,src/test_brand/**,tests/**}`
- `~/luana-platform/core/@luana/extension-sdk/{package.json,tsconfig.json,README.md,src/**}`
- `~/luana-platform/core/tests/architecture/test_story8_*.py` (12 new arch fitness tests)
- `~/luana-platform/docs/extension-points.md` (NEW)

**MODIFIED Story 8 files:**
- `~/luana-platform/pyproject.toml` (T-1 — append 3 workspace members + 3 sources entries alphabetical)
- `~/luana-platform/core/DEFERRED-FILES.md` (T-18 — append Story 8 section)

**MODIFIED AISALESHT-side files (allowed only):**
- `/home/chris/AISALESHT/.claude/rules/anti-duplication.md` (T-18 — append Extension SDK row)
- `/home/chris/AISALESHT/.claude/rules/auditor-downstream-regression.md` (T-18 — append Story 8 surface rows)

### §3.3 mechanical recipe (lift)

```bash
# luana-core-campaigns lift
SRC=/home/chris/AISALESHT/backend/src/modules/campaigns
DST_SRC=~/luana-platform/core/luana-core-campaigns/src/luana_core_campaigns

mkdir -p "$DST_SRC"
cp "$SRC"/__init__.py "$DST_SRC/"

for sub in api application domain infrastructure observability workers; do
  [ -e "$SRC/$sub" ] && cp -r "$SRC/$sub" "$DST_SRC/"
done

# Tests verbatim
rsync -av /home/chris/AISALESHT/backend/tests/modules/campaigns/ \
    ~/luana-platform/core/luana-core-campaigns/tests/

# Apply sed per §1.9
cd ~/luana-platform/core/luana-core-campaigns
# ... sed commands per §1.9

# Verify import path migration
grep -rn 'from src\.modules\|from src\.shared\|from src\.core' . | head
# → expected: empty
```

## §4. Skills + Rules to Load

| Skill / Rule | When | Owner |
|---|---|---|
| `backend-expert` | All BE tickets (T-1, T-3, T-4, T-7, T-9..T-13, T-14, T-15, T-16, T-17, T-18) | universal |
| `frontend-expert` | T-8 (@luana/extension-sdk TS mirror) | mandatory |
| `copilot-expert` | T-6 (EP-4 wraps Story 6 WorkflowRegistry — verify byte-stable + V-AG-3 golden snapshot) | mandatory |
| `sales-agent-expert` | T-6 (EP-3 wraps Story 7 ToolRegistry — verify byte-stable + V-AG-3 golden snapshot) | mandatory |
| `tessl__fastapi` | T-14 (apps/test-brand FastAPI lifespan) | mandatory |
| `tessl__graceful-degradation` | T-6 (EP-3/EP-4 adapter NotImplementedError graceful) | mandatory |
| `.claude/rules/anti-duplication.md` | T-5, T-6 (verify ExtensionPointRegistry / BrandContext SSoT cement) + T-18 (append inventory row) | mandatory |
| `.claude/rules/anti-default-flip-audit.md` | Verify Story 8 does NOT flip flag defaults (USE_OUTBOX_PATTERN_* etc.) — N/A status verified | mandatory |
| `.claude/rules/auditor-downstream-regression.md` | T-17 + T-18 (R3 SSoT table append) | mandatory |
| `.claude/rules/tdd-mandatory.md` | All tickets — RED first per layer | mandatory |
| `.claude/rules/parallel-safety.md` | All tickets — single Claude session 4 sequential autonomous | mandatory |
| `.claude/rules/spanish-text.md` | T-16 (docs/extension-points.md) — neutro LatAm enforcement | mandatory |
| `.claude/rules/backend-ddd.md` | T-10..T-13 (campaigns lift DDD layer preservation) | mandatory |
| `.claude/rules/architectural-fitness.md` | T-17 (12 new arch fitness tests Story 8) | mandatory |

## §5. Commit Conventions

```
chore(workspace): register Story 8 luana-core-campaigns + luana-core-extension-sdk + apps/test-brand   # T-1
feat(luana-core-extension-sdk): skeleton + pyproject.toml + README + zero-dep contract layer            # T-2
feat(luana-core-extension-sdk): BrandContext frozen dataclass 9 fields per §7.5.2 D3                    # T-3
feat(luana-core-extension-sdk): exceptions + 18 DataClass models + Protocol interfaces                  # T-4
feat(luana-core-extension-sdk): ExtensionPointRegistry critical EP-1..EP-5 EXECUTABLE + CC enforcement  # T-5
feat(luana-core-extension-sdk): EP-3+EP-4 read-only adapter pattern wraps Stories 6+7 byte-stable       # T-6
feat(luana-core-extension-sdk): EP-6..EP-18 backlog signature-only stubs raise NotImplementedError      # T-7
feat(@luana/extension-sdk): TS type mirror EP-6+EP-10+EP-18 (FE-mirror partial scope)                   # T-8
feat(luana-core-campaigns): skeleton + pyproject.toml + README                                          # T-9
feat(luana-core-campaigns): lift campaigns domain layer (12 files)                                      # T-10
feat(luana-core-campaigns): lift campaigns infrastructure layer (29 files)                              # T-11
feat(luana-core-campaigns): lift campaigns application layer (21 files) + observability                 # T-12
feat(luana-core-campaigns): lift campaigns api + workers (13 files)                                     # T-13
feat(apps/test-brand): FastAPI lifespan + 18 register_all handlers (5 executable + 13 stubs)            # T-14
test(apps/test-brand): smoke pack 10 scenarios D1-D3 + C1-C5 + frozen ctx GREEN                         # T-15
docs(luana-platform): docs/extension-points.md §1-§5 + vertical-agent-recipe + per-vertical examples    # T-16
test(arch): Story 8 12 NEW arch fitness tests (V-NF + V-AG-new-story-8 + V-F-ts + V-F-docs)             # T-17
chore(luana-platform): Story 8 lint + AISALESHT untouched + DEFERRED-FILES + anti-duplication.md + R3   # T-18
```

## §6. Halt criteria

Per checkpoint frontmatter `halt_criteria_session_4` + 01-spec §12 + 03-arch.md §6.

Builders MUST escalate Chris if:
1. Scope expansion needed (campaigns refactor / new EP / extra deferral)
2. EP signature decision surfaces during build NOT covered by §7.5
3. Stories 6+7 V-AG-3 golden snapshots break
4. AISALESHT campaigns touched by accident
5. Auditor REJECTED + 3 auto-fix Opus iter all fail
6. Cumulative session 4 cost crosses $2500 soft check-in
7. Builder cap_reached 10 iter on same ticket
8. Workspace pyproject conflict with parallel session

**NOT a halt:** Adapter wiring discovers Story 6+7 registry surfaces lack `register_*_from_extension` public method → graceful NotImplementedError path, test-brand injects None, defer to Stories 11-13. Per 03-arch-be.md §1.4 design intentional.

## §7. Cost-routing per ticket (R23 + R23 nuance)

Per 03-arch.md §2 + checkpoint binding_decisions:

| Ticket | Owner | Eligibility | Rationale |
|---|---|---|---|
| T-1 workspace register | `builder-backend` | `[sonnet, opus]` | mechanical pyproject append |
| T-2 SDK skeleton | `builder-backend` | `[sonnet, opus]` | pyproject + README + __init__ |
| T-3 BrandContext | `builder-backend` | `[sonnet, opus]` | frozen dataclass + tests |
| T-4 exceptions + models + protocols | `builder-backend` | `[sonnet, opus]` | DataClass models + exception types |
| **T-5 critical EP-1..EP-5 EXECUTABLE** | **`builder-agentic`** | **`[opus]`** | **R23 — CC enforcement runtime + EP-3/EP-4 adapter delegation. Opus REQUIRED.** |
| **T-6 _adapters.py + read-only wrappers** | **`builder-agentic`** | **`[opus]`** | **R23 — touches Stories 6+7 frozen registries semantically. V-AG-3 cardinal. Opus REQUIRED.** |
| T-7 backlog EP-6..EP-18 stubs | `builder-backend` | `[sonnet, opus]` | NotImplementedError dispatch — mechanical |
| T-8 TS mirror | `builder-frontend` | `[sonnet, opus]` | 3 TS interfaces, zero runtime |
| T-9 campaigns skeleton | `builder-backend` | `[sonnet, opus]` | pyproject + README |
| T-10..T-13 campaigns lift | `builder-backend` | `[sonnet, opus]` | mechanical lift mode §7.3 |
| T-14 apps/test-brand FastAPI | `builder-backend` | `[sonnet, opus]` | FastAPI lifespan + register_all |
| T-15 smoke tests | `builder-backend` | `[sonnet, opus]` | pytest scenarios |
| T-16 docs | `builder-backend` | `[sonnet, opus]` | Markdown content |
| T-17 arch fitness | `builder-backend` | `[sonnet, opus]` | 12 NEW pytest files |
| T-18 finalization | `builder-backend` | `[sonnet, opus]` | lint + git diff verify + rule appends |

**Opus required:** T-5 + T-6 = 2 tickets (R23 trigger).
**Sonnet eligible:** 16 tickets (mechanical/contract surface, not agentic runtime).

## §8. Story 6 + Story 7 frozen registry adapter wiring (CRITICAL)

Per 03-arch-be.md §1.4 + §6 halt criterion #8.

**T-6 builder-agentic Opus discovers via audit grep:**
```bash
grep -rn "register_tool_from_extension\|register_workflow_from_extension" \
    ~/luana-platform/core/luana-core-sales-agent/ \
    ~/luana-platform/core/luana-core-copilot/ 2>/dev/null
```

If these public methods EXIST on Story 7 ToolRegistry / Story 6 WorkflowRegistry → adapter implementation invokes them.

If NOT EXIST (likely current state — Stories 6+7 did not pre-stage these methods) → adapter classes raise `NotImplementedError("Story 7 ToolRegistry lacks public `register_tool_from_extension` method")` gracefully.

**Story 8 test-brand smoke pack injects `None` for both adapter args** (per §1.10 main.py lifespan). EP-3 + EP-4 record DataClass in SDK registry only; adapter delegation is no-op because adapter is None.

**Stories 11-13 brand bootstraps wire real adapters** by:
1. Adding `register_tool_from_extension` public method to luana-core-sales-agent ToolRegistry (separate sub-architect ticket per brand)
2. Adding `register_workflow_from_extension` public method to luana-core-copilot WorkflowRegistry (idem)
3. Wiring `ExtensionPointRegistry(sales_agent_tool_registry_adapter=_SalesAgentToolRegistryAdapter(tool_registry_instance), ...)` in brand app composition root

Auditor T-17 verifies:
- EP-3/EP-4 record DataClass in registry correctly (test-brand smoke V-F-test-brand-1)
- Adapter classes have `register_extension_tool` / `register_extension_workflow` methods that raise NotImplementedError gracefully when inner registry lacks public surface (T-6 unit test)
- V-AG-3 Story 6 + Story 7 golden snapshots continue GREEN (V-AG-3-story-6 + V-AG-3-story-7 validators)

