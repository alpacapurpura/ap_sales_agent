# Tasks

- [ ] Task 1: Create Section Component Architecture
    - [ ] SubTask 1.1: Define the `SectionComponent` interface and props structure.
    - [ ] SubTask 1.2: Create a registry/map of all available sections (mapping string keys to components).
    - [ ] SubTask 1.3: Create the `OfferBuilderConfig` type and initial configuration file.

- [ ] Task 2: Extract Existing Logic into Atomic Sections
    - [ ] SubTask 2.1: Extract "Strategy & Identity" logic from `OfferEditor` into `StrategySection.tsx`.
    - [ ] SubTask 2.2: Extract "Psychology" logic (wrapping `OfferPsychologyCard`) into `PsychologySection.tsx`.
    - [ ] SubTask 2.3: Extract "Promise & Solution" logic into `PromiseSection.tsx`.
    - [ ] SubTask 2.4: Extract "Pricing & Guarantee" logic into `SalesMechanicsSection.tsx`.
    - [ ] SubTask 2.5: Refactor `ProgramDetailsForm` and others to be compatible with the new Section interface.

- [ ] Task 3: Implement Dynamic Offer Editor
    - [ ] SubTask 3.1: Create `DynamicOfferEditor` component that reads `OfferType` and loads the config.
    - [ ] SubTask 3.2: Implement the sidebar navigation to be generated dynamically from the config.
    - [ ] SubTask 3.3: Implement the form rendering loop to render sections based on the config.

- [ ] Task 4: Migrate Existing Offer Types
    - [ ] SubTask 4.1: Define configurations for all existing `OfferTypes` (Group Coaching, Course, etc.) in the config file.
    - [ ] SubTask 4.2: Verify that all fields previously rendered by `PolymorphicFactory` are covered by the new sections.

- [ ] Task 5: Cleanup and Integration
    - [ ] SubTask 5.1: Replace the old `OfferEditor` route with the new `DynamicOfferEditor`.
    - [ ] SubTask 5.2: Remove `PolymorphicFactory` and unused code.
    - [ ] SubTask 5.3: Verify form validation and submission still work correctly with the fragmented structure.

# Task Dependencies
- Task 3 depends on Task 1 and Task 2.
- Task 4 depends on Task 3.
- Task 5 depends on Task 4.
