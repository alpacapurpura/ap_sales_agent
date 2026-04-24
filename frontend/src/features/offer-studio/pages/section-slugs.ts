import type { SectionKey } from "../api/archetype-catalog-api";

/**
 * Registro server-safe de los section keys del offer-studio.
 *
 * - Sin directiva `"use client"`.
 * - Sin imports de componentes, schemas ni módulos client-only.
 * - Habilita al Server Component `editor/[section]/page.tsx` a validar
 *   el slug (y hacer `notFound()`) sin tirar del grafo de los 21
 *   schemas + form-runtime completo, causa raíz del OOM en dev.
 *
 * Mismo orden y mismos keys que el histórico `OFFER_SECTION_PAGE_MAP`
 * (section-page-map.ts) — arch test de alineación con el catálogo
 * backend valida en lockstep con `SectionKey`.
 */
export const OFFER_STUDIO_SECTION_SLUGS = [
  "identity",
  "strategy",
  "psychology",
  "promise",
  "value_stack",
  "instructors",
  "knowledge",
  "closing",
  "product_details",
  "subscription_details",
  "gallery",
  "event_details",
  "pricing",
  "program_details",
  "service_details",
  "resources",
  "faq",
  "testimonials",
  "portfolio",
  "location",
  "platform_details",
] as const satisfies readonly SectionKey[];

export type OfferStudioSectionSlug = (typeof OFFER_STUDIO_SECTION_SLUGS)[number];

const SLUG_SET: ReadonlySet<string> = new Set(OFFER_STUDIO_SECTION_SLUGS);

/** True si `slug` es un section key válido — primer gate del catch-all. */
export function isOfferStudioSection(slug: string): slug is OfferStudioSectionSlug {
  return SLUG_SET.has(slug);
}
