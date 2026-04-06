'use client';

import { TrendingDown, TrendingUp, Users } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { MetricKpiData } from '../../../../types/metrics';

interface MailListGrowthIndicatorProps {
  kpis: MetricKpiData[];
}

export function MailListGrowthIndicator({ kpis }: MailListGrowthIndicatorProps) {
  const subscribersKpi = kpis.find(k => k.metricName === 'active_subscribers');
  const newSubsKpi = kpis.find(k => k.metricName === 'new_subscribers');

  const displayKpi = newSubsKpi ?? subscribersKpi;
  if (!displayKpi) return null;

  const value = displayKpi.currentValue;
  const isPositive = value >= 0;
  const label = newSubsKpi ? 'Nuevos suscriptores (periodo)' : 'Suscriptores activos';

  return (
    <div className="space-y-2">
      <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
        Crecimiento de Lista
      </h4>
      <div className="rounded-lg border bg-card p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-amber-500/10">
            <Users className="h-5 w-5 text-amber-500" />
          </div>
          <div className="flex-1">
            <p className="text-sm text-muted-foreground">{label}</p>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-semibold tabular-nums">
                {newSubsKpi ? (isPositive ? '+' : '') : ''}{value.toLocaleString('en-US')}
              </span>
              {displayKpi.deltaPct != null && (
                <span
                  className={cn(
                    'inline-flex items-center gap-0.5 text-xs font-medium',
                    displayKpi.deltaPct >= 0 ? 'text-emerald-600' : 'text-red-600',
                  )}
                >
                  {displayKpi.deltaPct >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                  {Math.abs(displayKpi.deltaPct).toFixed(1)}% vs anterior
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
