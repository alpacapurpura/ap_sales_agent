# Tasks

- [x] Task 1: Create `SmartFillSheet` Component (The Container)
  - [ ] Wrap `SmartFillCard` in a `Sheet` (Shadcn UI) component.
  - [ ] Accept `open` and `onOpenChange` props to control visibility.
  - [ ] Accept `mode` ("initial" | "update") prop.

- [x] Task 2: Create `BrandEmptyState` Component (Scenario 1)
  - [ ] Design a clean, centered "Hero Section" for new brands.
  - [ ] Implement "Autocompletar con IA" (Start with AI) button (Primary) -> Opens Sheet.
  - [ ] Implement "Configurar Manualmente" (Manual Setup) button (Secondary) -> Dismisses Hero.
  - [ ] Add illustrative icon/graphic (e.g., Wand or Rocket).

- [x] Task 3: Refactor `BrandStudioLayout` Logic (Scenarios 1-4)
  - [ ] Add state for `isSmartFillOpen` and `smartFillMode`.
  - [ ] Implement Logic: If `!settings.identity?.brand_name`, show `BrandEmptyState`.
  - [ ] Implement Logic: If `BrandEmptyState` is dismissed or data exists, show standard layout.
  - [ ] Remove the inline `SmartFillCard` code block.
  - [ ] Render `SmartFillSheet` conditionally (hidden by default).

- [x] Task 4: Update `HeaderSection` with Refinement Action (Scenarios 2-4)
  - [ ] Add "Refinar con IA" button to the header actions.
  - [ ] Ensure button is visible when brand data exists.
  - [ ] Connect button to open `SmartFillSheet` in "update" mode.

- [x] Task 5: Verify Mobile Responsiveness
  - [ ] Ensure Sheet works correctly on mobile (full width or slide-over).
  - [ ] Check Empty State layout on small screens (stack buttons).
