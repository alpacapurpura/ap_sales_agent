'use client';

import * as Sentry from "@sentry/nextjs";
import React, { useState, useCallback } from 'react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { ChannelMetric, CampaignMetric, MetricClickData, StageId } from '../../../types/metrics';
import { ConnectionBadge } from './ConnectionBadge';
import { CampaignDrillDown } from './CampaignDrillDown';
import { getChannelIcon, getChannelColor } from '../../../lib/channelIcons';
import { useMetricCatalog } from '../../../hooks/useMetricCatalog';
import { ChannelRowHeader } from './ChannelRowHeader';
import { ChannelRowMetrics } from './ChannelRowMetrics';
import { ChannelRowActions } from './ChannelRowActions';
import { getSummaryMetrics } from '../../../config/channel-display-registry';

/** Convert hex color to rgba for backgrounds. */
function hexToRgba(hex: string, alpha: number): string {
  if (hex.startsWith('hsl')) return hex;
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
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

  // ── Early return: unconnected channels ──────────────────────────────
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

  // ── Early return: "Proximamente" channels ───────────────────────────
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
        <Badge variant="secondary" className="text-[11px]">Próximamente</Badge>
      </div>
    );
  }

  // ── Derived data for connected channels ─────────────────────────────
  const leadsMetric = channel.metrics.find(m => m.name === 'leads');
  const hasZeroLeads = leadsMetric !== undefined && leadsMetric.value === 0;
  const hasNoData = channel.metrics.length === 0 || channel.metrics.every(m => m.value === 0);
  const conversationsMetric = channel.metrics.find(m => m.name === 'conversations');

  // Summary metrics from registry (channels without config show all metrics)
  const displayMetrics = getSummaryMetrics(channel.slug, channel.metrics);

  // Bottleneck badges
  const abandonmentMetric = channel.slug === 'abandoned-cart'
    ? channel.metrics.find(m => m.name === 'abandonment_rate')
    : undefined;
  const abandonmentBadge = abandonmentMetric && abandonmentMetric.value > 50
    ? 'critical' as const
    : abandonmentMetric && abandonmentMetric.value > 30
      ? 'warning' as const
      : null;

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
    ? 'critical' as const
    : noShowRate > 0.20
      ? 'warning' as const
      : null;

  // CampaignDrillDown wrapping
  const shouldWrapWithDrillDown = channel.channelType === 'retargeting' || channel.channelType === 'email';
  const campaigns: CampaignMetric[] = (channel as unknown as Record<string, unknown>).campaigns as CampaignMetric[] ?? [];

  // ── Main connected row ──────────────────────────────────────────────
  const rowContent = (
    <div
      className={cn(
        "flex items-center justify-between py-2.5 px-3 rounded-lg hover:bg-primary/5 transition-all duration-100 ease-out group",
        onChannelClick && "cursor-pointer"
      )}
      onClick={onChannelClick ? () => onChannelClick(channel) : undefined}
    >
      {/* Left: icon + name + status */}
      <ChannelRowHeader
        channel={channel}
        icon={Icon}
        iconColor={iconColor}
        abandonmentBadge={abandonmentBadge}
        noShowBadge={noShowBadge}
      />

      {/* Right: metrics + actions */}
      <div className="flex flex-row items-center gap-2 sm:gap-3 shrink-0 flex-wrap justify-end">
        <ChannelRowMetrics
          displayMetrics={displayMetrics}
          channelSlug={channel.slug}
          connected={channel.connected}
          stageId={stageId}
          conversationsMetric={conversationsMetric}
          hasNoData={hasNoData}
          hasZeroLeads={hasZeroLeads}
          catalogByName={catalogByName}
          onMetricClick={onMetricClick}
        />
        <ChannelRowActions
          stale={!!channel.stale}
          refreshing={refreshing}
          cooldown={cooldown}
          onRefresh={handleRefresh}
        />
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
