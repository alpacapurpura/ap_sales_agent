import { InteractionMode, ServiceCategory, ServiceFrequency } from "../types";

import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * SERVICIO archetype details — scope, modalidad y logística del servicio.
 *
 * Scope MIXED: la modalidad, entregables y logística son offer-wide
 * (misma para todas las convocatorias del servicio), pero la fecha de
 * inicio y los cupos de la convocatoria específica viven en la
 * ``LaunchEdition``. Servicios sin convocatorias agrupadas caen sobre
 * la edición virtual ``evergreen`` que oculta los campos per-launch.
 *
 * **Latam — decisiones de diseño:**
 * - ``scope_excluded`` es DECISIVO. Los presets ``consultor_proyecto_scope``,
 *   ``agencia_proyecto_unico``, ``agencia_retainer`` y ``salud_paquete_tratamiento``
 *   lo reclaman explícitamente en su ``suitability_note_es``: "Scope-in y
 *   scope-out con brutal claridad". Sin este campo, el servicio queda
 *   expuesto a scope creep → disputas → refunds.
 * - ``primary_communication_channel`` captura el canal preferido del
 *   cliente. WhatsApp Business domina B2B Latam. Si el vendedor cierra
 *   sobre email pero el cliente espera WhatsApp, el post-venta falla.
 * - ``min_contract_months`` + ``revision_rounds`` vienen del zod
 *   ``ServiceDetailsSchema`` — antes estaban persistiéndose pero no se
 *   exponían al editor (zombies invisibles). Ahora son campos de primer
 *   nivel con hint.
 *
 * **Sales agent grounding:**
 * - ``response_time_hours`` es lo que el agent promete al cliente cuando
 *   pregunta "¿en cuánto me respondés?". Sin este campo promete aire.
 * - ``turnaround_time_days`` idem para entregables de agencia / dictamen.
 */
