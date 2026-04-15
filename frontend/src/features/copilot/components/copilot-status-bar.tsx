"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";

import { getActiveInterview } from "../api/interview-api";
import { useCopilotStore } from "../store/copilot-store";

export function CopilotStatusBar() {
  const interviewSessionId = useCopilotStore((s) => s.interviewSessionId);
  const sidebarState = useCopilotStore((s) => s.sidebarState);
  const setInterviewSession = useCopilotStore((s) => s.setInterviewSession);
  const setFocusEntity = useCopilotStore((s) => s.setFocusEntity);
  const setSidebarState = useCopilotStore((s) => s.setSidebarState);
  const setInterviewProgress = useCopilotStore((s) => s.setInterviewProgress);
  const { getToken } = useAuth();

  const { data: active } = useQuery({
    queryKey: ["interview", "active"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) return null;
      return getActiveInterview(token);
    },
    staleTime: 60_000,
  });

  // Don't show if interview already active in sidebar
  if (interviewSessionId) return null;
  // Don't show if sidebar expanded (user in focus)
  if (sidebarState === "expanded") return null;
  // Don't show if no paused interview
  if (!active?.bloques_completados) return null;

  const handleContinue = () => {
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
  };

  return (
    <div className="mx-4 mt-2 flex items-center justify-between rounded-lg border border-purple-500 bg-[#1e1b4b] px-4 py-2.5">
      <div className="flex items-center gap-3">
        <div className="h-2 w-2 animate-pulse rounded-full bg-purple-500" />
        <span className="text-sm text-white">Entrevista {active.domain_label} en curso</span>
        <span className="text-xs text-gray-400">
          ({active.bloques_completados.length}/{active.total_bloques} bloques)
        </span>
      </div>
      <Button
        size="sm"
        onClick={handleContinue}
        className="bg-purple-600 text-xs text-white hover:bg-purple-700"
      >
        Continuar →
      </Button>
    </div>
  );
}
