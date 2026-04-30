"use client";

// [COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md
// Wires accept mutation onClick (PR-1 PI-2 S2).

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { useSuggestionAccept } from "../../hooks/use-suggestion-accept";
import { useSuggestions } from "../../hooks/use-suggestions";
import { useCopilotStore } from "../../store/copilot-store";

interface SuggestedChipsProps {
  onChipClick: (prompt: string) => void;
  className?: string;
}

/**
 * Horizontally scrollable suggested action chips.
 * Visible only when there are chips from the real engine.
 * Click: fires accept telemetry mutation (fire-and-forget) then prefills composer.
 */
export function SuggestedChips({ onChipClick, className }: SuggestedChipsProps) {
  const { chips, isLoading } = useSuggestions();
  const accept = useSuggestionAccept();
  const currentRoute = useCopilotStore((s) => s.currentRoute);
  const conversationId = useCopilotStore((s) => s.conversationId);

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
            onClick={() => {
              accept.mutate({ suggestion: chip, conversationId, currentRoute });
              onChipClick(chip.prompt);
            }}
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
