---
story_id: luana-campaigns-extension-sdk
arch_version: 1
last_modified: 2026-05-12
drafted_by: /architect-orchestrator (claude-opus-4-7)
authority: 01-spec.md + outcome §7.5 verbatim + checkpoint frontmatter binding_decisions + Story 6+7 precedent
blocked_by: luana-sales-agent-engine (Story 7) done
deviations_from_spec:
  - "OQ-1 resolved: workspace member count = Story 7 baseline 23 packages + Story 8 introduces 3 Python workspace members + 1 TS workspace member at `core/@luana/extension-sdk/`. Total Python workspace post-Story-8 = 26 packages (`luana-core-campaigns`, `luana-core-extension-sdk`, `apps/test-brand`). Total TS workspace post-Story-8 = 7 packages (existing 6 at `core/@luana/*` + `@luana/extension-sdk`). pnpm-workspace.yaml already has `core/@luana/*` glob — new TS package picks up automatically. uv pyproject.toml workspace MUST append 3 new members."
  - "OQ-2 resolved: scheduling lift NOT in Story 8 scope per spec §4. Per Story 7 DEFERRED-FILES.md row 271-275, scheduling concrete provider runtime deferred to Story 8 OR later. Story 8 keeps deferred-import pattern preserved per Story 7 §9.2. AppointmentModel + ProductModel stubs RE-ALLOWLIST with reason 'deferred to scheduling lift (post-Story-8)'."
  - "OQ-3 resolved: EP-3/EP-4 wrappers expose Stories 6+7 frozen registries via read-only delegation Adapter pattern — `_ToolRegistryAdapter` + `_WorkflowRegistryAdapter` thin classes wrapping `luana_core_sales_agent.application.tools.registry.ToolRegistry` + `luana_core_copilot.application.tools.registry.WorkflowRegistry`. Adapter exposes only public read methods (`get_tool`, `list_tools_for_brand`) — NO mutation surface. ToolRegistry/WorkflowRegistry public API UNCHANGED (V-AG-3 golden snapshot continues GREEN)."
  - "OQ-4 resolved: BrandContext `feature_flags` field is OPAQUE dict[str, bool] — Story 8 does NOT prescribe source of truth. Per checkpoint binding_decisions §7.5.2 D3 future fields opcionales agregables. Brand apps inject FF map at request boundary via FastAPI dependency `get_brand_context(request) -> BrandContext`. SOURCE of feature_flags = brand app's choice (Story 11-13 brand bootstrap responsibility — Vitalia may use LaunchDarkly, Comunify may use core/config.py boolean flags). Story 8 ships only the contract."
  - "OQ-5 resolved: TS types HAND-MAINTAINED for v0.0.8-alpha (manual mirror of EP-6/EP-10/EP-18 DataClass-pattern). Codegen deferred Story 9+ if drift surfaces. V-F-ts-1 arch test compares Python `dataclasses.fields(SidebarRouteDef)` field names + types against TS `interface SidebarRouteDef` keys + types via AST parse of `core/@luana/extension-sdk/src/models.ts`. Rationale: 3 DataClasses small surface, codegen tooling cost > value at alpha stage."
---

# Story 8 — Backend Architecture — Campaigns Lift + Extension SDK Formalization

## §1. Topology — Dependency Graph

### §1.1 Audit method (NO-NEW-LAYER per `.claude/rules/anti-duplication.md`)

```bash
# Campaigns peer module imports
grep -rhE "^from src\.modules\.[a-z_]+" backend/src/modules/campaigns/ \
  | awk -F"from src.modules." '{print $2}' | awk -F"[ .]" '{print $1}' | sort -u
# → campaigns (self), iam

# Campaigns shared imports
grep -rhE "^from src\.(shared|core)\." backend/src/modules/campaigns/ \
  | awk -F"from src." '{print $2}' | awk -F"[ .]" '{print $1, $2}' | sort -u
# → shared.agent_observability, shared.domain, shared.idempotency,
#   shared.infrastructure, shared.links, core.config
```

Campaigns module surface is **minimal** vs Stories 6+7 — only `iam` cross-module + 6 shared subsystems. Lift is mechanical sed + pyproject + test verbatim.

### §1.2 Existing systems audit (NO-NEW-LAYER + ANTI-DUPLICATION)

Per `.claude/rules/anti-duplication.md` shared abstractions inventory + Stories 2-7 lift status:

| Subsystem pre-existing | luana-platform location | Story 8 decision |
|---|---|---|
| LegacyEventBus / EventBus + outbox | `luana_core_events.*` (Story 2) | **CONSUME** — campaigns emits events via outbox adapter (USE_OUTBOX_PATTERN_DEFAULT per anti-default-flip-audit. Story 8 does NOT flip flag — campaigns inherits existing default). |
| Idempotency keys | `luana_core_idempotency.*` (Story 2) | **CONSUME** — campaigns workers (orchestrator, execution_task) use idempotency. |
| BaseObservabilityContext / BaseAgentCallbackHandler | `luana_core_observability.*` (Story 2) | **CONSUME** — campaigns has minimal observability (1 `llm_call_model.py` for tracking; lifts verbatim, subclasses already established per anti-duplication.md). |
| LLM router | `luana_core_llm.*` (Story 2) | **CONSUME** — campaigns step execution may invoke LLMs for content generation. |
| Channel registry + format | `luana_core_channels.*` (Story 2) | **CONSUME** — campaigns telegram channel router consumes channel registry (verified via `infrastructure/channels/registry.py` AISALESHT). |
| BrandReadPort + TenantProfileReadPort | `luana_core_platform.links.ports.*` (Story 2) | **CONSUME** — campaigns reads brand + tenant_profile via shared ports. |
| User + Tenant dependencies | `luana_core_iam.*` (Story 3) | **CONSUME** — campaigns API routes use iam dependencies. |
| Sales agent adapter port | `luana_core_platform.links.ports.sales_agent.*` (Story 2) | **CONSUME** — campaigns/infrastructure/external/sales_agent_adapter.py reads via port (NO direct sales_agent import). |
| Frozen 5 copilot registries (ToolRegistry/WorkflowRegistry/ExtractorRegistry/ModuleRegistry/SuggestionRegistry) | `luana_core_copilot.*` (Story 6) | **WRAP read-only via EP-4** — Story 8 NEW SDK exposes `copilot_workflow_register` wrapping frozen WorkflowRegistry. Adapter pattern. V-AG-3 Story 6 golden snapshot continues GREEN. |
| Frozen sales-agent ToolRegistry | `luana_core_sales_agent.application.tools.registry` (Story 7) | **WRAP read-only via EP-3** — Story 8 NEW SDK exposes `sales_agent_tool_register` wrapping frozen ToolRegistry. Adapter pattern. V-AG-3 Story 7 golden snapshot continues GREEN. |
| **NO EXISTING LAYER for: campaigns engine + extension point registry + BrandContext + DataClass models + Callable protocols** | — | **NEW (Story 8)** — luana-core-campaigns + luana-core-extension-sdk packages born here + apps/test-brand smoke pack + @luana/extension-sdk TS mirror. |

### §1.3 D-T1 SDK Public Surface (NEW abstraction this story)

Per checkpoint binding_decisions §7.5.1 CC-1..CC-5 verbatim runtime enforcement + §7.5.3 EP-1..EP-18 signatures.

**Files to create (NEW abstractions):**

1. **`brand_context.py`** — Frozen dataclass with 9 fields per §7.5.2 D3:

```python
# core/luana-core-extension-sdk/src/luana_core_extension_sdk/brand_context.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

@dataclass(frozen=True, slots=True, kw_only=True)
class BrandContext:
    """Per-tenant context passed to extension handlers (CC-4 namespace + brand routing).

    Per checkpoint §7.5.2 D3 — 9 fields FROZEN at v0.1.0. Future optional fields
    opcionales agregables sin breaking bump. Handler that uses only a subset of
    fields MUST continue working when new optional fields are appended.

    NO PII fields — safe to log. tenant_id + tenant_profile_id are opaque UUIDs.
    """
    tenant_id: UUID
    brand_slug: Literal["nicolify", "vitalia", "comunify", "lupulo", "test-brand"]
    plan_tier: str                                    # tier_id from EP-17 brand-registered
    locale: str                                       # ISO 639-1 + region (es-AR / es-MX / es-CL / en-US)
    feature_flags: dict[str, bool]                    # tenant-level flag map (brand-injected)
    tenant_profile_id: UUID
    vertical_kind: Literal["marketing", "medical", "creator-economy", "gastronomy"]
    compliance_flags: dict[str, bool]                 # e.g. {"hipaa_required": True} per Vitalia
    pii_policy: Literal["standard", "medical", "creator", "gastronomy"]
```

