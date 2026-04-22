"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { patchConversation } from "../api/conversations-api";

import type { PatchConversationRequest } from "../types/conversations";

/**
 * Mutation hook to rename or archive a conversation.
 * Invalidates conversation list on settle.
 */
export function usePatchConversation() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, body }: { id: string; body: PatchConversationRequest }) => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      return patchConversation(token, id, body);
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ["copilot", "conversations"] });
    },
  });
}
