import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Per-authority-item editor schema. Consumed by
 * ``AuthorityItemDetailPage`` inside the Finder 4-column layout.
 *
 * Backs the ``AuthorityUpdateDTO`` contract exposed by
 * ``/api/v1/social-proof/authority/{id}``.
 */
export const authorityItemSchema: SectionSchema = {
  key: "social-proof.authority-item",
  title: "Señal de autoridad",
  description:
    "Un premio, credencial, mención en medios, logo de cliente o prueba social similar. Se reutiliza cross-surface via placements.",
  kind: "collection",
  instanceDisplay: {
    primary: "entity_name",
    secondary: "authority_type",
    createLabel: "Agregar señal de autoridad",
  },
  fields: [
    // ── Identidad ────────────────────────────────────────────────
    {
      id: "entity_name",
      label: "Nombre de la entidad",
      type: "text",
      path: "entity_name",
      required: true,
      placeholder: "Ej: Forbes, Harvard, Google, etc.",
      group: "Identidad",
      lengthHint: { ideal: [2, 60] },
    },
    {
      id: "authority_type",
      label: "Tipo",
      type: "enum",
      path: "authority_type",
      required: true,
      options: [
        { value: "certification", label: "Certificación" },
        { value: "award", label: "Premio" },
        { value: "media_mention", label: "Mención en medios" },
        { value: "published_work", label: "Publicación propia" },
        { value: "client_logo", label: "Cliente destacado" },
        { value: "credential", label: "Credencial" },
        { value: "partnership", label: "Alianza" },
        { value: "speaking", label: "Ponencia / charla" },
        { value: "podcast", label: "Podcast" },
        { value: "other", label: "Otro" },
      ],
      group: "Identidad",
    },

    // ── Contexto ─────────────────────────────────────────────────
    {
      id: "context",
      label: "Contexto",
      type: "textarea",
      path: "context",
      rows: 4,
      group: "Contexto",
      placeholder: "Ej: Mencionado en la lista 30 Under 30 de 2024 por su trabajo en IA aplicada.",
      hint: "Describe cómo y cuándo se produjo esta señal. Esta línea la lee el SDR y aparece en landings.",
      lengthHint: { ideal: [60, 280] },
    },

    // ── Pruebas ──────────────────────────────────────────────────
    {
      id: "proof_url",
      label: "Enlace de prueba",
      type: "url",
      path: "proof_url",
      placeholder: "https://…",
      hint: "URL al artículo, certificado, premio o publicación original.",
      group: "Pruebas",
    },
    {
      id: "logo_url",
      label: "Logo",
      type: "url",
      path: "logo_url",
      placeholder: "https://…",
      hint: "Logo de la entidad para mostrar en landings.",
      group: "Pruebas",
    },

    // ── Fechas ───────────────────────────────────────────────────
    {
      id: "obtained_at",
      label: "Fecha obtenida",
      type: "text",
      path: "obtained_at",
      placeholder: "YYYY-MM-DD",
      group: "Fechas",
    },
    {
      id: "expires_at",
      label: "Vence",
      type: "text",
      path: "expires_at",
      placeholder: "YYYY-MM-DD",
      hint: "Solo aplica a certificaciones con vigencia.",
      group: "Fechas",
    },
  ],
};