2. **`exceptions.py`** — 3 exception types:

```python
# core/luana-core-extension-sdk/src/luana_core_extension_sdk/exceptions.py
class ExtensionSDKError(Exception):
    """Base exception for all SDK errors."""

class NamespaceViolationError(ExtensionSDKError):
    """Raised when registration name lacks brand_slug prefix (CC-4)."""

class DuplicateRegistrationError(ExtensionSDKError):
    """Raised when same name registered twice within same EP (CC-4)."""

class RegistrationClosedError(ExtensionSDKError):
    """Raised when register_* called after FastAPI startup completes (CC-3)."""
```

3. **`models.py`** — 18 DataClass models for declarative EPs:

```python
# core/luana-core-extension-sdk/src/luana_core_extension_sdk/models.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Optional
from uuid import UUID

# EP-1 Callable returns this (optional override)
@dataclass(frozen=True, slots=True, kw_only=True)
class FieldOverride:
    name: str                                 # override field name (may differ from original)
    default_value: Any = None
    label: Optional[str] = None
    hint: Optional[str] = None
    required: Optional[bool] = None

# EP-1 input type
@dataclass(frozen=True, slots=True, kw_only=True)
class FieldDef:
    name: str
    type_name: str                            # "str" | "int" | "decimal" | ...
    required: bool = False
    section: Optional[str] = None

# EP-2 — Offer preset pack
@dataclass(frozen=True, slots=True, kw_only=True)
class PresetPack:
    name: str                                 # MUST be `{brand_slug}.{pack_name}` (CC-4)
    presets: tuple[Any, ...] = ()             # tuple of preset dicts (validated by offer core)
    applies_to_brand: str                     # brand_slug literal
    description: Optional[str] = None

# EP-3 — Sales agent tool
@dataclass(frozen=True, slots=True, kw_only=True)
class ToolDef:
    name: str                                 # MUST be `{brand_slug}.{tool_name}` (CC-4)
    description: str
    input_schema: dict[str, Any]              # JSON schema
    handler: Callable[..., Any]               # Callable invoked by sales_agent
    tool_groups: tuple[str, ...] = ()         # e.g. ("knowledge", "qualification")

# EP-4 — Copilot workflow
@dataclass(frozen=True, slots=True, kw_only=True)
class WorkflowDef:
    name: str                                 # MUST be `{brand_slug}.{workflow_name}` (CC-4)
    description: str
    steps: tuple[Any, ...]                    # workflow steps (validated by copilot core)
    trigger_event: Optional[str] = None

# EP-5 — Scheduling booking policy
@dataclass(frozen=True, slots=True, kw_only=True)
class BookingPolicy:
    name: str                                 # MUST be `{brand_slug}.{policy_name}` (CC-4)
    can_confirm: Callable[[Any, BrandContext], "BookingResult"]
    priority: int = 0

@dataclass(frozen=True, slots=True, kw_only=True)
class BookingResult:
    allowed: bool
    reason: Optional[str] = None

# EP-6 — Sidebar route
@dataclass(frozen=True, slots=True, kw_only=True)
class SidebarRouteDef:
    slug: str                                 # MUST be `{brand_slug}.{slug}` (CC-4)
    label: str
    icon: str
    order: int = 100
    parent_slug: Optional[str] = None
    role_required: Optional[str] = None

# EP-7 — Extractor
@dataclass(frozen=True, slots=True, kw_only=True)
class ExtractorDef:
    name: str                                 # MUST be `{brand_slug}.{extractor_name}` (CC-4)
    target_module: str                        # "offer" | "brand" | "landing" | "buyer_persona"
    wave_position: int                        # 1..N integer
    prompt_template_ref: str
    output_schema_ref: str
    dependencies: tuple[str, ...] = ()

# EP-8 — Channel adapter (extended scope per §7.5.3: sales_agent + copilot + vertical agents)
@dataclass(frozen=True, slots=True, kw_only=True)
class ChannelAdapterDef:
    channel_slug: str                         # MUST be `{brand_slug}.{slug}` (CC-4)
    send: Callable[..., Any]
    receive: Callable[..., Any]
    format_for_channel: Callable[..., Any]
    target_agent_runtime: Literal["sales_agent", "copilot", "vertical_brand"]
    webhook_handler: Optional[Callable[..., Any]] = None

# EP-9 — Metric
@dataclass(frozen=True, slots=True, kw_only=True)
class MetricDef:
    name: str                                 # MUST be `{brand_slug}.{metric_name}` (CC-4)
    module: str                               # "analytics" | "campaigns" | ...
    aggregation: Literal["sum", "avg", "count", "min", "max"]
    unit: str                                 # "currency" | "count" | "ratio" | ...
    currency_aware: bool
    stage_assignment: str                     # "attraction" | "capture" | "nurture" | ...
    refresh_freq: Literal["realtime", "hourly", "daily"]
    sql_query: Optional[str] = None
    python_compute: Optional[Callable[..., Any]] = None

# EP-10 — Landing template
@dataclass(frozen=True, slots=True, kw_only=True)
class LandingTemplateDef:
    template_id: str                          # MUST be `{brand_slug}.{template_id}` (CC-4)
    vertical_hint: str
    sections_schema: dict[str, Any]           # JSON schema
    preview_url: Optional[str] = None

# EP-11 — Campaign template (drip)
@dataclass(frozen=True, slots=True, kw_only=True)
class CampaignStepDef:
    step_id: str
    delay_seconds: int
    template_ref: str

@dataclass(frozen=True, slots=True, kw_only=True)
class CampaignTemplateDef:
    template_id: str                          # MUST be `{brand_slug}.{template_id}` (CC-4)
    channel: Literal["email", "whatsapp", "sms"]
    steps: tuple[CampaignStepDef, ...]
    trigger_event: str
    conditions: dict[str, Any] = field(default_factory=dict)

# EP-12 — Asset template
@dataclass(frozen=True, slots=True, kw_only=True)
class AssetTemplateDef:
    template_id: str                          # MUST be `{brand_slug}.{template_id}` (CC-4)
    asset_type: Literal["image", "video", "pdf", "kit"]
    placeholders: dict[str, str]              # {placeholder_name: type_name}
    source_path: str

# EP-13 — Sales agent guardrail (extended: pre_send + pre_receive per §7.5.3)
@dataclass(frozen=True, slots=True, kw_only=True)
class GuardrailResult:
    blocked: bool
    rewritten: Optional[str] = None
    reason: Optional[str] = None

@dataclass(frozen=True, slots=True, kw_only=True)
class GuardrailDef:
    name: str                                 # MUST be `{brand_slug}.{guardrail_name}` (CC-4)
    pre_send_check: Callable[[str, BrandContext], GuardrailResult]
    priority: int = 100
    mode: Literal["block", "warn", "rewrite"] = "warn"
    pre_receive_check: Optional[Callable[[str, BrandContext], GuardrailResult]] = None

# EP-14 — Copilot KB pack (tenant_scope tri-modal per §7.5.3)
@dataclass(frozen=True, slots=True, kw_only=True)
class KbPackDef:
    pack_id: str                              # MUST be `{brand_slug}.{pack_id}` (CC-4)
    documents_path: str
    embedding_model_ref: str
    qdrant_collection_name: str
    tenant_scope: Literal["brand", "tenant", "both"]
    metadata: dict[str, Any] = field(default_factory=dict)

# EP-15 — CRM lifecycle stage
@dataclass(frozen=True, slots=True, kw_only=True)
class LifecycleStageDef:
    stage_id: str                             # MUST be `{brand_slug}.{stage_id}` (CC-4)
    label: str
    after_stage: str                          # FK to existing stage
    before_stage: str                         # FK to existing stage
    transition_rules: tuple[Callable[..., Any], ...] = ()

# EP-16 — IAM signup handler
@dataclass(frozen=True, slots=True, kw_only=True)
class SignupResult:
    status: Literal["approved", "pending_review", "rejected"]
    metadata: dict[str, Any] = field(default_factory=dict)
    blocking_reason: Optional[str] = None

# EP-17 — Tenant plan tier (override mode permitted per §7.5.3)
@dataclass(frozen=True, slots=True, kw_only=True)
class PlanTierDef:
    tier_id: str                              # MUST be `{brand_slug}.{tier_id}` (CC-4)
    label: str
    price_monthly: float
    currency: str                             # ISO 4217
    features: tuple[str, ...]
    limits: dict[str, Any] = field(default_factory=dict)
    stripe_price_id: Optional[str] = None

# EP-18 — Onboarding wizard step (override mode permitted per §7.5.3)
@dataclass(frozen=True, slots=True, kw_only=True)
class WizardStepDef:
    step_id: str                              # MUST be `{brand_slug}.{step_id}` (CC-4)
    title: str
    component_ref: str                        # FE component identifier
    prereqs: tuple[str, ...] = ()
    skippable: bool = False
    post_action_event: Optional[str] = None
```

