import { GuaranteeType } from "../types";

import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Closing — garantía, urgencia y último empujón para cerrar la venta.
 *
 * Scope OFFER_LEVEL: garantías y copy de cierre son consistentes entre
 * ediciones. Urgencia específica de una cohorte (countdown al deadline
 * de esa cohorte) vive computada sobre ``LaunchEdition.registration_end``.
 *
 * **Latam — decisiones de diseño:**
 * - ``refund_process_description`` es crítico Latam. La desconfianza es
 *   alta — explicitar CÓMO se devuelve el dinero (transferencia, reverso
 *   Mercado Pago, nota de crédito) vale más que declarar un "30 días de
 *   garantía" vago. Sin este campo la garantía no convence.
 * - ``scarcity_reason_honest`` combate la urgencia falsa endémica del
 *   infoproducto Latam. El agente la usa solo si es real — cupos
 *   limitados por logística, deadline por vencimiento de precio.
 * - ``bonus_if_act_now`` es un bonus condicional a actuar en ventana
 *   definida. Distinto del fast-action del value-stack: acá es acción
 *   de cierre de venta, allá es un item del stack.
 * - ``support_duration_days`` ya existía en ``OfferSchema`` como campo
 *   de primer nivel — lo exponemos acá porque es lo que el agente
 *   promete cuando el lead pregunta "¿y después qué?".
 */
export const offerClosingSchema: SectionSchema = {
  key: "offer.closing",
  // title + description resolved from the backend SectionCatalog.
  scope: "offer_level",
  fields: [
    // ─── Garantía ─────────────────────────────────────────────────────────
    {
      id: "guarantee_type",
      label: "Tipo de garantía",
      type: "enum",
      path: "guarantee_type",
      options: [
        { value: GuaranteeType.NONE, label: "Sin garantía explícita (no recomendado en Latam)" },
        {
          value: GuaranteeType.UNCONDITIONAL_30_DAY,
          label: "Incondicional 30 días (estándar infoproducto)",
        },
        {
          value: GuaranteeType.CONDITIONAL_ACTION_BASED,
          label: "Condicional por acción (ej: si hiciste los módulos y no funcionó)",
        },
        {
          value: GuaranteeType.DOUBLE_MONEY_BACK,
          label: "Doble devolución (tu dinero × 2)",
        },
        {
          value: GuaranteeType.SATISFACTION_OR_FREE_WORK,
          label: "Satisfacción o seguimos trabajando sin costo",
        },
      ],
      hint: "Garantía honesta es la mejor fricción-killer Latam. Un 'incondicional 30 días' convierte 40% más que 'sin garantía'. Doble devolución es fuerte pero arriesgada si la tasa de refund es alta.",
    },
    {
      id: "guarantee_terms",
      label: "Términos exactos de la garantía",
      type: "textarea",
      path: "guarantee_terms",
      rows: 5,
      placeholder:
        "Si en los próximos 30 días consideras que el programa no cumple con lo prometido, te devolvemos el 100% de tu inversión. Sin preguntas, sin formularios largos. Solo escríbenos a soporte@tudominio.com con tu comprobante de compra y procesamos la devolución dentro de las 72 horas hábiles siguientes.",
      hint: "Copia textual que aparece en landing + checkout + email post-venta. Tono: confiado, sin letra chica. Los términos específicos (72h, canal, requisitos) son el diferenciador vs una garantía vaga.",
    },
    {
      id: "refund_process_description",
      label: "Cómo devolvemos el dinero (crítico Latam)",
      type: "textarea",
      path: "refund_process_description",
      rows: 4,
      placeholder:
        "• Si pagaste por tarjeta: reverso automático a la misma tarjeta (puede tardar 5-10 días hábiles)\n• Si pagaste por Mercado Pago: reversión en el mismo medio en 24-72h\n• Si pagaste por transferencia: transferimos a la misma cuenta emisora\n• Si prefieres crédito en futuras compras: te damos 110% del valor pagado",
      hint: "Explicitar el proceso por método de pago vale más que el monto de la garantía. Combate directamente la desconfianza 'te pido refund y me fantasmean'. Es el campo que más aumenta confianza de compra en Latam.",
    },

    // ─── Urgencia + escasez ───────────────────────────────────────────────
    {
      id: "urgency_drivers",
      label: "Razones reales para comprar ahora",
      type: "textarea",
      path: "urgency_drivers",
      rows: 4,
      placeholder:
        "• El precio sube USD 300 el próximo mes (proyección real de ajuste por inflación)\n• Los bonus fast-action vencen el domingo a las 23:59 (hora Perú)\n• La cohorte empieza el 15 de mayo — si no entras ahora, esperas 3 meses",
      hint: "Uno por línea. Urgencia HONESTA — razones reales, no deadlines falsos. Si no tienes escasez real, no la inventes: suena a infoproductor gringo traducido y pierde confianza.",
    },
    {
      id: "scarcity_reason_honest",
      label: "Razón honesta de la escasez (si aplica)",
      type: "textarea",
      path: "scarcity_reason_honest",
      rows: 3,
      placeholder:
        "Trabajo con grupos de 12 personas máximo para poder atender personalmente a cada una en las sesiones de Q&A semanales. Cuando se llena la cohorte, la siguiente es en 3 meses.",
      hint: "Explica POR QUÉ hay cupos limitados — logística real, tiempo tuyo, calidad de atención. Los compradores Latam sensibilizados detectan escasez fake al instante y se ofenden.",
    },
    {
      id: "bonus_if_act_now",
      label: "Bonus por decidir ahora",
      type: "textarea",
      path: "bonus_if_act_now",
      rows: 4,
      placeholder:
        "Si te inscribes en las próximas 48 horas:\n• Sesión estratégica 1:1 de 60 min conmigo (valor USD 300)\n• Acceso anticipado al grupo de WhatsApp\n• Módulo bonus: 'Cómo cobrar en USD desde Latam'",
      hint: "Bonus condicional a ventana de acción. Distinto al fast-action del value-stack: acá es motor de cierre de venta. Más de 1 bonus es estándar. Valor USD declarado eleva percepción.",
    },

    // ─── Soporte post-venta ───────────────────────────────────────────────
    {
      id: "support_duration_days",
      label: "Duración del soporte post-compra (días)",
      type: "number",
      path: "support_duration_days",
      placeholder: "90",
      hint: "Cuántos días el cliente tiene acceso al soporte (chat, email, comunidad). Bootcamps: 90-180. Cursos self-paced: 30-60. Programas premium: acceso de por vida. Es la respuesta del agente cuando pregunta '¿y después qué?'.",
    },

    // ─── Último empujón ───────────────────────────────────────────────────
    {
      id: "final_push_copy",
      label: "Último empujón — copy para cerrar",
      type: "textarea",
      path: "final_push_copy",
      rows: 4,
      placeholder:
        "Mira, entiendo que es una inversión. Y también entiendo que hace meses que vienes diciendo 'el próximo mes'. Si sigues esperando, en 6 meses vas a estar en el mismo lugar. El programa tiene garantía incondicional de 30 días — si no te sirve, te devuelvo todo. Pero si te sirve, tu facturación de dentro de 90 días me va a dar la razón. ¿Empezamos?",
      hint: "La frase que el sales-agent usa cuando el lead está a un paso de decidir y necesita un empujón emocional. Tono: directo, empático, con recordatorio de garantía. Evita guilt-trips o presión manipulativa.",
    },
  ],
};
