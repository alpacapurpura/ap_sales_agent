import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Instructors — the people who back the offer with their authority. The
 * frontend reuses the brand-studio team roster as the canonical source:
 * this section carries references (ids) to ``KeyFigure`` records, not
 * duplicated personal data.
 *
 * Persists to ``Offer.instructors`` as an ordered array of ids. The
 * custom ``offer-instructors-picker`` action renders a picker that lets
 * the user add / remove references with a preview pulled from the
 * brand-studio team API.
 */
export const offerInstructorsSchema: SectionSchema = {
  key: "offer.instructors",
  // title + description resolved from the backend SectionCatalog.
  scope: "offer_level",
  fields: [
    {
      id: "instructors",
      label: "Instructores asignados",
      type: "custom",
      path: "instructors",
      action: "offer-instructors-picker",
      hint:
        "Agregá figuras desde tu equipo de marca. La descripción que verá el cliente vive en " +
        "Brand Studio > Equipo — un único lugar para editar biografía y credenciales.",
    },
    {
      id: "authority_notes",
      label: "Notas de autoridad (específicas de esta oferta)",
      type: "textarea",
      path: "authority_notes",
      rows: 4,
      hint:
        "Credenciales adicionales que el SDR puede citar solo para esta oferta (sin afectar al " +
        "perfil maestro del instructor).",
    },
  ],
};
