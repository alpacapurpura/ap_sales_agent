"use client";

import { offerProductDetailsSchema } from "@/features/offer-studio/schemas/product-details.schema";

import { createOfferSectionPage } from "../create-offer-section-page";

export const ProductDetailsPage = createOfferSectionPage({
  schema: offerProductDetailsSchema,
  sectionKey: "product_details",
  requiredScope: "offer_level",
  save: (h) => h.updateProductDetails,
});
