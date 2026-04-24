"use client";

import { offerPortfolioSchema } from "@/features/offer-studio/schemas/portfolio.schema";

import { createOfferSectionPage } from "../create-offer-section-page";

// Collection section — save vive en rutas de detalle dedicadas.
export const PortfolioPage = createOfferSectionPage({
  schema: offerPortfolioSchema,
  sectionKey: "portfolio",
  requiredScope: "offer_level",
});
