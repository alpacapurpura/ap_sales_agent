import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Public FAQ — preguntas frecuentes visibles en la landing y usadas por el
 * agente de ventas como primera línea de respuesta. Distinto de KNOWLEDGE
 * (documentos internos del agent).
 *
 * Latam: categorías típicas que concentran >80% de las dudas reales son
 * Pagos (cuotas, métodos locales), Envíos (tiempos, cobertura interior),
 * Devoluciones, Horarios de atención, Soporte post-compra. El frontend
 * agrupa por categoría en la landing.
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
      hint: "Pregunta + respuesta + categoría. El agente de ventas las usa como primera línea cuando un lead pregunta.",
      itemSchema: {
        description: "Una pregunta frecuente visible en landing y en el agente.",
        fields: [
          {
            id: "question",
            label: "Pregunta",
            type: "text",
            path: "question",
            required: true,
            placeholder: "Ej: ¿Puedo pagar en cuotas sin interés?",
            hint: "Formulala como la preguntaría tu cliente (no como la responderías vos).",
          },
          {
            id: "answer",
            label: "Respuesta",
            type: "textarea",
            path: "answer",
            required: true,
            rows: 3,
            placeholder: "Sí, aceptamos hasta 12 cuotas sin interés con Mercado Pago y tarjetas locales.",
            hint: "Sé concreto: monto, plazo, excepciones. Evitá el 'depende, consultanos'.",
          },
          {
            id: "category",
            label: "Categoría",
            type: "enum",
            path: "category",
            options: [
              { value: "general", label: "General" },
              { value: "pagos", label: "Pagos y cuotas" },
              { value: "envios", label: "Envíos y entrega" },
              { value: "devoluciones", label: "Devoluciones y garantía" },
              { value: "horarios", label: "Horarios y disponibilidad" },
              { value: "soporte", label: "Soporte post-compra" },
              { value: "tecnico", label: "Técnico / plataforma" },
              { value: "legal", label: "Legal y facturación" },
            ],
            hint: "Agrupar por categoría ayuda al cliente a encontrar su respuesta rápido.",
          },
          {
            id: "is_featured",
            label: "¿Destacar en landing?",
            type: "boolean",
            path: "is_featured",
            hint: "Las destacadas aparecen primero en la landing. Máximo 3-5 para no saturar.",
          },
        ],
      },
    },
  ],
};
