import type { SectionSchema } from "@/lib/form-runtime/schema";

export const teamSchema: SectionSchema = {
  key: "brand.team",
  title: "Equipo",
  description: "Las personas detrás de la marca. El sales agent puede citarlas.",
  fields: [
    {
      id: "members",
      label: "Miembros",
      type: "array",
      path: "members",
      itemSchema: {
        fields: [
          { id: "name", label: "Nombre", type: "text", path: "name", required: true },
          { id: "role", label: "Rol", type: "text", path: "role", required: true },
          {
            id: "bio",
            label: "Bio",
            type: "textarea",
            path: "bio",
            rows: 3,
            hint: "Trayectoria breve, experiencia relevante.",
          },
          {
            id: "is_primary_voice",
            label: "Es la voz principal",
            type: "boolean",
            path: "is_primary_voice",
          },
          {
            id: "gender",
            label: "Género",
            type: "text",
            path: "gender",
          },
          {
            id: "communication_style",
            label: "Estilo de comunicación",
            type: "text",
            path: "communication_style",
          },
          {
            id: "headshot_url",
            label: "Foto (URL)",
            type: "url",
            path: "headshot_url",
          },
          {
            id: "headshot_picker",
            label: "Seleccionar foto de la galería",
            type: "custom",
            path: "headshot_url",
            action: "image-gallery",
          },
          { id: "personal_website", label: "Sitio web", type: "url", path: "personal_website" },
          { id: "personal_linkedin", label: "LinkedIn", type: "url", path: "personal_linkedin" },
          {
            id: "personal_instagram",
            label: "Instagram",
            type: "text",
            path: "personal_instagram",
          },
          { id: "personal_tiktok", label: "TikTok", type: "text", path: "personal_tiktok" },
          { id: "personal_facebook", label: "Facebook", type: "text", path: "personal_facebook" },
          {
            id: "work_whatsapp",
            label: "WhatsApp de trabajo",
            type: "text",
            path: "work_whatsapp",
          },
        ],
      },
    },
  ],
};
