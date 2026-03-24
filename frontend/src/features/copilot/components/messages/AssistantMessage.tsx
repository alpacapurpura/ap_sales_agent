"use client";

import { Sparkles } from "lucide-react";
import type { CopilotMessage } from "../../store/copilot-store";
import { NavigationCard } from "./NavigationCard";
import { ProposalCard } from "./ProposalCard";

interface AssistantMessageProps {
  message: CopilotMessage;
  isStreaming?: boolean;
}

export function AssistantMessage({ message, isStreaming }: AssistantMessageProps) {
  const hasUIActions = message.uiActions && message.uiActions.length > 0;

  return (
    <div className="flex gap-2.5">
      <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-purple-100 dark:bg-purple-900/40">
        <Sparkles className="h-3.5 w-3.5 text-purple-600 dark:text-purple-400" />
      </div>
      <div className="max-w-[85%] space-y-2">
        <div className="rounded-2xl rounded-bl-sm bg-slate-100 px-4 py-2.5 text-sm text-slate-800 dark:bg-slate-800 dark:text-slate-200">
          <div className="whitespace-pre-wrap break-words">
            {message.content || (
              <span className="inline-flex items-center gap-1 text-slate-400">
                <span className="animate-pulse">●</span>
                <span className="animate-pulse [animation-delay:200ms]">●</span>
                <span className="animate-pulse [animation-delay:400ms]">●</span>
              </span>
            )}
            {isStreaming && message.content && (
              <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-purple-500" />
            )}
          </div>
        </div>

        {/* Render navigation/action cards and proposals */}
        {hasUIActions &&
          message.uiActions!.map((action, idx) =>
            action.type === "proposal" && action.updates ? (
              <ProposalCard
                key={`proposal-${idx}`}
                updates={action.updates}
              />
            ) : (
              <NavigationCard key={`${action.type}-${idx}`} action={action} />
            ),
          )}
      </div>
    </div>
  );
}
