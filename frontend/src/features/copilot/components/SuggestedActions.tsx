"use client";

// [COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md
// Drops ROUTE_SUGGESTIONS static map — consumes real engine via useSuggestions (PR-1 PI-2 S2).

import { Lightbulb } from "lucide-react";

import { Button } from "@/components/ui/button";

import { useCopilotChat } from "../hooks/use-copilot-chat";
import { useSuggestionAccept } from "../hooks/use-suggestion-accept";
import { useSuggestions } from "../hooks/use-suggestions";
import { useCopilotStore } from "../store/copilot-store";

import type { Suggestion } from "../types/suggestions";

/**
 * Route-aware quick actions shown when the copilot chat is empty.
 * Consumes the real suggestions engine (no static ROUTE_SUGGESTIONS map).
 * Clicking a chip fires the SuggestionAccepted telemetry event then sends
 * the prompt to the chat.
 */
export function SuggestedActions() {
  const { chips } = useSuggestions();
  const accept = useSuggestionAccept();
  const currentRoute = useCopilotStore((s) => s.currentRoute);
  const conversationId = useCopilotStore((s) => s.conversationId);
  const messages = useCopilotStore((s) => s.messages);
  const { sendMessage } = useCopilotChat();

  // Only show when chat is empty
  if (messages.length > 0) return null;

  if (chips.length === 0) return null;

  const handleClick = (chip: Suggestion) => {
    accept.mutate({ suggestion: chip, conversationId, currentRoute });
    void sendMessage(chip.prompt);
  };

  return (
    <div className="space-y-2 px-4 pb-2" data-testid="suggested-actions">
      <div className="flex items-center gap-1.5 text-xs text-slate-400">
        <Lightbulb className="h-3 w-3" />
        <span>Sugerencias</span>
      </div>
      <div className="flex flex-col gap-1.5">
        {chips.map((chip) => (
          <Button
            key={chip.id}
            variant="outline"
            size="sm"
            onClick={() => handleClick(chip)}
            className="h-auto justify-start whitespace-normal rounded-lg px-3 py-2 text-left text-xs font-normal text-slate-600 hover:bg-purple-50 hover:text-purple-700 dark:text-slate-300 dark:hover:bg-purple-900/20"
          >
            {chip.label}
          </Button>
        ))}
      </div>
    </div>
  );
}
