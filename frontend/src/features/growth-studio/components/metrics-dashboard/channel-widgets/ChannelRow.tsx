'use client';

import * as Sentry from "@sentry/nextjs";
import React, { useState, useCallback } from 'react';
import { RefreshCw } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { ChannelMetric, CampaignMetric, MetricValue, MetricClickData, StageId } from '../../../types/metrics';
import { ConnectionBadge } from './ConnectionBadge';
import { CostLink } from './CostLink';
import { CampaignDrillDown } from './CampaignDrillDown';
import { getChannelIcon, getChannelColor } from '../../../lib/channelIcons';
import { useMetricCatalog } from '../../../hooks/useMetricCatalog';

/** Fallback metric name -> Spanish label (used when catalog entry is unavailable). */
const METRIC_LABELS: Record<string, string> = {
  reach: 'Alcance',
  engagement: 'Engagement',
  sessions: 'Sesiones',
  users: 'Usuarios',
  clicks: 'Clicks',
  conversions: 'Conversiones',
  spend: 'Gasto',
  contacts: 'Contactos',
  responses: 'Respuestas',
  leads: 'Leads',
  cost: 'Costo',
  conversion_rate: 'Conversion',
  conversations: 'Conversaciones',
  emails_sent: 'Enviados',
  open_rate: 'Apertura',
  click_rate: 'Clicks',
  followups: 'Follow-ups',
  response_rate: 'Respuestas',
  campaigns: 'Campanas',
  count: 'Cantidad',
  value: 'Valor',
  abandonment_rate: 'Abandono',
  booked: 'Agendadas',
  completed: 'Completadas',
  no_show: 'No-Show',
  rescheduled: 'Reprogramadas',
  attendance_rate: 'Asistencia',
  impressions: 'Impresiones',
  visitors: 'Visitantes',
  new_subscribers: 'Nuevos Suscriptores',
  comment_triggers: 'Comment Triggers',
  dm_opens: 'DMs Abiertos',
  sequences_sent: 'Secuencias Enviadas',
  qualified_leads: 'Leads Calificados',
  meetings_requested: 'Reuniones Solicitadas',
  bofu_flows_triggered: 'Flows BOFU',
  consultations: 'Consultas',
  link_clicks: 'Links Clickeados',
  tag_applied: 'Tags Aplicados',
  flows_triggered: 'Flows Activados',
  unique_opens: 'Aperturas',
  click_to_open_rate: 'CTOR',
  unsubscribe_rate: 'Tasa Desuscripción',
  bounce_rate: 'Tasa Rebote',
  form_conversions: 'Conversiones Form',
  form_conversion_rate: 'Tasa Conversión',
  completion_rate: 'Tasa Completadas',
  reactivation_rate: 'Tasa Reactivación',
  active_subscribers: 'Suscriptores Activos',
  forwards: 'Reenvíos',
  hard_bounces: 'Rebotes Duros',
  soft_bounces: 'Rebotes Suaves',
  spam_reports: 'Spam',
  unique_clicks: 'Clicks Únicos',
  automation_completed: 'Automatizaciones',
  unsubscribes: 'Desuscripciones',
  // Instagram Organic
  ig_views: 'Vistas',
  total_interactions: 'Interacciones',
  ig_likes: 'Likes',
  ig_comments: 'Comentarios',
  ig_shares: 'Compartidos',
  ig_saves: 'Guardados',
  ig_replies: 'Respuestas Stories',
  ig_reposts: 'Reposts',
  ig_accounts_engaged: 'Cuentas Engaged',
  ig_follows_and_unfollows: 'Seguidores Netos',
  ig_profile_links_taps: 'Taps Perfil',
  ig_followers_count: 'Seguidores',
  ig_media_count: 'Publicaciones',
  ig_follower_demographics: 'Demografía',
  ig_engaged_audience_demographics: 'Demografía Engaged',
  // Meta Ads Expanded
  meta_inline_link_clicks: 'Clics al Destino',
  meta_outbound_clicks: 'Clics Salientes',
  meta_landing_page_views: 'Vistas de Landing',
  meta_cost_per_link_click: 'Costo por Clic al Destino',
  meta_cost_per_outbound_click: 'Costo por Clic Saliente',
  meta_leads: 'Leads',
  meta_add_to_cart: 'Agregar al Carrito',
  meta_initiate_checkout: 'Checkouts Iniciados',
  meta_registrations: 'Registros',
  meta_view_content: 'Vistas de Contenido',
  meta_search_actions: 'Búsquedas',
  meta_conversations_started: 'Conversaciones',
  meta_link_clicks: 'Link Clicks',
  meta_page_engagement: 'Engagement de Página',
  meta_video_views: 'Reproducciones de Video',
  meta_conversion_value: 'Valor de Conversiones',
  meta_purchase_roas: 'ROAS',
  meta_cost_per_purchase: 'Costo por Compra',
  meta_cost_per_lead: 'Costo por Lead',
  meta_cpp: 'CPP',
  meta_post_engagement: 'Engagement de Post',
  meta_video_p25: 'Video 25%',
  meta_video_p50: 'Video 50%',
  meta_video_p75: 'Video 75%',
  meta_video_p100: 'Video 100%',
  meta_video_30sec: 'Video 30s+',
  meta_video_avg_watch_time: 'Duración Promedio',
  // Meta Ads Breakdowns
  meta_reach_by_age: 'Alcance por Edad',
  meta_spend_by_age: 'Gasto por Edad',
  meta_impressions_by_age: 'Impresiones por Edad',
  meta_reach_by_gender: 'Alcance por Género',
  meta_spend_by_gender: 'Gasto por Género',
  meta_impressions_by_gender: 'Impresiones por Género',
  meta_reach_by_placement: 'Alcance por Plataforma',
  meta_spend_by_placement: 'Gasto por Plataforma',
  meta_impressions_by_placement: 'Impresiones por Plataforma',
};

