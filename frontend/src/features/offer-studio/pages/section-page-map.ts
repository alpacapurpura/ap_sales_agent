import {
  ClosingPage,
  CredentialsPage,
  EventDetailsPage,
  FaqPage,
  GalleryPage,
  IdentityPage,
  InstructorsPage,
  KnowledgePage,
  LocationPage,
  MethodologyPage,
  PlatformDetailsPage,
  PortfolioPage,
  PricingPage,
  ProductDetailsPage,
  ProgramDetailsPage,
  PromisePage,
  PsychologyPage,
  ResourcesPage,
  ServiceDetailsPage,
  StrategyPage,
  SubscriptionDetailsPage,
  TestimonialsPage,
  ValueStackPage,
} from "./section-pages";

import type { SectionKey } from "../api/archetype-catalog-api";

/**
 * Server-safe registry of offer-studio section pages. **No ``"use client"``
 * directive on purpose**: the App Router catch-all at
 * ``app/(main)/[tenantId]/(dashboard)/offer-studio/offer/[id]/edition/[code]/[section]/[[...fieldId]]/page.tsx``
 * is a Server Component and must index this map (``section in
 * OFFER_SECTION_PAGE_MAP``) before deciding whether to 404. If the map
 * lived in a client module its exports would be replaced with opaque
 * client references on the server and the lookup would silently return
 * ``false`` — the exact bug brand-studio hit in Sprint 3 (see
 * LEARNINGS.md §Sprint 3). Keep this file plain-server.
 *
 * Values are client components imported by reference; Next.js renders
 * them through the usual client boundary.
 */
export const OFFER_SECTION_PAGE_MAP = {
  identity: IdentityPage,
  strategy: StrategyPage,
  psychology: PsychologyPage,
  promise: PromisePage,
  value_stack: ValueStackPage,
  instructors: InstructorsPage,
  knowledge: KnowledgePage,
  closing: ClosingPage,
  product_details: ProductDetailsPage,
  subscription_details: SubscriptionDetailsPage,
  gallery: GalleryPage,
  event_details: EventDetailsPage,
  pricing: PricingPage,
  program_details: ProgramDetailsPage,
  service_details: ServiceDetailsPage,
  resources: ResourcesPage,
  // Nuevas secciones (Latam mass-market rollout)
  faq: FaqPage,
  testimonials: TestimonialsPage,
  portfolio: PortfolioPage,
  methodology: MethodologyPage,
  credentials: CredentialsPage,
  location: LocationPage,
  platform_details: PlatformDetailsPage,
} as const satisfies Readonly<
  Record<SectionKey, (props: { offerId: string; editionCode: string }) => React.JSX.Element>
>;

export type OfferStudioSectionSlug = keyof typeof OFFER_SECTION_PAGE_MAP;

/** True when ``slug`` is a valid section key — the catch-all's first gate. */
export function isOfferStudioSection(slug: string): slug is OfferStudioSectionSlug {
  return slug in OFFER_SECTION_PAGE_MAP;
}
