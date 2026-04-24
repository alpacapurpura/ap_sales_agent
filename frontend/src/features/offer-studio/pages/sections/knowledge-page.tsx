"use client";

import { offerKnowledgeSchema } from "@/features/offer-studio/schemas/knowledge.schema";

import { createOfferSectionPage } from "../create-offer-section-page";

// Collection section — save vive en rutas de detalle dedicadas.
export const KnowledgePage = createOfferSectionPage({
  schema: offerKnowledgeSchema,
  sectionKey: "knowledge",
  requiredScope: "offer_level",
});
