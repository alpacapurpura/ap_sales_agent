"use client";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { useSuggestions } from "../../hooks/use-suggestions";

interface SuggestedChipsProps {
  onChipClick: (prompt: string) => void;
  className?: string;
}

/**
 * Horizontally scrollable suggested action chips.
 * Visible only when there are no messages (empty conversation).
 * Click prefills the composer textarea.
 */
export function SuggestedChips({ onChipClick, className }: SuggestedChipsProps) {
  const { chips, isLoading } = useSuggestions();

  if (isLoading || chips.length === 0) return null;

  return (
    <div className={cn("relative", className)} aria-label="Sugerencias de preguntas">
      {/* Fade edges */}
      <div
        className="flex gap-2 overflow-x-auto px-1 py-1 scrollbar-hide"
        style={{
          maskImage:
            "linear-gradient(to right, transparent, black 8px, black calc(100% - 8px), transparent)",
          WebkitMaskImage:
            "linear-gradient(to right, transparent, black 8px, black calc(100% - 8px), transparent)",
        }}
      >
        {chips.map((chip) => (
          <Button
            key={chip.id}
            variant="outline"
            size="sm"
            onClick={() => onChipClick(chip.prompt)}
            className="shrink-0 rounded-full text-xs whitespace-nowrap h-7 px-3"
            type="button"
          >
            {chip.label}
          </Button>
        ))}
      </div>
    </div>
  );
}

SuggestedChips.displayName = "SuggestedChips";
