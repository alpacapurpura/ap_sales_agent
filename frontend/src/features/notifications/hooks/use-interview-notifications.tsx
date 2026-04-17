"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { Mic } from "lucide-react";
import { useMemo } from "react";

import { getActiveInterview } from "@/features/copilot/api/interview-api";
import { useCopilotStore } from "@/features/copilot/store/copilot-store";

import type { Notification } from "../types";

/**
 *
 */
export function useInterviewNotifications(): Notification[] {
  const { getToken } = useAuth();
  const setInterviewSession = useCopilotStore((s) => s.setInterviewSession);
  const setFocusEntity = useCopilotStore((s) => s.setFocusEntity);
  const setSidebarState = useCopilotStore((s) => s.setSidebarState);
  const setInterviewProgress = useCopilotStore((s) => s.setInterviewProgress);
  const interviewSessionId = useCopilotStore((s) => s.interviewSessionId);

  const { data: active } = useQuery({
    queryKey: ["interview", "active"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) return null;
      return getActiveInterview(token);
    },
    staleTime: 60_000,
  });

  return useMemo(() => {
    if (interviewSessionId) return [];
    if (!active?.bloques_completados) return [];

    const notification: Notification = {
      id: `interview-${active.session_id}`,
      type: "interview",
      title: `Entrevista ${active.domain_label} en pausa`,
      subtitle: `${active.bloques_completados.length}/${active.total_bloques} bloques completados`,
      icon: <Mic className="h-4 w-4 text-purple-500" />,
      severity: "info",
      dismissible: true,
      cta: {
        label: "Continuar",
        onClick: () => {
          setInterviewSession(active.session_id);
          setFocusEntity({
            domain: active.domain as "brand" | "offer" | "buyer_persona",
            label: active.domain_label,
          });
          setInterviewProgress({
            currentBlock: "",
            blocksCompleted: active.bloques_completados,
            totalBlocks: active.total_bloques,
          });
          setSidebarState("expanded");
        },
      },
    };
    return [notification];
  }, [
    active,
    interviewSessionId,
    setInterviewSession,
    setFocusEntity,
    setInterviewProgress,
    setSidebarState,
  ]);
}
