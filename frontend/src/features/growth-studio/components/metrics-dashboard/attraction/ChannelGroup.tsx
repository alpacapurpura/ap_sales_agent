'use client';

import React from 'react';
import { BarChart3, Crosshair } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ChannelMetric, MetricValue } from '../../../types/metrics';
import { getChannelIcon, getChannelColor } from '../../../lib/channelIcons';

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatNum(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}k`;
  return n.toLocaleString('es-ES');
}

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

// ─── Primary metric extraction per variant ──────────────────────────────────

function getPrimaryMetric(
  channel: ChannelMetric,
  variant: ChannelGroupVariant,
): { value: number; label: string } {
  const metrics = channel.metrics;
  switch (variant) {
    case 'paid': {
      const val = getMetricValue(metrics, 'impressions');
      return { value: val, label: 'impresiones' };
    }
    case 'organic': {
      const reach = getMetricValue(metrics, 'reach');
      const sessions = getMetricValue(metrics, 'sessions');
      if (reach > 0) return { value: reach, label: 'alcance' };
      return { value: sessions, label: 'sesiones' };
    }
    case 'outbound': {
      const contacts = getMetricValue(metrics, 'contacts') || getMetricValue(metrics, 'comment_triggers');
      return { value: contacts, label: 'contactos' };
    }
    case 'capture_web':
    case 'capture_messaging': {
      const leads = getMetricValue(metrics, 'leads');
      return { value: leads, label: 'leads' };
    }
  }
}

// ─── Channel icon wrapper (avoids creating components during render) ─────────

/* eslint-disable react-hooks/static-components -- dynamic icon from registry */
function ChannelIconBadge({ slug, className }: { slug: string; className?: string }) {
  const Icon = getChannelIcon(slug);
  const iconColor = getChannelColor(slug);
  return <Icon className={className} style={{ color: iconColor }} />;
}
/* eslint-enable react-hooks/static-components */

// ─── Website expanded metrics ────────────────────────────────────────────────

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const min = Math.floor(seconds / 60);
  const sec = Math.round(seconds % 60);
  return `${min}m ${sec}s`;
}

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
              variant={variant}
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
  variant,
  baseColor,
  onClick,
}: {
  channel: ChannelMetric;
  variant: ChannelGroupVariant;
  baseColor: keyof typeof COLOR_MAP;
  onClick?: () => void;
}) {
  const colors = COLOR_MAP[baseColor];
  const hasData = channel.metrics.length > 0 && channel.metrics.some((m) => m.value > 0);
  const { value, label } = getPrimaryMetric(channel, variant);

  return (
    <div
      className={cn(
        'border border-border rounded-md p-3 flex justify-between items-center bg-card transition-colors group cursor-pointer',
        colors.hoverBorder,
      )}
      onClick={onClick}
    >
      {/* Left: icon + name + status */}
      <div className="flex items-center gap-3">
        <div className={cn('w-8 h-8 rounded flex items-center justify-center shrink-0', colors.iconBg)}>
          <ChannelIconBadge slug={channel.slug} className="w-4 h-4" />
        </div>
        <div>
          <p className="text-sm font-medium text-foreground">{channel.name}</p>
          <p className={cn(
            'text-[10px] font-semibold',
            hasData ? 'text-emerald-600 dark:text-emerald-500' : 'text-amber-600 dark:text-amber-500',
          )}>
            {hasData ? 'Activo' : 'Sin datos'}
          </p>
        </div>
      </div>

      {/* Right: primary metric */}
      <div className="text-right">
        <p className={cn(
          'text-sm font-bold underline decoration-dashed underline-offset-4 transition-colors',
          hasData ? `text-foreground ${colors.hoverText}` : 'text-muted-foreground',
        )}>
          {hasData ? formatNum(value) : '0'}
        </p>
        <p className="text-[10px] text-muted-foreground">{label}</p>
      </div>
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

  const users = getMetricValue(channel.metrics, 'users');
  const sessions = getMetricValue(channel.metrics, 'sessions');
  const engagementRate = getMetricValue(channel.metrics, 'engagementRate');
  const bounceRate = getMetricValue(channel.metrics, 'bounceRate');
  const avgDuration = getMetricValue(channel.metrics, 'avgSessionDuration');

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
