import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Value stack — the itemised list of deliverables shown on landing pages
 * and checkout. Each deliverable carries a label + description + perceived
 * value used by the SDR to defend price.
 *
 * Persists to ``Offer.deliverables`` — shared across editions. Per-edition
 * deliverables are out of scope; if a launch needs extras, use the
 * ``resources`` section (MIXED) instead.
 */
export const offerValueStackSchema: SectionSchema = {
  key: "offer.value_stack",
  // title + description resolved from the backend SectionCatalog.
  scope: "offer_level",
  fields: [
    {
      id: "deliverables",
      label: "Entregables",
      type: "array",
      path: "deliverables",
      hint: "Cada entrega concreta que recibe el cliente. Agregá tantos como quieras defender.",
      itemSchema: {
        description: "Un componente del stack — concreto, enumerable, defendible.",
        fields: [
          { id: "title", label: "Título", type: "text", path: "title", required: true },
          {
            id: "description",
            label: "Descripción",
            type: "textarea",
            path: "description",
            rows: 3,
          },
          {
            id: "perceived_value",
            label: "Valor percibido (USD)",
            type: "number",
            path: "perceived_value",
            hint: "El precio que tendría si se vendiera suelto.",
          },
          {
            id: "fulfillment_note",
            label: "Nota de entrega",
            type: "text",
            path: "fulfillment_note",
            hint: "Cómo / cuándo se entrega (Ej: 'Semana 1', 'Descarga inmediata').",
          },
        ],
      },
    },
  ],
};
