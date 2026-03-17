'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { ChannelMetric, GroupType, MetricClickData, StageId } from '../../../types/metrics';
import { ChannelRow } from './ChannelRow';
import { buildSummary } from './ChannelGroup';

interface ChannelGroupCardProps {
  title: string;
  totals: Record<string, number>;
  channels: ChannelMetric[];
  groupType: GroupType;
  /** Stage context forwarded to ChannelRow for MetricClickData */
  stageId?: StageId;
  /** Callback forwarded to ChannelRow when user clicks a metric value */
  onMetricClick?: (metric: MetricClickData) => void;
}

export function ChannelGroupCard({ title, totals, channels, groupType, stageId, onMetricClick }: ChannelGroupCardProps) {
  const summary = buildSummary(groupType, totals, channels.length);

  return (
    <Card className="overflow-hidden border shadow-sm">
      <CardHeader className="py-4 bg-muted/30 border-b">
        <div className="flex flex-col items-start gap-1">
          <CardTitle className="text-base font-semibold">{title}</CardTitle>
          <span className="text-xs text-muted-foreground">{summary}</span>
        </div>
      </CardHeader>
      <CardContent className="p-2 space-y-1 bg-card">
        {channels.map((ch) => (
          <ChannelRow
            key={ch.slug}
            channel={ch}
            stageId={stageId}
            onMetricClick={onMetricClick}
          />
        ))}
      </CardContent>
    </Card>
  );
}
