import type { SectionSchema } from "@/lib/form-runtime/schema";

export const methodologySchema: SectionSchema = {
  key: "brand.methodology",
  title: "Metodología",
  description: "Cómo operas: el método propio que te distingue.",
  fields: [
    {
      id: "methodology_name",
      label: "Nombre de la metodología",
      type: "text",
      path: "methodology_name",
      hint: "El nombre propio de tu método o framework. Lo que hace memorable tu proceso frente a la competencia.",
    },
    {
      id: "methodology_description",
      label: "Descripción",
      type: "textarea",
      path: "methodology_description",
      rows: 4,
      hint: "Qué es tu método, por qué funciona y qué lo diferencia de enfoques convencionales del sector.",
    },
    {
      id: "methodology_pillars",
      label: "Pilares",
      type: "array",
      path: "methodology_pillars",
      hint: "Los componentes esenciales de tu método. 3-5 pilares es el rango ideal para recordar y comunicar.",
      itemSchema: {
        fields: [
          {
            id: "title",
            label: "Título",
            type: "text",
            path: "title",
            required: true,
            hint: "Nombre corto del pilar. Idealmente una palabra o concepto clave.",
            examples: [
              { brand: "Coach de liderazgo (CDMX)", text: "Claridad Estratégica" },
              { brand: "Consultora financiera (Lima, PE)", text: "Flujo Controlado" },
              { brand: "Mentora de negocios (Medellín, CO)", text: "Oferta Magnética" },
            ],
          },
          {
            id: "description",
            label: "Descripción",
            type: "textarea",
            path: "description",
            rows: 3,
            hint: "Qué abarca este pilar y por qué es fundamental en tu método. 1-2 oraciones.",
            examples: [
              {
                brand: "Coach de liderazgo (CDMX)",
                text: "Definimos el estilo de liderazgo que mejor se adapta a tu contexto antes de cambiar cualquier comportamiento.",
              },
              {
                brand: "Consultora financiera (Lima, PE)",
                text: "Separamos ingresos, costos fijos y variables para que el dinero fluya de forma predecible cada mes.",
              },
              {
                brand: "Mentora de negocios (Medellín, CO)",
                text: "Diseñamos una oferta irresistible basada en el problema que tu cliente quiere resolver hoy, no en tus credenciales.",
              },
            ],
          },
        ],
      },
    },
  ],
};
