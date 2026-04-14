/**
 * Central dictionary of metric descriptions for info tooltips in the
 * Email Automations UI. Used by table headers, KPIs, pipeline nodes,
 * and sidebar metric boxes.
 */

export interface MetricInfo {
  title: string;
  description: string;
  formula?: string;
  interpret?: {
    good: string;
    mid: string;
    bad: string;
  };
}

export const AUTOMATION_METRIC_INFO: Record<string, MetricInfo> = {
  ingresados: {
    title: "Ingresados",
    description:
      "Total de suscriptores que entraron a este flujo automatizado (completados + en cola actualmente).",
    formula: "completados + en_cola",
    interpret: {
      good: "Más ingresados = mayor alcance automatizado",
      mid: "",
      bad: "",
    },
  },
  completaron: {
    title: "Completaron",
    description:
      "Suscriptores que recibieron TODOS los emails de la secuencia. El porcentaje muestra la tasa de completación.",
    formula: "completados / ingresados × 100",
    interpret: {
      good: ">60% excelente retención",
      mid: "30-60% revisar contenido medio",
      bad: "<30% la secuencia pierde gente",
    },
  },
  openRate: {
    title: "Open Rate",
    description:
      "Porcentaje de emails abiertos sobre el total entregado. Refleja la calidad de tus subject lines.",
    formula: "emails abiertos / emails entregados × 100",
    interpret: {
      good: ">50% excelente",
      mid: "30-50% aceptable",
      bad: "<30% mejorar subjects",
    },
  },
  clickRate: {
    title: "Click Rate",
    description:
      "Porcentaje de emails donde al menos un enlace fue clickeado. Mide si tu contenido genera acción.",
    formula: "emails con click / emails entregados × 100",
    interpret: {
      good: ">5% muy bueno",
      mid: "2-5% promedio",
      bad: "<2% CTA no conecta",
    },
  },
  ctor: {
    title: "Click-to-Open Rate (CTOR)",
    description:
      "De los que abrieron, ¿cuántos hicieron click? La métrica más pura de engagement — elimina el efecto del subject line.",
    formula: "clicks únicos / aperturas únicas × 100",
    interpret: {
      good: ">15% contenido muy relevante",
      mid: "8-15% normal",
      bad: "<8% contenido no convence",
    },
  },
  unsubs: {
    title: "Desuscripciones",
    description:
      "Personas que se desuscribieron durante esta automatización. Un número alto indica que el contenido no cumple la expectativa.",
    interpret: {
      good: "0-1 normal",
      mid: "2-3 monitorear",
      bad: ">3 revisar frecuencia y relevancia",
    },
  },
  salud: {
    title: "Score de Salud",
    description:
      "Índice compuesto 0-100 que combina apertura, clicks, CTOR, completación y penaliza desuscripciones.",
    formula: "0.3×open + 0.25×click + 0.2×CTOR + 0.15×completion − 0.1×unsub_rate",
    interpret: {
      good: ">70 saludable",
      mid: "40-70 oportunidad de mejora",
      bad: "<40 acción urgente",
    },
  },
  dropoff: {
    title: "Caída entre pasos",
    description:
      "Porcentaje de suscriptores que dejaron de recibir el siguiente email. Una caída alta indica que el contenido o el timing no funciona.",
    formula: "(1 − siguiente_enviados / actual_enviados) × 100",
    interpret: {
      good: "<10% secuencia saludable",
      mid: "10-30% aceptable",
      bad: ">30% problema serio",
    },
  },
  stepOpen: {
    title: "Open Rate del email",
    description:
      "Porcentaje que abrió este email específico. Compara con otros pasos para detectar fatiga de secuencia.",
  },
  stepClick: {
    title: "Click Rate del email",
    description:
      "Porcentaje que hizo click en este email. Click bajo con open alto = el CTA o contenido no convence.",
  },
  enviados: {
    title: "Enviados",
    description: "Emails entregados exitosamente a la bandeja del suscriptor.",
  },
  abiertos: {
    title: "Abiertos",
    description:
      "Aperturas únicas. Cada suscriptor cuenta una sola vez aunque abra múltiples veces.",
  },
  clicks: {
    title: "Clicks",
    description: "Clicks únicos en cualquier enlace del email. Cada suscriptor cuenta una vez.",
  },
  bounces: {
    title: "Bounce Rate",
    description:
      "Porcentaje de emails que no pudieron ser entregados (direcciones inválidas o buzones llenos). Un bounce alto daña la reputación del dominio.",
    formula: "emails rebotados / emails enviados × 100",
    interpret: {
      good: "<2% lista saludable",
      mid: "2-5% limpiar lista",
      bad: ">5% lista desactualizada — pausar envíos",
    },
  },
  campaignHealth: {
    title: "Score de Salud de Campaña",
    description:
      "Índice compuesto 0-100 que combina apertura, clicks, CTOR y penaliza rebotes y desuscripciones. Ideal para priorizar qué campañas replicar y cuáles evitar.",
    formula: "0.35×open + 0.30×click + 0.25×CTOR − 0.10×unsub_rate − 0.10×bounce_rate",
    interpret: {
      good: ">70 campaña saludable",
      mid: "40-70 oportunidad de mejora",
      bad: "<40 revisar segmentación y contenido",
    },
  },
};
