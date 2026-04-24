/**
 * Registro server-safe de los slugs del brand-studio.
 *
 * - Sin directiva `"use client"`.
 * - Sin imports de componentes, schemas, ni módulos client-only.
 * - Habilita al Server Component `[section]/page.tsx` a decidir
 *   `notFound()` sin tirar del grafo de compilación de los 10 schemas +
 *   form-runtime completo.
 *
 * Replica la lista histórica en `SECTION_PAGE_MAP` (section-page-map.ts)
 * que desaparece post-refactor — mismo orden, mismos keys.
 *
 * Special sections NO listadas (rutas propias fuera del catch-all):
 *   - team / testimonials / authority → viven bajo
 *     `/{tenantId}/brand-studio/{slug}` con páginas estáticas via el
 *     Finder flow de social_proof; no llegan al catch-all.
 */
export const BRAND_STUDIO_SECTION_SLUGS = [
  "identity",
  "estilo",
  "legal",
  "visuals",
  "contact",
  "methodology",
  "story",
  "positioning",
  "narrative",
  "communication-assets",
] as const;

export type BrandStudioSectionSlug = (typeof BRAND_STUDIO_SECTION_SLUGS)[number];

const SLUG_SET: ReadonlySet<string> = new Set(BRAND_STUDIO_SECTION_SLUGS);

/** True si `slug` es un section key válido — primer gate del catch-all. */
export function isBrandStudioSection(slug: string): slug is BrandStudioSectionSlug {
  return SLUG_SET.has(slug);
}
