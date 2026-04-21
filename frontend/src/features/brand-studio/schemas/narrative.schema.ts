import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * StoryBrand 7-step narrative. Each StoryBrand step lives at its own dotted
 * path in the `narrative` slice of BrandSettings. The runtime writes those
 * nested paths back via the feature's update function (composed in
 * FormRuntimeProvider).
 */
export const narrativeSchema: SectionSchema = {
  key: "brand.narrative",
  title: "Narrativa (StoryBrand)",
  description: "7 pasos para que tu cliente sea el héroe y tu marca la guía.",
  fields: [
    {
      id: "one_liner",
      label: "One-liner",
      type: "textarea",
      path: "one_liner",
      rows: 2,
      hint: "Una frase que resume todo el StoryBrand. Se usa en presentaciones, bio de redes y primera línea del agente.",
    },

    {
      id: "hero_identity",
      label: "Héroe: identidad",
      type: "textarea",
      path: "hero.identity",
      rows: 2,
      hint: "Quién es el héroe de tu historia: tu cliente, no tu marca. Descríbelo por lo que quiere lograr.",
    },
    {
      id: "hero_desire",
      label: "Héroe: deseo",
      type: "textarea",
      path: "hero.desire",
      rows: 2,
      hint: "Qué quiere el héroe más que nada. El motor narrativo que impulsa toda la historia.",
    },

    {
      id: "problem_villain",
      label: "Villano",
      type: "textarea",
      path: "problem.villain",
      rows: 2,
      hint: "El obstáculo externo personificado. Puede ser una industria, un sistema o una situación.",
    },
    {
      id: "problem_external",
      label: "Problema externo",
      type: "textarea",
      path: "problem.external_problem",
      rows: 2,
      hint: "El problema concreto y visible que el cliente necesita resolver hoy.",
    },
    {
      id: "problem_internal",
      label: "Problema interno",
      type: "textarea",
      path: "problem.internal_problem",
      rows: 2,
      hint: "El sentimiento o creencia que acompaña al problema externo. Aquí vive la emoción de compra.",
    },
    {
      id: "problem_philosophical",
      label: "Problema filosófico",
      type: "textarea",
      path: "problem.philosophical_problem",
      rows: 2,
      hint: "Por qué esto no debería estar pasando. La injusticia o contradicción que da urgencia moral.",
    },

    {
      id: "guide_empathy",
      label: "Empatía de la guía",
      type: "textarea",
      path: "guide.empathy_statement",
      rows: 2,
      hint: "Cómo tu marca demuestra que entiende el dolor del héroe. Sin esta conexión no hay confianza.",
    },
    {
      id: "guide_authority",
      label: "Autoridad de la guía",
      type: "textarea",
      path: "guide.authority_statement",
      rows: 2,
      hint: "Por qué tu marca es competente para guiar al héroe. Credenciales, casos, experiencia.",
    },

    {
      id: "plan",
      label: "Plan (pasos)",
      type: "array",
      path: "plan",
      hint: "Los 3-5 pasos simples que le muestras al cliente para llegar del problema al resultado.",
      itemSchema: {
        fields: [
          {
            id: "step_number",
            label: "Número",
            type: "number",
            path: "step_number",
            required: true,
            hint: "Posición del paso en la secuencia. Empieza en 1.",
          },
          {
            id: "title",
            label: "Título",
            type: "text",
            path: "title",
            hint: "Nombre corto y accionable del paso. Máximo 5 palabras.",
          },
          {
            id: "description",
            label: "Descripción",
            type: "textarea",
            path: "description",
            rows: 2,
            hint: "Qué pasa en este paso. Concreto y sin jerga. Lo que el cliente espera al llegar aquí.",
            examples: [
              {
                brand: "Coach ejecutiva (CDMX)",
                text: "Hacemos una sesión de diagnóstico de 60 min para mapear tus prioridades y cuellos de botella actuales.",
              },
              {
                brand: "Agencia de marketing (Bogotá, CO)",
                text: "Auditamos tus campañas actuales e identificamos las 3 palancas que más impacto tendrán en los próximos 30 días.",
              },
              {
                brand: "Consultor financiero (Lima, PE)",
                text: "Revisamos tus estados de cuenta y categorizamos ingresos, gastos fijos y gastos variables.",
              },
            ],
          },
        ],
      },
    },

    {
      id: "cta_direct",
      label: "CTA directo",
      type: "text",
      path: "cta.direct_cta",
      hint: "El llamado principal a la acción: compra, reserva, agenda. Activo e imperativo.",
    },
    {
      id: "cta_transitional",
      label: "CTA transicional",
      type: "text",
      path: "cta.transitional_cta",
      hint: "Un CTA de menor compromiso para los que no están listos: descarga, webinar, diagnóstico gratis.",
    },

    {
      id: "outcome_success",
      label: "Transformación (éxito)",
      type: "textarea",
      path: "outcome.success_transformation",
      rows: 2,
      hint: "Cómo se ve la vida del cliente después de trabajar contigo. Concreto y aspiracional.",
    },
    {
      id: "outcome_failure",
      label: "Consecuencia (fracaso)",
      type: "textarea",
      path: "outcome.failure_consequence",
      rows: 2,
      hint: "Qué le pasa al cliente si no actúa. El costo real de la inacción. No exageres, pero nómbralo.",
    },
  ],
};
