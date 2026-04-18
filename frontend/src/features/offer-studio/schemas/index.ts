// Side-effect import: bootstraps the action registry before any schema
// with ``custom`` fields mounts. Matches brand-studio's pattern so pages
// only import schemas and never the registry directly.
import "@/features/offer-studio/actions/registry";

import { offerClosingSchema } from "./closing.schema";
import { offerEventDetailsSchema } from "./event-details.schema";
import { offerGallerySchema } from "./gallery.schema";
import { offerIdentitySchema } from "./identity.schema";
import { offerInstructorsSchema } from "./instructors.schema";
import { offerKnowledgeSchema } from "./knowledge.schema";
import { offerPricingSchema } from "./pricing.schema";
import { offerProductDetailsSchema } from "./product-details.schema";
import { offerProgramDetailsSchema } from "./program-details.schema";
import { offerPromiseSchema } from "./promise.schema";
import { offerPsychologySchema } from "./psychology.schema";
import { offerResourcesSchema } from "./resources.schema";
import { offerServiceDetailsSchema } from "./service-details.schema";
import { offerStrategySchema } from "./strategy.schema";
import { offerSubscriptionDetailsSchema } from "./subscription-details.schema";
import { offerValueStackSchema } from "./value-stack.schema";

import type { SectionKey } from "../api/archetype-catalog-api";
import type { SectionSchema } from "@/lib/form-runtime/schema";

export {
  offerClosingSchema,
  offerEventDetailsSchema,
  offerGallerySchema,
  offerIdentitySchema,
  offerInstructorsSchema,
  offerKnowledgeSchema,
  offerPricingSchema,
  offerProductDetailsSchema,
  offerProgramDetailsSchema,
  offerPromiseSchema,
  offerPsychologySchema,
  offerResourcesSchema,
  offerServiceDetailsSchema,
  offerStrategySchema,
  offerSubscriptionDetailsSchema,
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
};

/**
 * Lookup helper for direct access to a section schema by its key. Kept
 * alongside the registry so consumer code reads as
 * ``getOfferSchema("pricing")`` rather than manually indexing the map.
 */
export function getOfferSchema(key: SectionKey): SectionSchema {
  return OFFER_SCHEMA_REGISTRY[key];
}
