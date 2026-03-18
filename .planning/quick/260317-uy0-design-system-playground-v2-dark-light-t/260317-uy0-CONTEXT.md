# Quick Task 260317-uy0: Design System Playground v2 → Storybook Migration - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Task Boundary

Replace the custom `/playground/design-system` page with a proper Storybook setup. Install Storybook with dark/light mode toggle, write stories for all Shadcn UI components showing every variant, and include design token documentation as a story.

</domain>

<decisions>
## Implementation Decisions

### Strategy: Replace custom playground with Storybook
- Remove `/playground/design-system` route and its components
- Keep `frontend/src/lib/design-system/registry.ts` and `types.ts` as reference (useful for Claude AI to read before generating components)
- Keep `.planning/quick/260317-u42-*/AUDIT.md` as-is (diagnostic for future refactor)
- Storybook runs on its own port (default 6006)

### Storybook Framework Choice
- Use `@storybook/nextjs-vite` (Vite-based) — recommended for Next.js 15 + React 19
- NOT `@storybook/nextjs` (Webpack) — slower, less compatible

### Dark/Light Mode
- Use `@storybook/addon-themes` with `withThemeByClassName`
- Themes: `{ light: '', dark: 'dark' }` — matches our `html.dark` selector in globals.css
- Replaces the need for a custom ModeToggle in the playground

### Story Organization
- Follow Atomic Design hierarchy: `Tokens/`, `Atoms/`, `Molecules/`, `Organisms/`
- Each Shadcn component gets a `.stories.tsx` with ALL CVA variants as individual stories
- Feature-scoped components are NOT in Storybook (they require business context)
- Use `tags: ['autodocs']` for automatic documentation generation

### Addons to Install
- `@storybook/addon-themes` — dark/light toggle
- `@storybook/addon-a11y` — accessibility checks (nice to have)
- Built-in: Controls, Actions, Viewport, Docs

### Configuration
- `.storybook/main.ts` — framework: `@storybook/nextjs-vite`, stories pattern: `../src/**/*.stories.tsx`
- `.storybook/preview.ts` — import `../src/app/globals.css`, configure `withThemeByClassName`
- Tailwind v4 works via PostCSS (auto-detected by Vite)

### Docker Integration
- Add storybook dev script to `package.json`: `"storybook": "storybook dev -p 6006"`
- Add storybook build script: `"build-storybook": "storybook build"`
- For Docker: expose port 6006 in docker-compose.yml for dev

</decisions>

<specifics>
## Specific Ideas

- Our globals.css uses `:root` (light) and `html.dark` (dark) with HSL CSS vars — withThemeByClassName handles this perfectly
- ~37 Shadcn primitives need stories — Button (6 variants), Badge (4), Alert (2), Input, Select, Dialog, Sheet, Tabs, Card, etc.
- The component registry already has variant info per component — use it to guide story creation
- Design tokens story: render color swatches (light/dark side-by-side), typography scale, spacing, radii, shadows
- npm script for storybook inside Docker: `docker exec -it visionarias_client_dev npm run storybook`

</specifics>

<canonical_refs>
## Canonical References

- Storybook Next.js Vite framework: https://storybook.js.org/docs/get-started/frameworks/nextjs
- Storybook Tailwind recipe: https://storybook.js.org/recipes/tailwindcss
- @storybook/addon-themes: https://storybook.js.org/docs/essentials/themes
- Shadcn + Storybook guide: https://dev.to/shaikathaque/design-system-in-react-with-tailwind-shadcnui-and-storybook-17f
- Our globals.css: frontend/src/app/globals.css (lines 42-104 — all CSS custom properties)
- Our component registry: frontend/src/lib/design-system/registry.ts

</canonical_refs>
