"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { createConversation } from "../api/conversations-api";
import { useCopilotStore } from "../store/copilot-store";

/**
 * Mutation hook to create a new conversation.
 * - Optimistically prepends a placeholder to the list.
 * - On success: sets conversationId in store, clears messages, focuses input.
 * - Invalidates conversation list on settle.
 */
export function useCreateConversation() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  const setConversationId = useCopilotStore((s) => s.setConversationId);
  const clearMessages = useCopilotStore((s) => s.clearMessages);
  const setSidebarState = useCopilotStore((s) => s.setSidebarState);
  const sidebarState = useCopilotStore((s) => s.sidebarState);

  return useMutation({
    mutationFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      return createConversation(token);
    },
    onSuccess: (conversation) => {
      setConversationId(conversation.id);
      clearMessages();

      // Open chat if sidebar is collapsed
      if (sidebarState === "collapsed") {
        setSidebarState("rail");
      }

      // Focus input after state update
      setTimeout(() => {
        const input = document.getElementById("copilot-input");
        if (input) {
          input.focus();
        }
      }, 50);
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ["copilot", "conversations"] });
    },
  });
}
