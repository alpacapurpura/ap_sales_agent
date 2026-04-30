"use client";

// [COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md
// Real engine hook — React Query consuming POST /api/v1/copilot/suggestions.
// Replaces the ROUTE_SUGGESTIONS static stub (PR-1 PI-2 S2).

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";

import { fetchSuggestions } from "../api/suggestions-api";
import { useCopilotStore } from "../store/copilot-store";

import type { Suggestion } from "../types/suggestions";

export interface UseSuggestionsReturn {
  chips: Suggestion[];
  isLoading: boolean;
  refetch: () => void;
}

/**
 * Smart-chips dinámicas desde BE engine.
 *
 * Cache 5min staleTime — chips son route-scoped y raramente cambian (D-12).
 * Best-effort: retorna [] en error de engine o sin token (D-10).
 * Fire-and-forget accept: ver useSuggestionAccept hook (D-13).
 */
export function useSuggestions(): UseSuggestionsReturn {
  const { getToken } = useAuth();
  const currentRoute = useCopilotStore((s) => s.currentRoute);
  const conversationId = useCopilotStore((s) => s.conversationId);

  const query = useQuery({
    queryKey: ["copilot", "suggestions", currentRoute, conversationId],
    staleTime: 5 * 60 * 1000, // 5 min (D-12)
    gcTime: 10 * 60 * 1000, // 10 min
    retry: false, // best-effort — engine ya retorna [] internamente (D-10)
    queryFn: async () => {
      const token = await getToken();
      if (!token) return { suggestions: [] as Suggestion[] };
      const response = await fetchSuggestions(token, {
        current_route: currentRoute,
        conversation_id: conversationId,
        recent_message_ids: [],
        incomplete_fields: [],
      });
      return { suggestions: response.suggestions };
    },
  });

  return {
    chips: query.data?.suggestions ?? [],
    isLoading: query.isLoading,
    refetch: () => void query.refetch(),
  };
}
