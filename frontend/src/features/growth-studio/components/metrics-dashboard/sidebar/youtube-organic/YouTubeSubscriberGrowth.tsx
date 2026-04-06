'use client';

import { TrendingDown, TrendingUp, Users } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { MetricKpiData } from '../../../../types/metrics';

interface YouTubeSubscriberGrowthProps {
  kpis: MetricKpiData[];
}

export function YouTubeSubscriberGrowth({ kpis }: YouTubeSubscriberGrowthProps) {
  const gainedKpi = kpis.find(k => k.metricName === 'subscribers_gained');
  const lostKpi = kpis.find(k => k.metricName === 'subscribers_lost');

  if (!gainedKpi) return null;

  const gained = gainedKpi.currentValue;
  const lost = lostKpi?.currentValue ?? 0;
  const net = gained - lost;
  const isPositive = net >= 0;

  return (
    <div className="space-y-2">
      <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
        Crecimiento de Suscriptores
      </h4>
      <div className="rounded-lg border bg-card p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-500/10">
            <Users className="h-5 w-5 text-red-500" />
          </div>
          <div className="flex-1">
            <p className="text-sm text-muted-foreground">Suscriptores netos (periodo)</p>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-semibold tabular-nums">
                {isPositive ? '+' : ''}{net.toLocaleString('en-US')}
              </span>
              <span
                className={cn(
                  'inline-flex items-center gap-0.5 text-xs font-medium',
                  isPositive ? 'text-emerald-600' : 'text-red-600',
                )}
              >
                {isPositive ? (
                  <TrendingUp className="h-3 w-3" />
                ) : (
                  <TrendingDown className="h-3 w-3" />
                )}
                {gainedKpi.deltaPct != null
                  ? `${Math.abs(gainedKpi.deltaPct).toFixed(1)}% vs anterior`
                  : isPositive ? 'Creciendo' : 'Decreciendo'}
              </span>
            </div>
          </div>
        </div>
        {lost > 0 && (
          <div className="mt-3 flex gap-4 text-xs text-muted-foreground border-t pt-3">
            <span className="text-emerald-600">+{gained.toLocaleString('en-US')} ganados</span>
            <span className="text-red-600">-{lost.toLocaleString('en-US')} perdidos</span>
          </div>
        )}
      </div>
    </div>
  );
}
