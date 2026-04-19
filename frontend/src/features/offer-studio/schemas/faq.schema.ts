import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Public FAQ — preguntas frecuentes PÚBLICAS (landing + primera línea
 * del sales-agent). Distinto de ``knowledge`` que es interno del agent.
 *
 * Scope OFFER_LEVEL: las FAQs se escriben una vez por oferta y se
 * reutilizan en todas las ediciones. Si una FAQ es específica de una
 * cohorte ("¿hay parking en el venue?"), registrala en el campo
 * ``notes`` de la LaunchEdition.
 *
 * **Latam — decisiones de diseño:**
 * - Las categorías cubren las 8 agrupaciones que concentran >90% de
 *   las dudas reales en Latam: general, pagos (cuotas/métodos locales),
 *   envíos (cobertura interior), devoluciones, horarios, soporte,
 *   técnico y legal/facturación (RFC/RUC/CUIT).
 * - ``is_answered_by_agent`` permite marcar FAQs que el sales-agent
 *   DEBE responder con exactitud (preguntas de pago, devolución) vs
 *   FAQs opcionales que aparecen solo en landing. Sin esta distinción
 *   el agent puede inventar respuestas y el tenant no sabe dónde mirar.
 */
export const offerFaqSchema: SectionSchema = {
  key: "offer.faq",
  // title + description resolved from the backend SectionCatalog.
  scope: "offer_level",
  fields: [
    {
      id: "questions",
      label: "Preguntas frecuentes públicas",
      type: "array",
      path: "faq_public",
      hint: "Pregunta + respuesta + categoría. Se muestran en la landing agrupadas por categoría. El sales-agent las usa como primera línea de respuesta cuando el lead pregunta. 8-15 FAQs cubren la mayoría de casos sin saturar.",
      itemSchema: {
        description: "Una pregunta frecuente visible en landing y usada por el agente.",
        fields: [
          {
            id: "question",
            label: "Pregunta (en palabras del cliente)",
            type: "text",
            path: "question",
            required: true,
            placeholder: "¿Puedo pagar en cuotas sin interés con mi tarjeta de Lima?",
            hint: "Formulala como la escribiría tu cliente, no como la responderías vos. Si escuchás variaciones de la misma pregunta, usá la más común (la que incluye geografía o método específico Latam).",
          },
          {
            id: "answer",
            label: "Respuesta concreta",
            type: "textarea",
            path: "answer",
            required: true,
            rows: 4,
            placeholder:
              "Sí. Aceptamos hasta 12 cuotas sin interés con Mercado Pago (Visa, MasterCard, American Express de bancos peruanos). También podés pagar en 3 cuotas con Culqi o transferencia directa a cuenta BCP/BBVA. El acceso se habilita automáticamente al confirmar el pago.",
            hint: "Respuesta específica con números, métodos y condiciones. Evitá 'depende, consultanos' — eso desperdicia la FAQ. Si hay excepciones, listalas explícitas.",
          },
          {
            id: "category",
            label: "Categoría",
            type: "enum",
            path: "category",
            options: [
              { value: "general", label: "General" },
              { value: "pagos", label: "Pagos y cuotas" },
              { value: "envios", label: "Envíos y entrega (físicos)" },
              { value: "devoluciones", label: "Devoluciones y garantía" },
              { value: "horarios", label: "Horarios y disponibilidad" },
              { value: "soporte", label: "Soporte post-compra" },
              { value: "tecnico", label: "Técnico / plataforma / acceso" },
              { value: "legal", label: "Legal y facturación (RFC/RUC/CUIT)" },
            ],
            hint: "Agrupar por categoría en la landing ayuda al cliente a encontrar su respuesta rápido. El sales-agent también filtra por categoría según el contexto de la conversación.",
          },
          {
            id: "is_answered_by_agent",
            label: "¿El sales-agent DEBE responder con exactitud?",
            type: "boolean",
            path: "is_answered_by_agent",
            hint: "Marcar SÍ para preguntas donde el agent no puede improvisar: pagos, devoluciones, facturación legal. Si está en NO, el agent puede parafrasear. Para FAQs solo-landing (detalles estéticos, curiosidades), dejá NO.",
          },
          {
            id: "is_featured",
            label: "¿Destacar en landing?",
            type: "boolean",
            path: "is_featured",
            hint: "Las destacadas aparecen primero en la sección FAQ de landing. 3-5 máximo — las 'Top 5 preguntas que más hacen'. Las demás se muestran al hacer clic en 'Ver todas'.",
          },
        ],
      },
    },
  ],
};
