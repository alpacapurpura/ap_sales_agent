# Tasks

- [x] Task 1: Create Utility Hooks
  - [x] SubTask 1.1: Create `src/hooks/use-debounce.ts`
  - [x] SubTask 1.2: Create `src/hooks/use-local-storage.ts`
  - [x] SubTask 1.3: Create `src/hooks/use-intersection-observer.ts`
  - [x] SubTask 1.4: Export all hooks from `src/hooks/index.ts` (barrel file)

- [x] Task 2: Implement Error Boundary
  - [x] SubTask 2.1: Create `src/components/shared/error-boundary.tsx` with a fallback UI.
  - [x] SubTask 2.2: Wrap `OfferEditor` in `src/app/(main)/[tenantId]/(dashboard)/offer-studio/offer/[id]/page.tsx` with the ErrorBoundary.

- [x] Task 3: Refactor HeroSection to Compound Components
  - [x] SubTask 3.1: Create `src/features/offer-studio/components/landing/components/blocks/hero/hero-context.tsx` (if needed) or define components in `hero.tsx`.
  - [x] SubTask 3.2: Implement `Hero`, `Hero.Content`, `Hero.Headline`, `Hero.Subheadline`, `Hero.CTA`, `Hero.Media`.
  - [x] SubTask 3.3: Update usages of `HeroSection` to use the new compound components.

- [x] Task 4: Refactor OfferSectionWrapper to Compound Components
  - [x] SubTask 4.1: Create `src/features/offer-studio/components/editor/offer-section/offer-section.tsx` with sub-components.
  - [x] SubTask 4.2: Implement `OfferSection`, `OfferSection.Header`, `OfferSection.Content`, `OfferSection.EmptyState`, `OfferSection.Controls`.
  - [x] SubTask 4.3: Update usages of `OfferSectionWrapper` to use the new compound components.
