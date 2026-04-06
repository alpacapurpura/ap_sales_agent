'use client';

import { AlertTriangle } from 'lucide-react';

import { cn } from '@/lib/utils';
import type { FrequencyAlert, MetricKpiData } from '../../../../types/metrics';

interface ReachFrequencySectionProps {
  kpis: MetricKpiData[];
  frequencyAlert: FrequencyAlert | null;
}

export function ReachFrequencySection({ kpis, frequencyAlert }: ReachFrequencySectionProps) {
  const reach = kpis.find(k => k.metricName === 'reach');
  const frequency = kpis.find(k => k.metricName === 'frequency');

  if (!reach && !frequency) return null;

  return (
    <div className="space-y-2">
      <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
        Alcance y Frecuencia
      </h4>
      <div className="grid grid-cols-2 gap-3">
        {reach && (
          <div className="rounded-lg border bg-card p-3 space-y-1">
            <p className="text-xs text-muted-foreground">Alcance</p>
            <p className="text-lg font-semibold tabular-nums">
              {reach.currentValue.toLocaleString('en-US')}
            </p>
            <p className="text-[10px] text-muted-foreground">
              Personas unicas -- no es suma diaria
            </p>
          </div>
        )}
        {frequency && (
          <div className="rounded-lg border bg-card p-3 space-y-1">
            <p className="text-xs text-muted-foreground">Frecuencia</p>
            <p className="text-lg font-semibold tabular-nums">
              {frequency.currentValue.toFixed(2)}x
            </p>
            {frequencyAlert && (
              <div
                className={cn(
                  'flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] font-medium',
                  frequencyAlert.severity === 'critical'
                    ? 'bg-red-500/10 text-red-600'
                    : 'bg-amber-500/10 text-amber-600',
                )}
              >
                <AlertTriangle className="h-3 w-3" />
                {frequencyAlert.message}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
