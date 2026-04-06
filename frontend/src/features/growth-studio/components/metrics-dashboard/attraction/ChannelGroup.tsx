'use client';

import React from 'react';
import { BarChart3, Crosshair } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ChannelMetric, MetricValue } from '../../../types/metrics';
import { getChannelIcon, getChannelColor } from '../../../lib/channelIcons';
import { formatNum, formatMetricValue } from '../utils/format';
import { getPrimaryMetricSpec, getExpandedMetrics, getChannelConfig, getSummaryMetrics } from '../../../config/channel-display-registry';

function getMetricValue(metrics: MetricValue[], name: string): number {
  return metrics.find((m) => m.name === name)?.value ?? 0;
}

// ─── Color Map ───────────────────────────────────────────────────────────────

const COLOR_MAP = {
  blue: {
    iconBg: 'bg-blue-100 dark:bg-blue-500/20',
    iconText: 'text-blue-600 dark:text-blue-400',
    hoverBorder: 'hover:border-blue-300 dark:hover:border-blue-700',
    hoverText: 'group-hover:text-blue-600 dark:group-hover:text-blue-400',
    borderAccent: 'border-l-blue-400 hover:border-l-blue-500',
    headerIcon: 'text-blue-600',
    headerBg: 'bg-blue-500/5',
  },
  violet: {
    iconBg: 'bg-violet-100 dark:bg-violet-500/20',
    iconText: 'text-violet-600 dark:text-violet-400',
    hoverBorder: 'hover:border-violet-300 dark:hover:border-violet-700',
    hoverText: 'group-hover:text-violet-600 dark:group-hover:text-violet-400',
    borderAccent: 'border-l-violet-400 hover:border-l-violet-500',
    headerIcon: 'text-violet-600',
    headerBg: 'bg-violet-500/5',
  },
} as const;

// ─── Types ───────────────────────────────────────────────────────────────────

export type ChannelGroupVariant = 'paid' | 'organic' | 'outbound' | 'capture_web' | 'capture_messaging';

interface ChannelGroupProps {
  title: string;
  variant: ChannelGroupVariant;
  channels: ChannelMetric[];
  headerIcon: LucideIcon;
  baseColor: keyof typeof COLOR_MAP;
  summary?: string;
  summaryExtra?: string;
  accentBorder?: boolean;
  onChannelClick?: (channel: ChannelMetric) => void;
  onConfigure?: (slug: string, name: string) => void;
}

// ─── Channel icon wrapper (avoids creating components during render) ─────────

/* eslint-disable react-hooks/static-components -- dynamic icon from registry */
function ChannelIconBadge({ slug, className }: { slug: string; className?: string }) {
  const Icon = getChannelIcon(slug);
  const iconColor = getChannelColor(slug);
  return <Icon className={className} style={{ color: iconColor }} />;
}
/* eslint-enable react-hooks/static-components */

// ─── Component ───────────────────────────────────────────────────────────────

