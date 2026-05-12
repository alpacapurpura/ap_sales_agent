# Story 8 — Campaigns + Extension SDK formal

> **Outcome:** luana-platform-migration · **Sequence:** 8/14

## What

1. Lift `modules/campaigns/` → `luana-core-campaigns` (engine + scheduling + templates registry)
2. Define **Extension SDK formal** en `luana-core-extension-sdk`:

### EP-1..EP-5 críticos formalizados

```python
# luana-core-extension-sdk/python/extension_points.py

class ExtensionPointRegistry:
    def field_override(handler: Callable[[FieldDef, BrandContext], Optional[FieldOverride]]): ...
    def offer_preset_pack_register(pack: PresetPack): ...
    def sales_agent_tool_register(tool: ToolDef): ...
    def copilot_workflow_register(workflow: WorkflowDef): ...
    def scheduling_booking_policy_register(policy: BookingPolicy): ...
```

```typescript
// @luana/extension-sdk/src/index.ts
export interface ExtensionPointRegistry {
  fieldOverride(handler: (field: FieldDef, ctx: BrandContext) => FieldOverride | null): void;
  offerPresetPackRegister(pack: PresetPack): void;
  // ... etc
}
```

### EP-6..EP-18 backlog formalizadas (signatures only, no implementation)

EP-6 sidebarRoutes, EP-7 extractorRegister, EP-8 channelAdapterRegister, EP-9 metricRegister, EP-10 landingTemplateRegister, EP-11 campaignTemplateRegister, EP-12 assetTemplateRegister, EP-13 salesAgentGuardrailRegister, EP-14 copilotKbPackRegister, EP-15 crmLifecycleStageRegister, EP-16 iamSignupHandler, EP-17 tenantPlanTierRegister, EP-18 onboardingWizardSteps.

## Acceptance

- 1 package campaigns publicado v0.0.8-alpha
- 1 package extension-sdk publicado v0.0.8-alpha (Python + TS)
- Documentation: `docs/extension-points.md` con ejemplos de uso por brand
- Smoke test: stub brand `apps/test-brand/` puede usar SDK para registrar handler en cada EP-1..EP-5

## Effort: 10-14 tickets, ~3 días
