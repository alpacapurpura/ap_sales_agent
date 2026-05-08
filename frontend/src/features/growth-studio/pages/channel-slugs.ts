/**
 * Server-safe registry of growth-studio channel slugs.
 *
 * - Sin directiva `"use client"`.
 * - Sin imports de componentes, schemas, ni módulos client-only.
 * - Permite al Server Component `[stage]/[channelSlug]/page.tsx` decidir
 *   `notFound()` sin arrastrar dashboards al grafo del server.
 *
 * Slugs canónicos (verificados contra ChannelDashboardView.tsx 2026-05-07):
 *   ig-organic, meta-ads, yt-organic, email-nurture, website-total
 *
 * NOTA: Los slugs "youtube-organic", "mail", "website" son nombres amistosos
 * usados en docs. Los slugs reales del código son los listados arriba.
 */

export const GROWTH_STUDIO_CHANNEL_SLUGS = [
  "ig-organic",
  "meta-ads",
  "yt-organic",
  "email-nurture",
  "website-total",
] as const;

export type GrowthStudioChannelSlug = (typeof GROWTH_STUDIO_CHANNEL_SLUGS)[number];

const CHANNEL_SLUG_SET: ReadonlySet<string> = new Set(GROWTH_STUDIO_CHANNEL_SLUGS);

/** True si `slug` es un channel key válido. */
export function isGrowthStudioChannel(slug: string): slug is GrowthStudioChannelSlug {
  return CHANNEL_SLUG_SET.has(slug);
}
