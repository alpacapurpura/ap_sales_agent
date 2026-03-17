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
import type { StageSummary } from '../../types/metrics';

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
  if (unit === '$') {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
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
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Card
            onClick={onClick}
            className={cn(
              'relative flex flex-col items-center justify-center p-4 min-w-[120px] cursor-pointer',
              'transition-all duration-150 ease-out select-none snap-center',
              'bg-[#1e293b] border-[#1e293b] rounded-lg shadow-sm',
              'hover:scale-[1.02]',
              isActive
                ? 'ring-2 ring-primary/50 shadow-md'
                : 'hover:ring-1 hover:ring-slate-500/50 hover:shadow-md'
            )}
          >
            {/* Stage label */}
            <span className="text-xs font-medium text-slate-400 uppercase tracking-[0.6px]">
              {stage.label}
            </span>

            {/* Main KPI value */}
            {isLoading ? (
              <div className="mt-1 space-y-1 w-full flex flex-col items-center">
                <Skeleton className="h-7 w-16 bg-slate-600" />
                <Skeleton className="h-3 w-12 bg-slate-600" />
              </div>
            ) : (
              <>
                <span className="text-2xl font-bold mt-1 tabular-nums text-slate-50">
                  {formatKpiValue(stage.mainKpi.value, stage.mainKpi.unit)}
                </span>
                <span className="text-xs text-slate-400 mt-0.5">
                  {stage.mainKpi.label}
                </span>
              </>
            )}

            {/* Secondary KPI: conversion pill */}
            {!isLoading && (
              <div className="text-[8px] text-slate-800/70 bg-white px-2.5 py-0.5 rounded-full mt-2 tabular-nums font-medium">
                {secondaryText}
              </div>
            )}

            {/* Detail indicator when active */}
            {stage.hasDetail && isActive && !isLoading && (
              <span className="text-[10px] text-primary mt-1 font-medium">
                ▼ detalle
              </span>
            )}

            {/* Mock data badge — shown when data is fallback/simulated */}
            {isMock && !isLoading && (
              <Badge
                variant="secondary"
                className="absolute top-1 right-1 text-[8px] px-1 py-0 h-4 bg-slate-700 text-slate-300 font-normal"
              >
                datos simulados
              </Badge>
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
