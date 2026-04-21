import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Buyer persona (avatar) detail schema. Drives the per-persona detail page
 * where the sales agent reads the full profile from. Fields map 1:1 to the
 * BuyerPersonaSectionUpdateDTO shape.
 *
 * Dotted paths mirror the nested shape (demographics.age_range,
 * buyer_journey.awareness, etc.) — the form-runtime writes each path back
 * via the section's composed patch.
 */
export const buyerPersonaSchema: SectionSchema = {
  key: "brand.buyer-persona",
  title: "Buyer persona",
  description: "Perfil arquetípico del cliente ideal. El SDR lo usa para segmentar y personalizar.",
  fields: [
    // ── Identidad ────────────────────────────────────────────────────────
    {
      id: "name",
      label: "Nombre",
      type: "text",
      path: "name",
      required: true,
      placeholder: "Ej: María la creadora",
      hint: "Nombre de archivo para identificar al avatar internamente. No aparece en público.",
    },
    {
      id: "tagline",
      label: "Tagline",
      type: "text",
      path: "tagline",
      hint: "Una línea que describe quién es esta persona.",
    },

    // ── Demografía ───────────────────────────────────────────────────────
    {
      id: "age_range",
      label: "Rango etario",
      type: "text",
      path: "demographics.age_range",
      placeholder: "Ej: 28-45",
      hint: "Rango de edades del cliente ideal. El agente adapta referencias culturales y tono a esta franja.",
    },
    {
      id: "location",
      label: "Ubicación",
      type: "text",
      path: "demographics.location",
      placeholder: "Ej: Lima, Perú",
      hint: "Ciudad o región principal del avatar. Orienta al agente para mencionar contextos locales relevantes.",
    },
    {
      id: "occupation",
      label: "Ocupación",
      type: "text",
      path: "demographics.occupation",
      hint: "Profesión o rol del cliente ideal. Determina vocabulario técnico y nivel de sofisticación del agente.",
    },
    {
      id: "income",
      label: "Nivel de ingresos",
      type: "text",
      path: "demographics.income",
      hint: "Rango de ingresos aproximado. Calibra el pitch de precio y los argumentos de inversión del agente.",
    },

    // ── Psicografía ──────────────────────────────────────────────────────
    {
      id: "values",
      label: "Valores centrales",
      type: "textarea",
      path: "psychographics.values",
      rows: 3,
      hint: "Qué principios guían sus decisiones. El agente conecta la oferta con estos valores para resonar.",
    },
    {
      id: "aspirations",
      label: "Aspiraciones",
      type: "textarea",
      path: "psychographics.aspirations",
      rows: 3,
      hint: "A dónde quiere llegar este avatar. El agente pinta la oferta como el camino hacia esa visión.",
    },
    {
      id: "lifestyle",
      label: "Estilo de vida",
      type: "textarea",
      path: "psychographics.lifestyle",
      rows: 3,
      hint: "Cómo organiza su día, qué consume, qué le da identidad. Permite referencias culturales creíbles.",
    },

    // ── Dolores & deseos ─────────────────────────────────────────────────
    {
      id: "pain_points",
      label: "Pain points",
      type: "array",
      path: "pain_points",
      hint: "Situaciones concretas que este avatar no aguanta más. Cuanto más específico, más potente el pitch.",
      itemSchema: {
        fields: [
          {
            id: "description",
            label: "Descripción",
            type: "textarea",
            path: "description",
            rows: 2,
            required: true,
            hint: "El dolor concreto y su consecuencia. Usa lenguaje del cliente, no del vendedor.",
            examples: [
              {
                brand: "Nutricionista (Lima, PE)",
                text: "Sigo a dieta toda la semana y el fin de semana lo arruino todo, después me siento un fracaso.",
              },
              {
                brand: "Coach de negocios (Bogotá, CO)",
                text: "Trabajo 12 horas al día pero no sé cuánto dinero entra ni cuánto sale de mi empresa.",
              },
              {
                brand: "Consultora de marketing (CDMX)",
                text: "Mis clientes siempre piden 'un descuentito' y terminan pagando menos de lo que vale mi trabajo.",
              },
            ],
            formula: {
              template:
                "<slot>Situación concreta del cliente</slot> que resulta en <slot>costo emocional o práctico</slot>.",
            },
          },
          {
            id: "severity",
            label: "Severidad (1-5)",
            type: "number",
            path: "severity",
            hint: "Qué tan urgente o bloqueante es este dolor para el avatar. 5 = no puede seguir sin resolverlo.",
          },
        ],
      },
    },
    {
      id: "desires",
      label: "Deseos",
      type: "array",
      path: "desires",
      hint: "Lo que este avatar quiere lograr, sentir o ser. El agente usa esto como destino aspiracional.",
      itemSchema: {
        fields: [
          {
            id: "description",
            label: "Descripción",
            type: "textarea",
            path: "description",
            rows: 2,
            required: true,
            hint: "El deseo específico con resultado concreto. Incluye números si es posible.",
            examples: [
              {
                brand: "Coach de negocios (Bogotá, CO)",
                text: "Quiero facturar USD 5.000 al mes trabajando solo 4 horas por día desde cualquier lugar.",
              },
              {
                brand: "Nutricionista (Lima, PE)",
                text: "Quiero tener una relación normal con la comida y dejar de pensar en calorías todo el día.",
              },
              {
                brand: "Diseñadora (Santiago, CL)",
                text: "Quiero tener 3 clientes retainer que me paguen bien y dejar de hacer proyectos puntuales estresantes.",
              },
            ],
          },
          {
            id: "importance",
            label: "Importancia (1-5)",
            type: "number",
            path: "importance",
            hint: "Qué tan prioritario es este deseo para el avatar. 5 = haría lo que sea por lograrlo.",
          },
        ],
      },
    },
    {
      id: "objections",
      label: "Objeciones",
      type: "array",
      path: "objections",
      hint: "Las frases reales con las que este avatar evita comprar. El agente las detecta y responde.",
      itemSchema: {
        fields: [
          {
            id: "text",
            label: "Objeción",
            type: "textarea",
            path: "text",
            rows: 2,
            required: true,
            hint: "La frase textual que usaría este avatar para evitar avanzar. Sé específico, no genérico.",
            examples: [
              {
                brand: "Avatar: profesional 35+ (Lima, PE)",
                text: "Ya lo intenté antes y no me funcionó. No creo que esto sea para mí.",
              },
              {
                brand: "Avatar: emprendedora 28-35 (CDMX)",
                text: "Ahora no tengo tiempo, quizás en tres meses cuando esté más organizada.",
              },
              {
                brand: "Avatar: consultor (Bogotá, CO)",
                text: "Tengo que hablarlo con mi pareja antes de comprometer ese dinero.",
              },
            ],
          },
          {
            id: "response",
            label: "Respuesta sugerida",
            type: "textarea",
            path: "response",
            rows: 3,
            hint: "El argumento que el agente usa cuando el lead plantea esta objeción. Empático y concreto.",
          },
        ],
      },
    },

    // ── Canales & journey ────────────────────────────────────────────────
    {
      id: "preferred_channels",
      label: "Canales preferidos",
      type: "array",
      path: "preferred_channels",
      hint: "Dónde está este avatar y cómo prefiere que le contacten. Guía la estrategia de captación.",
      itemSchema: {
        fields: [
          {
            id: "channel",
            label: "Canal",
            type: "text",
            path: "channel",
            required: true,
            hint: "Nombre del canal: Instagram, WhatsApp, LinkedIn, email, TikTok, referidos, etc.",
          },
          {
            id: "usage",
            label: "Uso típico",
            type: "text",
            path: "usage",
            hint: "Cómo usa ese canal: consume contenido, busca información, chatea con marcas, etc.",
          },
        ],
      },
    },
    {
      id: "journey_awareness",
      label: "Etapa de awareness",
      type: "textarea",
      path: "buyer_journey.awareness",
      rows: 2,
      hint: "Cómo descubre por primera vez que tiene un problema o que existes. Define el ángulo de atracción.",
    },
    {
      id: "journey_consideration",
      label: "Etapa de consideración",
      type: "textarea",
      path: "buyer_journey.consideration",
      rows: 2,
      hint: "Cómo evalúa opciones antes de decidir. Qué compara, qué criterios usa, con quién consulta.",
    },
    {
      id: "journey_decision",
      label: "Etapa de decisión",
      type: "textarea",
      path: "buyer_journey.decision",
      rows: 2,
      hint: "Qué lo lleva al sí final: una prueba, una garantía, una conversación, un testimonio concreto.",
    },
  ],
};
