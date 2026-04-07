"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { toast } from "sonner";
import { stopAI, resumeAI, sendMessage, nudge, reactivate, diagnose } from "../api";
import type { ConversationDetail, InputMode } from "../types";

export function useConversationActions(leadId: string | null) {
  const { getToken } = useAuth();
  const qc = useQueryClient();

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["closer-studio"] });
  };

  const detailKey = ["closer-studio", "detail", leadId];

  const stop = useMutation({
    mutationFn: async () => {
      if (!leadId) throw new Error("No lead selected");
      const token = (await getToken()) ?? "";
      return stopAI(token, leadId);
    },
    onMutate: async () => {
      await qc.cancelQueries({ queryKey: detailKey });
      const previous = qc.getQueryData<ConversationDetail>(detailKey);
      if (previous) {
        qc.setQueryData<ConversationDetail>(detailKey, {
          ...previous,
          handler_mode: "human",
          paused_at: new Date().toISOString(),
        });
      }
      return { previous };
    },
    onSuccess: () => {
      toast.success("AI detenido — tienes el control");
      invalidate();
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        qc.setQueryData(detailKey, context.previous);
      }
      toast.error("Error al detener el AI");
    },
  });

  const resume = useMutation({
    mutationFn: async (objective: string | undefined) => {
      if (!leadId) throw new Error("No lead selected");
      const token = (await getToken()) ?? "";
      return resumeAI(token, leadId, objective);
    },
    onMutate: async () => {
      await qc.cancelQueries({ queryKey: detailKey });
      const previous = qc.getQueryData<ConversationDetail>(detailKey);
      if (previous) {
        qc.setQueryData<ConversationDetail>(detailKey, {
          ...previous,
          handler_mode: "ai",
          paused_at: null,
        });
      }
      return { previous };
    },
    onSuccess: () => {
      toast.success("AI reanudado");
      invalidate();
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        qc.setQueryData(detailKey, context.previous);
      }
      toast.error("Error al reanudar el AI");
    },
  });

  const send = useMutation({
    mutationFn: async ({ content, mode }: { content: string; mode: InputMode }) => {
      if (!leadId) throw new Error("No lead selected");
      const token = (await getToken()) ?? "";
      return sendMessage(token, leadId, content, mode);
    },
    onSuccess: invalidate,
    onError: () => {
      toast.error("Error al enviar mensaje");
    },
  });

  const nudgeAction = useMutation({
    mutationFn: async (context: string | undefined) => {
      if (!leadId) throw new Error("No lead selected");
      const token = (await getToken()) ?? "";
      return nudge(token, leadId, context);
    },
    onSuccess: () => {
      toast.success("Nudge enviado");
      invalidate();
    },
    onError: () => {
      toast.error("Error al enviar nudge");
    },
  });

  const reactivateAction = useMutation({
    mutationFn: async (objective: string | undefined) => {
      if (!leadId) throw new Error("No lead selected");
      const token = (await getToken()) ?? "";
      return reactivate(token, leadId, objective);
    },
    onSuccess: () => {
      toast.success("Conversación reactivada");
      invalidate();
    },
    onError: () => {
      toast.error("Error al reactivar conversación");
    },
  });

  const diagnoseAction = useMutation({
    mutationFn: async () => {
      if (!leadId) throw new Error("No lead selected");
      const token = (await getToken()) ?? "";
      return diagnose(token, leadId);
    },
    onSuccess: invalidate,
    onError: () => {
      toast.error("Error al diagnosticar");
    },
  });

  return { stop, resume, send, nudge: nudgeAction, reactivate: reactivateAction, diagnose: diagnoseAction };
}