/** Breakdown key -> Spanish label. */
const BREAKDOWN_LABELS: Record<string, string> = {
  likes: 'likes',
  comments: 'comentarios',
  shares: 'compartidos',
  saves: 'guardados',
  reactions: 'reacciones',
};

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}k`;
  return n.toLocaleString();
}

function formatCurrency(n: number, currency?: string): string {
  const symbol = currency === 'USD' || !currency ? '$' : currency;
  return `${symbol}${n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatBreakdown(breakdown: Record<string, number>): string {
  return Object.entries(breakdown)
    .filter(([, v]) => v > 0)
    .map(([key, val]) => `${BREAKDOWN_LABELS[key] ?? key} ${formatNumber(val)}`)
    .join(', ');
}

/** Convert hex color to rgba for backgrounds. */
function hexToRgba(hex: string, alpha: number): string {
  if (hex.startsWith('hsl')) return hex; // fallback, keep as-is
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

/* ── MetricDisplay ────────────────────────────────────────────────────── */

interface MetricDisplayProps {
  metric: MetricValue;
  channelSlug?: string;
  stageId?: StageId;
  onMetricClick?: (metric: MetricClickData) => void;
  catalogByName?: Record<string, { display_name: string; interpretation: string; formula?: string }>;
}

function MetricDisplay({ metric, channelSlug, stageId, onMetricClick, catalogByName }: MetricDisplayProps) {
  const catalogEntry = catalogByName?.[metric.name];
  const label = catalogEntry?.display_name ?? METRIC_LABELS[metric.name] ?? metric.name;
  const isCurrency = metric.unit === 'currency';
  const formatted = isCurrency
    ? formatCurrency(metric.value, metric.currency)
    : formatNumber(metric.value);

  const canClick = onMetricClick && channelSlug && stageId;

  const tooltipText = catalogEntry?.interpretation
    ? `${label}${catalogEntry.formula ? ` (${catalogEntry.formula})` : ''}: ${catalogEntry.interpretation}`
    : `Ver detalle: ${label}`;

  const content = (
    <div className="flex flex-col items-end min-w-[52px]">
      <span className="text-[10px] text-muted-foreground uppercase tracking-wide leading-tight">{label}</span>
      <span className="text-sm font-semibold tabular-nums leading-tight">{formatted}</span>
      {metric.breakdown && Object.keys(metric.breakdown).length > 0 && (
        <span className="text-[10px] text-muted-foreground truncate max-w-[180px]">
          {formatBreakdown(metric.breakdown)}
        </span>
      )}
    </div>
  );

  if (canClick) {
    return (
      <button
        onClick={() => onMetricClick({
          stageId,
          channelSlug,
          metricName: metric.name,
          currentValue: metric.value,
          currency: metric.currency,
        })}
        className="cursor-pointer hover:bg-primary/5 px-1.5 py-1 rounded-md transition-colors duration-100 focus:outline-none focus:ring-2 focus:ring-primary/20"
        title={tooltipText}
      >
        {content}
      </button>
    );
  }

  return <div title={tooltipText}>{content}</div>;
}

/* ── ChannelRow ────────────────────────────────────────────────────────── */

export interface ChannelRowProps {
  channel: ChannelMetric;
  /** Stage context — used for MetricClickData when onMetricClick is provided */
  stageId?: StageId;
  /** Callback when user clicks a metric value to open drill-down sidebar */
  onMetricClick?: (metric: MetricClickData) => void;
  /** Callback when the entire connected channel row is clicked */
  onChannelClick?: (channel: ChannelMetric) => void;
  /** Callback when user clicks "Configurar" on an unconnected channel */
  onConfigure?: (slug: string, name: string) => void;
}

export const ChannelRow = React.memo(function ChannelRow({ channel, stageId, onMetricClick, onChannelClick, onConfigure }: ChannelRowProps) {
  const [refreshing, setRefreshing] = useState(false);
  const [cooldown, setCooldown] = useState(false);
  const { catalogByName } = useMetricCatalog();

  const Icon = getChannelIcon(channel.slug);
  const iconColor = getChannelColor(channel.slug);

  const handleRefresh = useCallback(async () => {
    if (refreshing || cooldown) return;
    setRefreshing(true);
    try {
      const res = await fetch(`/api/v1/analytics/metrics/attraction/refresh/${channel.slug}`, {
        method: 'POST',
      });
      if (res.status === 429) {
        setCooldown(true);
        setTimeout(() => setCooldown(false), 60_000);
      }
    } catch (err) {
      Sentry.captureException(err, { tags: { channel: channel.slug, action: "etl_refresh" } });
    } finally {
      setRefreshing(false);
    }
  }, [channel.slug, refreshing, cooldown]);

  // Available (unconnected) channels: show name + Configurar badge
  if (!channel.connected) {
    return (
      <div className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-muted/40 transition-colors duration-100 opacity-60 hover:opacity-80">
        <div className="flex items-center gap-3 min-w-0">
          <div
            className="flex items-center justify-center w-8 h-8 rounded-lg shrink-0"
            style={{ backgroundColor: hexToRgba(iconColor, 0.1) }}
          >
            <Icon className="w-4 h-4" style={{ color: iconColor }} aria-hidden="true" />
          </div>
          <p className="text-sm font-medium truncate">{channel.name}</p>
        </div>
        <ConnectionBadge connected={false} onConfigure={onConfigure ? () => onConfigure(channel.slug, channel.name) : undefined} />
      </div>
    );
  }

  // AI SDR / checkout-lp / link-enviado with no data: show "Proximamente" badge
  const isProximamente =
    (channel.slug === 'ai-sdr' && (channel.metrics.length === 0 || channel.metrics.every(m => m.value === 0))) ||
    channel.slug === 'checkout-lp' ||
    (channel.slug === 'link-enviado' && channel.metrics.length === 0);
  if (isProximamente) {
    return (
      <div className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-muted/40 transition-colors duration-100">
        <div className="flex items-center gap-3 min-w-0">
          <div
            className="flex items-center justify-center w-8 h-8 rounded-lg shrink-0"
            style={{ backgroundColor: hexToRgba(iconColor, 0.1) }}
          >
            <Icon className="w-4 h-4" style={{ color: iconColor }} aria-hidden="true" />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium truncate">{channel.name}</p>
            <p className="text-xs text-muted-foreground truncate">{channel.sourceLabel}</p>
          </div>
        </div>
        <Badge variant="secondary" className="text-[11px]">Proximamente</Badge>
      </div>
    );
  }

  // Check for leads metric with zero value
  const leadsMetric = channel.metrics.find(m => m.name === 'leads');
  const hasZeroLeads = leadsMetric !== undefined && leadsMetric.value === 0;
  const hasNoData = channel.metrics.length === 0 || channel.metrics.every(m => m.value === 0);

  // Find conversations metric for AI Agent secondary line
  const conversationsMetric = channel.metrics.find(m => m.name === 'conversations');

  // Summary metrics for channels with many metrics — only show top 3 in the row
  const CHANNEL_ROW_SUMMARY_METRICS: Record<string, string[]> = {
    'ig-organic': ['reach', 'total_interactions', 'ig_followers_count'],
    'yt-organic': ['views', 'engagement', 'subscribers_gained'],
    'meta-ads': ['reach', 'spend', 'meta_purchase_roas'],
  };

  // Render metrics, excluding conversations (shown as secondary line) and handling CostLink
  const summaryFilter = CHANNEL_ROW_SUMMARY_METRICS[channel.slug];
  const displayMetrics = channel.metrics
    .filter(m => m.name !== 'conversations')
    .filter(m => !summaryFilter || summaryFilter.includes(m.name));

  // Inline bottleneck badge for abandoned-cart
  const abandonmentMetric = channel.slug === 'abandoned-cart'
    ? channel.metrics.find(m => m.name === 'abandonment_rate')
    : undefined;
  const abandonmentBadge = abandonmentMetric && abandonmentMetric.value > 50
    ? 'critical'
    : abandonmentMetric && abandonmentMetric.value > 30
      ? 'warning'
      : null;

  // Inline bottleneck badge for meeting-booked no-show rate
  const bookedMetric = channel.slug === 'meeting-booked'
    ? channel.metrics.find(m => m.name === 'booked')
    : undefined;
  const noShowMetric = channel.slug === 'meeting-booked'
    ? channel.metrics.find(m => m.name === 'no_show')
    : undefined;
  const noShowRate = bookedMetric && bookedMetric.value > 0 && noShowMetric
    ? noShowMetric.value / bookedMetric.value
    : 0;
  const noShowBadge = noShowRate > 0.40
    ? 'critical'
    : noShowRate > 0.20
      ? 'warning'
      : null;

  // Determine if this channel should be wrapped with CampaignDrillDown
  const shouldWrapWithDrillDown = channel.channelType === 'retargeting' || channel.channelType === 'email';
  const campaigns: CampaignMetric[] = (channel as unknown as Record<string, unknown>).campaigns as CampaignMetric[] ?? [];

  const rowContent = (
    <div
      className={cn(
        "flex items-center justify-between py-2.5 px-3 rounded-lg hover:bg-primary/5 transition-all duration-100 ease-out group",
        onChannelClick && "cursor-pointer"
      )}
      onClick={onChannelClick ? () => onChannelClick(channel) : undefined}
    >
      {/* Left: icon + name + status */}
      <div className="flex items-center gap-3 min-w-0">
        <div
          className={cn(
            'flex items-center justify-center w-8 h-8 rounded-lg shrink-0 transition-transform duration-100 group-hover:scale-105',
          )}
          style={{ backgroundColor: hexToRgba(iconColor, 0.12) }}
        >
          <Icon
            className="w-4 h-4"
            style={{ color: iconColor }}
            aria-hidden="true"
          />
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-sm font-medium truncate">{channel.name}</p>
            {/* Connected dot */}
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" title="Conectado" />
            {channel.stale && (
              <Badge variant="outline" className="border-yellow-500/50 text-yellow-600 dark:text-yellow-400 text-[10px] py-0">
                Desactualizado
              </Badge>
            )}
            {!channel.stale && channel.errorMessage?.startsWith('Parcial') && (
              <Badge variant="outline" className="border-orange-500/50 text-orange-600 dark:text-orange-400 text-[10px] py-0" title={channel.errorMessage}>
                Parcial
              </Badge>
            )}
            {abandonmentBadge === 'warning' && (
              <Badge variant="outline" className="border-yellow-500/50 text-yellow-600 dark:text-yellow-400 text-[10px] py-0">
                Alerta
              </Badge>
            )}
            {abandonmentBadge === 'critical' && (
              <Badge variant="outline" className="border-red-500/50 text-red-600 dark:text-red-400 text-[10px] py-0">
                Critico
              </Badge>
            )}
            {noShowBadge === 'warning' && (
              <Badge variant="outline" className="border-yellow-500/50 text-yellow-600 dark:text-yellow-400 text-[10px] py-0">
                Alerta
              </Badge>
            )}
            {noShowBadge === 'critical' && (
              <Badge variant="outline" className="border-red-500/50 text-red-600 dark:text-red-400 text-[10px] py-0">
                Critico
              </Badge>
            )}
          </div>
          <p className="text-[11px] text-muted-foreground truncate">
            {channel.sourceDisplayName
              ? `${channel.sourceLabel} · ${channel.sourceDisplayName}`
              : channel.sourceLabel}
          </p>
          {channel.stale && channel.lastUpdated && (
            <p className="text-[10px] text-yellow-600 dark:text-yellow-400">
              Ultima vez: {new Date(channel.lastUpdated).toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })}
            </p>
          )}
        </div>
      </div>

      {/* Right: metrics area */}
      <div className="flex flex-row items-center gap-2 sm:gap-3 shrink-0 flex-wrap justify-end">
        {hasNoData && !hasZeroLeads ? (
          <div className="flex flex-col items-end">
            <span className="text-sm font-semibold text-muted-foreground">---</span>
            <span className="text-[10px] text-muted-foreground">Sin datos</span>
          </div>
        ) : hasZeroLeads ? (
          <div className="flex flex-col items-end">
            <span className="text-sm font-semibold text-muted-foreground">0 leads</span>
            <span className="text-[10px] text-muted-foreground">Sin actividad en los ultimos 30 dias</span>
          </div>
        ) : (
          displayMetrics.map((m) => {
            // CostLink for unconfigured costs (value is 0/null and channel is connected)
            if (m.name === 'cost' && m.unit === 'currency' && m.value === 0 && channel.connected) {
              return <CostLink key={m.name} />;
            }

            // Leads metric with conversations secondary line
            if (m.name === 'leads' && conversationsMetric) {
              const canClick = onMetricClick && stageId;
              const leadsLabel = catalogByName[m.name]?.display_name ?? METRIC_LABELS[m.name] ?? m.name;
              const leadsContent = (
                <div className="flex flex-col items-end min-w-[52px]">
                  <span className="text-[10px] text-muted-foreground uppercase tracking-wide leading-tight">
                    {leadsLabel}
                  </span>
                  <span className="text-sm font-semibold tabular-nums leading-tight">{formatNumber(m.value)}</span>
                  <span className="text-[10px] text-muted-foreground">
                    de {conversationsMetric.value.toLocaleString('es-ES')} conversaciones
                  </span>
                </div>
              );
              if (canClick) {
                return (
                  <button
                    key={m.name}
                    onClick={() => onMetricClick({
                      stageId,
                      channelSlug: channel.slug,
                      metricName: m.name,
                      currentValue: m.value,
                    })}
                    className="cursor-pointer hover:bg-primary/5 px-1.5 py-1 rounded-md transition-colors duration-100 focus:outline-none focus:ring-2 focus:ring-primary/20"
                    title={`Ver detalle: ${leadsLabel}`}
                  >
                    {leadsContent}
                  </button>
                );
              }
              return <div key={m.name}>{leadsContent}</div>;
            }

            return (
              <MetricDisplay
                key={m.name}
                metric={m}
                channelSlug={channel.slug}
                stageId={stageId}
                onMetricClick={onMetricClick}
                catalogByName={catalogByName}
              />
            );
          })
        )}
        {channel.stale && (
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={handleRefresh}
            disabled={refreshing || cooldown}
            title={cooldown ? 'Disponible en unos minutos' : 'Actualizar datos'}
          >
            <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          </Button>
        )}
      </div>
    </div>
  );

  if (shouldWrapWithDrillDown) {
    return (
      <CampaignDrillDown campaigns={campaigns}>
        {rowContent}
      </CampaignDrillDown>
    );
  }

  return rowContent;
});
