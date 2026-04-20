import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Per-testimonial editor schema. Consumed by ``TestimonialDetailPage``
 * inside the Finder 4-column layout.
 *
 * Backs the ``TestimonialUpdateDTO`` contract exposed by
 * ``/api/v1/social-proof/testimonials/{id}``.
 */
export const testimonialItemSchema: SectionSchema = {
  key: "social-proof.testimonial",
  title: "Testimonio",
  description:
    "Una cita, video o audio de un cliente real. Se reutiliza en la marca, las ofertas y las landings via placements.",
  kind: "collection",
  instanceDisplay: {
    primary: "author_name",
    secondary: "author_role",
    createLabel: "Crear nuevo testimonio",
  },
  fields: [
    // ── Autor ────────────────────────────────────────────────────
    {
      id: "author_name",
      label: "Nombre del autor",
      type: "text",
      path: "author_name",
      required: true,
      placeholder: "Ej: Juana Pérez",
      group: "Autor",
      layout: "half",
      lengthHint: { ideal: [2, 60] },
    },
    {
      id: "author_role",
      label: "Rol / cargo",
      type: "text",
      path: "author_role",
      placeholder: "Ej: CEO de Alpaca Coffee",
      hint: "Cuanto más específico el rol, más confianza transmite el testimonio.",
      group: "Autor",
      layout: "half",
    },
    {
      id: "author_avatar_url",
      label: "Foto del autor",
      type: "url",
      path: "author_avatar_url",
      placeholder: "https://…",
      group: "Autor",
      layout: "full",
    },

    // ── Contenido ─────────────────────────────────────────────────
    {
      id: "content",
      label: "Contenido",
      type: "textarea",
      path: "content",
      rows: 6,
      group: "Contenido",
      hint: "Transcribí el testimonio en las palabras del cliente. Evita reescribirlo.",
      lengthHint: { ideal: [140, 480] },
    },
    {
      id: "media_type",
      label: "Tipo de medio",
      type: "enum",
      path: "media_type",
      options: [
        { value: "text", label: "Texto" },
        { value: "video", label: "Video" },
        { value: "audio", label: "Audio" },
        { value: "image", label: "Imagen" },
      ],
      group: "Contenido",
      layout: "half",
    },
    {
      id: "media_url",
      label: "URL del archivo",
      type: "url",
      path: "media_url",
      placeholder: "https://…",
      hint: "Para testimonios en video/audio/imagen.",
      group: "Contenido",
      layout: "half",
    },
    {
      id: "rating",
      label: "Puntuación (1-5)",
      type: "number",
      path: "rating",
      group: "Contenido",
      layout: "half",
    },

    // ── Metadata ──────────────────────────────────────────────────
    {
      id: "source_url",
      label: "Fuente original",
      type: "url",
      path: "source_url",
      placeholder: "https://twitter.com/…",
      hint: "Link al post, review o mensaje original. Útil para validar autenticidad.",
      group: "Metadata",
      layout: "full",
    },
    {
      id: "captured_at",
      label: "Fecha del testimonio",
      type: "text",
      path: "captured_at",
      placeholder: "YYYY-MM-DD",
      group: "Metadata",
      layout: "half",
    },
    {
      id: "language",
      label: "Idioma",
      type: "text",
      path: "language",
      placeholder: "es",
      hint: "ISO 639-1 (es, en, pt).",
      group: "Metadata",
      layout: "half",
    },
    {
      id: "tags",
      label: "Etiquetas",
      type: "array",
      path: "tags",
      group: "Metadata",
      hint: 'Etiquetas libres — ej: "roi", "rapidez", "soporte".',
      itemSchema: {
        fields: [
          {
            id: "value",
            label: "Etiqueta",
            type: "text",
            path: "value",
            required: true,
          },
        ],
      },
    },
  ],
};
