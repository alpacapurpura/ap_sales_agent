// Action registry bootstrap vive en `pages/SectionDispatcher.tsx`
// post-refactor Fase 2 — se ejecuta una vez cuando cualquier sección
// monta. Mantenerlo aquí hacía que el Server Component del catch-all
// tirara del registry durante la compilación del grafo.
// Consumers del barrel (tests, stories) que necesiten el registry deben
// importar `@/features/offer-studio/actions/registry` directamente.
import { offerClosingSchema } from "./closing.schema";
import { offerEventDetailsSchema } from "./event-details.schema";
import { offerFaqSchema } from "./faq.schema";
import { offerGallerySchema } from "./gallery.schema";
import { offerIdentitySchema } from "./identity.schema";
import { offerInstructorsSchema } from "./instructors.schema";
import { offerKnowledgeSchema } from "./knowledge.schema";
import { offerLocationSchema } from "./location.schema";
import { offerPlatformDetailsSchema } from "./platform-details.schema";
import { offerPortfolioSchema } from "./portfolio.schema";
import { offerPricingSchema } from "./pricing.schema";
import { offerProductDetailsSchema } from "./product-details.schema";
import { offerProgramDetailsSchema } from "./program-details.schema";
import { offerPromiseSchema } from "./promise.schema";
import { offerPsychologySchema } from "./psychology.schema";
import { offerResourcesSchema } from "./resources.schema";
import { offerServiceDetailsSchema } from "./service-details.schema";
import { offerStrategySchema } from "./strategy.schema";
import { offerSubscriptionDetailsSchema } from "./subscription-details.schema";
import { offerTestimonialsSchema } from "./testimonials.schema";
import { offerValueStackSchema } from "./value-stack.schema";

import type { SectionKey } from "../api/archetype-catalog-api";
import type { SectionSchema } from "@/lib/form-runtime/schema";

export {
  offerClosingSchema,
  offerEventDetailsSchema,
  offerFaqSchema,
  offerGallerySchema,
  offerIdentitySchema,
  offerInstructorsSchema,
  offerKnowledgeSchema,
  offerLocationSchema,
  offerPlatformDetailsSchema,
  offerPortfolioSchema,
  offerPricingSchema,
  offerProductDetailsSchema,
  offerProgramDetailsSchema,
  offerPromiseSchema,
  offerPsychologySchema,
  offerResourcesSchema,
  offerServiceDetailsSchema,
  offerStrategySchema,
  offerSubscriptionDetailsSchema,
  offerTestimonialsSchema,
  offerValueStackSchema,
};

/**
 * Keyed registry of every offer-studio section schema. Keys match the
 * backend ``SectionKey`` enum verbatim, so URL segments, copilot route-tool
 * maps, and schema lookups share a single identifier space.
 *
 * The arch test ``test-offer-schema-registry-alignment`` fails CI if a
 * ``SectionKey`` appears without a schema here (or vice versa) — keeping
 * the backend catalog and the frontend registry lockstep.
 */
export const OFFER_SCHEMA_REGISTRY: Readonly<Record<SectionKey, SectionSchema>> = {
  identity: offerIdentitySchema,
  strategy: offerStrategySchema,
  psychology: offerPsychologySchema,
  promise: offerPromiseSchema,
  value_stack: offerValueStackSchema,
  instructors: offerInstructorsSchema,
  knowledge: offerKnowledgeSchema,
  closing: offerClosingSchema,
  product_details: offerProductDetailsSchema,
  subscription_details: offerSubscriptionDetailsSchema,
  gallery: offerGallerySchema,
  event_details: offerEventDetailsSchema,
  pricing: offerPricingSchema,
  program_details: offerProgramDetailsSchema,
  service_details: offerServiceDetailsSchema,
  resources: offerResourcesSchema,
  // Nuevas secciones (Latam mass-market rollout)
  faq: offerFaqSchema,
  testimonials: offerTestimonialsSchema,
  portfolio: offerPortfolioSchema,
  location: offerLocationSchema,
  platform_details: offerPlatformDetailsSchema,
};

/**
 * Lookup helper for direct access to a section schema by its key. Kept
 * alongside the registry so consumer code reads as
 * ``getOfferSchema("pricing")`` rather than manually indexing the map.
 */
export function getOfferSchema(key: SectionKey): SectionSchema {
  return OFFER_SCHEMA_REGISTRY[key];
}
