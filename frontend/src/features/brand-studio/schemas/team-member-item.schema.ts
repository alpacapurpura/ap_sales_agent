import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Per-team-member editor schema. Consumed by ``TeamMemberDetailPage``
 * inside the Finder 4-column layout.
 *
 * Backs the ``TeamMemberUpdateDTO`` contract exposed by
 * ``/api/v1/social-proof/team/{id}``.
 */
export const teamMemberItemSchema: SectionSchema = {
  key: "social-proof.team-member",
  title: "Miembro del equipo",
  description:
    "Una persona que representa la marca: liderazgo, instructor, asesor. Se reutiliza cross-surface via placements.",
  kind: "collection",
  instanceDisplay: {
    primary: "name",
    secondary: "role",
    createLabel: "Agregar miembro al equipo",
  },
  fields: [
    // ── Identidad ────────────────────────────────────────────────
    {
      id: "name",
      label: "Nombre completo",
      type: "text",
      path: "name",
      required: true,
      placeholder: "Ej: María García",
      group: "Identidad",
      layout: "half",
      lengthHint: { ideal: [3, 60] },
    },
    {
      id: "role",
      label: "Rol",
      type: "text",
      path: "role",
      placeholder: "Ej: Fundadora, Instructor, Asesor legal",
      group: "Identidad",
      layout: "half",
    },
    {
      id: "is_primary_voice",
      label: "Voz principal de marca",
      type: "boolean",
      path: "is_primary_voice",
      hint: "Solo un miembro por tenant puede ser la voz principal (la voz que el Sales Agent imita).",
      group: "Identidad",
      layout: "half",
    },
    {
      id: "headshot_url",
      label: "Foto de perfil",
      type: "url",
      path: "headshot_url",
      placeholder: "https://…",
      group: "Identidad",
      layout: "half",
    },

    // ── Bio ──────────────────────────────────────────────────────
    {
      id: "bio",
      label: "Bio",
      type: "textarea",
      path: "bio",
      rows: 5,
      group: "Bio",
      hint: "Una bio corta tercera-persona. El SDR la cita para dar contexto cuando habla del equipo.",
      lengthHint: { ideal: [120, 400] },
    },
    {
      id: "gender",
      label: "Género",
      type: "text",
      path: "gender",
      placeholder: "Ej: femenino, masculino, no binario",
      hint: "Lo usa el SDR para concordancia gramatical al referirse a la persona.",
      group: "Bio",
      layout: "half",
    },
    {
      id: "communication_style",
      label: "Estilo de comunicación",
      type: "text",
      path: "communication_style",
      placeholder: "Ej: cálido, directo, académico",
      group: "Bio",
      layout: "half",
    },

    // ── Contacto ─────────────────────────────────────────────────
    {
      id: "work_whatsapp",
      label: "WhatsApp de trabajo",
      type: "text",
      path: "work_whatsapp",
      placeholder: "+51 999 999 999",
      hint: "Se muestra en páginas públicas solo si se vincula a la oferta via placements.",
      group: "Contacto",
      layout: "half",
    },

    // ── Redes personales ─────────────────────────────────────────
    {
      id: "personal_website",
      label: "Sitio web",
      type: "url",
      path: "personal_website",
      placeholder: "https://…",
      group: "Redes personales",
      layout: "full",
    },
    {
      id: "personal_linkedin",
      label: "LinkedIn",
      type: "url",
      path: "personal_linkedin",
      placeholder: "https://linkedin.com/in/…",
      group: "Redes personales",
      layout: "half",
    },
    {
      id: "personal_instagram",
      label: "Instagram",
      type: "url",
      path: "personal_instagram",
      placeholder: "https://instagram.com/…",
      group: "Redes personales",
      layout: "half",
    },
    {
      id: "personal_tiktok",
      label: "TikTok",
      type: "url",
      path: "personal_tiktok",
      placeholder: "https://tiktok.com/@…",
      group: "Redes personales",
      layout: "half",
    },
    {
      id: "personal_facebook",
      label: "Facebook",
      type: "url",
      path: "personal_facebook",
      placeholder: "https://facebook.com/…",
      group: "Redes personales",
      layout: "half",
    },

    // ── Multimedia ───────────────────────────────────────────────
    {
      id: "gallery",
      label: "Galería",
      type: "array",
      path: "gallery",
      group: "Multimedia",
      hint: "URLs de imágenes adicionales — retratos en acción, equipo, eventos.",
      itemSchema: {
        fields: [
          {
            id: "value",
            label: "URL",
            type: "url",
            path: "value",
            required: true,
          },
        ],
      },
    },
    {
      id: "sort_order",
      label: "Orden de aparición",
      type: "number",
      path: "sort_order",
      hint: "Valor bajo = aparece antes en listados públicos.",
      group: "Multimedia",
      layout: "half",
    },
  ],
};
