"use client";

import { Sparkles } from "lucide-react";
import type { InterviewMessage as InterviewMessageType, InterviewUIAction } from "../../hooks/useInterviewChat";
import { AlternativesCard } from "../cards/alternatives-card";
import { ClarifyCard } from "../cards/clarify-card";
import { CheckpointCard } from "../cards/checkpoint-card";
import { InterviewCompleteCard } from "../cards/interview-complete-card";

interface InterviewMessageProps {
  message: InterviewMessageType;
  isStreaming?: boolean;
  onCardAction: (text: string) => void;
}

export function InterviewMessage({
  message,
  isStreaming = false,
  onCardAction,
}: InterviewMessageProps) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-br-sm bg-purple-600 px-4 py-2.5 text-sm text-white">
          {message.content}
        </div>
      </div>
    );
  }

  // Assistant message
  return (
    <div className="flex gap-2.5">
      <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-purple-900/60">
        <Sparkles className="h-3.5 w-3.5 text-purple-400" />
      </div>

      <div className="max-w-[85%] space-y-2">
        {/* Text bubble */}
        <div className="rounded-2xl rounded-bl-sm bg-white/5 px-4 py-2.5 text-sm text-gray-200">
          <div className="whitespace-pre-wrap break-words">
            {message.content || (
              <span className="inline-flex items-center gap-1 text-gray-500">
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

        {/* UI action cards */}
        {message.uiActions?.map((action, idx) =>
          renderCard(action, idx, onCardAction),
        )}
      </div>
    </div>
  );
}

function renderCard(
  action: InterviewUIAction,
  idx: number,
  onCardAction: (text: string) => void,
): React.ReactNode {
  switch (action.type) {
    case "alternatives_card":
      return (
        <AlternativesCard
          key={`alt-${idx}`}
          fieldPath={action.field_path}
          question={action.question}
          alternatives={action.alternatives.map((a) => ({
            id: a.id,
            title: a.title,
            description: a.description,
            recommended: a.recommended,
            recommendationReason: a.recommendation_reason,
          }))}
          allowCustom={action.allow_custom}
          status={action.status}
          onSelect={(altId) => {
            const selected = action.alternatives.find((a) => a.id === altId);
            onCardAction(`Elegí: ${selected?.title ?? altId}`);
          }}
          onCustom={() => onCardAction("Quiero escribir mi propia respuesta")}
        />
      );

    case "clarify_card":
      return (
        <ClarifyCard
          key={`clarify-${idx}`}
          items={action.items.map((item) => ({
            fieldPath: item.field_path,
            issue: item.issue,
            options: item.options,
          }))}
          status={action.status}
          onResolve={(resolution) => onCardAction(resolution)}
        />
      );

    case "checkpoint_card":
      return (
        <CheckpointCard
          key={`chk-${idx}`}
          blockId={action.block_id}
          blockLabel={action.block_label}
          summary={action.summary}
          healthScore={action.health_score}
          blocksProgress={action.blocks_progress}
          status={action.status}
          onConfirm={() => onCardAction("[CHECKPOINT_CONFIRMED]")}
          onRevise={() => onCardAction("Quiero ajustar algo")}
        />
      );

    case "interview_complete":
      return (
        <InterviewCompleteCard
          key={`complete-${idx}`}
          healthScore={action.health_score}
          redirect={action.redirect}
        />
      );

    case "preview_update":
      // Silent — handled by the hook, never rendered
      return null;

    default:
      return null;
  }
}
