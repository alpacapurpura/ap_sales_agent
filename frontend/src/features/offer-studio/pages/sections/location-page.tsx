"use client";

import { offerLocationSchema } from "@/features/offer-studio/schemas/location.schema";

import { createOfferSectionPage } from "../create-offer-section-page";

export const LocationPage = createOfferSectionPage({
  schema: offerLocationSchema,
  sectionKey: "location",
  requiredScope: "mixed",
  save: (h) => h.updateLocation,
});
