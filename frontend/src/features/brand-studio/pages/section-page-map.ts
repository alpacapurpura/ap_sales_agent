import {
  CommunicationAssetsPage,
  CommunicationStylePage,
  ContactPage,
  IdentityPage,
  LegalPage,
  MethodologyPage,
  NarrativePage,
  PositioningPage,
  StoryPage,
  VisualsPage,
} from "./section-pages";

/**
 * Server-safe registry of brand-studio section pages. **This module has no
 * ``"use client"`` directive on purpose**: the Server Component
 * dispatcher at
 * ``app/(main)/[tenantId]/(dashboard)/brand-studio/[section]/page.tsx``
 * needs to index the map (``section in SECTION_PAGE_MAP``) and pick a
 * component. When the map lives in a ``"use client"`` module its exports
 * are replaced with opaque client references on the server and the index
 * lookup silently returns ``false`` → ``notFound()`` fires → 404 for every
 * real route. Defining the map here keeps it a plain server-land object
 * whose values happen to be client components — Next renders them through
 * the normal client boundary.
 *
 * Special sections NOT listed here (separate hooks or nested shapes):
 *   - estilo       → top-level "Estilo Comunicacional" section registered here,
 *                    backed by personality_profiles table (not BrandSettings JSONB).
 *   - logos        → nested under visuals.logos; renders under visuals page.
 *   - avatars      → sub-entity, covered by PersonaDetailPage.
 */
export const SECTION_PAGE_MAP = {
  identity: IdentityPage,
  estilo: CommunicationStylePage,
  legal: LegalPage,
  visuals: VisualsPage,
  contact: ContactPage,
  methodology: MethodologyPage,
  story: StoryPage,
  positioning: PositioningPage,
  narrative: NarrativePage,
  "communication-assets": CommunicationAssetsPage,
  // team / testimonials / authority live under their own static routes
  // (/{tenantId}/brand-studio/{slug}) served by the social_proof Finder flow
  // — they must NOT be registered here, otherwise the [section] catch-all
  // would render the legacy array-wrapper SectionPage for those slugs.
} as const satisfies Readonly<Record<string, () => React.JSX.Element>>;

export type BrandStudioSectionSlug = keyof typeof SECTION_PAGE_MAP;
