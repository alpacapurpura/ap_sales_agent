"use client";

import { BookOpen, Package, Undo2, User, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useCopilotStore } from "../store/copilot-store";
import { cn } from "@/lib/utils";

const DOMAIN_ICONS: Record<string, typeof Package> = {
  offer: Package,
  brand: BookOpen,
  buyer_persona: User,
};

export function FocusBar() {
  const focusEntity = useCopilotStore((s) => s.focusEntity);
  const focusSnapshot = useCopilotStore((s) => s.focusSnapshot);
  const interviewProgress = useCopilotStore((s) => s.interviewProgress);
  const clearFocus = useCopilotStore((s) => s.clearFocus);
  const clearInterview = useCopilotStore((s) => s.clearInterview);
  const setSidebarState = useCopilotStore((s) => s.setSidebarState);

  if (!focusEntity) return null;

  const Icon = DOMAIN_ICONS[focusEntity.domain] ?? Package;
  const hasSnapshot = focusSnapshot && Object.keys(focusSnapshot).length > 0;

  const handleExitFocus = () => {
    clearInterview();
    clearFocus();
    setSidebarState("open");
  };

  return (
    <div className="flex items-center gap-2 border-b border-slate-200 bg-purple-50 px-3 py-2 dark:border-slate-700 dark:bg-purple-900/20">
      <Icon className="h-4 w-4 shrink-0 text-purple-600 dark:text-purple-400" />
      <span className="min-w-0 truncate text-xs font-medium text-purple-800 dark:text-purple-300">
        {focusEntity.label}
      </span>

      {interviewProgress && (
        <div className="flex items-center gap-1 ml-auto mr-2">
          {Array.from({ length: interviewProgress.totalBlocks }).map((_, i) => {
            const isCompleted = i < interviewProgress.blocksCompleted.length;
            const isCurrent = i === interviewProgress.blocksCompleted.length;
            return (
              <div
                key={i}
                data-testid="progress-dot"
                className={cn(
                  "h-1.5 w-1.5 rounded-full",
                  isCompleted && "bg-green-500",
                  isCurrent && "bg-purple-500 animate-pulse",
                  !isCompleted && !isCurrent && "bg-slate-300 dark:bg-slate-600",
                )}
              />
            );
          })}
        </div>
      )}

      {!interviewProgress && <div className="flex-1" />}

      {hasSnapshot && (
        <Button
          size="sm" variant="ghost" onClick={() => {
            window.dispatchEvent(new CustomEvent("copilot:undo-all", { detail: { snapshot: focusSnapshot } }));
          }}
          className="h-6 gap-1 px-2 text-xs text-purple-600 hover:text-purple-800 dark:text-purple-400"
        >
          <Undo2 className="h-3 w-3" />
          Deshacer todo
        </Button>
      )}

      <Button
        size="sm" variant="ghost" onClick={handleExitFocus}
        className="h-6 gap-1 px-2 text-xs text-slate-500 hover:text-slate-700"
      >
        <X className="h-3 w-3" />
        Salir de Focus
      </Button>
    </div>
  );
}
