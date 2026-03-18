'use client';

import { useState, useCallback } from 'react';
import { RefreshCw } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import type { ChannelMetric, CampaignMetric, MetricValue, MetricClickData, StageId } from '../../../types/metrics';
import { ConnectionBadge } from './ConnectionBadge';
import { CostLink } from './CostLink';
import { CampaignDrillDown } from './CampaignDrillDown';
import { getChannelIcon, getChannelColor } from '../../../lib/channelIcons';
import { getConnectionView } from '../../../lib/channelViewMap';

/** Metric name -> Spanish label mapping. */
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

interface MetricDisplayProps {
  metric: MetricValue;
  channelSlug?: string;
  stageId?: StageId;
  onMetricClick?: (metric: MetricClickData) => void;
}

function MetricDisplay({ metric, channelSlug, stageId, onMetricClick }: MetricDisplayProps) {
  const label = METRIC_LABELS[metric.name] ?? metric.name;
  const isCurrency = metric.unit === 'currency';
  const formatted = isCurrency
    ? formatCurrency(metric.value, metric.currency)
    : formatNumber(metric.value);

  const canClick = onMetricClick && channelSlug && stageId;

  const content = (
    <div className="flex flex-col items-end min-w-[60px]">
      <span className="text-[10px] text-muted-foreground uppercase tracking-wide">{label}</span>
      <span className="text-sm font-semibold tabular-nums">{formatted}</span>
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
        className="cursor-pointer hover:bg-primary/5 px-1.5 py-1 rounded transition-colors duration-100 focus:outline-none focus:ring-2 focus:ring-primary/20"
        title={`Ver detalle: ${label}`}
      >
        {content}
      </button>
    );
  }

  return content;
}

interface ChannelRowProps {
  channel: ChannelMetric;
  /** Stage context — used for MetricClickData when onMetricClick is provided */
  stageId?: StageId;
  /** Callback when user clicks a metric value to open drill-down sidebar */
  onMetricClick?: (metric: MetricClickData) => void;
  /** Callback when user clicks "Configurar" on an unconnected channel */
  onConfigure?: (slug: string, name: string) => void;
}

export function ChannelRow({ channel, stageId, onMetricClick, onConfigure }: ChannelRowProps) {
  const [refreshing, setRefreshing] = useState(false);
  const [cooldown, setCooldown] = useState(false);

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
    } catch {
      // Silently handle network errors for refresh
    } finally {
      setRefreshing(false);
    }
  }, [channel.slug, refreshing, cooldown]);

  // Available (unconnected) channels: only show name + Configurar badge
  if (!channel.connected) {
    const hasView = getConnectionView(channel.slug) !== null;
    return (
      <div className="flex items-center justify-between py-2 px-3 rounded-md hover:bg-muted/50 transition-colors duration-100">
        <div className="flex items-center gap-3 min-w-0">
          <Icon className="w-5 h-5 flex-shrink-0" style={{ color: iconColor }} aria-hidden="true" />
          <p className="text-sm font-medium truncate">{channel.name}</p>
        </div>
        <ConnectionBadge
          connected={false}
          onConfigure={hasView && onConfigure ? () => onConfigure(channel.slug, channel.name) : undefined}
          comingSoon={!hasView}
        />
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
      <div className="flex items-center justify-between py-2 px-3 rounded-md hover:bg-muted/50 transition-colors duration-100">
        <div className="flex items-center gap-3 min-w-0">
          <Icon className="w-5 h-5 flex-shrink-0" style={{ color: iconColor }} aria-hidden="true" />
          <div className="min-w-0">
            <p className="text-sm font-medium truncate">{channel.name}</p>
            <p className="text-xs text-muted-foreground truncate">{channel.sourceLabel}</p>
          </div>
        </div>
        <Badge variant="secondary">Proximamente</Badge>
      </div>
    );
  }

  // Check for leads metric with zero value
  const leadsMetric = channel.metrics.find(m => m.name === 'leads');
  const hasZeroLeads = leadsMetric !== undefined && leadsMetric.value === 0;
  const hasNoData = channel.metrics.length === 0 || channel.metrics.every(m => m.value === 0);

  // Find conversations metric for AI Agent secondary line
  const conversationsMetric = channel.metrics.find(m => m.name === 'conversations');

  // Render metrics, excluding conversations (shown as secondary line) and handling CostLink
  const displayMetrics = channel.metrics.filter(m => m.name !== 'conversations');

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
    <div className="flex items-center justify-between py-2 px-3 rounded-md hover:bg-primary/5 transition-all duration-100 ease-out group">
      <div className="flex items-center gap-3 min-w-0">
        {/* Brand icon replacing emoji placeholder */}
        <Icon
          className="w-5 h-5 flex-shrink-0 transition-transform duration-100 group-hover:scale-110"
          style={{ color: iconColor }}
          aria-hidden="true"
        />
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-sm font-medium truncate">{channel.name}</p>
            {channel.stale && (
              <Badge variant="outline" className="border-yellow-500/50 text-yellow-600 dark:text-yellow-400 text-[10px] py-0">
                Desactualizado
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
          <p className="text-xs text-muted-foreground truncate">{channel.sourceLabel}</p>
          {channel.stale && channel.lastUpdated && (
            <p className="text-[10px] text-yellow-600 dark:text-yellow-400">
              Ultima vez: {new Date(channel.lastUpdated).toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })}
            </p>
          )}
        </div>
      </div>

      {/* Metrics area — responsive: flex-col on mobile, flex-row on sm+ */}
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
              const leadsContent = (
                <div className="flex flex-col items-end min-w-[60px]">
                  <span className="text-[10px] text-muted-foreground uppercase tracking-wide">
                    {METRIC_LABELS[m.name] ?? m.name}
                  </span>
                  <span className="text-sm font-semibold tabular-nums">{formatNumber(m.value)}</span>
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
                    className="cursor-pointer hover:bg-primary/5 px-1.5 py-1 rounded transition-colors duration-100 focus:outline-none focus:ring-2 focus:ring-primary/20"
                    title={`Ver detalle: ${METRIC_LABELS[m.name] ?? m.name}`}
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
}
