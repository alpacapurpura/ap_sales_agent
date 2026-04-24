"use client";

import { offerPromiseSchema } from "@/features/offer-studio/schemas/promise.schema";

import { createOfferSectionPage } from "../create-offer-section-page";

export const PromisePage = createOfferSectionPage({
  schema: offerPromiseSchema,
  sectionKey: "promise",
  requiredScope: "offer_level",
  save: (h) => h.updatePromise,
});
