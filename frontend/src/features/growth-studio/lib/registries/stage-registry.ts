/**
 * Stage Registry — SSoT for growth-studio funnel stages.
 *
 * 5 canonical stages in funnel order. Immutable (Object.freeze).
 * Consumers: StageDispatcher (T-2), tier pages (T-3), arch tests (T-6).
 *
 * DO NOT hardcode stage slugs elsewhere — consume this registry.
 */

// ─── Types ────────────────────────────────────────────────────────────────────

export type StageSlug =
  | "atraccion-captura"
  | "nutricion-oportunidad"
  | "ventas"
  | "adopcion"
  | "expansion-evangelizacion";

export interface StageRegistryEntry {
  /** Canonical slug (kebab-case). Used in URLs + API calls. */
  slug: StageSlug;
  /** Spanish neutro display label. */
  label: string;
  /** 1-indexed funnel order (ascending). */
  order: number;
  /** Lucide icon name for this stage. */
  iconName: string;
  /** Label for the primary KPI shown in stage summary cards. */
  mainKpiLabel: string;
}

// ─── Registry ────────────────────────────────────────────────────────────────

export const STAGE_REGISTRY: readonly StageRegistryEntry[] = Object.freeze([
  {
    slug: "atraccion-captura",
    label: "Atracción y Captura",
    order: 1,
    iconName: "Megaphone",
    mainKpiLabel: "Alcance total",
  },
  {
    slug: "nutricion-oportunidad",
    label: "Nutrición y Oportunidad",
    order: 2,
    iconName: "Mail",
    mainKpiLabel: "Tasa de apertura",
  },
  {
    slug: "ventas",
    label: "Ventas",
    order: 3,
    iconName: "ShoppingCart",
    mainKpiLabel: "Ingresos",
  },
  {
    slug: "adopcion",
    label: "Adopción",
    order: 4,
    iconName: "UserCheck",
    mainKpiLabel: "Clientes activos",
  },
  {
    slug: "expansion-evangelizacion",
    label: "Expansión y Evangelización",
    order: 5,
    iconName: "Star",
    mainKpiLabel: "NPS promedio",
  },
] as const satisfies StageRegistryEntry[]);

// ─── Accessors ───────────────────────────────────────────────────────────────

/** Get a stage entry by slug, or undefined if not found. */
export function getStage(slug: StageSlug): StageRegistryEntry | undefined {
  return STAGE_REGISTRY.find((s) => s.slug === slug);
}

/** Get all stage slugs in order. */
export function getStageSlugs(): StageSlug[] {
  return STAGE_REGISTRY.map((s) => s.slug);
}
