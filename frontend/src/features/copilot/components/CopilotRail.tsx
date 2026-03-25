"use client";

import { MessageCircle, Sparkles } from "lucide-react";
import { useAuth } from "@clerk/nextjs";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { useCopilotStore } from "../store/copilot-store";
import { useProactiveNudges } from "../hooks/useProactiveNudges";
import { reportCopilotEvent } from "../api/copilot-api";

export function CopilotRail() {
  const { openPanel, messages } = useCopilotStore();
  const { nudges } = useProactiveNudges();
  const { getToken } = useAuth();
  const hasMessages = messages.length > 0;
  const hasNudges = nudges.length > 0;

  const handleOpen = () => {
    openPanel();
    getToken().then((token) => {
      if (token) {
        reportCopilotEvent("copilot_opened", {}, token);
      }
    });
  };

  return (
    <div className="flex h-full w-[60px] flex-col items-center border-l border-slate-200 bg-white py-4 dark:border-slate-700 dark:bg-slate-900">
      <TooltipProvider delayDuration={200}>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              size="icon"
              variant="ghost"
              onClick={handleOpen}
              className="relative h-10 w-10 rounded-xl text-purple-600 hover:bg-purple-50 dark:text-purple-400 dark:hover:bg-purple-900/30"
            >
              <Sparkles className="h-5 w-5" />
              {hasMessages && (
                <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-purple-500" />
              )}
              {!hasMessages && hasNudges && (
                <span className="absolute right-1.5 top-1.5 h-2 w-2 animate-pulse rounded-full bg-amber-500" />
              )}
            </Button>
          </TooltipTrigger>
          <TooltipContent side="left">Copilot</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              size="icon"
              variant="ghost"
              onClick={handleOpen}
              className="mt-2 h-10 w-10 rounded-xl text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800"
            >
              <MessageCircle className="h-5 w-5" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="left">Chat</TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </div>
  );
}
