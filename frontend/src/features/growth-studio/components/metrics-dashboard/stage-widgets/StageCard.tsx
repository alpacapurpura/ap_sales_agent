'use client';

import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import { formatMoney } from '@/lib/format-money';
import type { StageSummary } from '../../../types/metrics';

interface StageCardProps {
  stage: StageSummary;
  isActive: boolean;
  onClick: () => void;
  /** When true, renders skeleton shimmer bars instead of KPI values */
  isLoading?: boolean;
  /** When true, data is from mock fallback — renders "datos simulados" badge */
  isMock?: boolean;
}

function formatKpiValue(value: number | string, unit?: string): string {
  if (typeof value === 'string') return value;
  // 3-letter uppercase = ISO currency code (e.g. 'USD', 'MXN', 'PEN')
  if (unit && /^[A-Z]{3}$/.test(unit)) {
    return formatMoney(value, unit, { fractionDigits: 0 });
  }
  // Legacy fallback for unit: '$'
  if (unit === '$') {
    return formatMoney(value, 'USD', { fractionDigits: 0 });
  }
  if (unit === '%') return `${value.toFixed(1)}%`;
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(value >= 10_000 ? 0 : 1)}k`;
  return value.toLocaleString('es-MX');
}

function formatConversionRate(rate: number): string {
  return `${rate.toFixed(1)}% Conversión`;
}

export function StageCard({ stage, isActive, onClick, isLoading = false, isMock = false }: StageCardProps) {
  // Derive secondary KPI display: prefer conversion rate from stage data pattern
  // StageSummary.secondaryKpi carries either conversionRate or another metric
  const secondaryText = stage.secondaryKpi.unit === '%'
    ? formatConversionRate(stage.secondaryKpi.value as number)
    : formatKpiValue(stage.secondaryKpi.value, stage.secondaryKpi.unit);

  return (
    <div
      onClick={onClick}
      className={cn(
        'w-full flex flex-col items-center justify-center p-4 cursor-pointer transition-all duration-300 ease-in-out relative',
        // Default state (Dark base, slightly transparent to show gradient behind)
        !isActive && 'bg-slate-900/95 hover:bg-slate-900/75 dark:bg-slate-950/95 dark:hover:bg-slate-950/75 text-slate-400',
        // Active state (White glass overlay)
        isActive && 'bg-white/15 dark:bg-white/10 backdrop-blur-[4px] text-white'
      )}
    >
      {/* Stage label */}
      <span 
        className={cn(
          "text-[10px] font-semibold uppercase tracking-[0.05em] mb-1 transition-colors duration-300",
          isActive ? "text-white drop-shadow-sm" : "text-slate-400"
        )}
      >
        {stage.label}
      </span>

      {/* Main KPI value */}
      {isLoading ? (
        <div className="space-y-1 w-full flex flex-col items-center">
          <Skeleton className="h-7 w-16 bg-slate-600/50" />
          <Skeleton className="h-3 w-12 bg-slate-600/50" />
        </div>
      ) : (
        <span 
          className={cn(
            "text-2xl font-bold tabular-nums transition-colors duration-300",
            isActive ? "text-white drop-shadow-md" : "text-slate-200"
          )}
        >
          {formatKpiValue(stage.mainKpi.value, stage.mainKpi.unit)}
        </span>
      )}

      {/* Metric Label */}
      {!isLoading && (
        <span 
          className={cn(
            "text-[10px] mt-0.5 transition-colors duration-300",
            isActive ? "text-white/90 font-medium" : "text-slate-500"
          )}
        >
          {stage.mainKpi.label}
        </span>
      )}

      {/* Mock data badge — shown when data is fallback/simulated */}
      {isMock && !isLoading && (
        <Badge
          variant="secondary"
          className="absolute top-1 right-1 text-[8px] px-1 py-0 h-4 bg-slate-800/50 text-slate-400 font-normal border-none"
        >
          simulado
        </Badge>
      )}
    </div>
  );
}
