import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Value stack — la lista enumerada de entregables que recibe el cliente,
 * con valor percibido USD. Es el bloque que ancla precio.
 *
 * Scope OFFER_LEVEL: los entregables son los mismos para todas las
 * ediciones. Bonus específicos de una cohorte/salida viven en
 * ``resources`` (edition-level).
 *
 * **Latam — decisiones de diseño:**
 * - ``total_perceived_value_anchor`` surface un headline numérico
 *   ("Valor total: USD 4.344") que landing y agente usan para el
 *   anclaje de precio clásico: "valor USD 4.344 · tu inversión USD 1.497".
 *   Sin este anclaje explícito el stack pierde 40-60% de su poder.
 * - Cada ``deliverable`` tiene ``item_type`` core/bonus para que el agente
 *   y la landing puedan diferenciar lo esencial del regalo. Bonus-only
 *   items se muestran en landing como "Además te llevas estos regalos".
 * - ``perceived_value`` es en USD (no moneda local) porque es el anclaje
 *   cross-Latam. Si el tenant cobra en moneda local, el dual display
 *   se resuelve en render (se multiplica por tipo de cambio).
 */
export const offerValueStackSchema: SectionSchema = {
  key: "offer.value_stack",
  // title + description resolved from the backend SectionCatalog.
  scope: "offer_level",
  fields: [
    {
      id: "deliverables",
      label: "Entregables y bonus",
      type: "array",
      path: "deliverables",
      hint: "Cada componente concreto del stack con su valor percibido. Ordena desde lo más valioso hacia los bonus complementarios. 4-8 items es el sweet spot — menos de 4 se ve pobre, más de 10 se vuelve ruido.",
      itemSchema: {
        description: "Un componente del stack — concreto, enumerable y defendible con valor USD.",
        fields: [
          {
            id: "title",
            label: "Título del entregable",
            type: "text",
            path: "title",
            required: true,
            placeholder: "Curso grabado completo (8 módulos, 32 lecciones)",
          },
          {
            id: "description",
            label: "Descripción específica",
            type: "textarea",
            path: "description",
            rows: 3,
            placeholder:
              "Sistema paso-a-paso para implementar el método en 8 semanas. Incluye ejercicios prácticos al final de cada módulo y acceso al LMS de por vida.",
          },
          {
            id: "perceived_value",
            label: "Valor percibido en USD",
            type: "number",
            path: "perceived_value",
            placeholder: "897",
            hint: "El precio que tendría si se vendiera suelto en el mercado. Debe ser defendible — no inflado. Suma todos los items: el total debe ser 2-4x el precio de venta para anclaje efectivo.",
          },
          {
            id: "item_type",
            label: "Tipo",
            type: "enum",
            path: "item_type",
            options: [
              { value: "core", label: "Core (parte central de la oferta)" },
              { value: "bonus", label: "Bonus (regalo adicional)" },
              { value: "fast_action", label: "Fast-action (solo si compra en X días)" },
            ],
            hint: "Core = el cliente lo espera. Bonus = sorpresa que eleva valor. Fast-action = bonus condicionado a urgencia real (útil en lanzamientos).",
          },
          {
            id: "fulfillment_note",
            label: "Cuándo se entrega",
            type: "text",
            path: "fulfillment_note",
            placeholder: "Acceso inmediato post-checkout / Semana 1 de la cohorte / Entregado en mano en el evento",
            hint: "Claridad sobre la entrega reduce tickets de soporte post-venta. Si es acceso inmediato, dilo explícito.",
          },
        ],
      },
    },
    {
      id: "total_perceived_value_anchor",
      label: "Anclaje de valor total (USD)",
      type: "number",
      path: "total_perceived_value_anchor",
      placeholder: "4344",
      hint: "La cifra de anclaje que aparece en landing: 'Valor total USD 4.344 · Tu inversión hoy USD 1.497'. Puede ser la suma de perceived_value o un round number cercano. Sin este headline el stack pierde impacto.",
    },
    {
      id: "stack_positioning_statement",
      label: "Frase de posicionamiento del stack",
      type: "textarea",
      path: "stack_positioning_statement",
      rows: 3,
      placeholder:
        "Por el precio de dos consultas presenciales te llevas el método completo que hoy cobraría USD 4.344 si lo armara cliente por cliente. Todo accesible desde tu celular, a tu ritmo, con mi acompañamiento directo.",
      hint: "Una frase de 2-3 líneas que resume el trade-off 'valor vs precio'. El agente de ventas la usa en el cierre. Landing la muestra debajo del stack.",
    },
  ],
};
