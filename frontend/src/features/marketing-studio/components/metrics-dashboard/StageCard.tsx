'use client';

import { Card } from '@/components/ui/card';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import type { StageSummary } from '../../types/metrics';

interface StageCardProps {
  stage: StageSummary;
  isActive: boolean;
  onClick: () => void;
}

function formatKpiValue(value: number, unit?: string): string {
  if (unit === '$') return `$${value.toLocaleString()}`;
  if (unit === '%') return `${value}%`;
  if (value >= 1000) return `${(value / 1000).toFixed(value >= 10000 ? 0 : 1)}k`;
  return value.toLocaleString();
}

export function StageCard({ stage, isActive, onClick }: StageCardProps) {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Card
            onClick={onClick}
            className={cn(
              'flex flex-col items-center justify-center p-4 min-w-[120px] cursor-pointer transition-all select-none snap-center',
              isActive
                ? 'border-primary ring-2 ring-primary/20 shadow-md'
                : 'hover:border-primary/50 hover:shadow-sm'
            )}
          >
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              {stage.label}
            </span>
            <span className="text-2xl font-bold mt-1 tabular-nums">
              {formatKpiValue(stage.mainKpi.value, stage.mainKpi.unit)}
            </span>
            <span className="text-xs text-muted-foreground mt-0.5">
              {stage.mainKpi.label}
            </span>
            {stage.hasDetail && isActive && (
              <span className="text-[10px] text-primary mt-1 font-medium">
                ▼ detalle
              </span>
            )}
          </Card>
        </TooltipTrigger>
        <TooltipContent>
          <p>{stage.description}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
