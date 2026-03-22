'use client';

import { Badge } from '@/components/ui/badge';
import type { StageSummary } from '../../../types/metrics';

interface PlaceholderDetailProps {
  stage: StageSummary;
}

function formatKpiValue(value: number | string, unit?: string): string {
  if (typeof value === 'string') return value;
  if (unit === '$') return `$${value.toLocaleString()}`;
  if (unit === '%') return `${value}%`;
  if (value >= 1000) return `${(value / 1000).toFixed(value >= 10000 ? 0 : 1)}k`;
  return value.toLocaleString();
}

export function PlaceholderDetail({ stage }: PlaceholderDetailProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 gap-4 text-center">
      <Badge variant="secondary" className="text-xs">
        Próximamente
      </Badge>
      <div>
        <h4 className="text-lg font-semibold">{stage.label}</h4>
        <p className="text-sm text-muted-foreground mt-1 max-w-md">
          {stage.description}
        </p>
      </div>
      <div className="flex gap-8 mt-2">
        <div className="text-center">
          <p className="text-2xl font-bold tabular-nums">
            {formatKpiValue(stage.mainKpi.value, stage.mainKpi.unit)}
          </p>
          <p className="text-xs text-muted-foreground">{stage.mainKpi.label}</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold tabular-nums">
            {formatKpiValue(stage.secondaryKpi.value, stage.secondaryKpi.unit)}
          </p>
          <p className="text-xs text-muted-foreground">{stage.secondaryKpi.label}</p>
        </div>
      </div>
      <p className="text-xs text-muted-foreground mt-4">
        Los datos detallados de esta etapa estarán disponibles pronto.
      </p>
    </div>
  );
}
