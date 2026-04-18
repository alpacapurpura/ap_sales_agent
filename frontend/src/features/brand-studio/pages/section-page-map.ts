import {
  AuthorityPage,
  CommunicationAssetsPage,
  ContactPage,
  IdentityPage,
  MethodologyPage,
  NarrativePage,
  PositioningPage,
  StoryPage,
  TeamPage,
  TestimonialsPage,
  VisualsPage,
} from "./section-pages";

/**
 * Server-safe registry of brand-studio section pages. **This module has no
 * ``"use client"`` directive on purpose**: the catch-all Server Component
 * dispatcher at
 * ``app/(main)/[tenantId]/(dashboard)/brand-studio/[section]/[[...fieldId]]/page.tsx``
 * needs to index the map (``section in SECTION_PAGE_MAP``) and pick a
 * component. When the map lives in a ``"use client"`` module its exports
 * are replaced with opaque client references on the server and the index
 * lookup silently returns ``false`` → ``notFound()`` fires → 404 for every
 * real route. Defining the map here keeps it a plain server-land object
 * whose values happen to be client components — Next renders them through
 * the normal client boundary.
 *
 * Special sections NOT listed here (separate hooks or nested shapes):
 *   - personality  → own API via usePersonalityHooks (Sprint 2 deferred).
 *   - voice        → subset of identity (voice_tone); renders under identity page.
 *   - logos        → nested under visuals.logos; renders under visuals page.
 *   - avatars      → sub-entity, covered by PersonaDetailPage.
 */
export const SECTION_PAGE_MAP = {
  identity: IdentityPage,
  visuals: VisualsPage,
  team: TeamPage,
  contact: ContactPage,
  methodology: MethodologyPage,
  story: StoryPage,
  testimonials: TestimonialsPage,
  positioning: PositioningPage,
  narrative: NarrativePage,
  "communication-assets": CommunicationAssetsPage,
  authority: AuthorityPage,
} as const satisfies Readonly<Record<string, () => React.JSX.Element>>;

export type BrandStudioSectionSlug = keyof typeof SECTION_PAGE_MAP;
