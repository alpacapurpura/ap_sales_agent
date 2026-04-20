import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Psychology — motivaciones + objeciones que el sales-agent maneja en tiempo
 * real. Es la sección que más alimenta al agente de ventas.
 *
 * Scope OFFER_LEVEL: psicología consistente entre ediciones. Para
 * objeciones edition-específicas (ej: fecha incómoda de una cohorte),
 * usa el campo ``notes`` de la ``LaunchEdition``.
 *
 * **Latam — decisiones de diseño:**
 * - ``cultural_trust_barriers`` captura barreras Latam específicas:
 *   desconfianza de pagos online, preferencia WhatsApp sobre formularios,
 *   tarjetas internacionales que rebotan, expectativa de negociación,
 *   exigencia de factura B2B. Sin este campo el agente ignora el 40%
 *   de fricciones reales Latam.
 * - ``objections_raw`` formato texto libre (una por línea) vs array
 *   tipado es deliberado: queremos que el usuario escriba con su voz;
 *   el copilot puede luego estructurarlas.
 * - ``status_drivers`` y ``regret_scenarios`` son armas psicológicas
 *   avanzadas — el agente las usa solo cuando el lead ya mostró
 *   objeción de precio o tiempo y aún no cierra.
 */
export const offerPsychologySchema: SectionSchema = {
  key: "offer.psychology",
  // title + description resolved from the backend SectionCatalog.
  scope: "offer_level",
  fields: [
    {
      id: "objections",
      label: "Objeciones típicas (una por línea)",
      type: "textarea",
      path: "objections_raw",
      rows: 8,
      placeholder:
        "• No tengo tiempo ahora\n• Es muy caro\n• Ya probé algo parecido y no funcionó\n• Tengo que consultarlo con mi pareja\n• Prefiero esperar al próximo mes / al aguinaldo\n• ¿Cómo sé que no es estafa?\n• No me siento listo todavía\n• Tengo dudas si es para mi nivel",
      hint: "Uno por línea. Las frases REALES que escuchas de prospectos que no cierran. Evita objeciones teóricas de libro de marketing — usa las palabras exactas de tus clientes. El agente de ventas las detecta en el chat y responde con el argumento correspondiente.",
    },
    {
      id: "cultural_trust_barriers",
      label: "Barreras de confianza específicas Latam",
      type: "textarea",
      path: "cultural_trust_barriers",
      rows: 5,
      placeholder:
        "• Desconfianza a pagar por internet — prefieren transferencia manual o Yape/Plin\n• 'Si no te veo la cara no confío' — necesitan videollamada antes de pagar\n• Tarjeta internacional rebotó — necesitan opción local (Mercado Pago, Culqi)\n• Quieren factura a nombre de la empresa — B2B requiere RFC/RUC/CUIT\n• Negocian precio — esperan flexibilidad en cuotas o descuento por pago único",
      hint: "Uno por línea. Barreras culturales Latam que no son objeciones clásicas. El agente las anticipa y ofrece la fricción-killer correspondiente (link de WhatsApp para video, pasarela local, comprobante fiscal, cuotas flexibles).",
    },
    {
      id: "emotional_triggers",
      label: "Disparadores emocionales positivos",
      type: "textarea",
      path: "emotional_triggers",
      rows: 4,
      placeholder:
        "• Miedo a quedarse estancado viendo a otros crecer en redes\n• Deseo de mostrar a la familia que 'sí se puede vivir del consultorio'\n• Ansiedad por depender económicamente de otro ingreso/persona\n• Identidad aspiracional: ser reconocido como referente en su rubro",
      hint: "Miedos, deseos y aspiraciones que mueven la decisión de compra. El agente los refleja cuando detecta interés genuino. Usar lenguaje emocional (no racional) convierte 3x más en cerrar.",
    },
    {
      id: "status_drivers",
      label: "Motores de estatus y reconocimiento",
      type: "textarea",
      path: "status_drivers",
      rows: 3,
      placeholder:
        "• Poder decir 'cobro consultas en dólares'\n• Aparecer en reels con el 'antes/después' de sus pacientes\n• Ser invitada a dar una charla en congresos del rubro",
      hint: "Qué cambia en la percepción social del cliente cuando compra y tiene éxito. El agente lo menciona cuando el lead tiene vanidad sana (sin caer en aspiracional fake).",
    },
    {
      id: "regret_scenarios",
      label: "Escenarios de arrepentimiento por NO comprar",
      type: "textarea",
      path: "regret_scenarios",
      rows: 3,
      placeholder:
        "• Seguir cobrando USD 15 por consulta en un año más cuando todos cobran USD 40+\n• Ver a colegas con menor experiencia tener agenda llena mientras ella sigue peleando por cada paciente\n• Llegar a diciembre sin haber facturado lo que necesita para vacaciones familiares",
      hint: "Situaciones concretas futuras donde el lead se va a arrepentir de no haber tomado acción hoy. El agente las usa como cierre emocional cuando el lead dice 'déjame pensarlo'.",
    },
  ],
};
