# Design System Audit

**Date:** 2026-03-18
**Audited by:** Claude (automated scan of all frontend component directories)
**Registry:** `frontend/src/lib/design-system/registry.ts`

---

## Summary Stats

| Metric | Count |
|--------|-------|
| **Total Components** | 120+ |
| **Atoms** | ~35 |
| **Molecules** | ~40 |
| **Organisms** | ~45 |
| **Components with Issues** | 22 |
| **Shadcn Primitives** | 37 files (29 registered + 8 sub-exports) |
| **Shared Components** | 6 |
| **Feature Components** | ~80+ |
| **Feature Slices with Components** | 8 (admin, audit, brand, connections, marketing-studio, offer-studio, sales, settings) |

### Per-Feature Breakdown

| Feature | Component Count | Has Atomic Structure |
|---------|----------------|---------------------|
| marketing-studio | ~45 | No (uses nested directories: channel-widgets, detail-panels, sidebar, ui) |
| offer-studio | ~20 | No (uses editor/sections structure) |
| sales | ~22 | **Partial** (has atoms/, molecules/, organisms/ but many components outside) |
| connections | 11 | No (flat file structure) |
| brand | 7 | No (uses concern-based directories: navigation, forms, legal) |
| audit | 7 | No (flat file structure) |
| settings | 6 | No (flat file structure) |
| admin | 1 | No |

---

## Inconsistencies Found

### 1. Non-Shadcn Components in `components/ui/`

The `components/ui/` directory should contain only Shadcn primitives (installed via `npx shadcn@latest add`). The following are custom additions that break this convention:

| Component | File | Should Be In |
|-----------|------|-------------|
| CurrencySelector | `ui/currency-selector.tsx` | `shared/` or `features/` |
| FieldInfo | `ui/field-info.tsx` | `shared/` |
| HighlightedText | `ui/highlighted-text.tsx` | `shared/` |
| RichSelect | `ui/rich-select.tsx` | `shared/` |
| SmartDatetimePicker | `ui/smart-datetime-picker.tsx` | `shared/` |
| TimezoneSelect | `ui/timezone-select.tsx` | `shared/` |

**Impact:** When upgrading Shadcn components, these custom files could be accidentally overwritten. They also confuse the boundary between framework primitives and project components.

### 2. Missing CVA Patterns

Several components use raw `cn()` className merging instead of CVA variants:

- **Input** (`ui/input.tsx`): No size or state variants
- **Textarea** (`ui/textarea.tsx`): No size or state variants
- **Card** (`ui/card.tsx`): No elevation/style variants (elevated, outlined, flat)

These are standard Shadcn patterns, but the lack of CVA means every usage has to manually compose classes instead of using declarative variants.

### 3. Inconsistent Naming Conventions

| Pattern | Examples | Issue |
|---------|----------|-------|
| PascalCase files | `ScoreRing.tsx`, `LeadCard.tsx`, `AuditDashboard.tsx` | Standard React |
| kebab-case files | `error-boundary.tsx`, `mode-toggle.tsx`, `sales-dashboard.tsx` | Shadcn style |
| Mixed in same directory | `SettingsView.tsx` + `team-view.tsx` + `ai-keys-form.tsx` | No consistent convention |

**Impact:** No way to predict file naming from component name.

### 4. Inconsistent Import Paths

- Shadcn UI uses `@/lib/utils` for `cn()`
- Plan references `@/shared/lib/utils` (FSD style) but actual code uses `@/lib/utils`
- Some feature components import directly from `@/components/ui/`, others may use barrel exports

### 5. `"use client"` Directive Inconsistency

- Most Shadcn components that use Radix have `"use client"` (Dialog, Sheet, Sonner, etc.)
- Some don't need it (Card, Table, Badge) and correctly omit it
- Custom components in `ui/` inconsistently apply it

---

## Duplications

### Direct Duplicates

| Component A | Component B | Issue |
|------------|------------|-------|
| `detail-panels/DetailSkeleton.tsx` | `ui/DetailSkeleton.tsx` | **Exact duplicate** in marketing-studio — two files with same name/purpose |
| `MetricSidebar.tsx` (root) | `sidebar/MetricSidebar.tsx` | **Duplicate** — same component in two locations |

### Functional Overlaps

| Component A | Component B | Overlap |
|------------|------------|---------|
| `LeadAvatar` (sales atom) | `Avatar` (shadcn) | LeadAvatar wraps or reimplements Avatar with initials fallback |
| `RichSelect` (ui) | `RichEnumSelect` (offer-studio) | Both provide enhanced select with rich rendering |
| `FieldInfo` (ui) | `ContextualHint` (offer-studio) | Both show hint text for form fields |
| `OfferCard` | `OfferHealthCard` | Both display offer metrics — could be one component with variants |
| `EditSheetManager` (brand) | `OfferEditSheetManager` (offer-studio) | Same pattern — could be a shared abstraction |
| `ChannelGroup` | `ChannelGroupCard` | Unclear boundary — both group channels |

### Components Ripe for Promotion to shared/

