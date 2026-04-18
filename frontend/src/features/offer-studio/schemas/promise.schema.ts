import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Promise — transformation the offer commits to deliver.
 *
 * Sits alongside ``identity.headline_promise`` with richer copy: the main
 * promise is the 1-line elevator; this section unpacks the ``why now``,
 * the ``before / after`` framing, and the ``primary_outcome`` support copy.
 */
export const offerPromiseSchema: SectionSchema = {
  key: "offer.promise",
  // title + description resolved from the backend SectionCatalog.
  scope: "offer_level",
  fields: [
    {
      id: "headline_promise",
      label: "Promesa principal",
      type: "textarea",
      path: "headline_promise",
      rows: 2,
      required: true,
      hint: "Copia exacta del titular de identidad — un solo lugar donde editarla.",
    },
    {
      id: "before_state",
      label: "Estado inicial (antes)",
      type: "textarea",
      path: "before_state",
      rows: 3,
      hint: "Cómo vive el avatar hoy, antes de conocer tu oferta.",
    },
    {
      id: "after_state",
      label: "Estado objetivo (después)",
      type: "textarea",
      path: "after_state",
      rows: 3,
      hint: "Cómo vive el avatar después de completar la experiencia.",
    },
    {
      id: "why_now",
      label: "¿Por qué ahora?",
      type: "textarea",
      path: "why_now",
      rows: 3,
      hint: "La razón por la que postergar tiene un costo concreto.",
    },
    {
      id: "primary_outcome",
      label: "Resultado medible",
      type: "textarea",
      path: "primary_outcome",
      rows: 2,
      hint: "El resultado con una métrica o marcador observable.",
    },
  ],
};
