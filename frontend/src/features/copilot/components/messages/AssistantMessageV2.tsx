"use client";

import { Sparkles } from "lucide-react";
import { memo } from "react";

import { cn } from "@/lib/utils";

import { BlockDispatcher } from "../blocks/BlockDispatcher";

import { MessageContextMenu } from "./MessageContextMenu";
import { ToolCallChip } from "./ToolCallChip";
import { TypingIndicator } from "./TypingIndicator";

import type { CopilotMessage } from "../../store/copilot-store";

// ── Types ────────────────────────────────────────────────────────────

interface AssistantMessageV2Props {
  message: CopilotMessage;
  onReply: (message: CopilotMessage) => void;
  sendCardAction?: (messageId: string, actionIndex: number, text: string) => void;
}

// ── Component ────────────────────────────────────────────────────────

/**
 * V2 assistant message — renders message.blocks[] via BlockDispatcher.
 * Falls back to legacy AssistantMessage if blocks are absent.
 * Shows streaming indicator when msgStatus === "streaming" and no content yet.
 */
export const AssistantMessageV2 = memo(function AssistantMessageV2({
  message,
  onReply,
  sendCardAction,
}: AssistantMessageV2Props) {
  const isStreaming = message.msgStatus === "streaming";
  const hasBlocks = message.blocks && message.blocks.length > 0;
  const isEmpty = !hasBlocks && !message.content;

  return (
    <div
      className={cn(
        "group relative flex gap-2.5 animate-in slide-in-from-bottom-2 fade-in duration-300",
      )}
      data-message-id={message.id}
      data-role="assistant"
    >
      {/* Avatar */}
      <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-purple-100 dark:bg-purple-900/40">
        <Sparkles className="h-3.5 w-3.5 text-purple-600 dark:text-purple-400" aria-hidden="true" />
      </div>

      {/* Content */}
      <div className="relative max-w-[85%] space-y-2 flex-1">
        {message.toolCalls && message.toolCalls.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {message.toolCalls.map((tc, idx) => (
              <ToolCallChip
                key={`${tc.tool}-${idx}`}
                tool={tc.tool}
                status={tc.status}
                jobId={tc.jobId}
              />
            ))}
          </div>
        )}
        <div className="relative rounded-2xl rounded-bl-sm bg-slate-100 px-4 py-2.5 text-sm text-slate-800 dark:bg-slate-800 dark:text-slate-200">
          {/* Context menu — pinned to the bubble's top-right, only visible on hover */}
          <div className="absolute right-1 top-1">
            <MessageContextMenu message={message} onReply={onReply} />
          </div>
          {isEmpty && isStreaming ? (
            <TypingIndicator />
          ) : message.blocks && message.blocks.length > 0 ? (
            /* V2 path: render blocks[] */
            <div className="space-y-2">
              {message.blocks.map((block, idx) => (
                <BlockDispatcher
                  key={block.id}
                  block={block}
                  sendCardAction={sendCardAction}
                  messageId={message.id}
                  actionIndex={idx}
                  isStreaming={isStreaming && idx === (message.blocks?.length ?? 0) - 1}
                />
              ))}
            </div>
          ) : (
            /* Legacy path: plain content */
            <div className="whitespace-pre-wrap break-words">
              {message.content}
              {isStreaming && message.content && (
                <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-purple-500" />
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
});
AssistantMessageV2.displayName = "AssistantMessageV2";
