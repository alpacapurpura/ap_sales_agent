'use client';

import { useState, useCallback } from 'react';
import { RefreshCw } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import type { ChannelMetric, MetricValue } from '../../../types/metrics';
import { ConnectionBadge } from './ConnectionBadge';
import { CostLink } from './CostLink';

const CHANNEL_ICONS: Record<string, string> = {
  'ig-organic': '\uD83D\uDCF8',
  'yt-organic': '\u25B6\uFE0F',
  'fb-organic': '\uD83D\uDC64',
  'tiktok-organic': '\uD83C\uDFB5',
  'linkedin-organic': '\uD83D\uDCBC',
  'google-organic': '\uD83D\uDD0D',
  'direct': '\uD83D\uDD17',
  'ai-search-organic': '\uD83E\uDD16',
  'meta-ads': '\uD83D\uDCE2',
  'google-ads': '\uD83C\uDFAF',
  'tiktok-ads': '\uD83C\uDFB5',
  'yt-ads': '\u25B6\uFE0F',
  'cold-contact': '\uD83D\uDCDE',
  'landing-form': '\uD83D\uDCC4',
  'mailerlite': '\uD83D\uDCE7',
  'ig-dm': '\uD83D\uDCF8',
  'fb-messenger': '\uD83D\uDCAC',
  'tiktok-dm': '\uD83C\uDFB5',
  'whatsapp-inbound': '\uD83D\uDCF1',
};

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

function MetricDisplay({ metric }: { metric: MetricValue }) {
  const label = METRIC_LABELS[metric.name] ?? metric.name;
  const isCurrency = metric.unit === 'currency';
  const formatted = isCurrency
    ? formatCurrency(metric.value, metric.currency)
    : formatNumber(metric.value);

  return (
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
}

interface ChannelRowProps {
  channel: ChannelMetric;
}

export function ChannelRow({ channel }: ChannelRowProps) {
  const [refreshing, setRefreshing] = useState(false);
  const [cooldown, setCooldown] = useState(false);

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
    return (
      <div className="flex items-center justify-between py-2 px-3 rounded-md hover:bg-muted/50 transition-colors">
        <div className="flex items-center gap-3 min-w-0">
          <span className="text-lg shrink-0">{CHANNEL_ICONS[channel.slug] ?? '\uD83D\uDCCA'}</span>
          <p className="text-sm font-medium truncate">{channel.name}</p>
        </div>
        <ConnectionBadge connected={false} />
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

  return (
    <div className="flex items-center justify-between py-2 px-3 rounded-md hover:bg-muted/50 transition-colors">
      <div className="flex items-center gap-3 min-w-0">
        <span className="text-lg shrink-0">{CHANNEL_ICONS[channel.slug] ?? '\uD83D\uDCCA'}</span>
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-sm font-medium truncate">{channel.name}</p>
            {channel.stale && (
              <Badge variant="outline" className="border-yellow-500/50 text-yellow-600 dark:text-yellow-400 text-[10px] py-0">
                Desactualizado
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

      <div className="flex items-center gap-3 shrink-0">
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
              return (
                <div key={m.name} className="flex flex-col items-end min-w-[60px]">
                  <span className="text-[10px] text-muted-foreground uppercase tracking-wide">
                    {METRIC_LABELS[m.name] ?? m.name}
                  </span>
                  <span className="text-sm font-semibold tabular-nums">{formatNumber(m.value)}</span>
                  <span className="text-[10px] text-muted-foreground">
                    de {conversationsMetric.value.toLocaleString('es-ES')} conversaciones
                  </span>
                </div>
              );
            }

            return <MetricDisplay key={m.name} metric={m} />;
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
}
