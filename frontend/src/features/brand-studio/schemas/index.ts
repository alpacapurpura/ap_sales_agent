// Side-effect import: every schema in this barrel references action keys
// registered by features/brand-studio/actions/registry. Importing here
// guarantees the registry is bootstrapped before any consumer page renders
// a custom field — pages only need to import schemas, never the registry.
import "@/features/brand-studio/actions/registry";

import { authorityItemSchema } from "./authority-item.schema";
import { avatarsSchema } from "./avatars.schema";
import { buyerPersonaSchema } from "./buyer-persona.schema";
import { communicationAssetsSchema } from "./communication-assets.schema";
import { contactSchema } from "./contact.schema";
import { identitySchema } from "./identity.schema";
import { legalSchema } from "./legal.schema";
import { logosSchema } from "./logos.schema";
import { methodologySchema } from "./methodology.schema";
import { narrativeSchema } from "./narrative.schema";
import { positioningSchema } from "./positioning.schema";
import { storySchema } from "./story.schema";
import { teamMemberItemSchema } from "./team-member-item.schema";
import { testimonialItemSchema } from "./testimonial-item.schema";
import { visualsSchema } from "./visuals.schema";

import type { SectionSchema } from "@/lib/form-runtime/schema";

export {
  authorityItemSchema,
  avatarsSchema,
  buyerPersonaSchema,
  communicationAssetsSchema,
  contactSchema,
  identitySchema,
  legalSchema,
  logosSchema,
  methodologySchema,
  narrativeSchema,
  positioningSchema,
  storySchema,
  teamMemberItemSchema,
  testimonialItemSchema,
  visualsSchema,
};

/**
 * Keyed registry of every brand-studio section schema. The key matches
 * SectionSchema.key and is the canonical identifier used by copilot tools
 * and URL query params.
 */
export const SCHEMA_REGISTRY: Readonly<Record<string, SectionSchema>> = {
  "brand.identity": identitySchema,
  "brand.legal": legalSchema,
  "brand.visuals": visualsSchema,
  "brand.logos": logosSchema,
  "brand.methodology": methodologySchema,
  "brand.story": storySchema,
  "brand.narrative": narrativeSchema,
  "brand.positioning": positioningSchema,
  "brand.communication-assets": communicationAssetsSchema,
  "brand.contact": contactSchema,
  "brand.avatars": avatarsSchema,
  "brand.buyer-persona": buyerPersonaSchema,
  // Per-instance schemas introduced by the social_proof SSoT.
  "social-proof.testimonial": testimonialItemSchema,
  "social-proof.authority-item": authorityItemSchema,
  "social-proof.team-member": teamMemberItemSchema,
};

export type BrandStudioSchemaKey = keyof typeof SCHEMA_REGISTRY;
