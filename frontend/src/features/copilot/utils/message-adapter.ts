// [COPILOT-LEGACY-ADAPTER] — docs/domains/copilot/UI-SPEC.md §6
// Bridges the legacy CopilotMessage (content: string + uiActions[])
// to the canonical MessageBlock[] used by AssistantMessageV2 / UserMessageV2.
// This adapter runs at render time — the store still stores both representations
// for backward compatibility. When the backend fully migrates to block events,
// this file can be deleted and the legacy fields retired.

import type { CopilotMessage, UIAction } from "../store/copilot-store";
import type { MessageBlock } from "../types/message-blocks";

// ── contentToBlocks ──────────────────────────────────────────────────

/**
 * Converts a plain-text `content` string and optional `uiActions[]`
 * into a canonical `MessageBlock[]`.
 *
 * Each `UIAction.type` maps to a `CardBlock` with the matching `card_kind`.
 * The text content (if non-empty) always becomes the first `TextBlock`.
 */
export function contentToBlocks(
  content: string,
  uiActions?: UIAction[],
  msgId?: string,
): MessageBlock[] {
  const blocks: MessageBlock[] = [];

  if (content) {
    blocks.push({
      id: msgId ? `${msgId}-text` : `text-${Date.now()}`,
      type: "text",
      markdown: content,
    });
  }

  if (uiActions) {
    uiActions.forEach((action, idx) => {
      blocks.push({
        id: msgId ? `${msgId}-card-${idx}` : `card-${idx}-${Date.now()}`,
        type: "card",
        card_kind: mapUIActionToCardKind(action.type),
        payload: action as unknown as Record<string, unknown>,
        status: action.card_status,
      });
    });
  }

  return blocks;
}

// ── blocksToContent ──────────────────────────────────────────────────

/**
 * Extracts plain-text content from a `MessageBlock[]`.
 * Only text blocks are included — other block types are ignored.
 * Used when legacy code needs the `content` string from a blocks-based message.
 */
export function blocksToContent(blocks: MessageBlock[]): string {
  return blocks
    .filter((b) => b.type === "text")
    .map((b) => (b.type === "text" ? b.markdown : ""))
    .join("\n\n");
}

// ── adaptLegacyMessage ───────────────────────────────────────────────

/**
 * Full legacy message → `MessageBlock[]` adapter.
 * If the message already has `blocks`, returns them directly.
 * Otherwise synthesizes from `content` + `uiActions`.
 */
export function adaptLegacyMessage(msg: CopilotMessage): MessageBlock[] {
  if (msg.blocks && msg.blocks.length > 0) {
    return msg.blocks;
  }
  return contentToBlocks(msg.content, msg.uiActions, msg.id);
}

// ── Helpers ──────────────────────────────────────────────────────────

type CardKind = import("../types/message-blocks").CardKind;

function mapUIActionToCardKind(actionType: UIAction["type"]): CardKind {
  switch (actionType) {
    case "proposal":
      return "proposal";
    case "alternatives_card":
      return "alternatives";
    case "clarify_card":
      return "clarify";
    case "checkpoint_card":
      return "checkpoint";
    case "interview_complete":
      return "interview_complete";
    case "metric_summary":
      return "metric_summary";
    case "comparison":
      return "comparison";
    case "checklist":
      return "checklist";
    case "multi_option":
      return "multi_option";
    case "navigate":
    case "scroll_to_field":
    case "open_form":
    case "procedure_progress":
    case "preview_update":
    default:
      return "navigation";
  }
}
