"use client";

import { offerPricingSchema } from "@/features/offer-studio/schemas/pricing.schema";

import { createOfferSectionPage } from "../create-offer-section-page";

export const PricingPage = createOfferSectionPage({
  schema: offerPricingSchema,
  sectionKey: "pricing",
  requiredScope: "mixed",
  save: (h) => h.updatePricing,
});
