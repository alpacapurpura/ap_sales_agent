"use client";

import { offerFaqSchema } from "@/features/offer-studio/schemas/faq.schema";

import { createOfferSectionPage } from "../create-offer-section-page";

// Collection section — save vive en rutas de detalle dedicadas.
export const FaqPage = createOfferSectionPage({
  schema: offerFaqSchema,
  sectionKey: "faq",
  requiredScope: "offer_level",
});
