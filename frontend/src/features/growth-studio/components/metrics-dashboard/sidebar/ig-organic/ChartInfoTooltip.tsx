'use client';

import { Info } from 'lucide-react';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';

interface ChartInfoTooltipProps {
  title: string;
  description: string;
}

export function ChartInfoTooltip({ title, description }: ChartInfoTooltipProps) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          type="button"
          className="inline-flex items-center gap-1 text-sm font-medium hover:text-foreground"
        >
          {title}
          <Info className="h-3.5 w-3.5 text-muted-foreground" />
        </button>
      </PopoverTrigger>
      <PopoverContent className="max-w-[280px] text-xs" side="top">
        {description}
      </PopoverContent>
    </Popover>
  );
}
