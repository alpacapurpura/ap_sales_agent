"use client";

import { offerClosingSchema } from "@/features/offer-studio/schemas/closing.schema";

import { createOfferSectionPage } from "../create-offer-section-page";

export const ClosingPage = createOfferSectionPage({
  schema: offerClosingSchema,
  sectionKey: "closing",
  requiredScope: "offer_level",
  save: (h) => h.updateClosing,
});
