"use client";

import { offerStrategySchema } from "@/features/offer-studio/schemas/strategy.schema";

import { createOfferSectionPage } from "../create-offer-section-page";

export const StrategyPage = createOfferSectionPage({
  schema: offerStrategySchema,
  sectionKey: "strategy",
  requiredScope: "offer_level",
  save: (h) => h.updateStrategy,
});
