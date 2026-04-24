"use client";

import { offerServiceDetailsSchema } from "@/features/offer-studio/schemas/service-details.schema";

import { createOfferSectionPage } from "../create-offer-section-page";

export const ServiceDetailsPage = createOfferSectionPage({
  schema: offerServiceDetailsSchema,
  sectionKey: "service_details",
  requiredScope: "mixed",
  save: (h) => h.updateServiceDetails,
});
