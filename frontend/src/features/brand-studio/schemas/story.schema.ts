import type { SectionSchema } from "@/lib/form-runtime/schema";

export const storySchema: SectionSchema = {
  key: "brand.story",
  title: "Historia",
  description: "De dónde venís y hacia dónde vas.",
  fields: [
    {
      id: "origin_story",
      label: "Historia de origen",
      type: "textarea",
      path: "origin_story",
      rows: 5,
      hint: "¿Por qué empezó este proyecto? ¿Cuál fue el detonante?",
    },
    {
      id: "mission",
      label: "Misión",
      type: "textarea",
      path: "mission",
      rows: 3,
    },
    {
      id: "vision",
      label: "Visión",
      type: "textarea",
      path: "vision",
      rows: 3,
    },
    {
      id: "milestones",
      label: "Hitos",
      type: "array",
      path: "milestones",
      itemSchema: {
        fields: [
          { id: "year", label: "Año", type: "text", path: "year", required: true },
          { id: "title", label: "Título", type: "text", path: "title", required: true },
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