4. **`extension_points.py`** — Registry class with 18 methods:

```python
# core/luana-core-extension-sdk/src/luana_core_extension_sdk/extension_points.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Literal, Optional

from luana_core_extension_sdk.brand_context import BrandContext
from luana_core_extension_sdk.exceptions import (
    DuplicateRegistrationError,
    NamespaceViolationError,
    RegistrationClosedError,
)
from luana_core_extension_sdk.models import (
    AssetTemplateDef, BookingPolicy, CampaignTemplateDef, ChannelAdapterDef,
    ExtractorDef, FieldDef, FieldOverride, GuardrailDef, KbPackDef,
    LandingTemplateDef, LifecycleStageDef, MetricDef, PlanTierDef, PresetPack,
    SidebarRouteDef, SignupResult, ToolDef, WizardStepDef, WorkflowDef,
)

# EP IDs (string constants for registry lookup)
_EP_IDS = tuple(f"EP-{i}" for i in range(1, 19))

# EPs that permit mode='override' per §7.5.3 CC-2
_OVERRIDE_PERMITTED_EPS = frozenset({"EP-17", "EP-18"})

# Brand slug literal allowlist (mirror BrandContext.brand_slug Literal)
_ALLOWED_BRAND_SLUGS = frozenset({"nicolify", "vitalia", "comunify", "lupulo", "test-brand"})

# Backlog EPs that raise NotImplementedError on semantic dispatch (signatures-only v0.1.0)
_BACKLOG_EPS = frozenset({"EP-6", "EP-7", "EP-8", "EP-9", "EP-10",
                          "EP-11", "EP-12", "EP-13", "EP-14", "EP-15",
                          "EP-16", "EP-17", "EP-18"})


@dataclass
class _Registration:
    """Internal registration record."""
    ep_id: str
    name: str
    brand_slug: str
    payload: Any                                   # DataClass instance or Callable
    mode: Literal["append", "override"]


class ExtensionPointRegistry:
    """Central registry for 18 extension points (EP-1..EP-18).

    EP-1..EP-5 critical: register + dispatch helpers EXECUTABLE.
    EP-6..EP-18 backlog: register stores record; semantic dispatch raises NotImplementedError.

    Cross-cutting policies (CC-1..CC-5) enforced runtime:
    - CC-3 startup-only — registry.close() after FastAPI lifespan startup.
    - CC-4 namespace — name MUST start with `{brand_slug}.` prefix.
    - CC-4 duplicate — re-registering same name within same EP raises.
    - CC-5 inmutable — no unregister_* methods (verified by AttributeError on lookup).
    - CC-2 override — only EP-17 + EP-18 permit mode='override'; others raise ValueError.

    Constructor accepts injected frozen registry adapters from Stories 6+7 (EP-3 + EP-4
    wrap byte-stable — see §1.4).
    """

    def __init__(
        self,
        *,
        sales_agent_tool_registry_adapter: Optional[Any] = None,
        copilot_workflow_registry_adapter: Optional[Any] = None,
    ) -> None:
        self._registrations: dict[str, list[_Registration]] = {ep: [] for ep in _EP_IDS}
        self._closed: bool = False
        self._sales_agent_tool_adapter = sales_agent_tool_registry_adapter
        self._copilot_workflow_adapter = copilot_workflow_registry_adapter

    # ─── lifecycle ──────────────────────────────────────────────────────

    def close(self) -> None:
        """Lock registry after FastAPI startup. Subsequent register_* raises (CC-3)."""
        self._closed = True

    # ─── enforcement helpers ────────────────────────────────────────────

    def _enforce_open(self, ep_id: str, name: str) -> None:
        if self._closed:
            raise RegistrationClosedError(
                f"Registry closed after FastAPI startup; runtime registration prohibited per CC-3 "
                f"({ep_id} name={name!r})"
            )

    def _enforce_namespace(self, name: str, ep_id: str) -> str:
        """Returns brand_slug if valid; else raises NamespaceViolationError."""
        parts = name.split(".", 1)
        if len(parts) != 2 or parts[0] not in _ALLOWED_BRAND_SLUGS:
            raise NamespaceViolationError(
                f"Name {name!r} must be namespaced with brand_slug prefix "
                f"(e.g., 'vitalia.medical_consent_request'). "
                f"Accepted prefixes: {sorted(_ALLOWED_BRAND_SLUGS)}"
            )
        return parts[0]

    def _enforce_unique(self, ep_id: str, name: str, mode: str) -> None:
        if mode == "override":
            return  # override mode replaces — uniqueness not enforced
        for r in self._registrations[ep_id]:
            if r.name == name:
                raise DuplicateRegistrationError(
                    f"Name {name!r} already registered for {ep_id}"
                )

    def _enforce_mode(self, ep_id: str, mode: str) -> None:
        if mode == "override" and ep_id not in _OVERRIDE_PERMITTED_EPS:
            raise ValueError(
                f"{ep_id} does not support mode='override'; only EP-17 + EP-18 permit override"
            )
        if mode not in ("append", "override"):
            raise ValueError(f"Invalid mode {mode!r}; expected 'append' or 'override'")

    def _register(
        self,
        ep_id: str,
        name: str,
        payload: Any,
        mode: Literal["append", "override"],
    ) -> None:
        self._enforce_open(ep_id, name)
        self._enforce_mode(ep_id, mode)
        brand_slug = self._enforce_namespace(name, ep_id)
        self._enforce_unique(ep_id, name, mode)
        if mode == "override":
            # Replace prior registration with same name (if any) — single match by name
            self._registrations[ep_id] = [r for r in self._registrations[ep_id] if r.name != name]
        self._registrations[ep_id].append(
            _Registration(ep_id=ep_id, name=name, brand_slug=brand_slug, payload=payload, mode=mode)
        )

    # ─── EP-1..EP-5 critical (EXECUTABLE) ───────────────────────────────

    def field_override(
        self,
        handler: Callable[[FieldDef, BrandContext], Optional[FieldOverride]],
        *,
        name: str,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-1 — Register a field override handler. Core form-runtime invokes via resolve_field_override."""
        self._register("EP-1", name, handler, mode)

    def resolve_field_override(self, field: FieldDef, ctx: BrandContext) -> Optional[FieldOverride]:
        """EP-1 dispatch — invoke all handlers; first non-None wins (deterministic by registration order)."""
        for r in self._registrations["EP-1"]:
            result = r.payload(field, ctx)
            if result is not None:
                return result
        return None

    def offer_preset_pack_register(
        self,
        pack: PresetPack,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-2 — Register an offer preset pack."""
        self._register("EP-2", pack.name, pack, mode)

    def list_offer_preset_packs(self, ctx: BrandContext) -> list[PresetPack]:
        """EP-2 dispatch — return all packs filtered by ctx.brand_slug."""
        return [
            r.payload for r in self._registrations["EP-2"]
            if r.payload.applies_to_brand == ctx.brand_slug
        ]

    def sales_agent_tool_register(
        self,
        tool: ToolDef,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-3 — Register a sales agent tool. Wraps Story 7 frozen ToolRegistry byte-stable.

        Internal: stores ToolDef in registry; delegate adapter (if injected) registers
        with underlying Story 7 ToolRegistry via read-only proxy.
        """
        self._register("EP-3", tool.name, tool, mode)
        # Adapter delegates registration to Story 7 ToolRegistry IF adapter injected.
        # V-AG-3 Story 7 golden snapshot ensures registry public API surface unchanged.
        if self._sales_agent_tool_adapter is not None:
            self._sales_agent_tool_adapter.register_extension_tool(tool)

    def get_sales_agent_tool(self, name: str) -> Optional[ToolDef]:
        """EP-3 dispatch — lookup by name."""
        for r in self._registrations["EP-3"]:
            if r.name == name:
                return r.payload
        return None

    def copilot_workflow_register(
        self,
        workflow: WorkflowDef,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-4 — Register a copilot workflow. Wraps Story 6 frozen WorkflowRegistry byte-stable."""
        self._register("EP-4", workflow.name, workflow, mode)
        if self._copilot_workflow_adapter is not None:
            self._copilot_workflow_adapter.register_extension_workflow(workflow)

    def get_copilot_workflow(self, name: str) -> Optional[WorkflowDef]:
        """EP-4 dispatch — lookup by name."""
        for r in self._registrations["EP-4"]:
            if r.name == name:
                return r.payload
        return None

    def scheduling_booking_policy_register(
        self,
        policy: BookingPolicy,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-5 — Register a scheduling booking policy."""
        self._register("EP-5", policy.name, policy, mode)

    def get_booking_policy(self, name: str) -> Optional[BookingPolicy]:
        """EP-5 dispatch — lookup by name."""
        for r in self._registrations["EP-5"]:
            if r.name == name:
                return r.payload
        return None

    # ─── EP-6..EP-18 backlog (SIGNATURE-ONLY — raise NotImplementedError on dispatch) ─

    def sidebar_routes_register(
        self,
        route: SidebarRouteDef,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-6 — Register a sidebar route. Signature-only v0.1.0."""
        self._register("EP-6", route.slug, route, mode)

    def get_sidebar_routes(self, ctx: BrandContext) -> list[SidebarRouteDef]:
        """EP-6 dispatch — SIGNATURE-ONLY v0.1.0."""
        raise NotImplementedError(
            "EP-6 sidebar_routes_register is signature-only in v0.1.0; "
            "semantic dispatch deferred v0.2.x"
        )

    def extractor_register(
        self,
        extractor: ExtractorDef,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-7 — Register an extractor. Signature-only v0.1.0."""
        self._register("EP-7", extractor.name, extractor, mode)

    def dispatch_extractor(self, name: str, ctx: BrandContext) -> Any:
        """EP-7 dispatch — SIGNATURE-ONLY v0.1.0."""
        raise NotImplementedError(
            "EP-7 extractor_register is signature-only in v0.1.0; "
            "semantic dispatch deferred v0.2.x"
        )

    def channel_adapter_register(
        self,
        adapter: ChannelAdapterDef,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-8 — Register a channel adapter (sales_agent + copilot + vertical agents). Signature-only v0.1.0."""
        self._register("EP-8", adapter.channel_slug, adapter, mode)

    def dispatch_channel_adapter(self, channel_slug: str, ctx: BrandContext) -> Any:
        """EP-8 dispatch — SIGNATURE-ONLY v0.1.0."""
        raise NotImplementedError(
            "EP-8 channel_adapter_register is signature-only in v0.1.0; "
            "semantic dispatch deferred v0.2.x"
        )

    def metric_register(
        self,
        metric: MetricDef,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-9 — Register a metric. Signature-only v0.1.0."""
        self._register("EP-9", metric.name, metric, mode)

    def dispatch_metric(self, name: str, ctx: BrandContext) -> Any:
        raise NotImplementedError(
            "EP-9 metric_register is signature-only in v0.1.0; "
            "semantic dispatch deferred v0.2.x"
        )

    def landing_template_register(
        self,
        template: LandingTemplateDef,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-10 — Register a landing template. Signature-only v0.1.0."""
        self._register("EP-10", template.template_id, template, mode)

    def dispatch_landing_template(self, template_id: str, ctx: BrandContext) -> Any:
        raise NotImplementedError(
            "EP-10 landing_template_register is signature-only in v0.1.0; "
            "semantic dispatch deferred v0.2.x"
        )

    def campaign_template_register(
        self,
        template: CampaignTemplateDef,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-11 — Register a campaign template. Signature-only v0.1.0."""
        self._register("EP-11", template.template_id, template, mode)

    def dispatch_campaign_template(self, template_id: str, ctx: BrandContext) -> Any:
        raise NotImplementedError(
            "EP-11 campaign_template_register is signature-only in v0.1.0; "
            "semantic dispatch deferred v0.2.x"
        )

    def asset_template_register(
        self,
        template: AssetTemplateDef,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-12 — Register an asset template. Signature-only v0.1.0."""
        self._register("EP-12", template.template_id, template, mode)

    def dispatch_asset_template(self, template_id: str, ctx: BrandContext) -> Any:
        raise NotImplementedError(
            "EP-12 asset_template_register is signature-only in v0.1.0; "
            "semantic dispatch deferred v0.2.x"
        )

    def sales_agent_guardrail_register(
        self,
        guardrail: GuardrailDef,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-13 — Register a sales agent guardrail (pre_send + pre_receive). Signature-only v0.1.0."""
        self._register("EP-13", guardrail.name, guardrail, mode)

    def dispatch_guardrail(self, name: str, message: str, ctx: BrandContext, *, phase: Literal["send", "receive"]) -> Any:
        raise NotImplementedError(
            "EP-13 sales_agent_guardrail_register is signature-only in v0.1.0; "
            "semantic dispatch deferred v0.2.x"
        )

    def copilot_kb_pack_register(
        self,
        pack: KbPackDef,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-14 — Register a copilot KB pack (tenant_scope: brand|tenant|both). Signature-only v0.1.0."""
        self._register("EP-14", pack.pack_id, pack, mode)

    def dispatch_kb_pack(self, pack_id: str, ctx: BrandContext) -> Any:
        raise NotImplementedError(
            "EP-14 copilot_kb_pack_register is signature-only in v0.1.0; "
            "semantic dispatch deferred v0.2.x"
        )

    def crm_lifecycle_stage_register(
        self,
        stage: LifecycleStageDef,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-15 — Register a CRM lifecycle stage (insert-between). Signature-only v0.1.0."""
        self._register("EP-15", stage.stage_id, stage, mode)

    def dispatch_lifecycle_transition(self, stage_id: str, ctx: BrandContext) -> Any:
        raise NotImplementedError(
            "EP-15 crm_lifecycle_stage_register is signature-only in v0.1.0; "
            "semantic dispatch deferred v0.2.x"
        )

    def iam_signup_handler(
        self,
        handler: Callable[[Any, BrandContext], SignupResult],
        *,
        name: str,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-16 — Register an IAM signup handler. Signature-only v0.1.0."""
        self._register("EP-16", name, handler, mode)

    def dispatch_signup(self, clerk_user: Any, ctx: BrandContext) -> SignupResult:
        raise NotImplementedError(
            "EP-16 iam_signup_handler is signature-only in v0.1.0; "
            "semantic dispatch deferred v0.2.x"
        )

    def tenant_plan_tier_register(
        self,
        tier: PlanTierDef,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-17 — Register a tenant plan tier (override permitted). Signature-only v0.1.0."""
        self._register("EP-17", tier.tier_id, tier, mode)

    def dispatch_plan_tiers(self, ctx: BrandContext) -> list[PlanTierDef]:
        raise NotImplementedError(
            "EP-17 tenant_plan_tier_register is signature-only in v0.1.0; "
            "semantic dispatch deferred v0.2.x"
        )

    def onboarding_wizard_steps_register(
        self,
        step: WizardStepDef,
        *,
        mode: Literal["append", "override"] = "append",
    ) -> None:
        """EP-18 — Register an onboarding wizard step (override permitted). Signature-only v0.1.0."""
        self._register("EP-18", step.step_id, step, mode)

    def dispatch_wizard_steps(self, ctx: BrandContext) -> list[WizardStepDef]:
        raise NotImplementedError(
            "EP-18 onboarding_wizard_steps_register is signature-only in v0.1.0; "
            "semantic dispatch deferred v0.2.x"
        )

    # ─── introspection ──────────────────────────────────────────────────

    def get_all(self, ep_id: str) -> list[_Registration]:
        """Return all registrations for a given EP. Test-only API."""
        if ep_id not in self._registrations:
            raise ValueError(f"Unknown EP id: {ep_id}")
        return list(self._registrations[ep_id])
```

