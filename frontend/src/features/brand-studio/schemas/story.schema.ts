import type { SectionSchema } from "@/lib/form-runtime/schema";

export const storySchema: SectionSchema = {
  key: "brand.story",
  title: "Historia",
  description: "De dónde vienes y hacia dónde vas.",
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
      hint: "Para qué existe tu negocio hoy. El cambio concreto que quieres producir en tus clientes.",
    },
    {
      id: "vision",
      label: "Visión",
      type: "textarea",
      path: "vision",
      rows: 3,
      hint: "Cómo se ve el mundo o tu industria si tu marca tiene éxito a largo plazo.",
    },
    {
      id: "milestones",
      label: "Hitos",
      type: "array",
      path: "milestones",
      hint: "Los momentos que marcaron el crecimiento de tu marca. Dan credibilidad y muestran trayectoria.",
      itemSchema: {
        fields: [
          {
            id: "year",
            label: "Año",
            type: "text",
            path: "year",
            required: true,
            hint: "El año en que ocurrió este hito (formato: 2023).",
          },
          {
            id: "title",
            label: "Título",
            type: "text",
            path: "title",
            required: true,
            hint: "Nombre corto del hito. Ej: 'Primera cohorte de 50 alumnos', 'Mención en Forbes'.",
          },
          {
            id: "description",
            label: "Descripción",
            type: "textarea",
            path: "description",
            rows: 2,
            hint: "Contexto del hito: qué pasó, qué significó para la marca y qué cambió después.",
          },
        ],
      },
    },
  ],
};
