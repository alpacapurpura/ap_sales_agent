"use client";

import { Instagram } from "lucide-react";

import { ChannelOverviewPanel } from "../shared/ChannelOverviewPanel";

import { IgOrganicGrowthIndicator } from "./IgOrganicGrowthIndicator";

import type { ChannelMetric } from "../../../../types/metrics";

const HERO_METRICS = [
  "total_interactions",
  "ig_views",
  "ig_follows_and_unfollows",
  "ig_engagement_rate",
];

interface IgOrganicOverviewPanelProps {
  channel: ChannelMetric;
  onClose: () => void;
  onExpand?: () => void;
  initialTab?: string | null;
}

/**
 *
 */
export function IgOrganicOverviewPanel({
  channel,
  onClose,
  onExpand,
}: IgOrganicOverviewPanelProps) {
  return (
    <ChannelOverviewPanel
      channel={channel}
      onClose={onClose}
      onExpand={onExpand}
      icon={Instagram}
      iconColor="text-pink-500"
      heroMetrics={HERO_METRICS}
      gradientPrefix="ig"
    >
      {(data) => <IgOrganicGrowthIndicator kpis={data.kpis} />}
    </ChannelOverviewPanel>
  );
}