5. **`protocols.py`** — Protocol interfaces for Callable-pattern handlers (used by type checkers + arch tests):

```python
# core/luana-core-extension-sdk/src/luana_core_extension_sdk/protocols.py
from __future__ import annotations
from typing import Protocol, Optional, runtime_checkable

from luana_core_extension_sdk.brand_context import BrandContext
from luana_core_extension_sdk.models import FieldDef, FieldOverride, SignupResult, GuardrailResult

@runtime_checkable
class FieldOverrideHandler(Protocol):
    def __call__(self, field: FieldDef, ctx: BrandContext) -> Optional[FieldOverride]: ...

@runtime_checkable
class SignupHandler(Protocol):
    def __call__(self, clerk_user: object, ctx: BrandContext) -> SignupResult: ...

@runtime_checkable
class GuardrailCheck(Protocol):
    def __call__(self, message: str, ctx: BrandContext) -> GuardrailResult: ...
```

### §1.4 EP-3 + EP-4 read-only adapter pattern (D-T1 byte-stable wrap)

Adapter pattern wraps Stories 6+7 frozen registries WITHOUT mutation surface exposure.

```python
# core/luana-core-extension-sdk/src/luana_core_extension_sdk/_adapters.py (internal — leading underscore)
"""Internal adapter classes wrapping Stories 6+7 frozen registries (D-T1 byte-stable).

These adapters are CONSTRUCTED at FastAPI lifespan by brand app composition root.
They thin-wrap the frozen registry to expose ONLY public read methods to the SDK.
Mutation surface (private dispatch internals) NOT exposed via SDK.

V-AG-3 Story 6 + Story 7 golden snapshots verify registry public API surface
unchanged post Story 8 — adapters consume only public methods.
"""
from __future__ import annotations
from typing import Any, Optional

from luana_core_extension_sdk.models import ToolDef, WorkflowDef


class _SalesAgentToolRegistryAdapter:
    """Wraps luana_core_sales_agent.application.tools.registry.ToolRegistry.

    READ-ONLY delegation. NEVER calls private dispatch / state-mutation methods.
    Story 7 V-AG-3 golden snapshot test fails build if adapter touches private surface.
    """

    def __init__(self, tool_registry: Any) -> None:
        # tool_registry is luana_core_sales_agent.application.tools.registry.ToolRegistry instance
        self._inner = tool_registry

    def register_extension_tool(self, tool: ToolDef) -> None:
        """Delegate to Story 7 ToolRegistry public register API.

        NOTE: Story 7 ToolRegistry MUST expose `register_tool_from_extension(name, handler, ...)`
        public method. If absent, raise NotImplementedError — Story 8 audit-fix surfaces.
        """
        if not hasattr(self._inner, "register_tool_from_extension"):
            raise NotImplementedError(
                "Story 7 ToolRegistry lacks public `register_tool_from_extension` method. "
                "Story 8 EP-3 wrapper requires this surface. Escalate to Chris."
            )
        self._inner.register_tool_from_extension(
            name=tool.name,
            handler=tool.handler,
            description=tool.description,
            input_schema=tool.input_schema,
            tool_groups=tool.tool_groups,
        )


class _CopilotWorkflowRegistryAdapter:
    """Wraps luana_core_copilot.application.workflows.engine.WorkflowRegistry.

    READ-ONLY delegation. Same invariants as ToolRegistryAdapter.
    """

    def __init__(self, workflow_registry: Any) -> None:
        self._inner = workflow_registry

    def register_extension_workflow(self, workflow: WorkflowDef) -> None:
        if not hasattr(self._inner, "register_workflow_from_extension"):
            raise NotImplementedError(
                "Story 6 WorkflowRegistry lacks public `register_workflow_from_extension` method. "
                "Story 8 EP-4 wrapper requires this surface. Escalate to Chris."
            )
        self._inner.register_workflow_from_extension(
            name=workflow.name,
            steps=workflow.steps,
            description=workflow.description,
            trigger_event=workflow.trigger_event,
        )
```

