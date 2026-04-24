/**
 * Superficie pública del módulo `pages/` de brand-studio.
 *
 * El App Router dispatcher en `/brand-studio/[section]/page.tsx` consume
 * `isBrandStudioSection` de `section-slugs.ts` (server-safe) y delega
 * el render al `SectionDispatcher` client que hace lazy-load per-slug.
 *
 * Los per-section files bajo `sections/` son module-internal — no se
 * importan directamente desde app routes ni otros features. La única
 * entrada es via dispatcher.
 */
export { SectionPage, type SectionPageProps } from "./SectionPage";
export {
  BRAND_STUDIO_SECTION_SLUGS,
  isBrandStudioSection,
  type BrandStudioSectionSlug,
} from "./section-slugs";
export { SectionDispatcher } from "./SectionDispatcher";
export { PersonaDetailPage } from "./PersonaDetailPage";
export { AvatarEditPage } from "./AvatarEditPage";
