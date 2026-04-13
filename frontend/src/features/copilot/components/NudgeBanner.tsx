"use client";

import { memo } from "react";
import { Lightbulb, X } from "lucide-react";
import { useAuth } from "@clerk/nextjs";
import { reportCopilotEvent } from "../api/copilot-api";

interface NudgeItem {
  id: string;
  type: string;
  title: string;
  message: string;
  suggested_prompt: string;
  priority: number;
}

interface NudgeBannerProps {
  nudge: NudgeItem;
  onAction: (prompt: string) => void;
  onDismiss: (id: string) => void;
}

export const NudgeBanner = memo(function NudgeBanner({ nudge, onAction, onDismiss }: NudgeBannerProps) {
  const { getToken } = useAuth();

  const handleAction = () => {
    onAction(nudge.suggested_prompt);
    getToken().then((token) => {
      if (token) {
        reportCopilotEvent("nudge_clicked", {
          nudge_id: nudge.id,
          nudge_type: nudge.type,
          nudge_title: nudge.title,
        }, token);
      }
    });
  };

  const handleDismiss = () => {
    onDismiss(nudge.id);
    getToken().then((token) => {
      if (token) {
        reportCopilotEvent("nudge_dismissed", {
          nudge_id: nudge.id,
          nudge_type: nudge.type,
        }, token);
      }
    });
  };

  return (
    <div className="mx-4 my-2 rounded-lg border-l-4 border-purple-500 bg-purple-50 px-3 py-2.5 dark:bg-purple-950/30">
      <div className="flex items-start gap-2">
        <Lightbulb className="mt-0.5 h-4 w-4 shrink-0 text-purple-500" />
        <div className="min-w-0 flex-1">
          <p className="text-xs font-medium text-slate-800 dark:text-slate-200">
            {nudge.title}
          </p>
          <p className="mt-0.5 text-[11px] text-slate-600 dark:text-slate-400">
            {nudge.message}
          </p>
          <button
            onClick={handleAction}
            className="mt-1.5 text-[11px] font-medium text-purple-600 hover:text-purple-800 dark:text-purple-400 dark:hover:text-purple-300"
          >
            {nudge.suggested_prompt} →
          </button>
        </div>
        <button
          onClick={handleDismiss}
          className="shrink-0 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
});
NudgeBanner.displayName = "NudgeBanner";