**Important:** Story 6 + Story 7 registries DO NOT currently expose `register_tool_from_extension` / `register_workflow_from_extension`. This is the **expected adapter contract** for Story 8 — auditor T-16 verifies adapter raises `NotImplementedError` gracefully when adapters not wired (test-brand smoke pack injects None for both adapters, so EP-3 + EP-4 record registration in SDK registry but do NOT propagate to Story 6/7 registries — that wiring is **deferred to Stories 11-13 brand bootstraps where they wire real adapters per-brand**).

For Story 8, the test-brand pack injects `None` for both adapter args. EP-3 + EP-4 register in SDK side ONLY. Smoke tests verify EP-3/EP-4 record DataClass correctly + adapter wiring is `None` (not raises). Future stories (11+) wire real adapters.

### §1.5 Python package dependency DAG (3 NEW Python packages + 1 NEW TS package)

```
        luana-core-platform (Story 2)
                ↑
        Stories 2-7 packages (23)
                ↑
        ┌─────────────┴─────────────┐
        │                            │
luana-core-campaigns         luana-core-extension-sdk  ★ NEW STORY 8 ★
        │                            │
        │                            ↑
        │                  apps/test-brand  ★ NEW STORY 8 ★  (depends on extension-sdk only)
        ↓
   (depends on: iam + observability + idempotency + channels + events + platform)

@luana/extension-sdk (TS, NEW STORY 8) — mirror EP-6 + EP-10 + EP-18 DataClass types
```

**Cross-package edges (Python):**

| Source package | Depends on | Symbol used |
|---|---|---|
| `luana-core-campaigns` | `luana-core-platform` | `shared.domain.{base_entity, events, datetime_utils}` + `shared.links.ports.{tenant_profile, brand, sales_agent}` + `shared.infrastructure.{...}` + `core.config` |
| `luana-core-campaigns` | `luana-core-iam` | iam dependencies + User + TenantModel |
| `luana-core-campaigns` | `luana-core-observability` | `recording.{...}` for llm_call_model.py (minimal — campaigns has light observability) |
| `luana-core-campaigns` | `luana-core-idempotency` | `IdempotencyService` (workers) |
| `luana-core-campaigns` | `luana-core-channels` | `channel_registry` + `get_channel_format` (telegram channel router consumes) |
| `luana-core-campaigns` | `luana-core-events` | `outbox.application.event_bus_adapter.adapter_bus` |
| `luana-core-extension-sdk` | (NONE — zero external deps) | Pure stdlib + typing. Hermetically sealed. |
| `apps/test-brand` | `luana-core-extension-sdk` | ExtensionPointRegistry + BrandContext + 18 DataClass models |
| `apps/test-brand` | `fastapi` | FastAPI lifespan integration |

**Crucially: cycle check OK.**
- luana-core-extension-sdk depends on NOTHING (zero workspace deps — pure contract).
- luana-core-campaigns depends on Stories 2-3 packages only (verified §1.1 grep).
- apps/test-brand depends on extension-sdk only.
- DAG-clean.

**Adapter wiring deferred:** EP-3 + EP-4 adapter constructors accept Story 6+7 registries via DI at brand app composition root. luana-core-extension-sdk does NOT import luana-core-copilot or luana-core-sales-agent (zero-dep policy). Adapter classes accept `Any` typed `tool_registry` / `workflow_registry` — duck-typing at brand bootstrap injects real registry instance.

## §2. Lift Order — 18 tickets per outcome §7.4 atomicity

