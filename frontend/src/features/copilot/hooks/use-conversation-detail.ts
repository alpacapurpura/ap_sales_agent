"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";

import { getConversation } from "../api/conversations-api";

import type { ConversationDetail } from "../types/conversations";

/**
 * Load a single conversation (summary + decoded messages).
 * Returns the React Query result so callers can gate hydration on
 * `data`, surface `isLoading`, and retry on `isError`.
 *
 * The query is keyed by conversation id and auto-disabled when id is null,
 * so the hook is safe to call unconditionally at component top level.
 */
export function useConversationDetail(conversationId: string | null) {
  const { getToken } = useAuth();

  return useQuery<ConversationDetail>({
    queryKey: ["copilot", "conversation", conversationId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      if (!conversationId) throw new Error("conversationId required");
      return getConversation(token, conversationId);
    },
    enabled: Boolean(conversationId),
    // Messages in a conversation are append-only on the server; we only
    // refetch on id change or when the server tells us (invalidate).
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}
