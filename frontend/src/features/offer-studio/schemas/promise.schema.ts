import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Promise — la transformación completa que compromete la oferta. Describe
 * el arco antes → después y argumenta la urgencia (por qué ahora).
 *
 * La frase titular y el resultado principal viven en ``IDENTITY`` (SSoT).
 * Este bloque los amplía con contexto narrativo que el agente de ventas
 * usa para pintar la transformación en conversaciones largas.
 */
export const offerPromiseSchema: SectionSchema = {
  key: "offer.promise",
  // title + description resolved from the backend SectionCatalog.
  scope: "offer_level",
  fields: [
    {
      id: "before_state",
      label: "Situación inicial del cliente",
      type: "textarea",
      path: "before_state",
      rows: 3,
      required: true,
      placeholder: "ej. Trabaja 60h semanales, se lleva pendientes a casa y siente que no avanza aunque está siempre ocupado.",
      hint: "Cómo vive tu cliente hoy ANTES de tu oferta. Pinta el dolor concreto. El agente lo cita para que el lead se sienta identificado.",
    },
    {
      id: "after_state",
      label: "Situación objetivo después",
      type: "textarea",
      path: "after_state",
      rows: 3,
      required: true,
      placeholder: "ej. Delega con confianza, termina la semana a las 6pm y sus reportes toman decisiones sin consultar todo.",
      hint: "Cómo vive tu cliente DESPUÉS de completar tu oferta. Evidencia concreta, no abstracta. El agente lo pinta como destino posible.",
    },
    {
      id: "why_now",
      label: "¿Por qué es urgente ahora?",
      type: "textarea",
      path: "why_now",
      rows: 3,
      placeholder: "ej. El mercado laboral premia líderes con equipos autónomos. Cada mes que postergás son oportunidades que el equipo ejecuta sin vos.",
      hint: "La razón por la que postergar tiene costo concreto. Evita caer en escasez falsa — conecta con el costo real de inacción.",
    },
    {
      id: "measurable_outcomes",
      label: "Resultados medibles concretos",
      type: "textarea",
      path: "measurable_outcomes",
      rows: 3,
      placeholder: "• Reducir 20h semanales de operación\n• 3 personas del equipo tomando decisiones sin escalarte\n• Cierre de semana viernes 6pm sin mails",
      hint: "Una métrica por línea con número. Es lo que diferencia tu promesa de 'vas a sentirte mejor'. El agente responde la objeción 'cómo sé que funciona' con esto.",
    },
  ],
};
