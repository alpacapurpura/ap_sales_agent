// Action registry bootstrap vive en `pages/SectionDispatcher.tsx`
// post-refactor Fase 2 — se ejecuta una vez cuando cualquier sección
// monta. Mantener el side-effect aquí causaba que el Server Component
// del catch-all tirara del registry durante la compilación del grafo.
// Consumers de barrel (tests, stories) que necesiten el registry deben
// importar `@/features/brand-studio/actions/registry` directamente.
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
