"use client";

// Side-effect: bootstrap del action registry una sola vez cuando
// cualquier sección monta. Antes vivía en `schemas/index.ts`; se movió
// aquí para que el Server Component del catch-all no tire del registry
// durante la validación de slug.
import "@/features/brand-studio/actions/registry";

import dynamic from "next/dynamic";

import { SectionPageLoading } from "@/lib/studio-section-page";

import type { BrandStudioSectionSlug } from "./section-slugs";

/**
 * Mapa per-slug → componente dinámico. Cada `dynamic(() => import(...))`
 * genera su propio chunk de Turbopack/webpack; visitar una sola sección
 * ya NO compila los 10 schemas + form-runtime completo en una sola
 * unidad, lo que causaba OOM en `visionarias_client_dev`.
 *
 * Los per-section files usan named exports (política
 * `test-no-default-exports`). `next/dynamic` requiere resolver a
 * `{ default }` — lo hacemos via `.then()`.
 *
 * El orden sigue `BRAND_STUDIO_SECTION_SLUGS` en `section-slugs.ts`.
 */
const SECTION_COMPONENT_MAP: Record<BrandStudioSectionSlug, ReturnType<typeof dynamic>> = {
  identity: dynamic(
    () => import("./sections/identity-page").then((m) => ({ default: m.IdentityPage })),
    { loading: () => <SectionPageLoading /> },
  ),
  estilo: dynamic(() => import("./sections/estilo-page").then((m) => ({ default: m.EstiloPage })), {
    loading: () => <SectionPageLoading />,
  }),
  legal: dynamic(() => import("./sections/legal-page").then((m) => ({ default: m.LegalPage })), {
    loading: () => <SectionPageLoading />,
  }),
  visuals: dynamic(
    () => import("./sections/visuals-page").then((m) => ({ default: m.VisualsPage })),
    { loading: () => <SectionPageLoading /> },
  ),
  contact: dynamic(
    () => import("./sections/contact-page").then((m) => ({ default: m.ContactPage })),
    { loading: () => <SectionPageLoading /> },
  ),
  methodology: dynamic(
    () => import("./sections/methodology-page").then((m) => ({ default: m.MethodologyPage })),
    { loading: () => <SectionPageLoading /> },
  ),
  story: dynamic(() => import("./sections/story-page").then((m) => ({ default: m.StoryPage })), {
    loading: () => <SectionPageLoading />,
  }),
  positioning: dynamic(
    () => import("./sections/positioning-page").then((m) => ({ default: m.PositioningPage })),
    { loading: () => <SectionPageLoading /> },
  ),
  narrative: dynamic(
    () => import("./sections/narrative-page").then((m) => ({ default: m.NarrativePage })),
    { loading: () => <SectionPageLoading /> },
  ),
  "communication-assets": dynamic(
    () =>
      import("./sections/communication-assets-page").then((m) => ({
        default: m.CommunicationAssetsPage,
      })),
    { loading: () => <SectionPageLoading /> },
  ),
};

export interface SectionDispatcherProps {
  slug: BrandStudioSectionSlug;
}

/**
 * Dispatcher client-side que carga lazy la per-section page del `slug`.
 * El Server Component del catch-all renderiza este componente pasando
 * el slug ya validado — la validación (`isBrandStudioSection`) vive en
 * `section-slugs.ts` para no arrastrar nada client al server.
 */
export function SectionDispatcher({ slug }: SectionDispatcherProps) {
  const Component = SECTION_COMPONENT_MAP[slug];
  return <Component />;
}