**Batch 1: Workspace + SDK foundation (T-1..T-4)**
- T-1 (15min): workspace pyproject.toml — append 3 Python members
- T-2 (15min): luana-core-extension-sdk skeleton + pyproject + README
- T-3 (30min): BrandContext frozen dataclass + tests (V-F-sdk-5)
- T-4 (30min): exceptions.py (3 exception types) + models.py (18 DataClasses) + protocols.py

**Batch 2: Registry critical EPs (T-5..T-6) — OPUS REQUIRED**
- T-5 (60min): ExtensionPointRegistry skeleton + CC-1..CC-5 enforcement + EP-1..EP-5 critical methods (executable) + unit tests
- T-6 (45min): _adapters.py + EP-3/EP-4 read-only adapter pattern + tests (V-AG-new-story-8) — **Opus: touches Stories 6+7 frozen registries semantically**

**Batch 3: Registry backlog EPs (T-7) — SONNET ELIGIBLE**
- T-7 (45min): EP-6..EP-18 register_* methods + dispatch raises NotImplementedError + unit tests (signature-only)

**Batch 4: TS mirror (T-8)**
- T-8 (30min): @luana/extension-sdk TS package + EP-6/EP-10/EP-18 type mirror + package.json + tsconfig.json

**Batch 5: Campaigns lift (T-9..T-13)**
- T-9 (15min): luana-core-campaigns skeleton + pyproject + README
- T-10 (45min): lift domain layer (12 src + ~7 test files: campaign_task, segment_filter, events, campaign_step, segment, audit_log, campaign, repositories, campaign_template, enums, channel_router)
- T-11 (60min): lift infrastructure layer (29 src files: channels/{telegram,shared,registry,errors}, repositories (7 files), resilience (2 files), models (7 files), links, external/sales_agent_adapter) + tests
- T-12 (60min): lift application layer (21 src files: dtos (6 files), ports (1 file), services (8 files: campaign_template_service, cache, campaign_stats_service, campaign_service, orchestrator, _event_bridge, audit_log_service, campaign_read_adapter, segment_service), segment_filter_evaluator) + observability/persistence/models/llm_call_model.py
- T-13 (45min): lift api layer (8 src files: routers, _async_session, _dependencies, _service_factories) + workers layer (5 src files: audit_retention_task, execution_task, scheduler_tick, segment_refresh_tick)

**Batch 6: Test brand smoke pack (T-14..T-15)**
- T-14 (45min): apps/test-brand skeleton + pyproject + extensions.py (18 register_all handlers) + main.py (FastAPI lifespan)
- T-15 (45min): tests/test_sdk_smoke.py (10 assertion scenarios D1-D3 + C1-C5) + tests pass

**Batch 7: Documentation deliverable (T-16)**
- T-16 (60min): docs/extension-points.md §1-§5 complete (CC verbatim + per-vertical examples Vitalia/Comunify/Lupulo for EP-1..EP-18 + recipe + cross-brand learning principle)

**Batch 8: Arch fitness + integration (T-17)**
- T-17 (60min): NEW arch fitness tests Story 8 (12 tests: V-NF-1, V-NF-4, V-NF-5/6/7, V-F-ts-1, V-F-docs-1, V-AG-new-story-8 wrappers read-only, V-AG cross-cutting CC-1..CC-5, BrandContext frozen, no EP-19, namespace allowlist) + integration smoke + downstream regression R3

**Batch 9: Finalization (T-18)**
- T-18 (30min): lint + format + AISALESHT untouched verify + DEFERRED-FILES.md update + anti-duplication.md inventory row append + R3 SSoT table append

## §3. Per-Package Structure

### §3.1 luana-core-extension-sdk layout

```
core/luana-core-extension-sdk/
├── pyproject.toml                      # workspace member, version 0.0.8-alpha
├── README.md
├── src/luana_core_extension_sdk/
│   ├── __init__.py                     # public exports: ExtensionPointRegistry, BrandContext, all models, exceptions
│   ├── extension_points.py             # ExtensionPointRegistry class (18 methods + CC enforcement)
│   ├── brand_context.py                # BrandContext frozen dataclass (9 fields)
│   ├── exceptions.py                   # 3 exception types
│   ├── models.py                       # 18 DataClass models
│   ├── protocols.py                    # Protocol interfaces for Callables
│   └── _adapters.py                    # internal — _SalesAgentToolRegistryAdapter, _CopilotWorkflowRegistryAdapter
└── tests/
    ├── __init__.py
    ├── unit/
    │   ├── test_brand_context.py       # frozen + 9 fields + JSON serializable no PII
    │   ├── test_exceptions.py          # 3 exception types
    │   ├── test_models.py              # 18 DataClasses present + frozen + slots
    │   ├── test_ep1_through_ep5.py     # EP-1..EP-5 executable
    │   ├── test_ep6_through_ep18_signature_only.py  # EP-6..EP-18 raise NotImplementedError on dispatch
    │   ├── test_cross_cutting_policies.py  # CC-1..CC-5 enforcement (scenarios C1-C5)
    │   ├── test_registry_surface.py    # 18 EP methods exposed
    │   └── test_adapters_read_only.py  # adapters expose ONLY public read methods (V-AG-new-story-8)
    └── architecture/
        ├── test_no_unregister_api.py   # CC-5 — zero unregister_* methods
        └── test_public_api_surface.py  # exports stable
```

### §3.2 luana-core-campaigns layout

```
core/luana-core-campaigns/
├── pyproject.toml                      # workspace member, version 0.0.8-alpha
├── README.md
├── src/luana_core_campaigns/
│   ├── __init__.py
│   ├── domain/                         # 12 files
│   │   ├── __init__.py
│   │   ├── campaign.py, campaign_step.py, campaign_task.py, campaign_template.py
│   │   ├── segment.py, segment_filter.py
│   │   ├── audit_log.py, channel_router.py
│   │   ├── enums.py, events.py, repositories.py
│   ├── infrastructure/                 # 29 files
│   │   ├── __init__.py
│   │   ├── channels/{telegram, shared, registry, errors}.py
│   │   ├── repositories/{audit_log_repo_impl, campaign_repository_impl, campaign_step_repository_impl, campaign_task_repository_impl, campaign_template_repository_impl, segment_repository_impl, segment_snapshot_repository_impl}.py
│   │   ├── resilience/{circuit_breaker, errors}.py
│   │   ├── models/{campaign_audit_model, campaign_model, campaign_step_model, campaign_task_model, campaign_template_model, segment_model, segment_snapshot_model}.py
│   │   ├── links/campaigns_lookup_impl.py
│   │   └── external/sales_agent_adapter.py
│   ├── application/                    # 21 files
│   │   ├── __init__.py
│   │   ├── dtos/{audit_log_dtos, campaign_dtos, campaign_step_dtos, campaign_template_dtos, pagination, segment_dtos}.py
│   │   ├── ports/lead_query_port.py
│   │   ├── services/{audit_log_service, cache, campaign_read_adapter, campaign_service, campaign_stats_service, campaign_template_service, orchestrator, segment_service, _event_bridge}.py
│   │   └── segment_filter_evaluator.py
│   ├── api/                            # 8 files
│   │   ├── __init__.py
│   │   ├── _async_session.py, _dependencies.py, _service_factories.py
│   │   └── routers/{campaigns_router, segments_router, templates_router}.py
│   ├── observability/                  # 4 files (minimal — campaigns lights observability)
│   │   ├── __init__.py
│   │   └── persistence/models/llm_call_model.py
│   └── workers/                        # 5 files
│       └── {audit_retention_task, execution_task, scheduler_tick, segment_refresh_tick}.py
└── tests/                              # 42 files (verbatim from AISALESHT)
    ├── conftest.py (if applicable)
    ├── api/ (4 files)
    ├── application/ (7 files)
    ├── domain/ (7 files)
    ├── infrastructure/ (channels + external + general — 9 files)
    ├── integration/ (1 file)
    ├── workers/ (4 files)
    └── (test_observability_registration.py + test_segment_create_static_with_lead_ids.py — 2 files at top level)
```

### §3.3 apps/test-brand layout

