"use client";

import { offerGallerySchema } from "@/features/offer-studio/schemas/gallery.schema";

import { createOfferSectionPage } from "../create-offer-section-page";

// Collection section — save vive en rutas de detalle dedicadas.
export const GalleryPage = createOfferSectionPage({
  schema: offerGallerySchema,
  sectionKey: "gallery",
  requiredScope: "offer_level",
});
