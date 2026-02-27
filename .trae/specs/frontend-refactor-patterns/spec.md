# Frontend Refactor Patterns Spec

## Why
The frontend codebase currently lacks essential utility hooks and robust error handling mechanisms, leading to potential code duplication and a fragile user experience. Additionally, some key components suffer from "prop drilling" and monolithic structures, violating modern React patterns like Compound Components.

## What Changes
- Create a centralized `src/hooks` directory.
- Implement standard utility hooks: `useDebounce`, `useLocalStorage`, `useIntersectionObserver`.
- Implement a reusable `ErrorBoundary` component.
- Apply `ErrorBoundary` to critical areas (e.g., `OfferEditor`).
- Refactor `HeroSection` to use the Compound Components pattern.
- Refactor `OfferSectionWrapper` to use the Compound Components pattern.

## Impact
- **Affected Specs**: None directly, but improves maintainability and robustness.
- **Affected Code**:
    - New files in `src/hooks/`.
    - New file `src/components/shared/error-boundary.tsx`.
    - Modified `src/app/(main)/[tenantId]/(dashboard)/offer-studio/offer/[id]/page.tsx`.
    - Modified `src/features/offer-studio/components/landing/components/blocks/HeroSection.tsx`.
    - Modified `src/features/offer-studio/components/editor/offer-section-wrapper.tsx`.

## ADDED Requirements
### Requirement: Utility Hooks
The system SHALL provide standard hooks in `src/hooks/` for common operations.
- `useDebounce`: For delaying function execution or state updates.
- `useLocalStorage`: For persisting state to local storage with SSR support.
- `useIntersectionObserver`: For detecting element visibility.

### Requirement: Error Handling
The system SHALL provide a reusable `ErrorBoundary` component that catches React render errors and displays a fallback UI.
- It MUST be applied to the `OfferEditor` page to prevent white screens on editor crashes.

### Requirement: Compound Components
The system SHALL use the Compound Components pattern for complex UI components to improve flexibility and readability.
- `HeroSection` MUST be refactored to expose sub-components like `Hero.Content`, `Hero.Media`, etc.
- `OfferSectionWrapper` MUST be refactored to expose sub-components like `OfferSection.Header`, `OfferSection.Body`, etc.

## MODIFIED Requirements
### Requirement: Hero Section
The `HeroSection` component shall no longer accept configuration props for layout and content but instead accept children components that define the structure.

### Requirement: Offer Section Wrapper
The `OfferSectionWrapper` component shall be refactored to use compound components, reducing the number of props passed to the main container.
