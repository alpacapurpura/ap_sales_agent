// Side-effect import: every schema in this barrel references action keys
// registered by features/brand-studio/actions/registry. Importing here
// guarantees the registry is bootstrapped before any consumer page renders
// a custom field — pages only need to import schemas, never the registry.
import "@/features/brand-studio/actions/registry";

import { authoritySchema } from "./authority.schema";
import { avatarsSchema } from "./avatars.schema";
import { buyerPersonaSchema } from "./buyer-persona.schema";
import { communicationAssetsSchema } from "./communication-assets.schema";
import { contactSchema } from "./contact.schema";
import { identitySchema } from "./identity.schema";
import { logosSchema } from "./logos.schema";
import { methodologySchema } from "./methodology.schema";
import { narrativeSchema } from "./narrative.schema";
import { personalitySchema } from "./personality.schema";
import { positioningSchema } from "./positioning.schema";
import { storySchema } from "./story.schema";
import { teamSchema } from "./team.schema";
import { testimonialsSchema } from "./testimonials.schema";
import { visualsSchema } from "./visuals.schema";
import { voiceSchema } from "./voice.schema";

import type { SectionSchema } from "@/lib/form-runtime/schema";

export {
  authoritySchema,
  avatarsSchema,
  buyerPersonaSchema,
  communicationAssetsSchema,
  contactSchema,
  identitySchema,
  logosSchema,
  methodologySchema,
  narrativeSchema,
  personalitySchema,
  positioningSchema,
  storySchema,
  teamSchema,
  testimonialsSchema,
  visualsSchema,
  voiceSchema,
};

/**
 * Keyed registry of every brand-studio section schema. The key matches
 * SectionSchema.key and is the canonical identifier used by copilot tools
 * and URL query params.
 */
export const SCHEMA_REGISTRY: Readonly<Record<string, SectionSchema>> = {
  "brand.identity": identitySchema,
  "brand.voice": voiceSchema,
  "brand.team": teamSchema,
  "brand.authority": authoritySchema,
  "brand.testimonials": testimonialsSchema,
  "brand.visuals": visualsSchema,
  "brand.logos": logosSchema,
  "brand.methodology": methodologySchema,
  "brand.story": storySchema,
  "brand.narrative": narrativeSchema,
  "brand.positioning": positioningSchema,
  "brand.communication-assets": communicationAssetsSchema,
  "brand.personality": personalitySchema,
  "brand.contact": contactSchema,
  "brand.avatars": avatarsSchema,
  "brand.buyer-persona": buyerPersonaSchema,
};

export type BrandStudioSchemaKey = keyof typeof SCHEMA_REGISTRY;
