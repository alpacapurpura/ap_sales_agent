import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Gallery — imágenes y video demo para la landing y los assets auto-
 * generados. Contenido universal a toda la oferta; si una edición necesita
 * visuales distintos se genera una landing edition-specific.
 *
 * Las capturas de testimonios con foto viven en la sección ``testimonials``
 * (campo ``author_photo_url`` por testimonio) — no duplicamos acá.
 */
export const offerGallerySchema: SectionSchema = {
  key: "offer.gallery",
  // title + description resolved from the backend SectionCatalog.
  scope: "offer_level",
  fields: [
    {
      id: "hero_image",
      label: "Imagen principal (hero)",
      type: "custom",
      path: "hero_image",
      action: "offer-gallery-single-image",
      actionProps: { purpose: "hero" },
      hint: "Imagen que abre la landing. Ratio 16:9, tamaño mínimo 1600x900 para pantallas retina. Si no cargás una, se usa el logo principal de tu marca.",
    },
    {
      id: "gallery_images",
      label: "Galería complementaria",
      type: "custom",
      path: "gallery_images",
      action: "offer-gallery-multi-image",
      hint: "Imágenes secundarias que rotan en la landing y alimentan los assets auto-generados (ads, reels). 4-8 imágenes diversificadas (producto, uso, instalación, equipo).",
    },
    {
      id: "video_demo_url",
      label: "Video demo de la oferta",
      type: "url",
      path: "video_demo_url",
      placeholder: "https://youtube.com/watch?v=... · https://vimeo.com/...",
      hint: "Video corto (60-120s) mostrando la oferta en acción. YouTube o Vimeo. El agente lo cita en objeciones del tipo 'no entiendo cómo funciona'.",
    },
    {
      id: "before_after_pairs",
      label: "Pares antes / después",
      type: "array",
      path: "before_after_pairs",
      hint: "Para ofertas de transformación (fitness, salud estética, coaching, diseño) — convierten 3x más que fotos sueltas.",
      itemSchema: {
        description: "Un par de imágenes antes/después con contexto del cliente.",
        fields: [
          { id: "before_url", label: "URL imagen antes", type: "url", path: "before_url", required: true },
          { id: "after_url", label: "URL imagen después", type: "url", path: "after_url", required: true },
          { id: "caption", label: "Epígrafe (opcional)", type: "text", path: "caption", placeholder: "María — 8 kg en 12 semanas" },
        ],
      },
    },
  ],
};
