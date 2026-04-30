"use client";

// [COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md
// Fire-and-forget mutation for SuggestionAccepted telemetry (PR-1 PI-2 S2).

import { useAuth } from "@clerk/nextjs";
import { useMutation } from "@tanstack/react-query";

import { acceptSuggestion } from "../api/suggestions-api";

import type { Suggestion } from "../types/suggestions";

interface AcceptArgs {
  suggestion: Suggestion;
  conversationId: string | null;
  currentRoute: string | null;
}

/**
 * Fire-and-forget producer of SuggestionAccepted telemetry event.
 *
 * NO query invalidation (D-13): accept click does not re-rank chips.
 * Telemetry failure is logged as warning — never surfaces to user.
 */
export function useSuggestionAccept() {
  const { getToken } = useAuth();

  return useMutation({
    mutationFn: async ({ suggestion, conversationId, currentRoute }: AcceptArgs) => {
      const token = await getToken();
      if (!token) return { ok: false };
      return acceptSuggestion(token, {
        suggestion_id: suggestion.id,
        conversation_id: conversationId,
        current_route: currentRoute,
        category: suggestion.category ?? "action",
        source_module: suggestion.source_module ?? "",
        accepted_at: new Date().toISOString(),
      });
    },
    onError: (error) => {
      // Telemetry failure: log but never surface to user
      console.warn("[copilot] suggestion accept telemetry failed", error);
    },
  });
}
