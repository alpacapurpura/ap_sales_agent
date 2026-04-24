"use client";

import { offerSubscriptionDetailsSchema } from "@/features/offer-studio/schemas/subscription-details.schema";

import { createOfferSectionPage } from "../create-offer-section-page";

export const SubscriptionDetailsPage = createOfferSectionPage({
  schema: offerSubscriptionDetailsSchema,
  sectionKey: "subscription_details",
  requiredScope: "offer_level",
  save: (h) => h.updateSubscriptionDetails,
});
