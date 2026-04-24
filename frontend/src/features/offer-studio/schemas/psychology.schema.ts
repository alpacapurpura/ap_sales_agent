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
 * - ``objections`` es un array estructurado (type/trigger_phrases/rebuttal/strategy).
 *   Tiene bulkPasteAction para flujo paste-AI via copilot tool structure_objections.
 *   renderAs: "cards" justificado: strategy auto-derivable de type → 3 campos
 *   visibles en el UI (form-runtime-array.md permite override documentado).
 * - ``status_drivers`` y ``regret_scenarios`` son armas psicológicas
 *   avanzadas — el agente las usa solo cuando el lead ya mostró
 *   objeción de precio o tiempo y aún no cierra.
 *
 * CONTRACT §9.4: paths aligned to canonical DB columns.
 * - objections_raw → objections (type: "array" structured, path: "objections")
 * - cultural_trust_barriers, emotional_triggers, status_drivers, regret_scenarios
 *   → storeAs: "newline_array" (JSONB string[] columns)
 */
export const offerPsychologySchema: SectionSchema = {
  key: "offer.psychology",
  // title + description resolved from the backend SectionCatalog.
  scope: "offer_level",
  fields: [
    {
      id: "objections",
      label: "Objeciones típicas",
      type: "array",
      path: "objections",
      // renderAs: "cards" override justified per form-runtime-array.md:
      // itemSchema has 4 sub-fields but "strategy" is auto-derived from "type",
      // making it perceptually a 3-field card. Override documented here.
      renderAs: "cards",
      itemSchema: {
        // mirrors backend ObjectionType enum
        itemNoun: "objeción",
        fields: [
          {
            id: "type",
            label: "Tipo",
            type: "enum",
            path: "type",
            required: true,
            hint: "Categoría de la objeción. Ayuda al sales-agent a elegir la estrategia de cierre correcta.",
            options: [
              { value: "price", label: "Precio" },
              { value: "time", label: "Tiempo" },
              { value: "trust", label: "Confianza" },
              { value: "partner", label: "Pareja / consulta" },
              { value: "fit", label: "No es para mí" },
              { value: "custom", label: "Otro" },
            ],
          },
          {
            id: "trigger_phrases",
            label: "Frases que la disparan (una por línea)",
            type: "textarea",
            path: "trigger_phrases",
            storeAs: "newline_array",
            rows: 3,
            hint: "Una por línea. El sales-agent las detecta en el chat.",
            placeholder: "• Está muy caro\n• No tengo el presupuesto ahora",
          },
          {
            id: "rebuttal",
            label: "Respuesta del agente",
            type: "textarea",
            path: "rebuttal",
            rows: 4,
            required: true,
            hint: "Qué responde el sales-agent cuando detecta esta objeción. Usa el tono de tu marca, no robótico.",
            placeholder: "Entiendo perfectamente. Si en 30 días no ves [resultado]…",
          },
          {
            id: "strategy",
            label: "Estrategia",
            type: "text",
            path: "strategy",
            hint: "Auto-sugerido desde el tipo de objeción. Editable.",
            placeholder: "ej. ROI Reframing",
          },
        ],
      },
      bulkPasteAction: {
        toolName: "structure_objections",
        label: "Pegar lista y estructurar con IA",
        placeholder:
          "No tengo presupuesto para esto ahora\nTengo que consultarlo primero\nYa probé algo similar y no me funcionó\n¿Hay devolución si no me resulta?",
        hint: "Pega objeciones, una por línea. Pueden ser frases de prospectos reales, notas de llamadas, mensajes de WhatsApp.",
      },
      hint: "Las frases reales que escuchas de prospectos que no cierran. El agente las detecta en el chat y responde con el argumento correspondiente.",
    },
    {
      id: "cultural_trust_barriers",
      label: "Barreras de confianza específicas Latam",
      type: "textarea",
      path: "cultural_trust_barriers",
      // DB column: products.cultural_trust_barriers JSONB string[].
      storeAs: "newline_array",
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
      // DB column: products.emotional_triggers JSONB string[].
      storeAs: "newline_array",
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
      // DB column: products.status_drivers JSONB string[].
      storeAs: "newline_array",
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
      // DB column: products.regret_scenarios JSONB string[].
      storeAs: "newline_array",
      rows: 3,
      placeholder:
        "• Seguir cobrando USD 15 por consulta en un año más cuando todos cobran USD 40+\n• Ver a colegas con menor experiencia tener agenda llena mientras ella sigue peleando por cada paciente\n• Llegar a diciembre sin haber facturado lo que necesita para vacaciones familiares",
      hint: "Situaciones concretas futuras donde el lead se va a arrepentir de no haber tomado acción hoy. El agente las usa como cierre emocional cuando el lead dice 'déjame pensarlo'.",
    },
  ],
};
