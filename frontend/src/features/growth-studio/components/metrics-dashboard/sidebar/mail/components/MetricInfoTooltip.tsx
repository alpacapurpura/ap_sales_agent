'use client';

import { Info } from 'lucide-react';

import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import type { MetricInfo } from '../../../../../utils/automation-metric-info';

interface MetricInfoTooltipProps {
  info: MetricInfo;
  iconSize?: 'xs' | 'sm';
  side?: 'top' | 'bottom' | 'left' | 'right';
  className?: string;
}

/**
 * Reusable info tooltip (ⓘ) showing title, description, formula, and
 * interpretation thresholds (good/mid/bad).
 *
 * Used on every metric in the Automations UI: table headers, KPI cards,
 * pipeline nodes, and sidebar metric boxes.
 */
export function MetricInfoTooltip({
  info,
  iconSize = 'sm',
  side = 'top',
  className,
}: MetricInfoTooltipProps) {
  const iconClass = iconSize === 'xs' ? 'h-2.5 w-2.5' : 'h-3 w-3';

  return (
    <TooltipProvider delayDuration={150}>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            type="button"
            onClick={(e) => e.stopPropagation()}
            className={cn(
              'inline-flex items-center justify-center rounded-full text-muted-foreground/60 hover:text-primary transition-colors cursor-help align-middle',
              className,
            )}
            aria-label={`Información sobre ${info.title}`}
          >
            <Info className={iconClass} />
          </button>
        </TooltipTrigger>
        <TooltipContent side={side} className="max-w-[260px] p-3">
          <div className="space-y-1.5">
            <p className="font-semibold text-xs">{info.title}</p>
            <p className="text-[11px] text-muted-foreground leading-relaxed">
              {info.description}
            </p>
            {info.formula && (
              <p className="text-[10px] font-mono bg-primary/10 text-primary rounded px-2 py-1">
                {info.formula}
              </p>
            )}
            {info.interpret &&
              (info.interpret.good ||
                info.interpret.mid ||
                info.interpret.bad) && (
                <div className="text-[10px] border-t border-border pt-1.5 space-y-0.5">
                  {info.interpret.good && (
                    <p>
                      <span className="font-semibold text-emerald-500">✓</span>{' '}
                      {info.interpret.good}
                    </p>
                  )}
                  {info.interpret.mid && (
                    <p>
                      <span className="font-semibold text-amber-500">~</span>{' '}
                      {info.interpret.mid}
                    </p>
                  )}
                  {info.interpret.bad && (
                    <p>
                      <span className="font-semibold text-red-500">✗</span>{' '}
                      {info.interpret.bad}
                    </p>
                  )}
                </div>
              )}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
