"use client";

import { offerTestimonialsSchema } from "@/features/offer-studio/schemas/testimonials.schema";

import { createOfferSectionPage } from "../create-offer-section-page";

// Collection section — save vive en rutas de detalle dedicadas.
export const TestimonialsPage = createOfferSectionPage({
  schema: offerTestimonialsSchema,
  sectionKey: "testimonials",
  requiredScope: "offer_level",
});
