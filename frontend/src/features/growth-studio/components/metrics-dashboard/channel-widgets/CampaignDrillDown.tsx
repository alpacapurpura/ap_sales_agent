'use client';

import { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import type { CampaignMetric, MetricValue } from '../../../types/metrics';
import { METRIC_LABELS } from '../../../lib/metric-labels';
import { formatMoney } from '@/lib/format-money';
import { useTenantLocale } from '@/features/tenant/context/tenant-locale-context';

// Format helpers (inline to avoid cross-file dependency)
function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}k`;
  return n.toLocaleString();
}

function formatMetricValue(m: MetricValue, fallbackCurrency: string): string {
  if (m.unit === 'currency') return formatMoney(m.value, m.currency || fallbackCurrency);
  if (m.unit === 'percentage') return `${m.value.toFixed(1)}%`;
  return formatNumber(m.value);
}

interface CampaignDrillDownProps {
  campaigns: CampaignMetric[];
  children: React.ReactNode; // The ChannelRow content to wrap
}

export function CampaignDrillDown({ campaigns, children }: CampaignDrillDownProps) {
  const [open, setOpen] = useState(false);
  const { currency: tenantCurrency } = useTenantLocale();

  if (campaigns.length === 0) {
    // No campaign data yet -- render the row content normally
    return (
      <div className="relative">
        {children}
      </div>
    );
  }

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <CollapsibleTrigger asChild>
        <div className="cursor-pointer">
          <div className="flex items-center">
            <div className="flex-1">{children}</div>
            <ChevronDown
              className={`h-4 w-4 shrink-0 text-muted-foreground transition-transform duration-200 mr-3 ${open ? 'rotate-180' : ''}`}
            />
          </div>
        </div>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="space-y-1 pl-8">
          {campaigns.map((campaign, idx) => (
            <div
              key={campaign.campaignId ?? idx}
              className="flex items-center justify-between py-2 px-3 rounded-md bg-muted/20 hover:bg-muted/30 transition-colors"
            >
              <span className="text-xs font-medium truncate max-w-[200px]">
                {campaign.campaignName}
              </span>
              <div className="flex items-center gap-3">
                {campaign.metrics.map((m) => (
                  <div key={m.name} className="flex flex-col items-end min-w-[50px]">
                    <span className="text-[10px] text-muted-foreground uppercase tracking-wide">
                      {METRIC_LABELS[m.name] ?? m.name}
                    </span>
                    <span className="text-xs font-semibold tabular-nums">
                      {formatMetricValue(m, tenantCurrency)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}
