import { InteractionMode, ServiceCategory, ServiceFrequency } from "../types";

import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * SERVICIO archetype details — scope + modality of the service.
 *
 * MIXED scope: category + mode + deliverables are offer-wide; the
 * specific convocatoria dates + capacity live on the LaunchEdition.
 * Services without editions default to the virtual ``evergreen`` URL
 * which hides the per-launch fields.
 */
export const offerServiceDetailsSchema: SectionSchema = {
  key: "offer.service_details",
  title: "Detalles del servicio",
  description: "Modalidad de trabajo y fechas de convocatoria.",
  scope: "mixed",
  fields: [
    {
      id: "category",
      label: "Categoría",
      type: "enum",
      path: "specific_details.category",
      owner: "offer",
      options: [
        { value: ServiceCategory.ADVISORY, label: "Asesoría / Consultoría" },
        { value: ServiceCategory.AGENCY, label: "Agencia (DFY)" },
        { value: ServiceCategory.AUTHORITY, label: "Autoridad (speaking, coaching)" },
      ],
    },
    {
      id: "interaction_mode",
      label: "Modo de interacción",
      type: "enum",
      path: "specific_details.interaction_mode",
      owner: "offer",
      options: [
        { value: InteractionMode.SYNC, label: "Sincrónico (vivo)" },
        { value: InteractionMode.ASYNC, label: "Asincrónico" },
        { value: InteractionMode.HYBRID, label: "Híbrido" },
      ],
    },
    {
      id: "frequency_type",
      label: "Frecuencia",
      type: "enum",
      path: "specific_details.frequency_type",
      owner: "offer",
      options: [
        { value: ServiceFrequency.ONE_OFF, label: "Contrato único" },
        { value: ServiceFrequency.RETAINER, label: "Retainer recurrente" },
      ],
    },
    {
      id: "deliverables_list",
      label: "Entregables (uno por línea)",
      type: "textarea",
      path: "specific_details.deliverables_list",
      owner: "offer",
      rows: 4,
      hint: "Lista concreta de lo que recibe el cliente en cada ciclo de entrega.",
    },
    {
      id: "session_duration_minutes",
      label: "Duración de sesión (min)",
      type: "number",
      path: "specific_details.session_duration_minutes",
      owner: "offer",
    },
    {
      id: "total_sessions_count",
      label: "Total de sesiones",
      type: "number",
      path: "specific_details.total_sessions_count",
      owner: "offer",
    },
    {
      id: "turnaround_time_days",
      label: "Tiempo de respuesta (días)",
      type: "number",
      path: "specific_details.turnaround_time_days",
      owner: "offer",
    },
    {
      id: "booking_url",
      label: "URL de reserva",
      type: "url",
      path: "specific_details.booking_url",
      owner: "offer",
      placeholder: "https://calendly.com/...",
    },
    {
      id: "onboarding_brief_url",
      label: "URL del brief de onboarding",
      type: "url",
      path: "specific_details.onboarding_brief_url",
      owner: "offer",
    },
    {
      id: "requires_contract_signature",
      label: "¿Requiere firma de contrato?",
      type: "boolean",
      path: "specific_details.requires_contract_signature",
      owner: "offer",
    },
    {
      id: "start_date",
      label: "Inicio de la convocatoria",
      type: "text",
      path: "start_date",
      owner: "edition",
      placeholder: "2026-05-01T00:00:00Z",
    },
    {
      id: "capacity",
      label: "Cupos esta convocatoria",
      type: "number",
      path: "capacity",
      owner: "edition",
    },
  ],
};
