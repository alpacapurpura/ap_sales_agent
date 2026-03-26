'use client';

import { Info } from 'lucide-react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface KpiTooltipProps {
  label: string;
  hint: string;
}

export function KpiTooltip({ label, hint }: KpiTooltipProps) {
  return (
    <TooltipProvider delayDuration={200}>
      <div className="flex items-center gap-1">
        <span className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</span>
        <Tooltip>
          <TooltipTrigger asChild>
            <Info className="h-3 w-3 text-muted-foreground cursor-help" />
          </TooltipTrigger>
          <TooltipContent className="max-w-[240px] text-xs">
            {hint}
          </TooltipContent>
        </Tooltip>
      </div>
    </TooltipProvider>
  );
}
