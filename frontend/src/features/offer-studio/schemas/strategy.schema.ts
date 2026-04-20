import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Strategy — el ICP (cliente ideal) y el posicionamiento de la oferta.
 *
 * Scope OFFER_LEVEL: el avatar + dolores + deseos + anti-avatar son
 * estables entre ediciones. Una misma oferta puede correrse en varias
 * cohortes/salidas — el ICP no cambia.
 *
 * **Latam — decisiones de diseño:**
 * - Los placeholders muestran ejemplos Latam reales (no "growth founder"
 *   abstractos). Un microempresario Latam se reconoce en "nutricionista
 *   con 2 años de carrera privada" más que en "wellness entrepreneur".
 * - ``anti_avatar_keywords`` es lo que el sales-agent usa para descartar
 *   leads mal calificados. Específico y concreto; si dejas vago, el
 *   agente acepta cualquiera y tu CAC se dispara.
 * - Los pain points deben ser específicos y medibles. El agent los usa
 *   para abrir conversación con empathy framing.
 */
export const offerStrategySchema: SectionSchema = {
  key: "offer.strategy",
  // title + description resolved from the backend SectionCatalog.
  scope: "offer_level",
  fields: [
    {
      id: "avatar_id",
      label: "Buyer persona principal (de Brand Studio)",
      type: "text",
      path: "avatar_id",
      placeholder: "Ej: Nutri Ale — 32 años, nutricionista con consultorio propio hace 2 años",
      hint: "Selecciona un buyer persona previamente definido en Brand Studio. El ID se resuelve en un picker en runtime. Vacío = aplica a cualquier audiencia (no recomendado: sin ICP el sales-agent no puede calificar).",
    },
    {
      id: "target_avatar_match",
      label: "Segmentos o arquetipos adicionales",
      type: "textarea",
      path: "target_avatar_match_raw",
      rows: 3,
      placeholder:
        "• Profesionales de salud con consultorio propio\n• Nutricionistas con 1-5 años de experiencia\n• Kinesiólogas que empiezan a hacer atención online",
      hint: "Uno por línea. Segmentos más amplios que el avatar principal a los que también les sirve la oferta. El agente abre conversación con el que más encaje.",
    },
    {
      id: "marketing_pain_points",
      label: "Dolores concretos del avatar",
      type: "textarea",
      path: "marketing_pain_points_raw",
      rows: 5,
      placeholder:
        "• No puedo más con pacientes que faltan a la cita y no pagan\n• Facturo apenas USD 800/mes y trabajo 10 horas por día\n• Mis pacientes no vuelven después de la primera consulta\n• No sé cómo cobrar por WhatsApp sin parecer informal",
      hint: "Uno por línea. Situaciones específicas y dolorosas que tu avatar ya no aguanta. Evitá genéricos como 'quiere crecer' — especificidad convierte. El sales-agent los cita textualmente al abrir.",
    },
    {
      id: "marketing_desires",
      label: "Deseos concretos del avatar",
      type: "textarea",
      path: "marketing_desires_raw",
      rows: 5,
      placeholder:
        "• Quiero facturar USD 3.000/mes trabajando 4 horas por día\n• Quiero tener 20 pacientes fijos que paguen mensual\n• Quiero que me agenden solos por un link y paguen por adelantado\n• Quiero dejar de perder tiempo explicando lo mismo 10 veces",
      hint: "Uno por línea. Lo que el avatar quiere LOGRAR (no solo 'evitar'). Con números concretos cuando se pueda. El sales-agent los usa como promesa en el pitch.",
    },
    {
      id: "anti_avatar_keywords",
      label: "Anti-avatar — palabras que descalifican",
      type: "textarea",
      path: "anti_avatar_keywords_raw",
      rows: 4,
      placeholder:
        "• Estudiante sin consultorio propio\n• Busca contenido gratis\n• No quiere invertir más de USD 100\n• Audiencia B2C masiva sin perfil definido\n• Pide 'trabajo a cambio de exposure'",
      hint: "Uno por línea. Si el lead menciona alguna, el sales-agent lo descalifica educadamente. Protege tu tiempo y mantiene tu conversion rate alto. Ser explícito acá reduce fricción de venta 30-40%.",
    },
  ],
};
