"use client";

import { offerInstructorsSchema } from "@/features/offer-studio/schemas/instructors.schema";

import { createOfferSectionPage } from "../create-offer-section-page";

// Collection section — save vive en rutas de detalle dedicadas.
export const InstructorsPage = createOfferSectionPage({
  schema: offerInstructorsSchema,
  sectionKey: "instructors",
  requiredScope: "offer_level",
});
