import type { SectionSchema } from "@/lib/form-runtime/schema";

export const methodologySchema: SectionSchema = {
  key: "brand.methodology",
  title: "Metodología",
  description: "Cómo operás: el método propio que te distingue.",
  fields: [
    {
      id: "methodology_name",
      label: "Nombre de la metodología",
      type: "text",
      path: "methodology_name",
    },
    {
      id: "methodology_description",
      label: "Descripción",
      type: "textarea",
      path: "methodology_description",
      rows: 4,
    },
    {
      id: "methodology_pillars",
      label: "Pilares",
      type: "array",
      path: "methodology_pillars",
      itemSchema: {
        fields: [
          { id: "title", label: "Título", type: "text", path: "title", required: true },
          {
            id: "description",
            label: "Descripción",
            type: "textarea",
            path: "description",
            rows: 3,
          },
        ],
      },
    },
  ],
};
