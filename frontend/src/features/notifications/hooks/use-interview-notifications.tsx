"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { Mic } from "lucide-react";
import { useMemo } from "react";

import { getActiveInterview } from "@/features/copilot/api/interview-api";
import { useCopilotStore } from "@/features/copilot/store/copilot-store";

import type { Notification } from "../types";

/**
 * Surfaces a "paused interview" notification when the backend reports an
 * unfinished interview for the tenant. Hidden while the user already has
 * an active copilot session; "Continuar" restores the paused interview
 * by installing it as the current session and opening the sidebar.
 */
export function useInterviewNotifications(): Notification[] {
  const { getToken } = useAuth();
  const setSession = useCopilotStore((s) => s.setSession);
  const setSidebarState = useCopilotStore((s) => s.setSidebarState);
  const session = useCopilotStore((s) => s.session);

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
    // Hide the paused-interview notification while a session is running.
    if (session) return [];
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
          setSession({
            sectionKey: `${active.domain}.root`,
            label: active.domain_label,
            entityId: null,
            procedure: "interview",
            sessionId: active.session_id,
            progress: {
              totalBlocks: active.total_bloques,
              blocksCompleted: active.bloques_completados,
            },
            startedAt: new Date(),
            snapshot: {},
          });
          setSidebarState("rail");
        },
      },
    };
    return [notification];
  }, [active, session, setSession, setSidebarState]);
}
