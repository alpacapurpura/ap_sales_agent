"use client";

import { offerResourcesSchema } from "@/features/offer-studio/schemas/resources.schema";

import { createOfferSectionPage } from "../create-offer-section-page";

// Collection section — save vive en rutas de detalle dedicadas.
export const ResourcesPage = createOfferSectionPage({
  schema: offerResourcesSchema,
  sectionKey: "resources",
  requiredScope: "mixed",
});
