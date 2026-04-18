import type { SectionSchema } from "@/lib/form-runtime/schema";

export const positioningSchema: SectionSchema = {
  key: "brand.positioning",
  title: "Posicionamiento",
  description: "Brand Love Key: UVP, insight, beneficios, RTBs, esencia.",
  fields: [
    {
      id: "unique_value_proposition",
      label: "Propuesta de valor única",
      type: "textarea",
      path: "unique_value_proposition",
      rows: 3,
    },
    {
      id: "discriminator",
      label: "Discriminador",
      type: "textarea",
      path: "discriminator",
      rows: 2,
      hint: "Qué te hace imposible de confundir con la competencia.",
    },
    { id: "brand_essence", label: "Esencia de marca", type: "text", path: "brand_essence" },

    // Competitive environment
    {
      id: "technical_enemy",
      label: "Enemigo técnico",
      type: "textarea",
      path: "competitive_environment.technical_enemy",
      rows: 2,
    },
    {
      id: "philosophical_enemy",
      label: "Enemigo filosófico",
      type: "textarea",
      path: "competitive_environment.philosophical_enemy",
      rows: 2,
    },

    // Insight
    {
      id: "insight_tension",
      label: "Insight: tensión",
      type: "textarea",
      path: "insight.tension",
      rows: 2,
    },
    {
      id: "insight_observation",
      label: "Insight: observación",
      type: "textarea",
      path: "insight.observation",
      rows: 2,
    },
    {
      id: "insight_implication",
      label: "Insight: implicación",
      type: "textarea",
      path: "insight.implication",
      rows: 2,
    },

    // Values + archetype
    {
      id: "archetype",
      label: "Arquetipo",
      type: "enum",
      path: "values.archetype",
      options: [
        { value: "sage", label: "Sabio" },
        { value: "hero", label: "Héroe" },
        { value: "rebel", label: "Rebelde" },
        { value: "explorer", label: "Explorador" },
        { value: "creator", label: "Creador" },
        { value: "caregiver", label: "Cuidador" },
        { value: "ruler", label: "Gobernante" },
        { value: "magician", label: "Mago" },
        { value: "innocent", label: "Inocente" },
        { value: "jester", label: "Bufón" },
        { value: "lover", label: "Amante" },
        { value: "everyman", label: "Persona común" },
      ],
    },

    // Reasons to believe (array)
    {
      id: "reasons_to_believe",
      label: "Reasons to believe",
      type: "array",
      path: "reasons_to_believe",
      itemSchema: {
        fields: [
          { id: "type", label: "Tipo", type: "text", path: "type" },
          {
            id: "statement",
            label: "Afirmación",
            type: "textarea",
            path: "statement",
            rows: 2,
            required: true,
          },
          { id: "proof_url", label: "URL de prueba", type: "url", path: "proof_url" },
        ],
      },
    },
  ],
};
