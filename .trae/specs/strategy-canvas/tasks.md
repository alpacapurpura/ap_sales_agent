# Tasks

- [ ] Task 1: Setup & Dependencies
  - [ ] Install `@visx/sankey`, `@visx/group`, `@visx/shape`, `@visx/responsive`, `@visx/gradient`, `@visx/tooltip`, `framer-motion` (for drawer animation).
  - [ ] Create directory structure `frontend/src/features/marketing-studio/components/strategy-canvas`.

- [ ] Task 2: Domain Modeling & Mock Data
  - [ ] Define TypeScript interfaces for `MarketingNode`, `MarketingActionLink`, `StrategyCanvasConfig` in `types.ts`.
  - [ ] Create `mock-data.ts` with the 8 fixed nodes and sample actions (edges) covering all statuses (Potential, Healthy, Bottleneck) and types.

- [ ] Task 3: Core Sankey Component
  - [ ] Create `StrategyCanvas.tsx` skeleton.
  - [ ] Implement `adapter.ts` to transform `StrategyCanvasConfig` into Visx Sankey data format.
  - [ ] Implement `NodeFactory.tsx` to render nodes with Title, Volume, and Efficiency metrics.
  - [ ] Implement `BaseLink.tsx` to render edges with correct styles (dashed, solid, pulsing) and colors.

- [ ] Task 4: Interactive Drawer
  - [ ] Create `ActionDetailsDrawer.tsx` using Shadcn Sheet or custom implementation.
  - [ ] Connect `onClick` event on edges to open the drawer with correct data.

- [ ] Task 5: Integration & Polish
  - [ ] Integrate `StrategyCanvas` into `frontend/src/features/marketing-studio/page.tsx` (or create a new route/view).
  - [ ] Verify responsive behavior.
  - [ ] Verify "Financial Nature" logic (Cost vs Revenue indicators).
