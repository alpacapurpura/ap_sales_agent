"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { fetchConversationDetail } from "../api";

export function useConversationDetail(leadId: string | null) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: ["closer-studio", "detail", leadId],
    queryFn: async () => {
      if (!leadId) return null;
      const token = (await getToken()) ?? "";
      return fetchConversationDetail(token, leadId);
    },
    enabled: !!leadId,
    staleTime: 5_000,
  });
}