export function ChannelGroup({
  title,
  variant,
  channels,
  headerIcon: HeaderIcon,
  baseColor,
  summary,
  summaryExtra,
  accentBorder,
  onChannelClick,
  onConfigure,
}: ChannelGroupProps) {
  const colors = COLOR_MAP[baseColor];

  return (
    <div className={cn(
      'bg-card rounded-lg border border-border shadow-sm overflow-hidden',
      accentBorder && `border-l-4 ${colors.borderAccent}`,
    )}>
      {/* Header */}
      <div className={cn(colors.headerBg, 'px-4 py-3 border-b border-border flex justify-between items-center')}>
        <span className="font-medium text-sm text-foreground/90 flex items-center">
          <HeaderIcon className={cn('w-4 h-4 mr-2', colors.headerIcon)} />
          {title}
        </span>
        <div className="flex gap-4 text-xs">
          {summary && <span className="text-muted-foreground">{summary}</span>}
          {summaryExtra && <span className="text-emerald-600 dark:text-emerald-400 font-semibold">{summaryExtra}</span>}
        </div>
      </div>

      {/* Channel cards */}
      <div className="p-4 grid grid-cols-1 gap-2">
        {channels.map((channel) => {
          if (channel.channelType === 'website') {
            return (
              <WebsiteExpandedRow
                key={channel.slug}
                channel={channel}
                baseColor={baseColor}
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

          return (
            <ChannelRowCard
              key={channel.slug}
              channel={channel}
              baseColor={baseColor}
              onClick={onChannelClick ? () => onChannelClick(channel) : undefined}
            />
          );
        })}
      </div>
    </div>
  );
}

// ─── Card-style channel row ─────────────────────────────────────────────────

function ChannelRowCard({
  channel,
  baseColor,
  onClick,
}: {
  channel: ChannelMetric;
  baseColor: keyof typeof COLOR_MAP;
  onClick?: () => void;
}) {
  const colors = COLOR_MAP[baseColor];
  const hasData = channel.metrics.length > 0 && channel.metrics.some((m) => m.value > 0);

  // Use summaryMetrics if configured, otherwise fall back to primaryMetric
  const config = getChannelConfig(channel.slug);
  const summaryMetrics = config ? getSummaryMetrics(channel.slug, channel.metrics) : [];
  const hasSummaryPills = summaryMetrics.length > 1;

  // Fallback: primaryMetric for channels without summaryMetrics config
  const spec = getPrimaryMetricSpec(channel.slug, channel.channelType);
  const primaryValue = getMetricValue(channel.metrics, spec.name);

  return (
    <div
      className={cn(
        'border border-border rounded-md p-3 flex justify-between items-center bg-card transition-colors group cursor-pointer',
        colors.hoverBorder,
      )}
      onClick={onClick}
    >
      {/* Left: icon + name + status */}
      <div className="flex items-center gap-3 min-w-0 shrink-0">
        <div className={cn('w-8 h-8 rounded flex items-center justify-center shrink-0', colors.iconBg)}>
          <ChannelIconBadge slug={channel.slug} className="w-4 h-4" />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-medium text-foreground truncate">{channel.name}</p>
          <p className={cn(
            'text-[10px] font-semibold',
            hasData ? 'text-emerald-600 dark:text-emerald-500' : 'text-amber-600 dark:text-amber-500',
          )}>
            {hasData ? 'Activo' : 'Sin datos'}
          </p>
        </div>
      </div>

      {/* Right: summary pills or single primary metric */}
      {hasData && hasSummaryPills ? (
        <div className="flex items-center gap-2 sm:gap-3 flex-wrap justify-end">
          {summaryMetrics.map((m) => {
            const metricSpec = config?.summaryMetrics.find(s => s.name === m.name);
            const isCurrency = m.unit === 'currency' || metricSpec?.format === 'currency';
            const formatted = isCurrency
              ? formatMetricValue(m.value, 'currency', m.currency)
              : formatNum(m.value);
            const metricLabel = metricSpec?.label ?? m.name;
            const isResponsiveSm = metricSpec?.responsive === 'sm';

            const pill = (
              <div className="flex flex-col items-end min-w-[44px]">
                <span className="text-[10px] text-muted-foreground uppercase tracking-wide leading-tight">{metricLabel}</span>
                <span className="text-sm font-semibold tabular-nums leading-tight">{formatted}</span>
              </div>
            );

            if (isResponsiveSm) {
              return <div key={m.name} className="hidden sm:flex">{pill}</div>;
            }
            return <div key={m.name}>{pill}</div>;
          })}
        </div>
      ) : (
        <div className="text-right">
          <p className={cn(
            'text-sm font-bold underline decoration-dashed underline-offset-4 transition-colors',
            hasData ? `text-foreground ${colors.hoverText}` : 'text-muted-foreground',
          )}>
            {hasData ? formatNum(primaryValue) : '0'}
          </p>
          <p className="text-[10px] text-muted-foreground">{spec.label}</p>
        </div>
      )}
    </div>
  );
}

// ─── Website expanded row ────────────────────────────────────────────────────

function WebsiteExpandedRow({
  channel,
  baseColor,
  onClick,
}: {
  channel: ChannelMetric;
  baseColor: keyof typeof COLOR_MAP;
  onClick?: () => void;
}) {
  const colors = COLOR_MAP[baseColor];
  const hasData = channel.connected && channel.metrics.some((m) => m.value > 0);
  const expandedSpecs = getExpandedMetrics(channel.slug);

  return (
    <div
      className={cn(
        'border border-border rounded-md p-3 bg-card transition-colors group',
        colors.hoverBorder,
        onClick && 'cursor-pointer',
      )}
      onClick={onClick}
    >
      {/* Top: icon + name */}
      <div className="flex items-center gap-3 mb-2">
        <div className={cn('w-8 h-8 rounded flex items-center justify-center shrink-0', colors.iconBg)}>
          <ChannelIconBadge slug={channel.slug} className="w-4 h-4" />
        </div>
        <div>
          <p className="text-sm font-medium">{channel.name}</p>
          <span className="text-[10px] text-muted-foreground">{channel.sourceLabel}</span>
        </div>
      </div>

      {/* Metrics grid or empty state */}
      {hasData && expandedSpecs ? (
        <div className={`grid grid-cols-3 sm:grid-cols-${expandedSpecs.length} gap-3 ml-11`}>
          {expandedSpecs.map((spec, i) => (
            <div key={spec.name} className={cn(i >= 3 && 'hidden sm:block')}>
              <p className="text-[10px] text-muted-foreground uppercase tracking-wider">
                {spec.label ?? spec.name}
              </p>
              <p className="text-base font-bold tabular-nums">
                {formatMetricValue(getMetricValue(channel.metrics, spec.name), spec.format, channel.metrics.find(m => m.name === spec.name)?.currency)}
              </p>
            </div>
          ))}
        </div>
      ) : !hasData ? (
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
      ) : null}
    </div>
  );
}

// ─── Unconnected row ─────────────────────────────────────────────────────────

function UnconnectedRow({
  channel,
  onConfigure,
}: {
  channel: ChannelMetric;
  onConfigure?: (slug: string, name: string) => void;
}) {
  return (
    <div
      className="bg-card text-card-foreground border border-border text-center p-3 rounded-md hover:bg-muted cursor-pointer transition-colors shadow-sm flex flex-col items-center justify-center gap-2"
      onClick={() => onConfigure?.(channel.slug, channel.name)}
    >
      <ChannelIconBadge slug={channel.slug} className="w-5 h-5 opacity-50" />
      <span className="text-xs font-medium text-foreground">{channel.name}</span>
    </div>
  );
}
