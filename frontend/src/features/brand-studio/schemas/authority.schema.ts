import type { SectionSchema } from "@/lib/form-runtime/schema";

export const authoritySchema: SectionSchema = {
  key: "brand.authority",
  title: "Autoridad",
  description: "Medios, premios, certificaciones y otros marcadores de credibilidad.",
  fields: [
    {
      id: "items",
      label: "Elementos de autoridad",
      type: "array",
      path: "items",
      itemSchema: {
        fields: [
          { id: "entity_name", label: "Nombre", type: "text", path: "entity_name", required: true },
          {
            id: "type",
            label: "Tipo",
            type: "enum",
            path: "type",
            options: [
              { value: "media", label: "Prensa / Medios" },
              { value: "award", label: "Premio" },
              { value: "certification", label: "Certificación" },
              { value: "partnership", label: "Partnership" },
              { value: "mention", label: "Mención" },
            ],
          },
          {
            id: "context",
            label: "Contexto",
            type: "textarea",
            path: "context",
            rows: 3,
            hint: "Cómo y cuándo obtuviste esta autoridad.",
          },
          { id: "proof_url", label: "URL de prueba", type: "url", path: "proof_url" },
          { id: "logo_url", label: "Logo (URL)", type: "url", path: "logo_url" },
        ],
      },
    },
  ],
};
