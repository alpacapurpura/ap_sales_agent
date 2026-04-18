import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Offer identity — name + SKU + headline that every edition inherits.
 *
 * All fields persist to the ``Offer`` aggregate; the ``evergreen`` URL
 * renders this unchanged and every specific-edition URL shows the shared
 * offer-level values (non-overridable — users change them once and they
 * apply everywhere).
 */
export const offerIdentitySchema: SectionSchema = {
  key: "offer.identity",
  // title + description intentionally omitted — resolved from the backend
  // SectionCatalog via useSectionMetadata("identity") in the consumer page.
  scope: "offer_level",
  fields: [
    {
      id: "public_name",
      label: "Nombre público",
      type: "text",
      path: "public_name",
      required: true,
      placeholder: "Ej: Mentoría Liderazgo Q2",
      hint: "El nombre que ve tu audiencia en anuncios, landings y checkout.",
    },
    {
      id: "internal_sku",
      label: "SKU interno",
      type: "text",
      path: "internal_sku",
      placeholder: "Ej: MENT-LIDER-Q2",
      hint: "Identificador corto para reportes y referencias cruzadas. Solo para ti.",
    },
    {
      id: "headline_promise",
      label: "Promesa en titular",
      type: "textarea",
      path: "headline_promise",
      rows: 2,
      placeholder: "Ej: Lidera sin agotarte en 12 semanas",
      hint: "Una línea. La promesa que debe recordarse después de ver el anuncio.",
    },
    {
      id: "primary_outcome",
      label: "Resultado principal",
      type: "textarea",
      path: "primary_outcome",
      rows: 2,
      hint: "¿Qué obtiene el cliente al terminar la experiencia?",
    },
    {
      id: "time_to_value",
      label: "Tiempo hasta el resultado",
      type: "text",
      path: "time_to_value",
      placeholder: "Ej: 30 días · 1 trimestre · Dentro de la primera semana",
      hint: "Cuánto tarda el cliente en sentir el primer resultado útil.",
    },
  ],
};
