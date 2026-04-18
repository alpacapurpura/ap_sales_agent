import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Strategy — who the offer is for and how it is positioned.
 *
 * Operates on the ``Offer`` row across editions: avatar match + pain/desires
 * are authored once and reused for every cohort, convocatoria, or salida.
 */
export const offerStrategySchema: SectionSchema = {
  key: "offer.strategy",
  title: "Estrategia y avatar",
  description: "Para quién es esta oferta y qué problema resuelve.",
  scope: "offer_level",
  fields: [
    {
      id: "avatar_id",
      label: "Buyer persona principal",
      type: "text",
      path: "avatar_id",
      hint: "Selecciona un buyer persona definido en Brand Studio. Vacío = cualquier audiencia.",
    },
    {
      id: "target_avatar_match",
      label: "Arquetipos adicionales (descriptivos)",
      type: "textarea",
      path: "target_avatar_match_raw",
      rows: 3,
      hint: "Uno por línea. Arquetipos que el SDR puede usar para abrir conversación.",
    },
    {
      id: "marketing_pain_points",
      label: "Dolores del avatar",
      type: "textarea",
      path: "marketing_pain_points_raw",
      rows: 4,
      hint: "Uno por línea. Situaciones concretas que el avatar ya no aguanta.",
    },
    {
      id: "marketing_desires",
      label: "Deseos del avatar",
      type: "textarea",
      path: "marketing_desires_raw",
      rows: 4,
      hint: "Uno por línea. Lo que el avatar quiere lograr / evitar.",
    },
    {
      id: "anti_avatar_keywords",
      label: "Anti-avatar (palabras para descalificar)",
      type: "textarea",
      path: "anti_avatar_keywords_raw",
      rows: 3,
      hint: "Uno por línea. Si el lead menciona alguna, el SDR lo descarta.",
    },
  ],
};
