"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { stopAI, resumeAI, sendMessage, nudge, reactivate, diagnose } from "../api";
import type { InputMode } from "../types";

export function useConversationActions(leadId: string | null) {
  const { getToken } = useAuth();
  const qc = useQueryClient();

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["closer-studio"] });
  };

  const stop = useMutation({
    mutationFn: async () => {
      if (!leadId) throw new Error("No lead selected");
      const token = (await getToken()) ?? "";
      return stopAI(token, leadId);
    },
    onSuccess: invalidate,
  });

  const resume = useMutation({
    mutationFn: async (objective: string | undefined) => {
      if (!leadId) throw new Error("No lead selected");
      const token = (await getToken()) ?? "";
      return resumeAI(token, leadId, objective);
    },
    onSuccess: invalidate,
  });

  const send = useMutation({
    mutationFn: async ({ content, mode }: { content: string; mode: InputMode }) => {
      if (!leadId) throw new Error("No lead selected");
      const token = (await getToken()) ?? "";
      return sendMessage(token, leadId, content, mode);
    },
    onSuccess: invalidate,
  });

  const nudgeAction = useMutation({
    mutationFn: async (context: string | undefined) => {
      if (!leadId) throw new Error("No lead selected");
      const token = (await getToken()) ?? "";
      return nudge(token, leadId, context);
    },
    onSuccess: invalidate,
  });

  const reactivateAction = useMutation({
    mutationFn: async (objective: string | undefined) => {
      if (!leadId) throw new Error("No lead selected");
      const token = (await getToken()) ?? "";
      return reactivate(token, leadId, objective);
    },
    onSuccess: invalidate,
  });

  const diagnoseAction = useMutation({
    mutationFn: async () => {
      if (!leadId) throw new Error("No lead selected");
      const token = (await getToken()) ?? "";
      return diagnose(token, leadId);
    },
    onSuccess: invalidate,
  });

  return { stop, resume, send, nudge: nudgeAction, reactivate: reactivateAction, diagnose: diagnoseAction };
}
