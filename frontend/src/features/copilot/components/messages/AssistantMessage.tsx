"use client";

import { Sparkles } from "lucide-react";
import { memo, useCallback } from "react";

import { AlternativesCard } from "../cards/AlternativesCard";
import { CheckpointCard } from "../cards/CheckpointCard";
import { ClarifyCard } from "../cards/ClarifyCard";
import { InterviewCompleteCard } from "../cards/InterviewCompleteCard";

import { ComparisonTable } from "./ComparisonTable";
import { MetricSummaryCard } from "./MetricSummaryCard";
import { MultiOptionSelector } from "./MultiOptionSelector";
import { NavigationCard } from "./NavigationCard";
import { ProgressChecklist } from "./ProgressChecklist";
import { ProposalCard } from "./ProposalCard";
import { ToolCallChip } from "./ToolCallChip";

import type { CopilotMessage, UIAction } from "../../store/copilot-store";

interface AssistantMessageProps {
  message: CopilotMessage;
  isStreaming?: boolean;
  sendCardAction?: (messageId: string, actionIndex: number, text: string) => void;
}

/** Maps a UIAction.alternatives array to the AlternativesCard prop shape. */
function mapAlternatives(
  alternatives: NonNullable<UIAction["alternatives"]>,
): React.ComponentProps<typeof AlternativesCard>["alternatives"] {
  return alternatives.map((a) => ({
    id: a.id,
    title: a.title,
    description: a.description,
    recommended: a.recommended ?? false,
    recommendationReason: a.recommendation_reason,
  }));
}

/** Maps a UIAction.clarify_items array to the ClarifyCard prop shape. */
function mapClarifyItems(
  clarifyItems: NonNullable<UIAction["clarify_items"]>,
): React.ComponentProps<typeof ClarifyCard>["items"] {
  return clarifyItems.map((item) => ({
    fieldPath: item.field_path,
    issue: item.issue,
    options: item.options,
  }));
}

/** Normalises a checkpoint card_status to the three allowed literal values. */
function checkpointStatus(cardStatus: string | undefined): "confirmed" | "revising" | "pending" {
  if (cardStatus === "confirmed") return "confirmed";
  if (cardStatus === "revising") return "revising";
  return "pending";
}

/**
 * Renders a single UIAction card.
 * Each case maps to one card component — the switch is the simplest representation
 * of a 10-way dispatch; further splitting would add indirection without clarity gain.
 */
