"use client";

import dynamic from "next/dynamic";

import { SectionPageLoading } from "@/lib/studio-section-page";

import type { GrowthStudioStageSlug } from "./stage-slugs";

/**
 * Mapa per-slug → componente dinámico (lazy-loaded via next/dynamic).
 *
 * Cada `dynamic(() => import(...))` genera su propio chunk de Turbopack/webpack.
 * Los keys DEBEN igualar exactamente `GROWTH_STUDIO_STAGE_SLUGS` de `stage-slugs.ts`
 * (TypeScript union `GrowthStudioStageSlug` lo garantiza en compile time).
 *
 * Las secciones usan named exports (política `test-no-default-exports`).
 * next/dynamic requiere resolver a `{ default }` — se usa `.then()`.
 *
 * Dispatcher contiene CERO slugs hardcoded fuera del Record key → arch test
 * `test-no-hardcoded-stage-list.test.ts` (T-6) valida esto.
 */
const STAGE_COMPONENT_MAP: Record<GrowthStudioStageSlug, ReturnType<typeof dynamic>> = {
  "atraccion-captura": dynamic(
    () =>
      import("./sections/atraccion-captura-page").then((m) => ({
        default: m.AtraccionCapturaPage,
      })),
    { loading: () => <SectionPageLoading /> },
  ),
  "nutricion-oportunidad": dynamic(
    () =>
      import("./sections/nutricion-oportunidad-page").then((m) => ({
        default: m.NutricionOportunidadPage,
      })),
    { loading: () => <SectionPageLoading /> },
  ),
  ventas: dynamic(() => import("./sections/ventas-page").then((m) => ({ default: m.VentasPage })), {
    loading: () => <SectionPageLoading />,
  }),
  adopcion: dynamic(
    () => import("./sections/adopcion-page").then((m) => ({ default: m.AdopcionPage })),
    { loading: () => <SectionPageLoading /> },
  ),
  "expansion-evangelizacion": dynamic(
    () =>
      import("./sections/expansion-evangelizacion-page").then((m) => ({
        default: m.ExpansionEvangelizacionPage,
      })),
    { loading: () => <SectionPageLoading /> },
  ),
};

export interface StageDispatcherProps {
  /** Slug canónico de la etapa (validado por `isGrowthStudioStage` en el Server Component). */
  slug: GrowthStudioStageSlug;
}

/**
 * Dispatcher client-side que carga lazy la per-stage page del `slug`.
 *
 * El Server Component del route renderiza este componente pasando
 * el slug ya validado. La validación (`isGrowthStudioStage`) vive en
 * `stage-slugs.ts` para no arrastrar nada client al server.
 *
 * Patrón idéntico a `SectionDispatcher` de brand-studio y offer-studio
 * (factory propia adapter mode por AD6 de growth-studio-folder-parity).
 */
export function StageDispatcher({ slug }: StageDispatcherProps) {
  const Component = STAGE_COMPONENT_MAP[slug];
  return <Component />;
}
