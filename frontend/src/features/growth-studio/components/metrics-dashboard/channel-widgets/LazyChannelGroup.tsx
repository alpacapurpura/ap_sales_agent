'use client';

import { memo, useMemo } from 'react';
import type React from 'react';
import type { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useIntersectionObserver } from '../../../hooks/useIntersectionObserver';
import { useGroupDetail } from '../../../hooks/useGroupDetail';
import { ChannelRow } from './ChannelRow';
import type { ChannelOverview, ChannelMetric, MetricClickData, StageId } from '../../../types/metrics';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';

const COLOR_MAP = {
  blue: {
    headerIcon: 'text-blue-600',
    headerBg: 'bg-blue-500/5',
  },
  violet: {
    headerIcon: 'text-violet-600',
    headerBg: 'bg-violet-500/5',
  },
} as const;

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
  /** Icon for the group header */
  headerIcon?: LucideIcon;
  /** Color scheme for the group */
  baseColor?: keyof typeof COLOR_MAP;
  /** Summary text in group header */
  summary?: string;
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
export const LazyChannelGroup = memo(function LazyChannelGroup({
  stage,
  groupKey,
  title,
  overviewChannels,
  defaultOpen = true,
  stageId,
  rootMargin = '200px',
  headerIcon: HeaderIcon,
  baseColor,
  summary,
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

  const colors = baseColor ? COLOR_MAP[baseColor] : null;

  return (
    <div ref={ref as React.Ref<HTMLDivElement>} className="bg-card rounded-lg border border-border shadow-sm overflow-hidden">
      <Accordion type="single" collapsible defaultValue={defaultOpen ? groupKey : undefined}>
        <AccordionItem value={groupKey} className="border-none">
          <AccordionTrigger className={cn(
            'hover:no-underline py-3 px-4 border-b border-border',
            colors?.headerBg,
          )}>
            <div className="flex items-center justify-between w-full pr-2">
              <span className="font-medium text-sm text-foreground/90 flex items-center">
                {HeaderIcon && <HeaderIcon className={cn('w-4 h-4 mr-2', colors?.headerIcon)} />}
                {title}
              </span>
              <div className="flex gap-4 text-xs">
                {summary && <span className="text-muted-foreground">{summary}</span>}
                <span className="text-muted-foreground">
                  ({channels.length} {channels.length === 1 ? 'canal' : 'canales'})
                </span>
              </div>
            </div>
          </AccordionTrigger>
          <AccordionContent className="pb-0">
            <div className="p-4 space-y-0.5">
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
});
LazyChannelGroup.displayName = 'LazyChannelGroup';