// eslint-disable-next-line sonarjs/cognitive-complexity -- 10-way type dispatch table; each case is a one-liner guard + component. Splitting into a lookup map would require boxing every conditional render, adding more complexity than it removes.
function renderUIAction(
  action: UIAction,
  idx: number,
  messageId: string,
  sendCardAction: ((messageId: string, actionIndex: number, text: string) => void) | undefined,
): React.ReactNode {
  switch (action.type) {
    case "proposal":
      return action.updates ? (
        <ProposalCard key={`proposal-${idx}`} updates={action.updates} />
      ) : null;
    case "metric_summary":
      return action.metrics ? (
        <MetricSummaryCard key={`metric-${idx}`} metrics={action.metrics} />
      ) : null;
    case "comparison":
      return action.columns && action.rows ? (
        <ComparisonTable
          key={`comparison-${idx}`}
          columns={action.columns}
          rows={action.rows}
          recommended={action.recommended}
        />
      ) : null;
    case "checklist":
      return action.items ? (
        <ProgressChecklist key={`checklist-${idx}`} items={action.items} />
      ) : null;
    case "multi_option":
      return action.options && action.field_id ? (
        <MultiOptionSelector
          key={`option-${idx}`}
          options={action.options}
          fieldId={action.field_id}
        />
      ) : null;
    case "alternatives_card":
      return action.alternatives ? (
        <AlternativesCard
          key={`alt-${idx}`}
          fieldPath={action.field_path ?? ""}
          question={action.question ?? ""}
          alternatives={mapAlternatives(action.alternatives)}
          allowCustom={action.allow_custom ?? false}
          onSelect={(altId) => {
            const alt = action.alternatives?.find((a) => a.id === altId);
            if (alt && sendCardAction) {
              sendCardAction(messageId, idx, `Selecciono: ${alt.title}`);
            }
          }}
          onCustom={() => {
            if (sendCardAction) {
              sendCardAction(messageId, idx, "Prefiero otra opción personalizada");
            }
          }}
          status={action.card_status === "resolved" ? "resolved" : "pending"}
        />
      ) : null;
    case "clarify_card":
      return action.clarify_items ? (
        <ClarifyCard
          key={`clarify-${idx}`}
          items={mapClarifyItems(action.clarify_items)}
          onResolve={(resolution) => {
            if (sendCardAction) {
              sendCardAction(messageId, idx, resolution);
            }
          }}
          status={action.card_status === "resolved" ? "resolved" : "pending"}
        />
      ) : null;
    case "checkpoint_card":
      return (
        <CheckpointCard
          key={`checkpoint-${idx}`}
          blockId={action.block_id ?? ""}
          blockLabel={action.block_label ?? ""}
          summary={typeof action.summary === "string" ? {} : (action.summary ?? {})}
          healthScore={action.health_score ?? 0}
          blocksProgress={action.blocks_progress ?? { completed: 0, total: 0 }}
          onConfirm={() => {
            if (sendCardAction) {
              sendCardAction(messageId, idx, "Confirmo, sigamos al siguiente bloque");
            }
          }}
          onRevise={() => {
            if (sendCardAction) {
              sendCardAction(messageId, idx, "Quiero ajustar algo en este bloque");
            }
          }}
          status={checkpointStatus(action.card_status)}
        />
      );
    case "interview_complete":
      return (
        <InterviewCompleteCard
          key={`complete-${idx}`}
          healthScore={action.health_score ?? 0}
          redirect={action.redirect ?? "/"}
        />
      );
    case "preview_update":
      return null;
    default:
      return <NavigationCard key={`${action.type}-${idx}`} action={action} />;
  }
}

export const AssistantMessage = memo(function AssistantMessage({
  message,
  isStreaming,
  sendCardAction,
}: AssistantMessageProps) {
  const hasUIActions = message.uiActions && message.uiActions.length > 0;

  // Stable callback reference so memo on card components isn't broken by
  // new function identity on every parent render.
  const stableSendCardAction = useCallback(
    (messageId: string, actionIndex: number, text: string) => {
      sendCardAction?.(messageId, actionIndex, text);
    },

    [sendCardAction],
  );

  return (
    <div className="flex gap-2.5 animate-in slide-in-from-bottom-2 fade-in duration-300">
      <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-purple-100 dark:bg-purple-900/40">
        <Sparkles className="h-3.5 w-3.5 text-purple-600 dark:text-purple-400" />
      </div>
      <div className="max-w-[85%] space-y-2">
        {message.toolCalls && message.toolCalls.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {message.toolCalls.map((tc, idx) => (
              <ToolCallChip key={`${tc.tool}-${idx}`} tool={tc.tool} status={tc.status} />
            ))}
          </div>
        )}
        <div className="rounded-2xl rounded-bl-sm bg-slate-100 px-4 py-2.5 text-sm text-slate-800 dark:bg-slate-800 dark:text-slate-200">
          <div className="whitespace-pre-wrap break-words">
            {message.content || (
              <span
                className="inline-flex items-center gap-1 text-slate-400"
                // data-testid only on the active streaming placeholder so
                // Playwright strict-mode never resolves >1 typing indicator.
                {...(isStreaming
                  ? {
                      "data-testid": "typing-indicator",
                      "aria-label": "El asistente está escribiendo",
                    }
                  : {})}
              >
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

        {/* Render navigation/action cards, proposals, and generative UI */}
        {hasUIActions &&
          message.uiActions?.map((action, idx) =>
            renderUIAction(action, idx, message.id, stableSendCardAction),
          )}
      </div>
    </div>
  );
});
AssistantMessage.displayName = "AssistantMessage";
