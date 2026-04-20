import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Offer identity — nombre público + frase titular + tiempo hasta el
 * resultado. Todos los campos persisten al ``Offer`` aggregate y son
 * compartidos entre todas las ediciones (no se sobreescriben por edición).
 *
 * SKU interno se auto-genera en el backend al crear la oferta — no lo
 * expone el editor para evitar fricción al microempresario. Las otras
 * secciones que tenían duplicados de ``headline_promise`` +
 * ``primary_outcome`` fueron removidas — IDENTITY es la SSoT.
 */
export const offerIdentitySchema: SectionSchema = {
  key: "offer.identity",
  // title + description resolved from the backend SectionCatalog.
  scope: "offer_level",
  fields: [
    {
      id: "public_name",
      label: "Nombre público",
      type: "text",
      path: "public_name",
      required: true,
      placeholder: "ej. Mentoría Liderazgo Q2",
      hint: "El nombre que ve tu audiencia en anuncios, landings y checkout. El agente lo usa al responder consultas.",
    },
    {
      id: "headline_promise",
      label: "Frase titular",
      type: "textarea",
      path: "headline_promise",
      rows: 2,
      required: true,
      placeholder: "ej. Lidera sin agotarte en 12 semanas",
      hint: "Una línea memorable con el resultado que prometes. Es la promesa central que debe recordarse después del anuncio. Cárgala concreta y en primera persona del beneficio.",
    },
    {
      id: "primary_outcome",
      label: "Resultado principal",
      type: "textarea",
      path: "primary_outcome",
      rows: 2,
      placeholder: "ej. Duplicar capacidad de liderar equipos sin agotamiento",
      hint: "Lo que el cliente obtiene al terminar. Más descriptivo que la frase titular — el agente lo cita en conversaciones de descubrimiento.",
    },
    {
      id: "time_to_value",
      label: "Tiempo hasta el primer resultado",
      type: "text",
      path: "time_to_value",
      placeholder: "ej. 30 días · 1 trimestre · Primera semana",
      hint: "Cuánto tarda el cliente en sentir el primer resultado útil. Reduce la ansiedad pre-compra y lo usa el agente para manejar la objeción 'cuánto tarda'.",
    },
  ],
};
