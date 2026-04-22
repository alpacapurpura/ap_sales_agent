"use client";

import { useAuth } from "@clerk/nextjs";
import { useInfiniteQuery } from "@tanstack/react-query";

import { listConversations } from "../api/conversations-api";

interface UseConversationListParams {
  limit?: number;
  includeArchived?: boolean;
}

/**
 * Infinite query hook for paginated conversation history.
 * staleTime: 30s (frequent background updates expected).
 */
export function useConversationList({
  limit = 6,
  includeArchived = false,
}: UseConversationListParams = {}) {
  const { getToken, isLoaded, isSignedIn } = useAuth();

  return useInfiniteQuery({
    queryKey: ["copilot", "conversations", { limit, includeArchived }],
    queryFn: async ({ pageParam }) => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      return listConversations(token, {
        limit,
        cursor: pageParam,
        includeArchived,
      });
    },
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => lastPage.nextCursor ?? undefined,
    staleTime: 30_000,
    enabled: isLoaded && isSignedIn === true,
  });
}
