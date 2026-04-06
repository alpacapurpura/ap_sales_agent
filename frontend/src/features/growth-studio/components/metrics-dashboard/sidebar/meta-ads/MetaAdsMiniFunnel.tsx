'use client';

import { cn } from '@/lib/utils';
import type { FunnelStep } from '../../../../types/metrics';

interface MetaAdsMiniFunnelProps {
  steps: FunnelStep[];
}

export function MetaAdsMiniFunnel({ steps }: MetaAdsMiniFunnelProps) {
  if (steps.length === 0) return null;
  const maxValue = Math.max(...steps.map(s => s.value), 1);

  return (
    <div className="space-y-2">
      <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
        Funnel de Conversión
      </h4>
      <div className="space-y-1.5">
        {steps.map((step, i) => (
          <div key={step.metricName} className="space-y-0.5">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">{step.label}</span>
              <div className="flex items-center gap-2">
                <span className="font-medium tabular-nums">
                  {step.value.toLocaleString('en-US')}
                </span>
                {step.conversionRate != null && i > 0 && (
                  <span className="text-muted-foreground">
                    ({step.conversionRate.toFixed(1)}%)
                  </span>
                )}
              </div>
            </div>
            <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
              <div
                className={cn(
                  'h-full rounded-full transition-all',
                  i === 0 ? 'bg-blue-500' : 'bg-blue-500/70',
                )}
                // Inline style required for dynamic percentage width calculation
                style={{ width: `${Math.max((step.value / maxValue) * 100, 2)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
