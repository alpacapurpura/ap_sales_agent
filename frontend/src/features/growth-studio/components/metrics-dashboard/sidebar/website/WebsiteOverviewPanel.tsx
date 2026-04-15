"use client";

import { Globe } from "lucide-react";

import { ChannelOverviewPanel } from "../shared/ChannelOverviewPanel";

import type { ChannelMetric } from "../../../../types/metrics";

const HERO_METRICS = [
  "sessions",
  "engagementRate",
  "bounceRate",
  "conversions",
  "averageSessionDuration",
  "users",
];

interface WebsiteOverviewPanelProps {
  channel: ChannelMetric;
  onClose: () => void;
  onExpand?: () => void;
  initialTab?: string | null;
}

export function WebsiteOverviewPanel({ channel, onClose, onExpand }: WebsiteOverviewPanelProps) {
  return (
    <ChannelOverviewPanel
      channel={channel}
      onClose={onClose}
      onExpand={onExpand}
      icon={Globe}
      iconColor="text-blue-500"
      heroMetrics={HERO_METRICS}
      gradientPrefix="web"
      dashboardSlug="website-total"
    />
  );
}
