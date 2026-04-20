"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";

import { fetchConversations } from "../api";
import { useCloserStore } from "../store/closer-store";

/**
 *
 */
export function useConversations() {
  const { getToken } = useAuth();
  const filters = useCloserStore((s) => s.filters);

  return useQuery({
    queryKey: ["closer-studio", "conversations", filters],
    queryFn: async () => {
      const token = (await getToken()) ?? "";
      return fetchConversations(token, filters);
    },
    refetchInterval: 30_000,
    staleTime: 10_000,
  });
}
