---
ticket: T-8
story_id: luana-campaigns-extension-sdk
title: "@luana/extension-sdk TS type mirror (EP-6 + EP-10 + EP-18 — FE-mirror partial scope)"
owner: builder-backend (Sonnet, builder-frontend-eligible per ticket)
state: done
completed_at: 2026-05-12
luana_platform_commit: fbdc39c
---

# T-8 Implementation Log

## Summary

Created `core/@luana/extension-sdk/` TypeScript type mirror package. FE-mirror partial scope per §3.4 + §7.5.3 FE-surface analysis.

## Files created

```
core/@luana/extension-sdk/
├── package.json           # v0.0.8-alpha, private: true, no dependencies
├── tsconfig.json          # strict TS, noEmit
├── README.md              # doc stub per ticket spec
└── src/
    ├── index.ts           # barrel exports (type-only)
    ├── brand-context.ts   # BrandContext 9 fields (camelCase mirror of Python snake_case)
    └── models.ts          # 3 TS interfaces: SidebarRouteDef + LandingTemplateDef + WizardStepDef
```

## TypeScript interfaces

### BrandContext (brand-context.ts)
9 fields mirroring Python `BrandContext` frozen dataclass:
- `tenantId: string` ← `tenant_id: UUID`
- `brandSlug: BrandSlug` ← `brand_slug: Literal[...]`
- `planTier: string` ← `plan_tier: str`
- `locale: string` ← `locale: str`
- `featureFlags: Record<string, boolean>` ← `feature_flags: dict[str, bool]`
- `tenantProfileId: string` ← `tenant_profile_id: UUID`
- `verticalKind: VerticalKind` ← `vertical_kind: Literal[...]`
- `complianceFlags: Record<string, boolean>` ← `compliance_flags: dict[str, bool]`
- `piiPolicy: PiiPolicy` ← `pii_policy: Literal[...]`

### SidebarRouteDef (EP-6 — models.ts)
6 fields: `slug`, `label`, `icon`, `order`, `parentSlug?`, `roleRequired?`

### LandingTemplateDef (EP-10 — models.ts)
4 fields: `templateId`, `verticalHint`, `sectionsSchema`, `previewUrl?`

### WizardStepDef (EP-18 — models.ts)
6 fields: `stepId`, `title`, `componentRef`, `prereqs`, `skippable`, `postActionEvent?`

## Workspace registration

`pnpm-workspace.yaml` already had `core/@luana/*` glob — new package picked up automatically.

Verification:
```
pnpm list -r --json | grep '@luana/extension-sdk'
→ "name": "@luana/extension-sdk", "path": ".../core/@luana/extension-sdk"
```

## TypeScript compile

```
cd core/@luana/extension-sdk && npx tsc --noEmit
→ 0 errors (exit 0)
```

## Design notes (OQ-5 hand-maintained alpha)

- Field naming: snake_case (Python) → camelCase (TS) per OQ-5 resolution
- V-F-ts-1 arch fitness test (T-17) will verify field-by-field parity via AST parse
- No codegen tool — manual mirror is adequate at alpha stage (3 DataClass surfaces = low drift risk)
- `private: true` + no `publishConfig` per V-NF-5

## Validators addressed

- V-NF-2: package declares version "0.0.8-alpha"
- V-NF-5: no publishConfig
- V-F-ts-1: TS types mirror Python DataClasses (3 interfaces)
- V-D-1: package.json ships with README.md
