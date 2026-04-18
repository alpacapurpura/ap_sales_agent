import type { SectionSchema } from "@/lib/form-runtime/schema";

export const testimonialsSchema: SectionSchema = {
  key: "brand.testimonials",
  title: "Testimonios",
  description: "Casos de éxito que tu SDR puede citar en conversación.",
  fields: [
    {
      id: "items",
      label: "Testimonios",
      type: "array",
      path: "items",
      itemSchema: {
        fields: [
          {
            id: "type",
            label: "Formato",
            type: "enum",
            path: "type",
            options: [
              { value: "text", label: "Texto" },
              { value: "video", label: "Video" },
            ],
          },
          {
            id: "content",
            label: "Contenido",
            type: "textarea",
            path: "content",
            rows: 4,
            required: true,
          },
          {
            id: "author_name",
            label: "Nombre del autor",
            type: "text",
            path: "author_name",
            required: true,
          },
          { id: "author_role", label: "Rol / Empresa", type: "text", path: "author_role" },
          {
            id: "rating",
            label: "Rating (1-5)",
            type: "number",
            path: "rating",
          },
          { id: "author_avatar", label: "Avatar (URL)", type: "url", path: "author_avatar" },
        ],
      },
    },
  ],
};
