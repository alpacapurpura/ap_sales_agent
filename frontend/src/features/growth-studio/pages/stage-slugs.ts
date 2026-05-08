/**
 * Server-safe registry of growth-studio stage slugs.
 *
 * - Sin directiva `"use client"`.
 * - Sin imports de componentes, schemas, ni módulos client-only.
 * - Permite al Server Component `[stage]/page.tsx` decidir `notFound()`
 *   sin arrastrar el grafo de compilación de dashboards ni form-runtime.
 *
 * Slugs canónicos (confirmados por grep arquitecto 2026-05-07):
 *   atraccion-captura, nutricion-oportunidad, ventas, adopcion,
 *   expansion-evangelizacion
 */

export const GROWTH_STUDIO_STAGE_SLUGS = [
  "atraccion-captura",
  "nutricion-oportunidad",
  "ventas",
  "adopcion",
  "expansion-evangelizacion",
] as const;

export type GrowthStudioStageSlug = (typeof GROWTH_STUDIO_STAGE_SLUGS)[number];

const SLUG_SET: ReadonlySet<string> = new Set(GROWTH_STUDIO_STAGE_SLUGS);

/** True si `slug` es un stage key válido. */
export function isGrowthStudioStage(slug: string): slug is GrowthStudioStageSlug {
  return SLUG_SET.has(slug);
}
