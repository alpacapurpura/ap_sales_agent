/**
 * Tooltip copy library for the Meta Ads Resumen tab.
 *
 * Source of truth: `docs/superpowers/artifacts/2026-04-10-meta-ads-resumen/UI-SPEC.md` §4.
 *
 * Each entry has a `title` (short, used as the tooltip header) and a `body`
 * (≤ 200 chars, plain-language explanation in Spanish). Tildes and ñ are
 * mandatory — `.claude/rules/spanish-text.md`.
 */

export interface TooltipContent {
  title: string;
  body: string;
}

export const RESUMEN_TOOLTIPS: Record<string, TooltipContent> = {
  // ─────────── Inversión ───────────
  spend: {
    title: 'Inversión',
    body: 'Lo que gastaste en Meta Ads en el período. Incluye todas las campañas activas. Base de cálculo para ROAS, CPA y CTR.',
  },
  spend_branding: {
    title: 'Inversión en Branding',
    body: 'Gasto en campañas de awareness (sin objetivo de venta). Invertís para que más gente te conozca, no para cerrar hoy.',
  },
  spend_unassigned: {
    title: 'Inversión sin asignar',
    body: 'Gasto de campañas que todavía no vinculaste a un producto. Estás pagando, pero no sabés qué offer está generando resultados.',
  },

  // ─────────── ROAS ───────────
  roas: {
    title: 'ROAS · Retorno sobre inversión',
    body: 'Por cada $1 que gastás, cuánto volvés a facturar. ROAS 2x = recuperás $2 por cada $1. Sano: ≥ 2x. Rojo: < 1x.',
  },

  // ─────────── Resultados (generales y por tipo) ───────────
  results_all: {
    title: 'Resultados totales',
    body: 'Suma de todos los resultados primarios de tus offers (ventas, leads, mensajes). Es la cosecha real del período.',
  },
  results_leads: {
    title: 'Leads',
    body: 'Personas que dejaron sus datos (email, WhatsApp) para que los contactes. Siguiente paso: nutrirlos hasta la venta.',
  },
  results_purchases: {
    title: 'Compras',
    body: 'Ventas directas atribuidas a Meta Ads. Requiere Pixel con evento Purchase configurado en tu checkout.',
  },
  results_messages: {
    title: 'Mensajes iniciados',
    body: 'Conversaciones nuevas que arrancó Meta Ads (DM, WhatsApp). Cada uno es un prospecto caliente que escribió primero.',
  },
  results_calls: {
    title: 'Llamadas',
    body: 'Clics en el botón de llamar de tu anuncio. Mide interés alto — si llaman, casi compran.',
  },
  results_registrations: {
    title: 'Registros',
    body: 'Inscripciones completadas (webinar, curso gratis, evento). Sirven para calificar prospectos antes de vender.',
  },
  results_forms: {
    title: 'Forms completados',
    body: 'Formularios llenos y enviados. Son leads más calificados que un simple clic porque dedicaron tiempo a completar.',
  },

  // ─────────── Costos por resultado ───────────
  cpa: {
    title: 'CPA · Costo por adquisición',
    body: 'Cuánto te cuesta cada venta. Más bajo es mejor. Compará contra tu margen: si CPA > ganancia por venta, estás perdiendo.',
  },
  cpl: {
    title: 'CPL · Costo por lead',
    body: 'Cuánto pagás por cada persona que te dejó sus datos. Sano: entre $1 y $15 según nicho. Más bajo no siempre es mejor si la calidad cae.',
  },
  cost_per_result: {
    title: 'Costo por resultado',
    body: 'Lo que te cuesta generar un resultado primario de esta offer. Usalo como guía — compará contra tu ticket promedio.',
  },
  cost_per_message: {
    title: 'Costo por mensaje',
    body: 'Lo que pagás por cada conversación iniciada. Si es bajo pero nadie cierra, el problema no es el anuncio sino tu respuesta.',
  },
  cost_per_call: {
    title: 'Costo por llamada',
    body: 'Gasto por cada clic en el botón de llamar. Sano si tu ticket es alto; caro si vendés productos de bajo precio.',
  },
  cost_per_registration: {
    title: 'Costo por registro',
    body: 'Lo que cuesta conseguir una inscripción. Medí la tasa de registro → venta para saber si el registro es barato o caro real.',
  },
  cost_per_form: {
    title: 'Costo por form',
    body: 'Lo que cuesta un formulario lleno. Suelen ser leads de mejor calidad que un clic simple — justifica un CPA más alto.',
  },

  // ─────────── CTR / CPC / CPM ───────────
  ctr: {
    title: 'CTR · Click-through rate',
    body: '% de personas que ven tu anuncio y hacen clic. Bueno: > 1%. Bajo < 0.5% indica que la creativa no engancha — cambiá imagen o copy.',
  },
  ctr_unassigned: {
    title: 'CTR (sin asignar)',
    body: '% de clics de campañas que no vinculaste a una offer. Útil para ver si esas campañas están tirando bien antes de asignarlas.',
  },
  cpc: {
    title: 'CPC · Costo por clic',
    body: 'Lo que pagás por cada clic al anuncio. Depende de nicho y puja. Si sube sin razón, revisá frecuencia y calidad de audiencia.',
  },
  cpm: {
    title: 'CPM · Costo por mil impresiones',
    body: 'Lo que cuesta mostrar tu anuncio 1.000 veces. Mide precio de la audiencia. CPM alto = audiencia cara (competida o pequeña).',
  },

  // ─────────── Reach / Impresiones / Frecuencia ───────────
  reach_all: {
    title: 'Alcance total',
    body: 'Personas únicas que vieron al menos un anuncio tuyo. NO es la suma de días ni campañas — es gente, no vistas.',
  },
  reach_offer: {
    title: 'Alcance de esta offer',
    body: 'Personas únicas alcanzadas por las campañas de esta offer. Disponible cuando hay 1 campaña por offer (sin solape).',
  },
  reach_branding: {
    title: 'Alcance de Branding',
    body: 'Personas únicas expuestas a tus campañas de awareness. Medí crecimiento mes a mes — es tu cuota de atención.',
  },
  impressions: {
    title: 'Impresiones',
    body: 'Cantidad de veces que se mostró tu anuncio. Incluye repeticiones a la misma persona (dividí por alcance = frecuencia).',
  },
  clicks: {
    title: 'Clics',
    body: 'Total de clics en tus anuncios. Incluye clics a link, al perfil o al botón CTA. Dividí por impresiones para sacar CTR.',
  },
  frequency: {
    title: 'Frecuencia',
    body: 'Cuántas veces en promedio ve tu anuncio cada persona. Sana: 1.5–3. Arriba de 5 aburrís a tu audiencia — rotá la creativa.',
  },

  // ─────────── Campañas activas / sin asignar ───────────
  active_campaigns_branding: {
    title: 'Campañas activas',
    body: 'Campañas de branding corriendo hoy. Normal: 1 a 3 por vez. Más de 5 y se canibalizan entre sí — consolidá.',
  },
  unassigned_campaigns: {
    title: 'Campañas sin asignar',
    body: 'Campañas que tenés en Meta pero que no vinculaste a ninguna offer. Asigná cada una para ver métricas por producto.',
  },

  // ─────────── Estados ───────────
  unavailable_generic: {
    title: 'Dato no disponible',
    body: 'No hay información suficiente para calcular este valor con confianza en este filtro y período.',
  },
  unavailable_reach_overlap: {
    title: 'Alcance no combinable',
    body: "El alcance de varias campañas no se puede sumar — las audiencias se solapan. Disponible en 'Todas' o en offers de 1 sola campaña.",
  },
  unavailable_pixel: {
    title: 'Requiere Meta Pixel',
    body: 'Esta métrica necesita el Meta Pixel instalado en tu sitio, con los eventos configurados (Lead, Purchase, etc.).',
  },
  unavailable_period_pending: {
    title: 'Alcance en consolidación',
    body: 'El alcance se calcula al cierre de cada día. Volvé mañana para ver el valor definitivo del período.',
  },
  unavailable_no_events: {
    title: 'Sin eventos reportados',
    body: 'No hubo eventos primarios de esta offer en el período. Verificá que el Pixel esté disparando y que la campaña esté activa.',
  },
  unavailable_metric_not_supported: {
    title: 'Métrica no soportada',
    body: 'Esta offer no tiene una métrica primaria compatible con Meta Ads. Configurala en Offer Studio para activar el tracking.',
  },

  // ─────────── Funnel steps ───────────
  funnel_impressions: {
    title: 'Impresiones',
    body: 'Veces que se mostró tu anuncio en el período filtrado. Es la boca del embudo: cuanta más gente lo vea, más oportunidades abajo.',
  },
  funnel_clicks: {
    title: 'Clics',
    body: 'Personas que hicieron clic después de ver el anuncio. La tasa clics/impresiones es tu CTR.',
  },
  funnel_landing: {
    title: 'Vistas de Landing',
    body: 'Personas que llegaron a tu página desde el clic. Si hay caída fuerte clics → landing, revisá velocidad y enlace del anuncio.',
  },
  funnel_leads: {
    title: 'Leads',
    body: 'Prospectos que completaron un formulario o dejaron sus datos. Requiere evento Lead del Pixel en tu landing.',
  },
  funnel_conversions: {
    title: 'Conversiones',
    body: 'Ventas o resultados finales atribuidos a Meta Ads. Requiere evento Purchase (o el que uses) del Pixel.',
  },
};
