import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Portfolio — casos de éxito concretos con resultados medibles. Distinto
 * de TESTIMONIALS (citas/reseñas cortas); PORTFOLIO son cases largos con
 * estructura desafío → solución → resultado.
 *
 * Latam: crítico para consultorías, agencias, coaches, academias y SaaS.
 * Los números duros ("ROI 320% en 6 meses") pesan más que el texto
 * narrativo. Si hay NDAs, usar "Cliente en industria Y" en vez del nombre.
 */
export const offerPortfolioSchema: SectionSchema = {
  key: "offer.portfolio",
  scope: "offer_level",
  fields: [
    {
      id: "cases",
      label: "Casos de éxito",
      type: "array",
      path: "portfolio_cases",
      hint: "Cada caso: título, cliente, industria, desafío, solución, resultados medibles. 4-6 casos diversos mueven más la aguja que 15 similares.",
      itemSchema: {
        description: "Un caso de éxito documentado.",
        fields: [
          {
            id: "title",
            label: "Título del caso",
            type: "text",
            path: "title",
            required: true,
            placeholder: "Tripliqué ventas de agencia PYME en Lima",
            hint: "Una frase que resuma el resultado. Los decimales y tiempos venden.",
          },
          {
            id: "client_name",
            label: "Cliente",
            type: "text",
            path: "client_name",
            placeholder: "Agencia Alfa — o 'Consultora financiera en México' si hay NDA",
            hint: "Si tenés NDA, usá sector + país sin nombre propio.",
          },
          {
            id: "client_logo_url",
            label: "Logo del cliente",
            type: "url",
            path: "client_logo_url",
            hint: "Logo simplifica credibilidad. Solo si tenés autorización.",
          },
          {
            id: "industry",
            label: "Industria",
            type: "text",
            path: "industry",
            placeholder: "Retail, SaaS B2B, Salud, Educación",
          },
          {
            id: "country",
            label: "País del caso",
            type: "text",
            path: "country",
            placeholder: "Perú, México, Colombia",
            hint: "Para prospectos Latam, ver casos del mismo país convierte más.",
          },
          {
            id: "challenge",
            label: "Desafío inicial",
            type: "textarea",
            path: "challenge",
            rows: 3,
            required: true,
            placeholder: "Tenían 8 años sin crecer, dependientes de 2 clientes grandes.",
            hint: "El contexto del problema. Lo que tu cliente reconocerá como propio.",
          },
          {
            id: "solution",
            label: "Qué hicimos",
            type: "textarea",
            path: "solution",
            rows: 3,
            required: true,
            placeholder: "Rediseño de oferta + funnel de captación + playbook de ventas.",
            hint: "El 'qué' concreto. No jerga. Diferenciá tu método de otros.",
          },
          {
            id: "results_summary",
            label: "Resultado resumido",
            type: "text",
            path: "results_summary",
            required: true,
            placeholder: "3x en facturación · 40% menos dependencia de cliente top · 6 meses",
            hint: "Una línea con los números duros. Es lo que mira el prospecto.",
          },
          {
            id: "results_metrics",
            label: "Métricas clave (detalle)",
            type: "array",
            path: "results_metrics",
            hint: "Opcional. Cada métrica con su número y ventana de tiempo.",
            itemSchema: {
              description: "Una métrica con su resultado cuantificado.",
              fields: [
                {
                  id: "metric",
                  label: "Métrica",
                  type: "text",
                  path: "metric",
                  placeholder: "ROI, retención, NPS, ventas, LTV",
                },
                {
                  id: "value",
                  label: "Valor",
                  type: "text",
                  path: "value",
                  placeholder: "320%, USD 85.000, 4.8/5",
                },
                {
                  id: "timeframe",
                  label: "Período",
                  type: "text",
                  path: "timeframe",
                  placeholder: "6 meses, trimestre, 12 semanas",
                },
              ],
            },
          },
          {
            id: "proof_url",
            label: "URL de prueba pública",
            type: "url",
            path: "proof_url",
            hint: "Link al case study público, nota de prensa, video testimonial del cliente o reporte verificable. Con esto el caso deja de ser 'dicho por vos' y pasa a ser verificable.",
          },
          {
            id: "case_period_start",
            label: "Inicio del proyecto (mes/año)",
            type: "text",
            path: "case_period_start",
            placeholder: "2025-03",
            hint: "Contexto temporal. Un caso de 2019 tiene menos peso que uno de 2025. Formato YYYY-MM.",
          },
          {
            id: "case_period_end",
            label: "Fin del proyecto (mes/año)",
            type: "text",
            path: "case_period_end",
            placeholder: "2025-09",
            hint: "Cuándo se logró el resultado. Vacío si sigue en curso (retainer activo). Formato YYYY-MM.",
          },
          {
            id: "team_involvement",
            label: "Equipo involucrado",
            type: "text",
            path: "team_involvement",
            placeholder: "Solo / Equipo de 3 / Yo + cliente + su team de 5",
            hint: "Claridad sobre quién hizo qué. Evita confusiones sobre si fue tu trabajo exclusivo o colaborativo.",
          },
          {
            id: "is_featured",
            label: "¿Destacar en landing?",
            type: "boolean",
            path: "is_featured",
            hint: "Los destacados aparecen en el hero o carrusel principal. 2-3 máximo.",
          },
          {
            id: "permission_to_publish",
            label: "¿Tenés permiso documentado del cliente?",
            type: "boolean",
            path: "permission_to_publish",
            hint: "Legal Latam — LGPD/Habeas Data/LOPD. Especialmente relevante si mostrás logo, nombre y métricas del cliente. WhatsApp o email con OK explícito basta; guardá el comprobante.",
          },
        ],
      },
    },
    {
      id: "client_logos",
      label: "Logos de clientes (hall of fame)",
      type: "array",
      path: "client_logos",
      hint: "Logos de clientes atendidos — ideal 6-12. Grid en la landing: 'Empresas que confían en nosotros'.",
      itemSchema: {
        description: "Logo individual de un cliente.",
        fields: [
          {
            id: "name",
            label: "Nombre del cliente",
            type: "text",
            path: "name",
            required: true,
          },
          {
            id: "logo_url",
            label: "URL del logo",
            type: "url",
            path: "logo_url",
            required: true,
          },
        ],
      },
    },
    {
      id: "aggregate_results",
      label: "Resultados agregados",
      type: "textarea",
      path: "aggregate_results",
      rows: 3,
      placeholder: "1.200+ alumnos graduados · USD 4M gestionados · 98% satisfacción",
      hint: "Métricas totales del negocio completo (no de un caso individual). Se muestra como banner de números.",
    },
  ],
};