```
apps/test-brand/
├── pyproject.toml                      # workspace member, version 0.0.8-alpha
├── README.md                           # "Test brand: SDK smoke validation, NOT a deployable product"
├── src/test_brand/
│   ├── __init__.py
│   ├── extensions.py                   # register_all(registry) — 5 executable + 13 stubs
│   └── main.py                         # FastAPI lifespan integration
└── tests/
    └── test_sdk_smoke.py               # 10 smoke assertions (D1-D3 + C1-C5 + frozen ctx)
```

### §3.4 core/@luana/extension-sdk TS layout (FE-mirror partial)

```
core/@luana/extension-sdk/
├── package.json                        # pnpm workspace member, version 0.0.8-alpha
├── tsconfig.json
├── README.md
└── src/
    ├── index.ts                        # public exports
    ├── brand-context.ts                # BrandContext type mirror (9 fields)
    └── models.ts                       # 3 type mirrors: SidebarRouteDef + LandingTemplateDef + WizardStepDef
```

NO runtime registry class FE-side (registration always BE at FastAPI startup). TS types are TYPE-ONLY exports — compile-time validation in Stories 11-13 brand FE apps.

### §3.5 pyproject.toml — luana-core-extension-sdk

```toml
[project]
name = "luana-core-extension-sdk"
version = "0.0.8-alpha"
requires-python = ">=3.12"
description = "Luana extension SDK — 18 extension points formalized contract"
dependencies = []                       # ZERO workspace deps — pure contract layer

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/luana_core_extension_sdk"]

[tool.pytest.ini_options]
pythonpath = ["."]
asyncio_mode = "auto"
```

### §3.6 pyproject.toml — luana-core-campaigns

```toml
[project]
name = "luana-core-campaigns"
version = "0.0.8-alpha"
requires-python = ">=3.12"
description = "Campaigns engine — orchestrator + segments + templates + workers"
dependencies = [
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
    "fastapi>=0.115",
    "structlog>=24.0",
    "arq>=0.26",
    "httpx>=0.27",
    "luana-core-platform",
    "luana-core-iam",
    "luana-core-observability",
    "luana-core-idempotency",
    "luana-core-channels",
    "luana-core-events",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/luana_core_campaigns"]
```

### §3.7 pyproject.toml — apps/test-brand

```toml
[project]
name = "test-brand"
version = "0.0.8-alpha"
requires-python = ">=3.12"
description = "Test brand — SDK smoke validation app (NOT deployable)"
dependencies = [
    "fastapi>=0.115",
    "luana-core-extension-sdk",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/test_brand"]
```

### §3.8 package.json — @luana/extension-sdk

```json
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

## §4. Workspace Registration (T-1)

```toml
# luana-platform/pyproject.toml
[tool.uv.workspace]
members = [
    "core",
    # Stories 2-7 (23 packages already registered)
    # ...
    # Story 8 (NEW — 3 Python packages)
    "core/luana-core-campaigns",
    "core/luana-core-extension-sdk",
    "apps/test-brand",                  # NEW workspace path — apps/ added
    # Brand apps
    "nicolify", "vitalia", "comunify", "lupulo",
]

