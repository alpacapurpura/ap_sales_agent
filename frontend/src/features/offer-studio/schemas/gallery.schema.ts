import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Visual gallery — images and videos used on landing pages + checkout.
 *
 * Images apply offer-wide (the hero photo is the hero photo regardless
 * of cohort). Per-edition hero overrides are not modelled — if a launch
 * needs different visuals, create an edition-specific landing.
 */
export const offerGallerySchema: SectionSchema = {
  key: "offer.gallery",
  title: "Galería visual",
  description: "Imágenes y recursos visuales para assets y landing.",
  scope: "offer_level",
  fields: [
    {
      id: "hero_image",
      label: "Imagen principal",
      type: "custom",
      path: "hero_image",
      action: "offer-gallery-single-image",
      actionProps: { purpose: "hero" },
      hint: "La imagen que abre la landing. Tamaño ideal: 1600x900.",
    },
    {
      id: "gallery_images",
      label: "Galería completa",
      type: "custom",
      path: "gallery_images",
      action: "offer-gallery-multi-image",
      hint: "Imágenes secundarias que rotan en la landing y se usan en assets.",
    },
    {
      id: "testimonial_images",
      label: "Testimonios con foto",
      type: "custom",
      path: "testimonial_images",
      action: "offer-gallery-testimonials",
      hint: "Capturas de testimonios + foto del cliente. Mejoran conversion en landing.",
    },
  ],
};
