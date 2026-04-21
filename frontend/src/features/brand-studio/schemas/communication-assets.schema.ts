import type { SectionSchema } from "@/lib/form-runtime/schema";

export const communicationAssetsSchema: SectionSchema = {
  key: "brand.communication-assets",
  title: "Assets de comunicación",
  description: "Conceptos creativos y piezas de funnel listas para usar.",
  fields: [
    {
      id: "creative_concepts",
      label: "Conceptos creativos",
      type: "array",
      path: "creative_concepts",
      hint: "Ideas grandes que guían cómo luce y suena tu marca al comunicar. Cada concepto tiene nombre, descripción y tono asociado.",
      itemSchema: {
        fields: [
          { id: "name", label: "Nombre", type: "text", path: "name", required: true },
          {
            id: "description",
            label: "Descripción",
            type: "textarea",
            path: "description",
            rows: 3,
          },
          { id: "tone", label: "Tono", type: "text", path: "tone" },
        ],
      },
    },
    {
      id: "assets",
      label: "Assets de funnel",
      type: "array",
      path: "assets",
      hint: "Piezas concretas de contenido listas para publicar o programar (reels, correos, carruseles). Organiza por etapa del funnel.",
      itemSchema: {
        fields: [
          { id: "title", label: "Título", type: "text", path: "title", required: true },
          {
            id: "funnel_stage",
            label: "Etapa del funnel",
            type: "enum",
            path: "funnel_stage",
            options: [
              { value: "attraction", label: "Atracción" },
              { value: "capture", label: "Captura" },
              { value: "nurture", label: "Nutrición" },
              { value: "conversion", label: "Conversión" },
              { value: "retention", label: "Retención" },
              { value: "expansion", label: "Expansión" },
            ],
          },
          { id: "asset_type", label: "Tipo de asset", type: "text", path: "asset_type" },
          { id: "idea", label: "Idea", type: "textarea", path: "idea", rows: 3 },
          {
            id: "copy_draft",
            label: "Borrador de copy",
            type: "textarea",
            path: "copy_draft",
            rows: 4,
          },
          { id: "objective", label: "Objetivo", type: "text", path: "objective" },
          { id: "concept_id", label: "Concepto asociado (id)", type: "text", path: "concept_id" },
          {
            id: "status",
            label: "Estado",
            type: "enum",
            path: "status",
            options: [
              { value: "draft", label: "Borrador" },
              { value: "ready", label: "Listo" },
              { value: "published", label: "Publicado" },
            ],
          },
        ],
      },
    },
  ],
};
