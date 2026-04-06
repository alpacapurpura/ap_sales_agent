'use client';

import React, { useMemo } from 'react';
import { useIntersectionObserver } from '../../../hooks/useIntersectionObserver';
import { useGroupDetail } from '../../../hooks/useGroupDetail';
import { ChannelRow } from './ChannelRow';
import type { ChannelOverview, ChannelMetric, MetricClickData, StageId } from '../../../types/metrics';
import { getChannelIcon, getChannelColor } from '../../../lib/channelIcons';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';

interface LazyChannelGroupProps {
  /** Stage name for API call (e.g., 'attraction') */
  stage: string;
  /** Group key for API filtering (e.g., 'paid', 'organic_social') */
  groupKey: string;
  /** Display title for the group */
  title: string;
  /** Channels from overview endpoint (headline KPI only) */
  overviewChannels: ChannelOverview[];
  /** Whether the accordion is open by default */
  defaultOpen?: boolean;
  /** Stage ID for metric click data */
  stageId?: StageId;
  /** IntersectionObserver rootMargin for pre-fetching */
  rootMargin?: string;
  /** Callback when user clicks a metric value */
  onMetricClick?: (metric: MetricClickData) => void;
  /** Callback when a connected channel row is clicked */
  onChannelClick?: (channel: ChannelMetric) => void;
  /** Callback when user clicks "Configurar" on unconnected channel */
  onConfigure?: (slug: string, name: string) => void;
}

/**
 * A ChannelGroup that lazily loads full metrics data when it enters the viewport.
 *
 * Renders immediately with overview data (channel names + 1 headline KPI).
 * When scrolled into view, fetches full detail for just this group's channels.
 */
export function LazyChannelGroup({
  stage,
  groupKey,
  title,
  overviewChannels,
  defaultOpen = true,
  stageId,
  rootMargin = '200px',
  onMetricClick,
  onChannelClick,
  onConfigure,
}: LazyChannelGroupProps) {
  const { ref, isVisible } = useIntersectionObserver({ rootMargin });
  const { data: groupDetail } = useGroupDetail(stage, groupKey, { enabled: isVisible });

  // Merge overview data with full detail when available
  const channels: ChannelMetric[] = useMemo(() => {
    if (groupDetail?.channels) {
      return groupDetail.channels;
    }

    // Fallback: convert overview channels to ChannelMetric format
    return overviewChannels.map((ch) => ({
      slug: ch.slug,
      name: ch.name,
      channelType: ch.channelType,
      metrics: ch.headlineKpi ? [{ name: ch.headlineKpi.name, value: ch.headlineKpi.value, unit: ch.headlineKpi.unit }] : [],
      sourceLabel: ch.name,
      connected: ch.connected,
      lastUpdated: ch.lastUpdated,
      stale: ch.stale,
      providerName: ch.providerName,
    }));
  }, [groupDetail, overviewChannels]);

  if (channels.length === 0) return null;

  return (
    <div ref={ref as React.Ref<HTMLDivElement>}>
      <Accordion type="single" collapsible defaultValue={defaultOpen ? groupKey : undefined}>
        <AccordionItem value={groupKey} className="border-none">
          <AccordionTrigger className="hover:no-underline py-2 px-1">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold">{title}</span>
              <span className="text-xs text-muted-foreground">
                ({channels.length} {channels.length === 1 ? 'canal' : 'canales'})
              </span>
            </div>
          </AccordionTrigger>
          <AccordionContent className="pb-0">
            <div className="space-y-0.5">
              {channels.map((channel) => (
                <ChannelRow
                  key={channel.slug}
                  channel={channel}
                  stageId={stageId}
                  onMetricClick={onMetricClick}
                  onChannelClick={onChannelClick}
                  onConfigure={onConfigure}
                />
              ))}
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </div>
  );
}
