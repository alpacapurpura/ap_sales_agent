import type { SectionSchema } from "@/lib/form-runtime/schema";

export const positioningSchema: SectionSchema = {
  key: "brand.positioning",
  title: "Posicionamiento",
  description: "Brand Love Key: UVP, insight, beneficios, RTBs, esencia.",
  fields: [
    {
      id: "unique_value_proposition",
      label: "Propuesta de valor única",
      type: "textarea",
      path: "unique_value_proposition",
      rows: 3,
      hint: "El beneficio específico que solo tú das y que tu cliente ideal más valora.",
      examples: [
        {
          brand: "Coach ejecutiva (CDMX)",
          text: "Líderas equipos remotos sin perder tu bienestar ni tu vida personal en 12 semanas.",
        },
        {
          brand: "Agencia de marketing (Bogotá, CO)",
          text: "Triplicamos tu ROI en Meta Ads en 90 días o devolvemos el mes de retainer.",
        },
        {
          brand: "Nutricionista (Santiago, CL)",
          text: "Normalización de tu relación con la comida sin dietas restrictivas ni conteos de calorías.",
        },
      ],
      formula: {
        template:
          "Para <slot>quién</slot> que <slot>tiene este problema</slot>, <slot>tu marca</slot> es <slot>categoría</slot> que <slot>beneficio único</slot>.",
      },
      downstreamUses: [
        { label: "Hero de landings" },
        { label: "Primera línea del pitch del agente" },
      ],
    },
    {
      id: "discriminator",
      label: "Discriminador",
      type: "textarea",
      path: "discriminator",
      rows: 2,
      hint: "Qué te hace imposible de confundir con la competencia.",
    },
    {
      id: "brand_essence",
      label: "Esencia de marca",
      type: "text",
      path: "brand_essence",
      hint: "La idea central que define todo lo que tu marca hace y comunica. Máximo una frase corta.",
    },

    // Competitive environment
    {
      id: "technical_enemy",
      label: "Enemigo técnico",
      type: "textarea",
      path: "competitive_environment.technical_enemy",
      rows: 2,
      hint: "El obstáculo concreto (herramienta, método, situación) que bloquea a tu cliente para lograr su objetivo.",
    },
    {
      id: "philosophical_enemy",
      label: "Enemigo filosófico",
      type: "textarea",
      path: "competitive_environment.philosophical_enemy",
      rows: 2,
      hint: "La creencia o mentalidad limitante que le impide avanzar. El agente la derrumba con argumentos.",
    },

    // Insight
    {
      id: "insight_tension",
      label: "Insight: tensión",
      type: "textarea",
      path: "insight.tension",
      rows: 2,
      hint: "La contradicción o paradoja que vive tu cliente y que nadie en el mercado ha nombrado todavía.",
    },
    {
      id: "insight_observation",
      label: "Insight: observación",
      type: "textarea",
      path: "insight.observation",
      rows: 2,
      hint: "El comportamiento real que observas en tu cliente ideal que revela algo no obvio de sus necesidades.",
    },
    {
      id: "insight_implication",
      label: "Insight: implicación",
      type: "textarea",
      path: "insight.implication",
      rows: 2,
      hint: "Qué significa ese insight para tu marca: qué oportunidad abre o qué ángulo de comunicación habilita.",
    },

    // Reasons to believe (array)
    {
      id: "reasons_to_believe",
      label: "Reasons to believe",
      type: "array",
      path: "reasons_to_believe",
      hint: "Evidencias que respaldan tu propuesta: datos, casos, certificaciones o hechos verificables.",
      itemSchema: {
        fields: [
          {
            id: "type",
            label: "Tipo",
            type: "text",
            path: "type",
            hint: "Categoría de la evidencia: dato, caso de éxito, certificación, reconocimiento, testimonial.",
          },
          {
            id: "statement",
            label: "Afirmación",
            type: "textarea",
            path: "statement",
            rows: 2,
            required: true,
            hint: "La afirmación concreta que prueba tu propuesta. Con números siempre que sea posible.",
            examples: [
              {
                brand: "Coach ejecutiva (CDMX)",
                text: "+200 líderes graduados con un 87% que reportó aumento de productividad.",
              },
              {
                brand: "Agencia digital (Lima, PE)",
                text: "ROI promedio de 3.4x en 60 días para e-commerce de salud y bienestar.",
              },
              {
                brand: "Consultor financiero (Buenos Aires, AR)",
                text: "Certificado CFP con 12 años de experiencia gestionando carteras +USD 5M.",
              },
            ],
          },
          {
            id: "proof_url",
            label: "URL de prueba",
            type: "url",
            path: "proof_url",
            hint: "Link al caso, certificación, artículo o reporte que valida la afirmación.",
          },
        ],
      },
    },
  ],
};
