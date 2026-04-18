import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Resources — material the customer receives. The ``base_resources`` list
 * applies offer-wide; ``edition_resources`` is a per-launch addition
 * (cohort-exclusive templates, guest speaker recordings, etc.).
 *
 * Under ``/edition/evergreen/`` only ``base_resources`` shows. Under a
 * specific edition URL the user sees the offer baseline (read-only
 * reminder) and can add / remove edition-specific items separately.
 */
export const offerResourcesSchema: SectionSchema = {
  key: "offer.resources",
  // title + description resolved from the backend SectionCatalog.
  scope: "mixed",
  fields: [
    {
      id: "base_resources",
      label: "Recursos base (todas las ediciones)",
      type: "array",
      path: "assets",
      owner: "offer",
      hint: "Recursos que recibe cualquier cliente que compre esta oferta, sin importar la edición.",
      itemSchema: {
        description: "Un recurso del paquete base.",
        fields: [
          { id: "name", label: "Nombre", type: "text", path: "name", required: true },
          {
            id: "type",
            label: "Tipo",
            type: "text",
            path: "type",
            placeholder: "PDF · URL · VIDEO",
          },
          { id: "url", label: "URL", type: "url", path: "url" },
          {
            id: "description",
            label: "Descripción",
            type: "textarea",
            path: "description",
            rows: 2,
          },
        ],
      },
    },
    {
      id: "edition_resources",
      label: "Recursos extra de esta edición",
      type: "array",
      path: "edition_resources",
      owner: "edition",
      hint: "Recursos exclusivos de la cohorte / salida / convocatoria actual.",
      itemSchema: {
        description: "Recurso agregado solo a esta edición.",
        fields: [
          { id: "name", label: "Nombre", type: "text", path: "name", required: true },
          { id: "type", label: "Tipo", type: "text", path: "type" },
          { id: "url", label: "URL", type: "url", path: "url" },
          {
            id: "description",
            label: "Descripción",
            type: "textarea",
            path: "description",
            rows: 2,
          },
        ],
      },
    },
  ],
};
