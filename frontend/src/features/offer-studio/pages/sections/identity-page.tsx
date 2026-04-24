"use client";

import { offerIdentitySchema } from "@/features/offer-studio/schemas/identity.schema";

import { createOfferSectionPage } from "../create-offer-section-page";

export const IdentityPage = createOfferSectionPage({
  schema: offerIdentitySchema,
  sectionKey: "identity",
  requiredScope: "offer_level",
  save: (h) => h.updateIdentity,
});
