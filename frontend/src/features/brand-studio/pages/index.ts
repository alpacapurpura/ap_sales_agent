/**
 * Public surface of brand-studio's pages module.
 *
 * The App Router dispatcher at ``/brand-studio/[section]/page.tsx``
 * consumes ``SECTION_PAGE_MAP`` + ``BrandStudioSectionSlug`` from
 * ``section-page-map.ts`` (the server-safe module — see its header for why
 * it is separate from the ``"use client"`` page components in
 * ``section-pages.tsx``). Per-section page components (IdentityPage,
 * VisualsPage, …) are module-internal and must not be imported directly
 * by app routes or other features — route through the map so a new
 * section only requires one edit.
 */
export { SectionPage, type SectionPageProps } from "./SectionPage";
export { SECTION_PAGE_MAP, type BrandStudioSectionSlug } from "./section-page-map";
export { PersonaDetailPage } from "./PersonaDetailPage";
export { AvatarEditPage } from "./AvatarEditPage";
