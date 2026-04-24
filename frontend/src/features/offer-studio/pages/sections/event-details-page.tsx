"use client";

import { offerEventDetailsSchema } from "@/features/offer-studio/schemas/event-details.schema";

import { createOfferSectionPage } from "../create-offer-section-page";

export const EventDetailsPage = createOfferSectionPage({
  schema: offerEventDetailsSchema,
  sectionKey: "event_details",
  requiredScope: "edition_level",
  save: (h) => h.updateEventDetails,
});
