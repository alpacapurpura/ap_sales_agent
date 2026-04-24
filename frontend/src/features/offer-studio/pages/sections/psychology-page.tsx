"use client";

import { offerPsychologySchema } from "@/features/offer-studio/schemas/psychology.schema";

import { createOfferSectionPage } from "../create-offer-section-page";

export const PsychologyPage = createOfferSectionPage({
  schema: offerPsychologySchema,
  sectionKey: "psychology",
  requiredScope: "offer_level",
  save: (h) => h.updatePsychology,
});
