# Refactor Offer Builder Architecture Spec

## Why
The current `OfferEditor` relies on a monolithic structure with hardcoded phases and a `PolymorphicFactory` that switches based on `OfferType`. This makes adding new offer types or customizing the flow for specific types difficult and error-prone. The user wants a system where `OfferTypes` can be composed atomically from reusable "sections" or "forms" on demand, facilitating scalability and reuse.

## What Changes
- **Architecture**: Move from a "Monolithic Editor + Factory" pattern to a **"Composition-Based Builder"** pattern.
- **New Registry**: Create a `OFFER_TYPE_CONFIG` registry that maps each `OfferType` to an ordered list of `SectionComponent` keys.
- **Atomic Sections**: Extract logic from `OfferEditor.tsx` into standalone, reusable section components (e.g., `StrategySection`, `IdentitySection`, `PsychologySection`, `PromiseSection`, `PricingSection`, `ClosingSection`).
- **Dynamic Rendering**: Replace the hardcoded render logic in `OfferEditor` with a dynamic renderer that iterates over the configuration for the selected `OfferType`.
- **Form State**: Maintain the unified `react-hook-form` context but allow sections to register/unregister fields or just render what they need.

## Impact
- **Affected Specs**: None directly, but affects how future `OfferTypes` are specified.
- **Affected Code**:
    - `frontend/src/features/offer-studio/components/offer-editor.tsx` (Major Refactor)
    - `frontend/src/features/offer-studio/components/ui/polymorphic-factory.tsx` (Deprecated/Removed)
    - New directory: `frontend/src/features/offer-studio/components/sections/`
    - New config: `frontend/src/features/offer-studio/config/offer-builder-config.ts`

## ADDED Requirements
### Requirement: Offer Type Configuration
The system SHALL allow defining an `OfferType`'s structure via a configuration object.
Example:
```typescript
export const OFFER_BUILDER_CONFIG = {
  [OfferType.GROUP_COACHING_PROGRAM]: [
    'strategy', 'identity', 'psychology', 'promise', 'program_details', 'pricing', 'guarantee'
  ],
  [OfferType.FREE_RESOURCE]: [
    'strategy', 'identity', 'promise', 'digital_delivery', 'optin_mechanics'
  ]
}
```

### Requirement: Section Component Interface
Each section component SHALL accept a standard set of props (mainly the form context) to ensure interoperability.

## MODIFIED Requirements
### Requirement: Offer Editor Rendering
The `OfferEditor` SHALL NO LONGER contain hardcoded switch statements for offer types. It SHALL render the sidebar and form sections based purely on the loaded configuration.

## REMOVED Requirements
### Requirement: PolymorphicFactory
The `PolymorphicFactory` component will be removed in favor of the dynamic section renderer.
