/**
 * Single source of truth for metric name -> Spanish label mappings.
 *
 * Merged from ChannelRow, SidebarContent, ChannelDetailSidebar, and
 * CampaignDrillDown to eliminate DRY violations and drift risk.
 */

/** Fallback metric name -> Spanish label (used when catalog entry is unavailable). */
export const METRIC_LABELS: Record<string, string> = {
  // ─── General / Shared ───────────────────────────────────────────────────────
  reach: "Alcance",
  engagement: "Engagement",
  sessions: "Sesiones",
  users: "Usuarios",
  clicks: "Clicks",
  conversions: "Conversiones",
  spend: "Gasto",
  contacts: "Contactos",
  responses: "Respuestas",
  leads: "Leads",
  cost: "Costo",
  conversion_rate: "Conversion",
  conversations: "Conversaciones",
  emails_sent: "Enviados",
  open_rate: "Apertura",
  click_rate: "Clicks",
  followups: "Follow-ups",
  response_rate: "Respuestas",
  campaigns: "Campanas",
  count: "Cantidad",
  value: "Valor",
  abandonment_rate: "Abandono",
  booked: "Agendadas",
  completed: "Completadas",
  no_show: "No-Show",
  rescheduled: "Reprogramadas",
  attendance_rate: "Asistencia",
  impressions: "Impresiones",
  visitors: "Visitantes",

  // ─── ManyChat / AI Agent ────────────────────────────────────────────────────
  new_subscribers: "Nuevos Suscriptores",
  comment_triggers: "Comment Triggers",
  dm_opens: "DMs Abiertos",
  sequences_sent: "Secuencias Enviadas",
  qualified_leads: "Leads Calificados",
  meetings_requested: "Reuniones Solicitadas",
  bofu_flows_triggered: "Flows BOFU",
  consultations: "Consultas",
  link_clicks: "Links Clickeados",
  tag_applied: "Tags Aplicados",
  flows_triggered: "Flows Activados",

  // ─── Email / MailerLite ─────────────────────────────────────────────────────
  unique_opens: "Aperturas",
  click_to_open_rate: "CTOR",
  unsubscribe_rate: "Tasa Desuscripción",
  bounce_rate: "Tasa Rebote",
  form_conversions: "Conversiones Form",
  form_conversion_rate: "Tasa Conversión",
  completion_rate: "Tasa Completadas",
  reactivation_rate: "Tasa Reactivación",
  active_subscribers: "Suscriptores Activos",
  forwards: "Reenvíos",
  hard_bounces: "Rebotes Duros",
  soft_bounces: "Rebotes Suaves",
  spam_reports: "Spam",
  unique_clicks: "Clicks Únicos",
  automation_completed: "Automatizaciones",
  unsubscribes: "Desuscripciones",

  // ─── Email / Advanced ────────────────────────────────────────────────────────
  deliverability_rate: "Entregabilidad",
  list_growth_rate: "Crecimiento de Lista",
  churn_rate: "Tasa de Churn",
  forward_rate: "Tasa de Reenvío",
  opens_count: "Aperturas Totales",
  clicks_count: "Clics Totales",

  // ─── Instagram Organic ──────────────────────────────────────────────────────
  ig_views: "Vistas",
  total_interactions: "Interacciones",
  ig_likes: "Likes",
  ig_comments: "Comentarios",
  ig_shares: "Compartidos",
  ig_saves: "Guardados",
  ig_replies: "Respuestas Stories",
  ig_reposts: "Reposts",
  ig_accounts_engaged: "Cuentas Engaged",
  ig_follows_and_unfollows: "Seguidores Netos",
  ig_follows_gained: "Seguidores Ganados",
  ig_follows_lost: "Seguidores Perdidos",
  ig_profile_links_taps: "Taps Perfil",
  ig_followers_count: "Seguidores",
  ig_media_count: "Publicaciones",
  ig_follower_demographics: "Demografia",
  ig_engaged_audience_demographics: "Demografia Engaged",

  // ─── Meta Ads Expanded ──────────────────────────────────────────────────────
  meta_inline_link_clicks: "Clics al Destino",
  meta_outbound_clicks: "Clics Salientes",
  meta_landing_page_views: "Vistas de Landing",
  meta_cost_per_link_click: "Costo por Clic al Destino",
  meta_cost_per_outbound_click: "Costo por Clic Saliente",
  meta_leads: "Leads",
  meta_add_to_cart: "Agregar al Carrito",
  meta_initiate_checkout: "Checkouts Iniciados",
  meta_registrations: "Registros",
  meta_view_content: "Vistas de Contenido",
  meta_search_actions: "Busquedas",
  meta_conversations_started: "Conversaciones",
  meta_link_clicks: "Link Clicks",
  meta_page_engagement: "Engagement de Pagina",
  meta_video_views: "Reproducciones de Video",
  meta_conversion_value: "Valor de Conversiones",
  meta_purchase_roas: "ROAS",
  meta_cost_per_purchase: "Costo por Compra",
  meta_cost_per_lead: "Costo por Lead",
  meta_cpp: "CPP",
  meta_post_engagement: "Engagement de Post",
  meta_video_p25: "Video 25%",
  meta_video_p50: "Video 50%",
  meta_video_p75: "Video 75%",
  meta_video_p100: "Video 100%",
  meta_video_30sec: "Video 30s+",
  meta_video_avg_watch_time: "Duracion Promedio",

  // ─── Meta Ads Breakdowns ────────────────────────────────────────────────────
  meta_reach_by_age: "Alcance por Edad",
  meta_spend_by_age: "Gasto por Edad",
  meta_impressions_by_age: "Impresiones por Edad",
  meta_reach_by_gender: "Alcance por Genero",
  meta_spend_by_gender: "Gasto por Genero",
  meta_impressions_by_gender: "Impresiones por Genero",
  meta_reach_by_placement: "Alcance por Plataforma",
  meta_spend_by_placement: "Gasto por Plataforma",
  meta_impressions_by_placement: "Impresiones por Plataforma",

  // ─── YouTube Organic ────────────────────────────────────────────────────────
  views: "Vistas",
  watch_time_minutes: "Minutos Vistos",
  avg_view_duration: "Duracion Promedio",
  avg_view_percentage: "% Retencion Promedio",
  subscribers_gained: "Suscriptores Ganados",
  subscribers_lost: "Suscriptores Perdidos",
  comments: "Comentarios",
  shares: "Compartidos",
  card_clicks: "Clics en Tarjetas",
  card_impressions: "Impresiones Tarjetas",
  card_click_rate: "CTR Tarjetas",
  end_screen_clicks: "Clics Pantalla Final",
  end_screen_impressions: "Imp. Pantalla Final",
  end_screen_click_rate: "CTR Pantalla Final",

  // ─── Google Analytics / GA4 ─────────────────────────────────────────────────
  bounceRate: "Tasa de Rebote",
  engagedSessions: "Sesiones Activas",
  newUsers: "Nuevos Usuarios",
  screenPageViews: "Vistas de Pagina",
  averageSessionDuration: "Duracion promedio",
  ctr: "CTR",
  cpm: "CPM",
  cpc: "CPC",
  frequency: "Frecuencia",

  // ─── Sidebar-specific (funnel / detail panels) ──────────────────────────────
  total_leads: "Total Leads",
  total_mqls: "Total MQLs",
  total_sqls: "Total SQLs",
  revenue: "Revenue",
  offer_detail: "Detalle de Oferta",
  pipeline: "Pipeline (SQLs)",
  customers: "Clientes",
  health_pct: "Salud del Cliente",
  net_mrr: "Ingreso Recurrente Neto",
  k_factor: "K-Factor",
  pixel_pageviews: "Visitas al sitio (Pixel)",
  pixel_view_content: "Vieron contenido",
  pixel_leads: "Dejaron datos",
  pixel_add_to_cart: "Agregaron al carrito",
  pixel_purchases: "Compraron",
  top_pages: "Paginas mas vistas",
  traffic_sources: "Fuentes de trafico",
  device_split: "Dispositivos",
};

/**
 * Resolve a human-readable label for a metric name.
 *
 * Priority:
 * 1. Metric catalog entry (display_name) if available
 * 2. METRIC_LABELS dictionary fallback
 * 3. Raw metric name as last resort
 */
export function getMetricLabel(
  metricName: string,
  catalogByName?: Record<string, { display_name: string }>,
): string {
  const catalogEntry = catalogByName?.[metricName];
  if (catalogEntry?.display_name) return catalogEntry.display_name;
  return METRIC_LABELS[metricName] ?? metricName;
}
