"use client";

import { offerValueStackSchema } from "@/features/offer-studio/schemas/value-stack.schema";

import { createOfferSectionPage } from "../create-offer-section-page";

export const ValueStackPage = createOfferSectionPage({
  schema: offerValueStackSchema,
  sectionKey: "value_stack",
  requiredScope: "offer_level",
  save: (h) => h.updateValueStack,
});
