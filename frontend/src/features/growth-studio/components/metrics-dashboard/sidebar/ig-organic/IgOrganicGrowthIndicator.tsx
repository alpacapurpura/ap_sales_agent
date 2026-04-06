'use client';

import { TrendingDown, TrendingUp, Users } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { MetricKpiData } from '../../../../types/metrics';

interface IgOrganicGrowthIndicatorProps {
  kpis: MetricKpiData[];
}

export function IgOrganicGrowthIndicator({ kpis }: IgOrganicGrowthIndicatorProps) {
  const followsKpi = kpis.find(k => k.metricName === 'ig_follows_and_unfollows');
  if (!followsKpi) return null;

  const netFollows = followsKpi.currentValue;
  const isPositive = netFollows >= 0;

  return (
    <div className="space-y-2">
      <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
        Crecimiento de Audiencia
      </h4>
      <div className="rounded-lg border bg-card p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-pink-500/10">
            <Users className="h-5 w-5 text-pink-500" />
          </div>
          <div className="flex-1">
            <p className="text-sm text-muted-foreground">Seguidores netos (periodo)</p>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-semibold tabular-nums">
                {isPositive ? '+' : ''}{netFollows.toLocaleString('en-US')}
              </span>
              <span
                className={cn(
                  'inline-flex items-center gap-0.5 text-xs font-medium',
                  isPositive ? 'text-emerald-600' : 'text-red-600',
                )}
              >
                {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                {followsKpi.deltaPct != null
                  ? `${Math.abs(followsKpi.deltaPct).toFixed(1)}% vs anterior`
                  : isPositive ? 'Creciendo' : 'Decreciendo'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
