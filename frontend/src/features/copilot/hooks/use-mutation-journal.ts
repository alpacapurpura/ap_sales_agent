"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";

import { fetchMutationJournal } from "../api/mutation-journal-api";

import type { MutationJournalResponse } from "../api/mutation-journal-api";

/**
 * Query hook for the mutation journal of a conversation.
 * Used to determine if the MutationUndoButton should be visible.
 * Note: endpoint path is TBD per UI-SPEC §15 — returns empty on 404.
 */
export function useMutationJournal(conversationId: string | null) {
  const { getToken, isLoaded, isSignedIn } = useAuth();

  return useQuery({
    queryKey: ["copilot", "mutation-journal", conversationId],
    queryFn: async (): Promise<MutationJournalResponse> => {
      if (!conversationId) return { entries: [], activeCount: 0 };

      const token = await getToken();
      if (!token) throw new Error("Not authenticated");

      return fetchMutationJournal(token, conversationId);
    },
    staleTime: 10_000,
    enabled: isLoaded && isSignedIn === true && conversationId !== null,
  });
}