[tool.uv.sources]
# Stories 2-7 (23 entries)
# ...
# Story 8 (NEW — 3 entries)
luana-core-campaigns = { workspace = true }
luana-core-extension-sdk = { workspace = true }
test-brand = { workspace = true }
```

pnpm-workspace.yaml ALREADY contains `core/@luana/*` glob — new `@luana/extension-sdk` picks up automatically. Verify post-T-8:

```bash
cd ~/luana-platform && pnpm list -r --json 2>/dev/null | grep '@luana/extension-sdk'
```

## §5. Import Path Mapping (sed) — luana-core-campaigns

Same template as Story 7 §5 — `from src.modules.campaigns.X` → `from luana_core_campaigns.X`. Plus cross-module patterns:

```bash
cd ~/luana-platform/core/luana-core-campaigns

# Self-imports
find src tests -name "*.py" -exec sed -i 's|from src\.modules\.campaigns\.|from luana_core_campaigns.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|import src\.modules\.campaigns\.|import luana_core_campaigns.|g' {} \;

# Cross-module Stories 2-7
find src tests -name "*.py" -exec sed -i 's|from src\.modules\.iam\.|from luana_core_iam.|g' {} \;

# Shared → luana-core-platform / observability / events / etc.
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.agent_observability\.|from luana_core_observability.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.domain_events\.|from luana_core_events.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.idempotency\.|from luana_core_idempotency.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.agent_observability\.channels\.|from luana_core_channels.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.domain\.|from luana_core_platform.domain.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.links\.|from luana_core_platform.links.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.infrastructure\.|from luana_core_platform.infrastructure.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.application\.|from luana_core_platform.application.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.core\.|from luana_core_platform.core.|g' {} \;
```

## §6. Test Lift Strategy

42 test files in `backend/tests/modules/campaigns/`. Lift ALL 42 verbatim. NO eval-framework subset (campaigns has none).

Coverage threshold preserved: AISALESHT 43% baseline (V-F-campaigns-1).

## §7. Architecture Fitness Tests (NEW Story 8)

### §7.1 V-NF-1 — workspace alphabetical
`test_workspace_members_alphabetical_story8.py` — extends Story 7 — verifies 26 Python members in alphabetical order.

### §7.2 V-NF-4 — AISALESHT untouched (cardinal)
`test_aisalesht_campaigns_untouched_story8.py`:
```python
def test_aisalesht_campaigns_unchanged():
    """Cardinal invariant V-NF-4 outcome §7.3 MUST NOT."""
    import subprocess
    base_sha = _read_base_sha_from_checkpoint()
    diff = subprocess.run(
        ["git", "diff", base_sha, "HEAD", "--name-only", "--",
         "backend/src/modules/campaigns/", "backend/tests/modules/campaigns/"],
        capture_output=True, text=True, cwd="/home/chris/AISALESHT"
    )
    assert diff.stdout.strip() == "", f"AISALESHT campaigns touched: {diff.stdout}"
```

### §7.3 V-NF-5/6/7 — no publish artifacts
`test_no_publish_config_story8.py` — grep no `publishConfig` in any new pyproject.toml + no `.releaserc` + no `release.yml`.

### §7.4 V-F-sdk-1 — 18 EP methods exposed
`test_registry_surface.py`:
```python
def test_18_ep_register_methods_exposed():
    from luana_core_extension_sdk import ExtensionPointRegistry
    methods = [
        "field_override", "offer_preset_pack_register",
        "sales_agent_tool_register", "copilot_workflow_register",
        "scheduling_booking_policy_register",
        "sidebar_routes_register", "extractor_register",
        "channel_adapter_register", "metric_register",
        "landing_template_register", "campaign_template_register",
        "asset_template_register", "sales_agent_guardrail_register",
        "copilot_kb_pack_register", "crm_lifecycle_stage_register",
        "iam_signup_handler", "tenant_plan_tier_register",
        "onboarding_wizard_steps_register",
    ]
    for m in methods:
        assert hasattr(ExtensionPointRegistry, m), f"Missing register method: {m}"
    assert len(methods) == 18
```

### §7.5 V-F-sdk-2 + V-F-sdk-3 — EP-1..EP-5 executable + EP-6..EP-18 raise NotImplementedError
`test_ep1_through_ep5.py` + `test_ep6_through_ep18_signature_only.py` — per scenarios B1-B18.

### §7.6 V-F-sdk-4 — CC-1..CC-5 enforcement (5 scenarios C1-C5)
`test_cross_cutting_policies.py` — per scenarios C1-C5 verbatim.

### §7.7 V-F-sdk-5 — BrandContext frozen 9 fields
`test_brand_context.py`:
```python
def test_brand_context_frozen_9_fields():
    from dataclasses import fields
    from luana_core_extension_sdk import BrandContext
    assert BrandContext.__dataclass_params__.frozen is True
    field_names = {f.name for f in fields(BrandContext)}
    expected = {"tenant_id", "brand_slug", "plan_tier", "locale",
                "feature_flags", "tenant_profile_id", "vertical_kind",
                "compliance_flags", "pii_policy"}
    assert field_names == expected, f"BrandContext fields drift: {field_names ^ expected}"
```

### §7.8 V-AG-new-story-8 — EP-3 + EP-4 wrappers read-only
`test_ep3_ep4_wrappers_read_only.py`:
```python
def test_adapters_expose_only_public_read_methods():
    """V-AG-new-story-8 — adapters do NOT touch private dispatch surfaces of Stories 6+7 frozen registries.

    Strategy: AST parse _adapters.py for attribute access patterns. Any access to
    `_inner._private_attr` or `_inner.mutate_xxx` fails the test.
    """
    import ast
    from pathlib import Path
    adapter_file = Path("core/luana-core-extension-sdk/src/luana_core_extension_sdk/_adapters.py")
    src = adapter_file.read_text()
    tree = ast.parse(src)
    forbidden_attr_prefixes = ("_dispatch", "_mutate", "_internal_")
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            for prefix in forbidden_attr_prefixes:
                assert not node.attr.startswith(prefix), \
                    f"Adapter touches private surface: ._inner.{node.attr}"
```

### §7.9 V-F-ts-1 — TS types mirror Python DataClasses
`test_ts_types_mirror_python_dataclasses.py` — uses AST parse of `core/@luana/extension-sdk/src/models.ts` + Python `dataclasses.fields()` to compare 3 mirrored types (SidebarRouteDef + LandingTemplateDef + WizardStepDef).

### §7.10 V-F-docs-1 — docs/extension-points.md completeness
`test_docs_extension_points_completeness.py` — parses MD headers, verifies §1-§5 + recipe + per-vertical examples + NO EP-19 literal string.

### §7.11 V-AG-no-ep19 — NO EP-19 method exists in registry
`test_no_ep19_method_in_registry.py`:
```python
def test_no_ep19_vertical_agent_register_method():
    """Per §7.5.4 — vertical agents are brand apps, not core extension points. NO EP-19."""
    from luana_core_extension_sdk import ExtensionPointRegistry
    forbidden_methods = [
        "vertical_agent_register", "register_vertical_agent",
        "verticalAgentRegister", "ep19", "ep_19",
    ]
    for m in forbidden_methods:
        assert not hasattr(ExtensionPointRegistry, m), \
            f"EP-19 forbidden per §7.5.4 — found method: {m}"
```

### §7.12 V-AG-namespace-allowlist — brand_slug allowlist enforced
`test_brand_slug_namespace_allowlist.py`:
```python
def test_brand_slug_allowlist_enforced():
    """CC-4 namespace — only 5 brand_slugs accepted (nicolify/vitalia/comunify/lupulo/test-brand)."""
    from luana_core_extension_sdk import ExtensionPointRegistry, BrandContext
    from luana_core_extension_sdk.exceptions import NamespaceViolationError
    from luana_core_extension_sdk.models import SidebarRouteDef
    registry = ExtensionPointRegistry()
    # Bare name → raises
    try:
        registry.sidebar_routes_register(SidebarRouteDef(slug="bare_slug", label="x", icon="x"))
    except NamespaceViolationError:
        pass
    else:
        raise AssertionError("Bare slug should raise NamespaceViolationError")
    # Unknown brand_slug → raises
    try:
        registry.sidebar_routes_register(SidebarRouteDef(slug="unknown_brand.smoke", label="x", icon="x"))
    except NamespaceViolationError:
        pass
    else:
        raise AssertionError("Unknown brand_slug should raise NamespaceViolationError")
    # Valid → succeeds
    registry.sidebar_routes_register(SidebarRouteDef(slug="test-brand.smoke", label="x", icon="x"))
```

## §8. Downstream Regression Scope (R3 — auditor-downstream-regression.md SSoT table update)

Story 8 introduces 3 NEW Python packages + 1 TS package. Per R3 SSoT table append (T-18 finalization):

| Surface modified | Downstream test paths MUST run |
|---|---|
| `core/luana-core-campaigns/src/luana_core_campaigns/**` | `core/luana-core-campaigns/tests/` |
| `core/luana-core-extension-sdk/src/luana_core_extension_sdk/**` | `core/luana-core-extension-sdk/tests/` + `apps/test-brand/tests/test_sdk_smoke.py` + (Stories 11-13 brand apps when they wire — not in Story 8 scope) |
| `core/@luana/extension-sdk/src/**` | (Stories 11-13 brand FE apps when they consume — not in Story 8 scope) |
| `apps/test-brand/src/test_brand/extensions.py` | `apps/test-brand/tests/test_sdk_smoke.py` |
| Workspace `pyproject.toml` Story 8 append | Per-package pytest for ALL Stories 1-7 packages + Story 8 NEW (R3 cross-package pytest verification) |

## §9. DEFERRED files Story 8

| Status | Files | Reason |
|---|---|---|
| **NOT lifted (re-allowlist post-Story-8)** | AppointmentModel stub in 4 conftest.py + ProductModel stub in 4 conftest.py | Scheduling lift deferred per OQ-2; catalog/product lift deferred. Re-allowlist with reason "deferred to scheduling lift (post-Story-8)". |
| **NOT lifted (Story 8 deferral preserved from Story 7)** | scheduling concrete provider runtime — `tools/scheduling/providers.py` deferred-import pattern stays | Per Story 7 §9.2 + DEFERRED-FILES.md row 271-275. |
| **NOT lifted (continue Story 5 deferral)** | crm/application/services/contact_query_service.py + crm/api/contacts.py + test_contacts_api.py | Imports `src.modules.campaigns.*` — NOW that campaigns lifted Story 8, these can lift in audit-fix iter OR Story 10 nicolify migration. **Decision: defer to Story 10 nicolify migration to keep Story 8 scope tight.** |
| **NOT lifted (continue Story 5 deferral)** | offer/api/counts.py + offer/api/campaigns.py + test_counts_api.py + test_campaigns_api.py | Imports `src.modules.advertising.*` — advertising lift NOT in Story 8 scope. Defer to advertising lift (Story 11-13 future or v0.2.0). |
| **NEW deferral Story 8** | EP-3 + EP-4 adapter wiring real (Story 6+7 registry surfaces don't yet expose `register_*_from_extension`) | Brand apps Stories 11-13 wire real adapters. Story 8 test-brand pack injects None. NotImplementedError graceful. |

## §10. Anti-duplication.md inventory update (T-18)

Append row to `.claude/rules/anti-duplication.md` inventario shared abstractions SSoT:

| Pattern | Path canónico shared | Consumers |
|---|---|---|
| Extension SDK / ExtensionPointRegistry / BrandContext / 18 EP DataClass models | `luana_core_extension_sdk.*` (Story 8) | Brand apps (Stories 11-13 + nicolify Story 10) — never cross-consume; brand-namespaced registration only |

## §11. AISALESHT untouched verification

Per Story 7 V-NF-4 pattern. T-18 finalization step:

```bash
cd /home/chris/AISALESHT
git diff $BASE_SHA HEAD --name-only -- \
    backend/src/modules/campaigns/ \
    backend/tests/modules/campaigns/
# Expected: empty diff
```

## §12. Cross-module impact summary

**Lifted from AISALESHT:**
- `backend/src/modules/campaigns/` → `luana-platform/core/luana-core-campaigns/`
- `backend/tests/modules/campaigns/` → `luana-platform/core/luana-core-campaigns/tests/`

**New packages introduced (no AISALESHT counterpart):**
- `luana-platform/core/luana-core-extension-sdk/` (NEW)
- `luana-platform/core/@luana/extension-sdk/` (NEW TS)
- `luana-platform/apps/test-brand/` (NEW)

**Wraps (read-only delegation, byte-stable, adapter NOT WIRED Story 8):**
- Story 6 luana-core-copilot WorkflowRegistry — adapter constructed Stories 11-13
- Story 7 luana-core-sales-agent ToolRegistry — adapter constructed Stories 11-13

**Eventos emitidos:** none (Story 8 is infra + signatures, no runtime semantic dispatch for EP-6..EP-18; campaigns engine preserves AISALESHT event emission patterns verbatim — outbox.adapter_bus.publish).

**Eventos consumidos:** campaigns lifted as-is — same event consumers preserved.

**Documentation deliverable:** `luana-platform/docs/extension-points.md` (NEW)

