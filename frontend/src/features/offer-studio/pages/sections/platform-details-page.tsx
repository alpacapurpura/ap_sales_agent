"use client";

import { offerPlatformDetailsSchema } from "@/features/offer-studio/schemas/platform-details.schema";

import { createOfferSectionPage } from "../create-offer-section-page";

export const PlatformDetailsPage = createOfferSectionPage({
  schema: offerPlatformDetailsSchema,
  sectionKey: "platform_details",
  requiredScope: "offer_level",
  save: (h) => h.updatePlatformDetails,
});
