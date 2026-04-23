"use client";

import { AlternativesCard } from "../cards/AlternativesCard";
import { CheckpointCard } from "../cards/CheckpointCard";
import { ClarifyCard } from "../cards/ClarifyCard";
import { ExtractionSummaryCard } from "../cards/ExtractionSummaryCard";
import { InterviewCompleteCard } from "../cards/InterviewCompleteCard";
import { ComparisonTable } from "../messages/ComparisonTable";
import { MetricSummaryCard } from "../messages/MetricSummaryCard";
import { MultiOptionSelector } from "../messages/MultiOptionSelector";
import { NavigationCard } from "../messages/NavigationCard";
import { ProgressChecklist } from "../messages/ProgressChecklist";
import { ProposalCard } from "../messages/ProposalCard";

import type { UIAction } from "../../store/copilot-store";
import type { CardBlock as CardBlockType, ExtractionSummaryData } from "../../types/message-blocks";

interface CardBlockProps {
  block: CardBlockType;
  sendCardAction?: (messageId: string, actionIndex: number, text: string) => void;
  messageId?: string;
  actionIndex?: number;
}

/** Maps card_kind / UIAction.type to the correct legacy card component. */
// eslint-disable-next-line sonarjs/cognitive-complexity -- 10-way card dispatch table; same structure as AssistantMessage.renderUIAction
function renderCard(
  block: CardBlockType,
  sendCardAction: CardBlockProps["sendCardAction"],
  messageId: string,
  actionIndex: number,
): React.ReactNode {
  // The payload is a UIAction-shaped object stored as Record<string, unknown>
  const action = block.payload as unknown as UIAction;

  switch (block.card_kind) {
    case "proposal":
      return action.updates ? <ProposalCard updates={action.updates} /> : null;

    case "metric_summary":
      return action.metrics ? <MetricSummaryCard metrics={action.metrics} /> : null;

    case "comparison":
      return action.columns && action.rows ? (
        <ComparisonTable
          columns={action.columns}
          rows={action.rows}
          recommended={action.recommended}
        />
      ) : null;

    case "checklist":
      return action.items ? <ProgressChecklist items={action.items} /> : null;

    case "multi_option":
      return action.options && action.field_id ? (
        <MultiOptionSelector options={action.options} fieldId={action.field_id} />
      ) : null;

    case "alternatives":
      return action.alternatives ? (
        <AlternativesCard
          fieldPath={action.field_path ?? ""}
          question={action.question ?? ""}
          alternatives={action.alternatives.map((a) => ({
            id: a.id,
            title: a.title,
            description: a.description,
            recommended: a.recommended ?? false,
            recommendationReason: a.recommendation_reason,
          }))}
          allowCustom={action.allow_custom ?? false}
          onSelect={(altId) => {
            const alt = action.alternatives?.find((a) => a.id === altId);
            if (alt && sendCardAction) {
              sendCardAction(messageId, actionIndex, `Selecciono: ${alt.title}`);
            }
          }}
          onCustom={() => {
            sendCardAction?.(messageId, actionIndex, "Prefiero otra opción personalizada");
          }}
          status={action.card_status === "resolved" ? "resolved" : "pending"}
        />
      ) : null;

    case "clarify":
      return action.clarify_items ? (
        <ClarifyCard
          items={action.clarify_items.map((item) => ({
            fieldPath: item.field_path,
            issue: item.issue,
            options: item.options,
          }))}
          onResolve={(resolution) => {
            sendCardAction?.(messageId, actionIndex, resolution);
          }}
          status={action.card_status === "resolved" ? "resolved" : "pending"}
        />
      ) : null;

    case "checkpoint":
      return (
        <CheckpointCard
          blockId={action.block_id ?? ""}
          blockLabel={action.block_label ?? ""}
          summary={typeof action.summary === "string" ? {} : (action.summary ?? {})}
          healthScore={action.health_score ?? 0}
          blocksProgress={action.blocks_progress ?? { completed: 0, total: 0 }}
          onConfirm={() => {
            sendCardAction?.(messageId, actionIndex, "Confirmo, sigamos al siguiente bloque");
          }}
          onRevise={() => {
            sendCardAction?.(messageId, actionIndex, "Quiero ajustar algo en este bloque");
          }}
          status={
            action.card_status === "confirmed"
              ? "confirmed"
              : action.card_status === "revising"
                ? "revising"
                : "pending"
          }
        />
      );

    case "interview_complete":
      return (
        <InterviewCompleteCard
          healthScore={action.health_score ?? 0}
          redirect={action.redirect ?? "/"}
        />
      );

    case "extraction_summary":
      return (
        <ExtractionSummaryCard data={block.payload as unknown as ExtractionSummaryData} />
      );

    case "navigation":
    default:
      return <NavigationCard action={action} />;
  }
}

/**
 * Adapter block that dispatches to the appropriate legacy card component
 * based on `block.card_kind`. Preserves all existing card interactivity.
 */
export function CardBlock({
  block,
  sendCardAction,
  messageId = "",
  actionIndex = 0,
}: CardBlockProps) {
  return <>{renderCard(block, sendCardAction, messageId, actionIndex)}</>;
}

CardBlock.displayName = "CardBlock";
