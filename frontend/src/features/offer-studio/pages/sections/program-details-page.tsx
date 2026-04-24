"use client";

import { offerProgramDetailsSchema } from "@/features/offer-studio/schemas/program-details.schema";

import { createOfferSectionPage } from "../create-offer-section-page";

export const ProgramDetailsPage = createOfferSectionPage({
  schema: offerProgramDetailsSchema,
  sectionKey: "program_details",
  requiredScope: "mixed",
  save: (h) => h.updateProgramDetails,
});
