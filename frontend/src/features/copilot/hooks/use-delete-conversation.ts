"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { deleteConversation } from "../api/conversations-api";
import { useCopilotStore } from "../store/copilot-store";

/**
 * Mutation hook to archive (soft-delete) a conversation.
 * - Optimistic: removes from local list immediately.
 * - Invalidates list on settle.
 */
export function useDeleteConversation() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  const conversationId = useCopilotStore((s) => s.conversationId);
  const resetConversation = useCopilotStore((s) => s.resetConversation);

  return useMutation({
    mutationFn: async (id: string) => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      return deleteConversation(token, id);
    },
    onSuccess: (_, deletedId) => {
      // If the deleted conversation is currently active, drop both id and messages
      if (conversationId === deletedId) {
        resetConversation();
      }
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ["copilot", "conversations"] });
    },
  });
}
