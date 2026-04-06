'use client';

import { Loader2 } from 'lucide-react';

import { BenchmarkBadge } from '../../../channel-widgets/BenchmarkBadge';
import { ReachFrequencySection } from '../ReachFrequencySection';
import { formatMoney } from '@/lib/format-money';
import type { ChannelDashboardData, MetricKpiData } from '../../../../../types/metrics';

interface CostsTabProps {
  data: ChannelDashboardData | undefined;
  isLoading: boolean;
}

const COST_METRICS = ['CPC', 'CPM', 'CPL', 'CPA'];

function formatCost(value: number, currency?: string): string {
  return formatMoney(value, currency || 'USD');
}

export function CostsTab({ data, isLoading }: CostsTabProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="py-24 text-center text-sm text-muted-foreground">
        No hay datos disponibles
      </div>
    );
  }

  const costKpis = COST_METRICS
    .map(name => data.kpis.find(k => k.metricName === name))
    .filter((k): k is MetricKpiData => k != null);

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {costKpis.map(kpi => (
          <div key={kpi.metricName} className="space-y-1.5 rounded-lg border bg-card p-4">
            <p className="text-xs text-muted-foreground">{kpi.displayName}</p>
            <p className="text-2xl font-semibold tabular-nums">{formatCost(kpi.currentValue, kpi.currency)}</p>
            {kpi.benchmark && (
              <BenchmarkBadge
                value={kpi.currentValue}
                benchmark={kpi.benchmark}
                higherIsBetter={kpi.higherIsBetter}
              />
            )}
          </div>
        ))}
      </div>

      <ReachFrequencySection kpis={data.kpis} frequencyAlert={data.frequencyAlert} />
    </div>
  );
}
