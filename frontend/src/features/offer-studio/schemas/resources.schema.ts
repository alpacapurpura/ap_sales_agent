import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Resources — material descargable, accesos y plantillas que recibe el cliente.
 *
 * Scope MIXED con split owner:
 * - ``base_resources`` (owner=offer): recursos que recibe todo cliente
 *   que compra esta oferta, independiente de la edición.
 * - ``edition_resources`` (owner=edition): recursos exclusivos de esta
 *   cohorte / salida / convocatoria. Bonus por ediciones premium.
 *
 * Bajo la URL virtual ``evergreen`` solo rinden los recursos base. Bajo
 * una edición específica, el editor muestra los base como read-only
 * (reminder) + los edition-resources editables.
 *
 * **Latam — decisiones de diseño:**
 * - ``availability_window_description`` evita tickets "no encuentro el
 *   recurso" cuando el acceso se abre en diferido (ej: módulo desbloquea
 *   semana a semana).
 * - El tipo es texto libre en vez de enum porque los formatos Latam
 *   varían mucho: Loom, Framer, Notion, Google Drive, WhatsApp channel,
 *   Telegram canal, bit.ly, Dropbox. Forzar enum limita más de lo que
 *   organiza.
 */
export const offerResourcesSchema: SectionSchema = {
  key: "offer.resources",
  // title + description resolved from the backend SectionCatalog.
  scope: "mixed",
  fields: [
    {
      id: "base_resources",
      label: "Recursos base (incluidos siempre)",
      type: "array",
      path: "assets",
      owner: "offer",
      hint: "Recursos que recibe cualquier cliente que compre esta oferta, sin importar en qué cohorte/salida entró. Estos son los 'entregables digitales' core.",
      itemSchema: {
        description: "Un recurso del paquete base.",
        fields: [
          {
            id: "name",
            label: "Nombre del recurso",
            type: "text",
            path: "name",
            required: true,
            placeholder: "Workbook del Módulo 1 — Diagnóstico de consultorio",
          },
          {
            id: "type",
            label: "Tipo / formato",
            type: "text",
            path: "type",
            placeholder: "PDF descargable / Video en Loom / Template Notion / Carpeta Drive",
            hint: "Indica el formato o la plataforma. El cliente evalúa si tiene la app o si lo puede usar offline.",
          },
          {
            id: "url",
            label: "URL de acceso",
            type: "url",
            path: "url",
            placeholder: "https://drive.google.com/file/d/... / https://tally.so/r/... / https://www.notion.so/...",
            hint: "Link al recurso. Valida que no caduca (Google Drive enlaces públicos con permisos correctos, Notion páginas publicadas).",
          },
          {
            id: "description",
            label: "Descripción corta",
            type: "textarea",
            path: "description",
            rows: 2,
            placeholder:
              "Plantilla editable en Notion para mapear tu consultorio actual. Te toma 20 min completarla.",
            hint: "¿Qué logra el cliente con este recurso? Tiempo estimado de uso ayuda a que lo consuma y no lo archive.",
          },
          {
            id: "availability_window_description",
            label: "Cuándo se desbloquea / entrega",
            type: "text",
            path: "availability_window_description",
            placeholder: "Inmediato post-checkout / Semana 1 de la cohorte / Al completar el Módulo 3",
            hint: "Cuándo el cliente tiene acceso. Recurso que 'llega después' sin aviso genera tickets 'no lo encuentro'. Si es gated, explicítalo.",
          },
        ],
      },
    },
    {
      id: "edition_resources",
      label: "Recursos extras (solo esta edición)",
      type: "array",
      path: "edition_resources",
      owner: "edition",
      hint: "Bonus exclusivos de la cohorte / salida / convocatoria actual. Ej: grabación de la sesión especial con speaker invitado, plantilla fruto de las discusiones del grupo.",
      itemSchema: {
        description: "Recurso agregado solo a esta edición específica.",
        fields: [
          {
            id: "name",
            label: "Nombre del recurso",
            type: "text",
            path: "name",
            required: true,
            placeholder: "Grabación de la sesión con Dr. Fabián Torres (cohorte Q2 2026)",
          },
          {
            id: "type",
            label: "Tipo / formato",
            type: "text",
            path: "type",
            placeholder: "Video en Zoom Cloud / PDF / Link a Miro",
          },
          {
            id: "url",
            label: "URL de acceso",
            type: "url",
            path: "url",
          },
          {
            id: "description",
            label: "Descripción",
            type: "textarea",
            path: "description",
            rows: 2,
            placeholder:
              "Sesión especial de 90 min sobre cirugía maxilofacial aplicada a la consulta dental privada. Solo disponible para esta cohorte.",
          },
        ],
      },
    },
  ],
};
