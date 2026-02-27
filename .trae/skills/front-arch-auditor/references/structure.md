# Frontend Project Structure

Project uses Next.js App Router with Feature-Sliced Design.

/src/app
Routes and layouts only. Minimal logic.
- (main)/: Main application routes (Dashboard, Auth).
- (landing)/: Landing page editor (Fullscreen).
- api/: Backend proxy or edge functions.

/src/features
Core business logic modules. Search here first for functional code.
Structure per feature (e.g., brand, sales, settings):
- /api: Backend proxy or edge functions.
- /components: UI specific to the feature.
- /hooks: Logic, state, and data fetching.
- /types: Domain interfaces.
- /utils: Feature-specific utilities.
- index.ts: Public exports.

## Feature Internal Structure Rules
1. **No Nested Features**: Do NOT create `features/parent/features/child`.
2. **Sub-domains in Components**: Use `features/<name>/components/<sub-domain>` for logical grouping.
   - Example: `features/brand/components/voice/` (Contains form, preview, manager).
3. **Semantic Grouping**: For complex sub-modules (like editors), use semantic folder names instead of generic `components`.
   - Example: `features/offer-studio/components/editor/sections/` (Instead of `.../editor/components`).

/src/components
- /ui: Shadcn UI primitives (dumb components).
- /shared: Reusable global components (Navbar, Sidebar).
- /providers: Context providers (Theme, Query).

/src/lib
Global utilities, API clients, and configuration.

/src/hooks
Generic hooks shared across features (e.g., use-toast).

Key Features & Specific Patterns:
- **brand**:
  - `components/`: Grouped by domain (identity, voice, avatars).
  - Forms reside in `components/<domain>/<domain>-form.tsx`.
- **offer-studio**:
  - `components/dashboard`: List view.
  - `components/editor`: Complex editor view.
    - `sections/`: Semantic grouping for Offer Sections (pricing, promise).
    - `ui/`: Editor-specific UI components.
  - `components/landing`: Public view.

Rules:
- UI Logic belongs in features/[name]/hooks.
- Pages in app/ import from features/.
- Do not modify components/ui internals.
