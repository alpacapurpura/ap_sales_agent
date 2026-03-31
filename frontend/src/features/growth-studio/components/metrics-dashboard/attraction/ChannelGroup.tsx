'use client';

import React from 'react';
import { ChevronRight, BarChart3, Crosshair } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { ChannelMetric, MetricValue } from '../../../types/metrics';
import { getChannelIcon, getChannelColor } from '../../../lib/channelIcons';

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatNum(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}k`;
  return n.toLocaleString('es-ES');
}

function formatMoney(n: number): string {
  return `$${n.toLocaleString('es-ES', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}

function hexToRgba(hex: string, alpha: number): string {
  if (hex.startsWith('hsl')) return hex;
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

function getMetricValue(metrics: MetricValue[], name: string): number {
  return metrics.find((m) => m.name === name)?.value ?? 0;
}

// ─── Types ───────────────────────────────────────────────────────────────────

export type ChannelGroupVariant = 'paid' | 'organic' | 'outbound' | 'capture_web' | 'capture_messaging';

interface ChannelGroupProps {
  title: string;
  variant: ChannelGroupVariant;
  channels: ChannelMetric[];
  /** Max primary value across ALL groups (for proportional bars) */
  maxPrimary: number;
  /** Summary text for the header right side */
  summary?: string;
  /** Additional summary element (e.g., spend total) */
  summaryExtra?: string;
  /** Total leads for share computation (capture groups) */
  totalLeads?: number;
  onChannelClick?: (channel: ChannelMetric) => void;
  onConfigure?: (slug: string, name: string) => void;
}

// ─── Secondary metric extraction per variant ─────────────────────────────────

function getSecondaryMetrics(
  channel: ChannelMetric,
  variant: ChannelGroupVariant,
): { secondary1: string; secondary2: string } {
  const metrics = channel.metrics;

  switch (variant) {
    case 'paid': {
      const spend = getMetricValue(metrics, 'spend');
      const costType = channel.costType ?? 'CPM';
      let efficiency = '';
      if (costType === 'CPC') {
        const clicks = getMetricValue(metrics, 'clicks');
        efficiency = clicks > 0 ? `CPC ${formatMoney(spend / clicks)}` : '';
      } else if (costType === 'CPV') {
        const views = getMetricValue(metrics, 'reach');
        efficiency = views > 0 ? `CPV ${formatMoney(spend / views)}` : '';
      } else {
        const reach = getMetricValue(metrics, 'reach') || getMetricValue(metrics, 'impressions');
        efficiency = reach > 0 ? `CPM ${formatMoney((spend / reach) * 1000)}` : '';
      }
      return { secondary1: formatMoney(spend), secondary2: efficiency };
    }
    case 'organic': {
      const engagement = getMetricValue(metrics, 'engagement');
      const reach = getMetricValue(metrics, 'reach');
      const sessions = getMetricValue(metrics, 'sessions');
      // GA4-type channels show sessions + bounce rate
      if (sessions > 0 && reach === 0) {
        const bounce = getMetricValue(metrics, 'bounceRate') || getMetricValue(metrics, 'bounce_rate');
        return {
          secondary1: `${formatNum(sessions)} sessions`,
          secondary2: bounce > 0 ? `bounce ${bounce.toFixed(0)}%` : '',
        };
      }
      // Social channels show engagement + rate
      const rate = reach > 0 ? (engagement / reach) * 100 : 0;
      return {
        secondary1: engagement > 0 ? `eng ${formatNum(engagement)}` : '',
        secondary2: rate > 0 ? `rate ${rate.toFixed(1)}%` : '',
      };
    }
    case 'outbound': {
      const contacts = getMetricValue(metrics, 'contacts') || getMetricValue(metrics, 'comment_triggers') || getMetricValue(metrics, 'flows_triggered');
      const responses = getMetricValue(metrics, 'responses') || getMetricValue(metrics, 'dm_opens');
      const rate = contacts > 0 ? (responses / contacts) * 100 : 0;
      return {
        secondary1: responses > 0 ? `${formatNum(responses)} resp` : '',
        secondary2: rate > 0 ? `${rate.toFixed(0)}%` : '',
      };
    }
    case 'capture_web':
    case 'capture_messaging': {
      return { secondary1: '', secondary2: '' };
    }
  }
}

function getPrimaryValue(channel: ChannelMetric, variant: ChannelGroupVariant): number {
  const metrics = channel.metrics;
  switch (variant) {
    case 'paid':
      return getMetricValue(metrics, 'reach') || getMetricValue(metrics, 'impressions') || getMetricValue(metrics, 'sessions');
    case 'organic':
      return getMetricValue(metrics, 'reach') || getMetricValue(metrics, 'sessions');
    case 'outbound':
      return getMetricValue(metrics, 'contacts') || getMetricValue(metrics, 'comment_triggers') || getMetricValue(metrics, 'flows_triggered');
    case 'capture_web':
    case 'capture_messaging':
      return getMetricValue(metrics, 'leads');
  }
}

// ─── Channel icon wrapper (avoids creating components during render) ─────────

/* eslint-disable react-hooks/static-components -- dynamic icon from registry */
function ChannelIconBadge({ slug, className, style }: { slug: string; className?: string; style?: React.CSSProperties }) {
  const Icon = getChannelIcon(slug);
  return <Icon className={className} style={style} />;
}
/* eslint-enable react-hooks/static-components */

// ─── Component ───────────────────────────────────────────────────────────────

export function ChannelGroup({
  title,
  variant,
  channels,
  maxPrimary,
  summary,
  summaryExtra,
  totalLeads,
  onChannelClick,
  onConfigure,
}: ChannelGroupProps) {
  const isCapture = variant === 'capture_web' || variant === 'capture_messaging';

  return (
    <div className="bg-card border border-border rounded-lg overflow-hidden">
      {/* Header */}
      <div className="bg-muted/50 px-4 py-2.5 flex justify-between items-center border-b border-border">
        <span className="text-sm font-medium text-foreground/90">{title}</span>
        <div className="flex gap-4 text-xs">
          {summary && <span className="text-muted-foreground">{summary}</span>}
          {summaryExtra && <span className="text-emerald-600 dark:text-emerald-400 font-semibold">{summaryExtra}</span>}
        </div>
      </div>

      {/* Channel rows */}
      <div className="divide-y divide-border/50">
        {channels.map((channel) => {
          // Website expanded row
          if (channel.channelType === 'website') {
            return (
              <WebsiteExpandedRow
                key={channel.slug}
                channel={channel}
                onClick={onChannelClick ? () => onChannelClick(channel) : undefined}
              />
            );
          }

          if (!channel.connected) {
            return (
              <UnconnectedRow
                key={channel.slug}
                channel={channel}
                onConfigure={onConfigure}
              />
            );
          }

          const primary = getPrimaryValue(channel, variant);
          const hasData = channel.metrics.length > 0 && channel.metrics.some((m) => m.value > 0);
          const { secondary1, secondary2 } = getSecondaryMetrics(channel, variant);
          const barPct = maxPrimary > 0 ? (primary / maxPrimary) * 100 : 0;
          const shareOfLeads = isCapture && totalLeads && totalLeads > 0
            ? ((primary / totalLeads) * 100).toFixed(1)
            : null;

          return (
            <ChannelRowInner
              key={channel.slug}
              channel={channel}
              primary={primary}
              barPct={barPct}
              secondary1={secondary1}
              secondary2={isCapture && shareOfLeads ? `${shareOfLeads}% share` : secondary2}
              hasData={hasData}
              onClick={onChannelClick ? () => onChannelClick(channel) : undefined}
            />
          );
        })}
      </div>
    </div>
  );
}

// ─── Row sub-components ──────────────────────────────────────────────────────

function ChannelRowInner({
  channel,
  primary,
  barPct,
  secondary1,
  secondary2,
  hasData,
  onClick,
}: {
  channel: ChannelMetric;
  primary: number;
  barPct: number;
  secondary1: string;
  secondary2: string;
  hasData: boolean;
  onClick?: () => void;
}) {
  const iconColor = getChannelColor(channel.slug);

  return (
    <div
      className={cn(
        'flex items-center justify-between px-4 py-2.5 hover:bg-muted/30 transition-colors group',
        onClick && 'cursor-pointer',
      )}
      onClick={onClick}
    >
      {/* Left: icon + name + status */}
      <div className="flex items-center gap-3 min-w-0 shrink-0">
        <div
          className="flex items-center justify-center w-8 h-8 rounded-lg shrink-0 transition-transform duration-100 group-hover:scale-105"
          style={{ backgroundColor: hexToRgba(iconColor, 0.12) }}
        >
          <ChannelIconBadge slug={channel.slug} className="w-4 h-4" style={{ color: iconColor }} />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-medium truncate">{channel.name}</p>
          <div className="flex items-center gap-1.5">
            <span
              className={cn(
                'w-1.5 h-1.5 rounded-full shrink-0',
                hasData ? 'bg-emerald-400' : 'bg-amber-400',
              )}
            />
            <span className="text-[10px] text-muted-foreground truncate">
              {channel.subSources && channel.subSources.length > 1
                ? channel.subSources.map((s) => s.name).join(' + ')
                : channel.sourceDisplayName
                  ? `${channel.sourceLabel} · ${channel.sourceDisplayName}`
                  : channel.sourceLabel}
            </span>
            {channel.stale && (
              <Badge variant="outline" className="border-yellow-500/50 text-yellow-600 dark:text-yellow-400 text-[10px] py-0 h-4">
                Desactualizado
              </Badge>
            )}
            {channel.errorMessage && (
              <Badge variant="outline" className="border-red-500/50 text-red-600 dark:text-red-400 text-[10px] py-0 h-4">
                Error
              </Badge>
            )}
          </div>
        </div>
      </div>

      {/* Right: bar + metrics + chevron */}
      <div className="flex items-center gap-4 shrink-0">
        {/* Proportional bar + value */}
        <div className="hidden sm:flex w-28 items-center gap-2">
          <div className="flex-1 bg-muted rounded-full h-2 overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${Math.max(barPct, 1)}%`,
                backgroundColor: iconColor,
                opacity: hasData ? 0.7 : 0.2,
              }}
            />
          </div>
          <span className={cn(
            'text-sm font-semibold tabular-nums w-12 text-right',
            !hasData && 'text-muted-foreground',
          )}>
            {hasData ? formatNum(primary) : '0'}
          </span>
        </div>
        {/* Mobile: just the number */}
        <span className="sm:hidden text-sm font-semibold tabular-nums">
          {hasData ? formatNum(primary) : '0'}
        </span>

        {/* Secondary metrics */}
        {secondary1 && (
          <span className="hidden md:block text-xs text-muted-foreground min-w-[60px] text-right">
            {secondary1}
          </span>
        )}
        {secondary2 && (
          <span className="hidden md:block text-xs text-muted-foreground min-w-[80px] text-right">
            {secondary2}
          </span>
        )}

        {/* Chevron */}
        {onClick && (
          <ChevronRight className="w-4 h-4 text-muted-foreground/40 group-hover:text-muted-foreground transition-colors" />
        )}
      </div>
    </div>
  );
}

