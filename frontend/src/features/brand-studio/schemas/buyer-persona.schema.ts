import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Buyer persona (avatar) detail schema. Drives the per-persona detail page
 * where the sales agent reads the full profile from. Fields map 1:1 to the
 * BuyerPersonaSectionUpdateDTO shape.
 *
 * Dotted paths mirror the nested shape (demographics.age_range,
 * buyer_journey.awareness, etc.) — the form-runtime writes each path back
 * via the section's composed patch.
 */
export const buyerPersonaSchema: SectionSchema = {
  key: "brand.buyer-persona",
  title: "Buyer persona",
  description: "Perfil arquetípico del cliente ideal. El SDR lo usa para segmentar y personalizar.",
  fields: [
    // ── Identidad ────────────────────────────────────────────────────────
    {
      id: "name",
      label: "Nombre",
      type: "text",
      path: "name",
      required: true,
      placeholder: "Ej: María la creadora",
    },
    {
      id: "tagline",
      label: "Tagline",
      type: "text",
      path: "tagline",
      hint: "Una línea que describe quién es esta persona.",
    },

    // ── Demografía ───────────────────────────────────────────────────────
    {
      id: "age_range",
      label: "Rango etario",
      type: "text",
      path: "demographics.age_range",
      placeholder: "Ej: 28-45",
    },
    {
      id: "location",
      label: "Ubicación",
      type: "text",
      path: "demographics.location",
      placeholder: "Ej: Lima, Perú",
    },
    {
      id: "occupation",
      label: "Ocupación",
      type: "text",
      path: "demographics.occupation",
    },
    {
      id: "income",
      label: "Nivel de ingresos",
      type: "text",
      path: "demographics.income",
    },

    // ── Psicografía ──────────────────────────────────────────────────────
    {
      id: "values",
      label: "Valores centrales",
      type: "textarea",
      path: "psychographics.values",
      rows: 3,
    },
    {
      id: "aspirations",
      label: "Aspiraciones",
      type: "textarea",
      path: "psychographics.aspirations",
      rows: 3,
    },
    {
      id: "lifestyle",
      label: "Estilo de vida",
      type: "textarea",
      path: "psychographics.lifestyle",
      rows: 3,
    },

    // ── Dolores & deseos ─────────────────────────────────────────────────
    {
      id: "pain_points",
      label: "Pain points",
      type: "array",
      path: "pain_points",
      itemSchema: {
        fields: [
          {
            id: "description",
            label: "Descripción",
            type: "textarea",
            path: "description",
            rows: 2,
            required: true,
          },
          { id: "severity", label: "Severidad (1-5)", type: "number", path: "severity" },
        ],
      },
    },
    {
      id: "desires",
      label: "Deseos",
      type: "array",
      path: "desires",
      itemSchema: {
        fields: [
          {
            id: "description",
            label: "Descripción",
            type: "textarea",
            path: "description",
            rows: 2,
            required: true,
          },
          { id: "importance", label: "Importancia (1-5)", type: "number", path: "importance" },
        ],
      },
    },
    {
      id: "objections",
      label: "Objeciones",
      type: "array",
      path: "objections",
      itemSchema: {
        fields: [
          {
            id: "text",
            label: "Objeción",
            type: "textarea",
            path: "text",
            rows: 2,
            required: true,
          },
          {
            id: "response",
            label: "Respuesta sugerida",
            type: "textarea",
            path: "response",
            rows: 3,
          },
        ],
      },
    },

    // ── Canales & journey ────────────────────────────────────────────────
    {
      id: "preferred_channels",
      label: "Canales preferidos",
      type: "array",
      path: "preferred_channels",
      itemSchema: {
        fields: [
          { id: "channel", label: "Canal", type: "text", path: "channel", required: true },
          { id: "usage", label: "Uso típico", type: "text", path: "usage" },
        ],
      },
    },
    {
      id: "journey_awareness",
      label: "Etapa de awareness",
      type: "textarea",
      path: "buyer_journey.awareness",
      rows: 2,
    },
    {
      id: "journey_consideration",
      label: "Etapa de consideración",
      type: "textarea",
      path: "buyer_journey.consideration",
      rows: 2,
    },
    {
      id: "journey_decision",
      label: "Etapa de decisión",
      type: "textarea",
      path: "buyer_journey.decision",
      rows: 2,
    },
  ],
};
