"use client";

import { cn } from "@/lib/utils";
import { Check, Info } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface Option {
  value: string;
  label: string;
  description?: string;
  icon?: React.ReactNode;
}

interface RichEnumSelectProps {
  options: Option[];
  value: string;
  onChange: (value: string) => void;
  className?: string;
}

export function RichEnumSelect({ options, value, onChange, className }: RichEnumSelectProps) {
  return (
    <div className={cn("grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3", className)}>
      {options.map((option) => {
        const isSelected = value === option.value;
        return (
          <div
            key={option.value}
            onClick={() => onChange(option.value)}
            className={cn(
              "cursor-pointer rounded-lg border p-4 transition-all hover:bg-accent",
              isSelected
                ? "border-primary bg-primary/5 ring-1 ring-primary"
                : "border-muted bg-card hover:border-primary/50"
            )}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2">
                {option.icon}
                <span className="font-medium text-sm">{option.label}</span>
              </div>
              {isSelected && <Check className="h-4 w-4 text-primary" />}
            </div>
            {option.description && (
              <p className="mt-2 text-xs text-muted-foreground line-clamp-2">
                {option.description}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}