| Component | Current Location | Why Promote |
|-----------|-----------------|-------------|
| `KpiTooltip` | marketing-studio | Reusable tooltip pattern for any KPI |
| `BottleneckBanner` | marketing-studio | Reusable warning banner pattern |
| `AiAssistButton` | offer-studio | AI auto-fill trigger used across studios |
| `HealthBar` | marketing-studio | Reusable proportional bar visualization |
| `DetailSkeleton` | marketing-studio | Generic loading skeleton |
| `DetailEmpty` | marketing-studio | Generic empty state |
| `DetailError` | marketing-studio | Generic error state |

---

## Missing from Shadcn

Standard Shadcn components NOT installed that the project hand-rolls or could benefit from:

| Component | Status | Alternative in Use |
|-----------|--------|-------------------|
| `Breadcrumb` | Not installed | None — pages lack breadcrumb navigation |
| `NavigationMenu` | Not installed | Custom nav rails in brand/offer |
| `Toggle` | Not installed | Custom button-based toggles |
| `ToggleGroup` | Not installed | Custom implementations |
| `Carousel` | Not installed | None |
| `Drawer` | Not installed | Uses Sheet for everything (fine if intentional) |
| `Sidebar` | Not installed | Custom AppSidebar instead |

---

## Atomic Level Violations

### "Atoms" That Are Actually Molecules

| Component | Classified As | Actually | Reason |
|-----------|--------------|----------|--------|
| `Accordion` | atom | molecule | Composes trigger + content + animations |
| `CurrencySelector` | molecule (correctly) | molecule | Good classification |
| `SmartDatetimePicker` | molecule (correctly) | organism | Composes Calendar + Input + Popover (3+ primitives) |

### Organisms Without Container Structure

Many organisms sit at the root of their directory instead of an `organisms/` folder:

- `features/sales/components/sales-dashboard.tsx` (organism, not in organisms/)
- `features/sales/components/availability-view.tsx` (organism, not in organisms/)
- All `features/connections/components/*-view.tsx` (organisms, flat structure)
- All `features/settings/components/*View.tsx` (organisms, flat structure)

### Sales Feature: Partial Atomic but Inconsistent

The sales feature has `atoms/`, `molecules/`, `organisms/` directories BUT many components live outside them:
- `generate-link-modal.tsx` (molecule, root level)
- `event-type-form.tsx` (molecule, root level)
- `event-type-view.tsx` (organism, root level)
- `overlay/` directory contains molecules and organisms mixed
- `dashboard/` directory has its own implicit hierarchy

---

## Technical Debt Summary

### Critical (Blocks Consistent Generation)

1. **No design system manifest was being used** — Claude had no single source of truth before this registry
2. **6 custom components pollute `components/ui/`** — confuses Shadcn boundary
3. **2 direct file duplicates** — DetailSkeleton and MetricSidebar exist twice

### High (Causes Inconsistency)

4. **Mixed file naming** — PascalCase vs kebab-case with no rule
5. **Only 1 of 8 features uses atomic directories** (and even that one is partial)
6. **7 components should be promoted to shared/** — duplicated patterns across features
7. **3 functional duplications** — RichSelect/RichEnumSelect, FieldInfo/ContextualHint, OfferCard/OfferHealthCard

### Medium (Quality of Life)

8. **Input/Textarea lack CVA variants** — every usage manually composes classes
9. **Card has no variants** — missing elevated/outlined/flat options
10. **`use client` directive applied inconsistently** across custom components
11. **No test files** for most feature components (only marketing-studio has some)

---

## Recommendations (Prioritized)

### Phase 1: Foundation (Do First)

1. **Move 6 custom components out of `components/ui/`** to `components/shared/` or appropriate feature
2. **Delete duplicate files** (DetailSkeleton, MetricSidebar root)
3. **Promote 7 reusable components to `components/shared/`** (KpiTooltip, BottleneckBanner, AiAssistButton, HealthBar, DetailSkeleton, DetailEmpty, DetailError)
4. **Establish naming convention rule** — pick either PascalCase or kebab-case and apply consistently

### Phase 2: Patterns (Next)

5. **Add CVA variants to Input, Textarea, Card** — standard sizes at minimum
6. **Merge functional duplicates** — RichSelect/RichEnumSelect, FieldInfo/ContextualHint
7. **Create shared SheetManager abstraction** — unify EditSheetManager/OfferEditSheetManager
8. **Extend Shadcn Avatar** in LeadAvatar instead of reimplementing

### Phase 3: Structure (Later)

9. **Adopt atomic directories across all features** — atoms/molecules/organisms within each feature
10. **Install missing Shadcn components** where hand-rolled alternatives exist
11. **Add component tests** — at minimum for shared/ and reusable atoms

---

## For Claude (AI Guidelines)

When generating new components, **ALWAYS** check `frontend/src/lib/design-system/registry.ts` first:

1. Does a similar component already exist? Extend it.
2. Is it a Shadcn primitive? Use `@/components/ui/[name]` directly.
3. Is it reusable across features? Put in `components/shared/`.
4. Is it feature-specific? Put in `features/[name]/components/`.
5. Use CVA for any component with visual variants.
6. Use `cn()` from `@/lib/utils` for className merging.
7. Follow kebab-case for file names (Shadcn convention, majority pattern).
8. Add `"use client"` only when the component uses hooks, event handlers, or browser APIs.
