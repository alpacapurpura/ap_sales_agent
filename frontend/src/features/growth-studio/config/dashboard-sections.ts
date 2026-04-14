/**
 * Registry of all deep-linkable section IDs within Growth Studio channel dashboards.
 *
 * Each entry maps a channel slug to its tabs, and each tab to the section slugs
 * rendered inside it. These slugs are used as DOM `id` attributes (via `ChartSection`)
 * and can be targeted by the Copilot navigator via `UIAction.section_id`.
 *
 * URL format:
 *   /[tenantId]/growth-studio/[stage]/[channelSlug]?tab=[tab]&period=[period]#[sectionSlug]
 *
 * IMPORTANT: These slugs are part of the deep-link contract. Changing them breaks
 * existing Copilot prompts and any bookmarked/shared URLs.
 */
export const DASHBOARD_SECTIONS = {
  "ig-organic": {
    overview: ["kpis", "engagement-vs-vistas", "embudo", "crecimiento"],
    contenido: ["engagement-diario", "distribucion-engagement"],
    audiencia: ["seguidores-netos", "demografia"],
    alcance: ["tendencia-vistas", "taps-perfil"],
  },
  "meta-ads": {
    resumen: ["kpis", "alertas", "inversion-vs-resultados", "embudo"],
    campanas: ["campanas-tabla"],
    creativos: ["top-creativos", "comparacion-formato", "retencion-video"],
    audiencia: ["alcance-frecuencia", "demografia"],
    costos: ["kpis-costos", "tendencia-costos", "desglose-costos-campana"],
  },
  "yt-organic": {
    overview: ["kpis", "vistas-vs-minutos", "embudo", "crecimiento-suscriptores"],
    videos: ["top-videos", "fuentes-trafico"],
    audiencia: ["demografia"],
    engagement: ["kpis-ctr", "tendencia-engagement"],
    retencion: ["kpis-retencion", "tendencia-retencion"],
  },
  "email-nurture": {
    overview: ["kpis", "volumen-vs-engagement", "embudo", "crecimiento-lista"],
    engagement: [
      "kpis-engagement",
      "engagement-diario",
      "distribucion-engagement",
      "tendencia-ctor",
    ],
    entregabilidad: [
      "salud-entregabilidad",
      "kpis-entregabilidad",
      "desglose-rebotes",
      "tendencia-salud",
    ],
    lista: ["kpis-lista", "crecimiento-lista", "ratio-churn", "formularios"],
    automatizacion: ["kpis-automatizacion", "funnel-automatizacion", "tendencia-completado"],
  },
} as const;

export type DashboardChannel = keyof typeof DASHBOARD_SECTIONS;
export type DashboardTab<C extends DashboardChannel> = keyof (typeof DASHBOARD_SECTIONS)[C];
