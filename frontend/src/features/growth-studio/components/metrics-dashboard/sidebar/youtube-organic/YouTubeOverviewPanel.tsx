'use client';

import { Youtube } from 'lucide-react';
import type { ChannelMetric } from '../../../../types/metrics';
import { ChannelOverviewPanel } from '../shared/ChannelOverviewPanel';
import { YouTubeSubscriberGrowth } from './YouTubeSubscriberGrowth';

const HERO_METRICS = ['views', 'watch_time_minutes', 'subscribers_gained', 'avg_view_percentage'];

interface YouTubeOverviewPanelProps {
  channel: ChannelMetric;
  onClose: () => void;
  onExpand?: () => void;
  initialTab?: string | null;
}

export function YouTubeOverviewPanel({
  channel,
  onClose,
  onExpand,
}: YouTubeOverviewPanelProps) {
  return (
    <ChannelOverviewPanel
      channel={channel}
      onClose={onClose}
      onExpand={onExpand}
      icon={Youtube}
      iconColor="text-red-500"
      heroMetrics={HERO_METRICS}
      gradientPrefix="yt"
      formatOptions={{ percentDecimals: 1 }}
    >
      {(data) => <YouTubeSubscriberGrowth kpis={data.kpis} />}
    </ChannelOverviewPanel>
  );
}
