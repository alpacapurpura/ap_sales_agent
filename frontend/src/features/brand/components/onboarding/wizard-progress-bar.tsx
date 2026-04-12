"use client";

import { cn } from "@/lib/utils";

interface WizardProgressBarProps {
  currentIndex: number;
  totalSteps: number;
  labels?: string[];
}

export function WizardProgressBar({ currentIndex, totalSteps, labels }: WizardProgressBarProps) {
  return (
    <div className="flex items-center justify-center gap-2 py-4">
      {Array.from({ length: totalSteps }).map((_, i) => (
        <div key={i} className="flex items-center gap-2">
          <div
            className={cn(
              "flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold transition-all",
              i < currentIndex && "bg-primary text-primary-foreground",
              i === currentIndex && "bg-primary text-primary-foreground ring-4 ring-primary/20",
              i > currentIndex && "border-2 border-muted-foreground/30 text-muted-foreground"
            )}
          >
            {i < currentIndex ? "✓" : i + 1}
          </div>
          {labels?.[i] && (
            <span
              className={cn(
                "hidden text-xs font-medium sm:inline",
                i <= currentIndex ? "text-foreground" : "text-muted-foreground"
              )}
            >
              {labels[i]}
            </span>
          )}
          {i < totalSteps - 1 && (
            <div
              className={cn(
                "h-0.5 w-8 transition-colors",
                i < currentIndex ? "bg-primary" : "bg-muted-foreground/30"
              )}
            />
          )}
        </div>
      ))}
    </div>
  );
}
