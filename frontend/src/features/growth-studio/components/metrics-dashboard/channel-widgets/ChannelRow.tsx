"use client";

import React from "react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

import { getSummaryMetrics } from "../../../lib/channel-display-registry";
import { useMetricCatalog } from "../../../hooks/use-metric-catalog";
import { useSyncChannel } from "../../../hooks/use-sync-channel";
import { getChannelIcon, getChannelColor } from "../../../lib/channel-icons";

import { CampaignDrillDown } from "./CampaignDrillDown";
import { ChannelRowActions } from "./ChannelRowActions";
import { ChannelRowHeader } from "./ChannelRowHeader";
import { ChannelRowMetrics } from "./ChannelRowMetrics";

import type {
  ChannelMetric,
  CampaignMetric,
  MetricClickData,
  StageId,
} from "../../../types/metrics";

/** Convert hex color to rgba for backgrounds. */
function hexToRgba(hex: string, alpha: number): string {
  if (hex.startsWith("hsl")) return hex;
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

/** Renders a channel icon by slug. Uses createElement to avoid static-components lint false positive. */
function ChannelIconDisplay({
  slug,
  className,
  style,
}: {
  slug: string;
  className?: string;
  style?: React.CSSProperties;
}) {
  return React.createElement(getChannelIcon(slug), { className, style, "aria-hidden": true });
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
}

// eslint-disable-next-line sonarjs/cognitive-complexity -- Irreducible: rendering path already delegates to ChannelRowHeader, ChannelRowMetrics, ChannelRowActions sub-components. Remaining complexity is channel-specific bottleneck badge derivation (abandonment-cart, meeting-booked no-show rate) and the próximamente early-return — all inherently conditional on channel slug.
export const ChannelRow = React.memo(function ChannelRow({
  channel,
  stageId,
  onMetricClick,
  onChannelClick,
}: ChannelRowProps) {
  const { catalogByName } = useMetricCatalog();
  const { sync, isSyncing, cooldownMinutes } = useSyncChannel(channel.slug);

  const iconColor = getChannelColor(channel.slug);

  // ── Early return: "Proximamente" channels ───────────────────────────
  const isProximamente =
    (channel.slug === "ai-sdr" &&
      (channel.metrics.length === 0 || channel.metrics.every((m) => m.value === 0))) ||
    channel.slug === "checkout-lp" ||
    (channel.slug === "link-enviado" && channel.metrics.length === 0);
  if (isProximamente) {
    return (
      <div
        id={`channel-${channel.slug}`}
        className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-muted/40 transition-colors duration-100"
      >
        <div className="flex items-center gap-3 min-w-0">
          <div
            className="flex items-center justify-center w-8 h-8 rounded-lg shrink-0"
            style={{ backgroundColor: hexToRgba(iconColor, 0.1) }}
          >
            <ChannelIconDisplay
              slug={channel.slug}
              className="w-4 h-4"
              style={{ color: iconColor }}
            />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium truncate">{channel.name}</p>
            <p className="text-xs text-muted-foreground truncate">{channel.sourceLabel}</p>
          </div>
        </div>
        <Badge variant="secondary" className="text-[11px]">
          Próximamente
        </Badge>
      </div>
    );
  }

  // ── Derived data for connected channels ─────────────────────────────
  const leadsMetric = channel.metrics.find((m) => m.name === "leads");
  const hasZeroLeads = leadsMetric?.value === 0;
  const hasNoData = channel.metrics.length === 0 || channel.metrics.every((m) => m.value === 0);
  const conversationsMetric = channel.metrics.find((m) => m.name === "conversations");

  // Summary metrics from registry (channels without config show all metrics)
  const displayMetrics = getSummaryMetrics(channel.slug, channel.metrics);

  // Bottleneck badges
  const abandonmentMetric =
    channel.slug === "abandoned-cart"
      ? channel.metrics.find((m) => m.name === "abandonment_rate")
      : undefined;
  const abandonmentBadge =
    abandonmentMetric && abandonmentMetric.value > 50
      ? ("critical" as const)
      : abandonmentMetric && abandonmentMetric.value > 30
        ? ("warning" as const)
        : null;

  const bookedMetric =
    channel.slug === "meeting-booked"
      ? channel.metrics.find((m) => m.name === "booked")
      : undefined;
  const noShowMetric =
    channel.slug === "meeting-booked"
      ? channel.metrics.find((m) => m.name === "no_show")
      : undefined;
  const noShowRate =
    bookedMetric && bookedMetric.value > 0 && noShowMetric
      ? noShowMetric.value / bookedMetric.value
      : 0;
  const noShowBadge =
    noShowRate > 0.4 ? ("critical" as const) : noShowRate > 0.2 ? ("warning" as const) : null;

  // CampaignDrillDown wrapping
  const shouldWrapWithDrillDown =
    channel.channelType === "retargeting" || channel.channelType === "email";
  const campaigns: CampaignMetric[] =
    ((channel as unknown as Record<string, unknown>).campaigns as CampaignMetric[]) ?? [];

  // ── Main connected row ──────────────────────────────────────────────
  const rowContent = (
    <div
      id={`channel-${channel.slug}`}
      className={cn(
        "flex items-center justify-between py-2.5 px-3 rounded-lg hover:bg-primary/5 transition-all duration-100 ease-out group",
        onChannelClick && "cursor-pointer",
      )}
      onClick={onChannelClick ? () => onChannelClick(channel) : undefined}
    >
      {/* Left: icon + name + status */}
      <ChannelRowHeader
        channel={channel}
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
          refreshing={isSyncing}
          cooldown={cooldownMinutes > 0}
          onRefresh={() => sync()}
        />
      </div>
    </div>
  );

  if (shouldWrapWithDrillDown) {
    return <CampaignDrillDown campaigns={campaigns}>{rowContent}</CampaignDrillDown>;
  }

  return rowContent;
});