export const offerServiceDetailsSchema: SectionSchema = {
  key: "offer.service_details",
  // title + description resolved from the backend SectionCatalog.
  scope: "mixed",
  fields: [
    // ─── Modalidad ────────────────────────────────────────────────────────
    {
      id: "category",
      label: "Categoría del servicio",
      type: "enum",
      path: "specific_details.category",
      owner: "offer",
      options: [
        {
          value: ServiceCategory.ADVISORY,
          label: "Consultoría / asesoría (tú orientas, el cliente ejecuta)",
        },
        {
          value: ServiceCategory.AGENCY,
          label: "Agencia / DFY (tú o tu equipo ejecutan por el cliente)",
        },
        {
          value: ServiceCategory.AUTHORITY,
          label: "Autoridad (coaching, speaking, mentoría, consulta médica)",
        },
      ],
      hint: "Cambia la expectativa del cliente y cómo lo cobras. Consultoría = alto margen sin ejecución. Agencia = scope fijo con entregable. Autoridad = tu tiempo 1:1.",
    },
    {
      id: "interaction_mode",
      label: "¿Cómo trabajan juntos?",
      type: "enum",
      path: "specific_details.interaction_mode",
      owner: "offer",
      options: [
        { value: InteractionMode.SYNC, label: "En vivo (videollamadas, llamadas, reuniones)" },
        {
          value: InteractionMode.ASYNC,
          label: "A tu ritmo (mensajes, videos grabados, documentos)",
        },
        { value: InteractionMode.HYBRID, label: "Híbrido (llamadas + mensajes entre llamadas)" },
      ],
      hint: "Clientes que valoran speed eligen asíncrono. Clientes que valoran conexión eligen en vivo. Híbrido es lo más común en consultoría Latam: 1 call quincenal + WhatsApp de seguimiento.",
    },
    {
      id: "frequency_type",
      label: "Frecuencia del servicio",
      type: "enum",
      path: "specific_details.frequency_type",
      owner: "offer",
      options: [
        { value: ServiceFrequency.ONE_OFF, label: "Proyecto único (empieza, termina, cerrado)" },
        { value: ServiceFrequency.RETAINER, label: "Retainer mensual (facturación recurrente)" },
      ],
      hint: "Proyecto único = factura anticipada por hitos. Retainer = facturación mensual, a menudo con permanencia mínima.",
    },

    // ─── Alcance (qué incluye y qué NO incluye) ───────────────────────────
    {
      id: "deliverables_list",
      label: "Qué incluye el servicio",
      type: "textarea",
      path: "specific_details.deliverables_list",
      owner: "offer",
      rows: 5,
      placeholder:
        "• Auditoría completa de tu cuenta de Meta Ads\n• Estrategia mensual con 3 campañas nuevas\n• Reporte semanal por WhatsApp\n• Optimización diaria de pujas",
      hint: "Uno por línea. Sé específico y medible. Evita 'soporte personalizado' o 'asesoría continua' vagos — el cliente mide con lo que acá digas.",
    },
    {
      id: "scope_excluded",
      label: "Qué NO incluye (crítico para evitar discusiones)",
      type: "textarea",
      path: "specific_details.scope_excluded",
      owner: "offer",
      rows: 4,
      placeholder:
        "• Creación de video o producción audiovisual\n• Traducción de copy a otros idiomas\n• Soporte técnico de tu tienda online\n• Cambios fuera del alcance inicial",
      hint: "Uno por línea. Tan importante como lo que incluyes. El 80% de las disputas post-venta en agencias y consultorías Latam vienen de scope-out no declarado. Si no lo escribes, el cliente va a asumir que sí está incluido.",
    },
    {
      id: "revision_rounds",
      label: "Rondas de revisión incluidas",
      type: "number",
      path: "specific_details.revision_rounds",
      owner: "offer",
      placeholder: "2",
      hint: "Cuántas veces el cliente puede pedir cambios sobre un entregable sin costo extra. Típico en agencia/diseño: 2-3 rondas. Más rondas = trabajo infinito → pon un número.",
    },

    // ─── Logística (cuánto dura, cuándo responde) ─────────────────────────
    {
      id: "session_duration_minutes",
      label: "Duración por sesión (minutos)",
      type: "number",
      path: "specific_details.session_duration_minutes",
      owner: "offer",
      placeholder: "60",
      hint: "Solo si aplica. Coaching/mentoría: 45-60 min. Consulta médica: 30 min. VIP Day: 480 min (día completo).",
    },
    {
      id: "total_sessions_count",
      label: "Total de sesiones o encuentros",
      type: "number",
      path: "specific_details.total_sessions_count",
      owner: "offer",
      placeholder: "8",
      hint: "Cuántas sesiones incluye el paquete. Deja vacío si es retainer o proyecto sin sesiones fijas.",
    },
    {
      id: "turnaround_time_days",
      label: "Plazo de entrega (días hábiles)",
      type: "number",
      path: "specific_details.turnaround_time_days",
      owner: "offer",
      placeholder: "10",
      hint: "Desde kickoff hasta primer entregable. En Latam se espera contar días hábiles (lunes a viernes). Agencia de diseño web: 15-30 días hábiles. Dictamen legal: 5-15 días.",
    },
    {
      id: "response_time_hours",
      label: "Tiempo de respuesta a mensajes del cliente",
      type: "number",
      path: "specific_details.response_time_hours",
      owner: "offer",
      placeholder: "24",
      hint: "En horas hábiles. Lo que el agente de ventas promete. Sin este número, el cliente asume 'inmediato' y viene la frustración. Retainer profesional típico: 4-24h.",
    },

    // ─── Contrato y canal (cómo se formaliza y se comunican) ──────────────
    {
      id: "requires_contract_signature",
      label: "¿Requiere firma de contrato?",
      type: "boolean",
      path: "specific_details.requires_contract_signature",
      owner: "offer",
      hint: "En B2B Latam, contratos con razón social + CUIT/RFC/RUC son esperados para proyectos > USD 500. Reduce fricción de cobranza si el cliente no paga.",
    },
    {
      id: "min_contract_months",
      label: "Permanencia mínima (meses)",
      type: "number",
      path: "specific_details.min_contract_months",
      owner: "offer",
      placeholder: "3",
      hint: "Solo para retainer. Justifica curva de aprendizaje + setup inicial. Típico Latam: 3-6 meses. Con permanencia alta, bajas el precio mensual para compensar.",
    },
    {
      id: "primary_communication_channel",
      label: "Canal principal de comunicación",
      type: "enum",
      path: "specific_details.primary_communication_channel",
      owner: "offer",
      options: [
        { value: "whatsapp_business", label: "WhatsApp Business (dominante Latam B2B)" },
        { value: "email", label: "Email formal" },
        { value: "slack_shared", label: "Slack compartido (típico SaaS/Tech)" },
        { value: "telegram", label: "Telegram" },
        { value: "platform_internal", label: "Plataforma propia / portal del cliente" },
      ],
      hint: "WhatsApp es lo dominante Latam para retainers y servicios recurrentes. El agente de ventas lo menciona al cerrar. Si el cliente espera otro canal, defínelo explícito.",
    },

    // ─── Reserva y onboarding (cómo arranca el cliente) ───────────────────
    {
      id: "booking_url",
      label: "Link de agendamiento (Calendly / Cal.com)",
      type: "url",
      path: "specific_details.booking_url",
      owner: "offer",
      placeholder: "https://cal.com/tu-usuario/consulta",
      hint: "Si integras scheduling nativo, deja vacío — el sistema lo genera automáticamente. Cal.com es más económico que Calendly para Latam.",
    },
    {
      id: "onboarding_brief_url",
      label: "Formulario de brief / onboarding",
      type: "url",
      path: "specific_details.onboarding_brief_url",
      owner: "offer",
      placeholder: "https://tally.so/...",
      hint: "Cuestionario que el cliente llena antes de la primera reunión. Ahorra una sesión entera de descubrimiento. Tally y Typeform son los más usados Latam.",
    },

    // ─── Convocatoria específica (edition-level) ──────────────────────────
    {
      id: "start_date",
      label: "Inicio de esta convocatoria",
      type: "text",
      path: "start_date",
      owner: "edition",
      placeholder: "2026-05-01T00:00:00Z",
      hint: "Solo si el servicio se ofrece en convocatorias agrupadas (varios clientes arrancan al mismo tiempo). Formato ISO 8601 UTC.",
    },
    {
      id: "capacity",
      label: "Cupos en esta convocatoria",
      type: "number",
      path: "capacity",
      owner: "edition",
      placeholder: "10",
      hint: "Cuántos clientes aceptas en esta convocatoria. Vacío = sin límite. Escasez real (cupos limitados) convierte mejor que urgencia fake.",
    },
  ],
};
