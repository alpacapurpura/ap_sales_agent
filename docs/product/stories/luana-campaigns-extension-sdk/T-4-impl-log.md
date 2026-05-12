---
ticket: T-4
title: "Implement exceptions.py + models.py (18 DataClass models) + protocols.py + tests (TDD)"
story_id: luana-campaigns-extension-sdk
completed_at: 2026-05-12
iteration: 1
commit: ee0b15a
---

## Files Created

- `core/luana-core-extension-sdk/tests/unit/test_exceptions.py` — 6 RED tests
- `core/luana-core-extension-sdk/tests/unit/test_models.py` — 8 RED tests
- `core/luana-core-extension-sdk/src/luana_core_extension_sdk/exceptions.py` — GREEN (4 classes)
- `core/luana-core-extension-sdk/src/luana_core_extension_sdk/models.py` — GREEN (22 DataClass models)
- `core/luana-core-extension-sdk/src/luana_core_extension_sdk/protocols.py` — GREEN (3 Protocol interfaces)

## Files Modified

- `core/luana-core-extension-sdk/src/luana_core_extension_sdk/__init__.py` — full public API exports

## Implementation

### RED Phase

**test_exceptions.py** (6 tests):
- `test_3_exception_classes_importable` — imports ExtensionSDKError, NamespaceViolationError, DuplicateRegistrationError, RegistrationClosedError from `luana_core_extension_sdk.exceptions`
- `test_all_inherit_extension_sdk_error` — asserts 3 subclasses all inherit from ExtensionSDKError
- `test_namespace_violation_raiseable` — assert raises NamespaceViolationError
- `test_duplicate_registration_raiseable` — assert raises DuplicateRegistrationError
- `test_registration_closed_raiseable` — assert raises RegistrationClosedError
- `test_extension_sdk_error_is_exception` — base class inherits from Exception

**test_models.py** (8 tests):
- `test_all_18_models_importable` — 22 names (18 EP models + 4 auxiliary: BookingResult, CampaignStepDef, GuardrailResult, SignupResult)
- `test_all_18_models_are_dataclasses` — all are dataclasses
- `test_all_frozen_dataclasses` — all frozen=True
- `test_field_override_fields` — FieldOverride has name/default_value/label/hint/required
- `test_tool_def_has_handler` — ToolDef has handler/name/description/input_schema
- `test_brand_context_not_in_models` — BrandContext in brand_context.py, NOT models.py
- `test_guardrail_def_has_pre_send_and_pre_receive` — EP-13 extended scope §7.5.3
- `test_kb_pack_def_has_tenant_scope` — EP-14 tri-modal per §7.5.3

All tests failed with ImportError before implementation.

### GREEN Phase

**exceptions.py** — 4 classes:
- `ExtensionSDKError(Exception)` — base
- `NamespaceViolationError(ExtensionSDKError)` — CC-4 brand_slug prefix violation
- `DuplicateRegistrationError(ExtensionSDKError)` — CC-5 duplicate raise
- `RegistrationClosedError(ExtensionSDKError)` — CC-1 startup-only enforcement

**models.py** — 22 `@dataclass(frozen=True, slots=True, kw_only=True)` classes:
- EP-1: FieldOverride + FieldDef
- EP-2: PresetPack
- EP-3: ToolDef (handler: Callable)
- EP-4: WorkflowDef
- EP-5: BookingPolicy + BookingResult (auxiliary)
- EP-6: SidebarRouteDef
- EP-7: ExtractorDef
- EP-8: ChannelAdapterDef (target_agent_runtime: Literal["sales_agent", "copilot", "vertical_brand"])
- EP-9: MetricDef
- EP-10: LandingTemplateDef
- EP-11: CampaignTemplateDef + CampaignStepDef (auxiliary)
- EP-12: AssetTemplateDef
- EP-13: GuardrailDef + GuardrailResult (auxiliary, extended scope §7.5.3: pre_send_check + pre_receive_check)
- EP-14: KbPackDef (tenant_scope: Literal["brand", "tenant", "both"] — §7.5.3 tri-modal)
- EP-15: LifecycleStageDef
- EP-16: SignupResult (auxiliary)
- EP-17: PlanTierDef (mode='override' permitted per §7.5.3)
- EP-18: WizardStepDef (mode='override' permitted per §7.5.3)

**protocols.py** — 3 `@runtime_checkable` Protocol interfaces:
- `FieldOverrideHandler`: `(FieldDef, BrandContext) -> Optional[FieldOverride]`
- `SignupHandler`: `(clerk_user: object, BrandContext) -> SignupResult`
- `GuardrailCheck`: `(message: str, BrandContext) -> GuardrailResult`

TYPE_CHECKING pattern used for BrandContext/model imports to avoid circular imports.

**__init__.py** updated to export full public API: BrandContext, 4 exceptions, 22 models, 3 protocols. ExtensionPointRegistry commented (T-5's job).

## Validators Run

- V-F-sdk-2: 22 model names importable from models.py → PASS
- V-F-sdk-3: all models frozen=True → PASS
- V-F-sdk-4: 3 Protocols @runtime_checkable in protocols.py → PASS
- `uv run --package luana-core-extension-sdk pytest tests/unit/ -q` → 18 PASS, 0 fail

## Deviations

- **22 vs 18 classes**: 06-tickets.yaml T-4 says "18 DataClass models" but specifies 22 names (18 EP-primary + 4 auxiliary companion classes). EXPECTED_MODEL_NAMES in test_models.py includes all 22. Behavior matches 03-arch-be.md which lists all 22 verbatim.
- **Ruff lint fixes required**: I001 (import sort) in models.py + protocols.py; F401 (unused imports) in models.py (UUID, BrandContext under TYPE_CHECKING removed — Callables use Any). Fixed via `uv run ruff check --fix`.
