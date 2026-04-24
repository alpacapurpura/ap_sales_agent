"use client";

// Side-effect: bootstrap del action registry una vez cuando cualquier
// sección del offer-studio monta. Antes vivía en `schemas/index.ts`;
// se movió aquí para que el Server Component del catch-all no tire del
// registry durante la validación de slug.
import "@/features/offer-studio/actions/registry";

import dynamic from "next/dynamic";

import { SectionPageLoading } from "@/lib/studio-section-page";

import type { OfferStudioSectionSlug } from "./section-slugs";
import type { ComponentType } from "react";

type OfferSectionComponent = ComponentType<{ offerId: string; editionCode: string }>;

/**
 * Mapa per-slug → componente dinámico. Cada `dynamic(() => import(...))`
 * genera su propio chunk de Turbopack/webpack. Visitar
 * `/editor/{slug}` NO compila los 21 schemas + form-runtime en una sola
 * unidad (causa raíz del OOM en `visionarias_client_dev`).
 *
 * Los per-section files usan named exports (política
 * `test-no-default-exports`). `next/dynamic` requiere resolver a
 * `{ default }` — lo hacemos via `.then()`.
 *
 * El orden sigue `OFFER_STUDIO_SECTION_SLUGS` en `section-slugs.ts`.
 */
const SECTION_COMPONENT_MAP: Record<OfferStudioSectionSlug, OfferSectionComponent> = {
  identity: dynamic(
    () => import("./sections/identity-page").then((m) => ({ default: m.IdentityPage })),
    { loading: () => <SectionPageLoading /> },
  ),
  strategy: dynamic(
    () => import("./sections/strategy-page").then((m) => ({ default: m.StrategyPage })),
    { loading: () => <SectionPageLoading /> },
  ),
  psychology: dynamic(
    () => import("./sections/psychology-page").then((m) => ({ default: m.PsychologyPage })),
    { loading: () => <SectionPageLoading /> },
  ),
  promise: dynamic(
    () => import("./sections/promise-page").then((m) => ({ default: m.PromisePage })),
    { loading: () => <SectionPageLoading /> },
  ),
  value_stack: dynamic(
    () => import("./sections/value-stack-page").then((m) => ({ default: m.ValueStackPage })),
    { loading: () => <SectionPageLoading /> },
  ),
  instructors: dynamic(
    () => import("./sections/instructors-page").then((m) => ({ default: m.InstructorsPage })),
    { loading: () => <SectionPageLoading /> },
  ),
  knowledge: dynamic(
    () => import("./sections/knowledge-page").then((m) => ({ default: m.KnowledgePage })),
    { loading: () => <SectionPageLoading /> },
  ),
  closing: dynamic(
    () => import("./sections/closing-page").then((m) => ({ default: m.ClosingPage })),
    { loading: () => <SectionPageLoading /> },
  ),
  product_details: dynamic(
    () =>
      import("./sections/product-details-page").then((m) => ({
        default: m.ProductDetailsPage,
      })),
    { loading: () => <SectionPageLoading /> },
  ),
  subscription_details: dynamic(
    () =>
      import("./sections/subscription-details-page").then((m) => ({
        default: m.SubscriptionDetailsPage,
      })),
    { loading: () => <SectionPageLoading /> },
  ),
  gallery: dynamic(
    () => import("./sections/gallery-page").then((m) => ({ default: m.GalleryPage })),
    { loading: () => <SectionPageLoading /> },
  ),
  event_details: dynamic(
    () =>
      import("./sections/event-details-page").then((m) => ({
        default: m.EventDetailsPage,
      })),
    { loading: () => <SectionPageLoading /> },
  ),
  pricing: dynamic(
    () => import("./sections/pricing-page").then((m) => ({ default: m.PricingPage })),
    { loading: () => <SectionPageLoading /> },
  ),
  program_details: dynamic(
    () =>
      import("./sections/program-details-page").then((m) => ({
        default: m.ProgramDetailsPage,
      })),
    { loading: () => <SectionPageLoading /> },
  ),
  service_details: dynamic(
    () =>
      import("./sections/service-details-page").then((m) => ({
        default: m.ServiceDetailsPage,
      })),
    { loading: () => <SectionPageLoading /> },
  ),
  resources: dynamic(
    () => import("./sections/resources-page").then((m) => ({ default: m.ResourcesPage })),
    { loading: () => <SectionPageLoading /> },
  ),
  faq: dynamic(() => import("./sections/faq-page").then((m) => ({ default: m.FaqPage })), {
    loading: () => <SectionPageLoading />,
  }),
  testimonials: dynamic(
    () => import("./sections/testimonials-page").then((m) => ({ default: m.TestimonialsPage })),
    { loading: () => <SectionPageLoading /> },
  ),
  portfolio: dynamic(
    () => import("./sections/portfolio-page").then((m) => ({ default: m.PortfolioPage })),
    { loading: () => <SectionPageLoading /> },
  ),
  location: dynamic(
    () => import("./sections/location-page").then((m) => ({ default: m.LocationPage })),
    { loading: () => <SectionPageLoading /> },
  ),
  platform_details: dynamic(
    () =>
      import("./sections/platform-details-page").then((m) => ({
        default: m.PlatformDetailsPage,
      })),
    { loading: () => <SectionPageLoading /> },
  ),
};

export interface SectionDispatcherProps {
  slug: OfferStudioSectionSlug;
  offerId: string;
  editionCode: string;
}

/**
 * Dispatcher client-side que carga lazy la per-section page del `slug`.
 * El Server Component del catch-all valida el slug via
 * `isOfferStudioSection` (server-safe) y pasa `offerId` + `editionCode`
 * como props. Este componente solo mapea el slug → chunk dinámico.
 */
export function SectionDispatcher({ slug, offerId, editionCode }: SectionDispatcherProps) {
  const Component = SECTION_COMPONENT_MAP[slug];
  return <Component offerId={offerId} editionCode={editionCode} />;
}
