"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";

import { revertMutations } from "../api/conversations-api";
import { useCopilotStore } from "../store/copilot-store";

import type { RevertRequest } from "../types/conversations";

/**
 * Mutation hook to revert applied mutations in a conversation.
 * On success: shows toast + clears messages so history re-syncs.
 * On error: shows error toast.
 */
export function useRevertMutations(conversationId: string) {
  const { getToken } = useAuth();
  const clearMessages = useCopilotStore((s) => s.clearMessages);
  const activeBridge = useCopilotStore((s) => s.activeBridge);

  return useMutation({
    mutationFn: async (body: RevertRequest = {}) => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      return revertMutations(token, conversationId, body);
    },
    onSuccess: (result) => {
      toast.success(`Se revirtieron ${result.revertedCount} cambios.`);
      clearMessages();
      // If a form bridge is mounted, trigger a re-read of its snapshot so
      // reverted values propagate back into the UI. The bridge publishes
      // snapshot changes via its internal subscriber list.
      activeBridge?.getSnapshot?.();
    },
    onError: () => {
      toast.error("No se pudieron deshacer los cambios. Intenta de nuevo.");
    },
  });
}
