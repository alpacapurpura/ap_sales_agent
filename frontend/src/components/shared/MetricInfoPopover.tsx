"use client";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils";

interface MetricInfoPopoverProps {
  displayName: string;
  description: string;
  formula?: string;
  benchmark?: {
    value: number;
    source?: string;
  };
  interpretation?: string;
  higherIsBetter?: boolean;
  children: React.ReactNode;
  className?: string;
}

export function MetricInfoPopover({
  displayName,
  description,
  formula,
  benchmark,
  interpretation,
  children,
  className,
}: MetricInfoPopoverProps) {
  return (
    <span className={cn("inline-flex items-center gap-1", className)}>
      {children}
      <Popover>
        <PopoverTrigger asChild>
          <button
            type="button"
            aria-label="info"
            className="inline-flex h-3.5 w-3.5 items-center justify-center rounded-full border border-muted-foreground/30 text-[9px] text-muted-foreground/60 hover:border-muted-foreground/60 hover:text-muted-foreground transition-colors"
          >
            i
          </button>
        </PopoverTrigger>
        <PopoverContent side="top" align="start" className="w-72 p-3 text-sm">
          <div className="space-y-2">
            <p className="font-semibold text-foreground">{displayName}</p>
            <p className="text-xs text-muted-foreground">{description}</p>
            {formula && (
              <code className="block rounded bg-muted px-2 py-1 text-xs font-mono text-muted-foreground">
                {formula}
              </code>
            )}
            {benchmark && (
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Benchmark industria:</span>
                <span className="font-semibold text-emerald-500">
                  {benchmark.value}
                  {benchmark.source && (
                    <span className="ml-1 text-muted-foreground/50">({benchmark.source})</span>
                  )}
                </span>
              </div>
            )}
            {interpretation && (
              <p className="text-xs text-muted-foreground/80 italic">{interpretation}</p>
            )}
          </div>
        </PopoverContent>
      </Popover>
    </span>
  );
}