// ─── Website expanded row ─────────────────────────────────────────────────────

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const min = Math.floor(seconds / 60);
  const sec = Math.round(seconds % 60);
  return `${min}m ${sec}s`;
}

function WebsiteExpandedRow({
  channel,
  onClick,
}: {
  channel: ChannelMetric;
  onClick?: () => void;
}) {
  const iconColor = getChannelColor(channel.slug);
  const hasData = channel.connected && channel.metrics.some((m) => m.value > 0);

  const users = getMetricValue(channel.metrics, 'users');
  const sessions = getMetricValue(channel.metrics, 'sessions');
  const engagementRate = getMetricValue(channel.metrics, 'engagementRate');
  const bounceRate = getMetricValue(channel.metrics, 'bounceRate');
  const avgDuration = getMetricValue(channel.metrics, 'avgSessionDuration');

  return (
    <div
      className={cn(
        'px-4 py-3 hover:bg-muted/30 transition-colors group',
        onClick && 'cursor-pointer',
      )}
      onClick={onClick}
    >
      {/* Top: icon + name + chevron */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-3">
          <div
            className="flex items-center justify-center w-8 h-8 rounded-lg shrink-0 transition-transform duration-100 group-hover:scale-105"
            style={{ backgroundColor: hexToRgba(iconColor, 0.12) }}
          >
            <ChannelIconBadge slug={channel.slug} className="w-4 h-4" style={{ color: iconColor }} />
          </div>
          <div>
            <p className="text-sm font-medium">{channel.name}</p>
            <span className="text-[10px] text-muted-foreground">
              {channel.sourceLabel}
            </span>
          </div>
        </div>
        {onClick && (
          <ChevronRight className="w-4 h-4 text-muted-foreground/40 group-hover:text-muted-foreground transition-colors" />
        )}
      </div>

      {/* Metrics grid or empty state */}
      {hasData ? (
        <div className="grid grid-cols-3 sm:grid-cols-5 gap-3 ml-11">
          <div>
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Visitantes</p>
            <p className="text-base font-bold tabular-nums">{formatNum(users)}</p>
          </div>
          <div>
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Sesiones</p>
            <p className="text-base font-bold tabular-nums">{formatNum(sessions)}</p>
          </div>
          <div>
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Engagement</p>
            <p className="text-base font-bold tabular-nums">{engagementRate.toFixed(1)}%</p>
          </div>
          <div className="hidden sm:block">
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Bounce</p>
            <p className="text-base font-bold tabular-nums">{bounceRate.toFixed(1)}%</p>
          </div>
          <div className="hidden sm:block">
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Duracion</p>
            <p className="text-base font-bold tabular-nums">{formatDuration(avgDuration)}</p>
          </div>
        </div>
      ) : (
        <div className="ml-11">
          <p className="text-xs text-muted-foreground mb-2">
            Tu sitio web siempre esta aqui. Conecta Google Analytics o el Meta Pixel para medir visitas.
          </p>
          <div className="flex flex-wrap gap-2">
            <a href="/settings/connections" className="inline-flex items-center gap-1 text-[10px] font-medium text-primary border border-primary/30 rounded-md px-2 py-1 hover:bg-primary/5 transition-colors">
              <BarChart3 className="w-3 h-3" /> Google Analytics
            </a>
            <a href="/settings/connections" className="inline-flex items-center gap-1 text-[10px] font-medium text-muted-foreground border border-border rounded-md px-2 py-1 hover:bg-muted transition-colors">
              <Crosshair className="w-3 h-3" /> Meta Pixel
            </a>
          </div>
        </div>
      )}
    </div>
  );
}

function UnconnectedRow({
  channel,
  onConfigure,
}: {
  channel: ChannelMetric;
  onConfigure?: (slug: string, name: string) => void;
}) {
  const iconColor = getChannelColor(channel.slug);

  return (
    <div
      className="flex items-center justify-between px-4 py-2.5 opacity-50 hover:opacity-70 transition-opacity cursor-pointer"
      onClick={() => onConfigure?.(channel.slug, channel.name)}
    >
      <div className="flex items-center gap-3">
        <div
          className="flex items-center justify-center w-8 h-8 rounded-lg shrink-0"
          style={{ backgroundColor: hexToRgba(iconColor, 0.08) }}
        >
          <ChannelIconBadge slug={channel.slug} className="w-4 h-4" style={{ color: iconColor }} />
        </div>
        <div>
          <p className="text-sm font-medium text-muted-foreground">{channel.name}</p>
          <span className="text-[10px] text-muted-foreground">No conectado</span>
        </div>
      </div>
      <button className="text-xs text-primary border border-primary/30 rounded-md px-3 py-1 hover:bg-primary/10 transition-colors">
        Conectar
      </button>
    </div>
  );
}
