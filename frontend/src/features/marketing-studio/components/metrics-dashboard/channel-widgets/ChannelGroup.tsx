'use client';

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import type { ChannelMetric } from '../../../types/metrics';
import { ChannelRow } from './ChannelRow';

interface ChannelGroupProps {
  title: string;
  totalValue: number;
  totalCost?: number;
  channels: ChannelMetric[];
  defaultOpen?: boolean;
}

function formatNumber(n: number): string {
  if (n >= 1000) return `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}k`;
  return n.toLocaleString();
}

export function ChannelGroup({ title, totalValue, totalCost, channels, defaultOpen = true }: ChannelGroupProps) {
  const summary = totalCost !== undefined
    ? `${formatNumber(totalValue)} clics — $${totalCost.toLocaleString()} invertidos`
    : `${formatNumber(totalValue)} visitantes`;

  return (
    <Accordion type="single" collapsible defaultValue={defaultOpen ? 'group' : undefined}>
      <AccordionItem value="group" className="border-none">
        <AccordionTrigger className="hover:no-underline py-3">
          <div className="flex flex-col items-start gap-0.5">
            <span className="text-sm font-semibold">{title}</span>
            <span className="text-xs text-muted-foreground">{summary}</span>
          </div>
        </AccordionTrigger>
        <AccordionContent>
          <div className="space-y-1">
            {channels.map((ch) => (
              <ChannelRow key={ch.slug} channel={ch} />
            ))}
          </div>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}
