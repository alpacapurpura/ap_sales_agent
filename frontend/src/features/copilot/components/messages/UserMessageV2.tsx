"use client";

import { memo } from "react";

import { cn } from "@/lib/utils";

import { BlockDispatcher } from "../blocks/BlockDispatcher";

import { MessageContextMenu } from "./MessageContextMenu";

import type { CopilotMessage } from "../../store/copilot-store";

// ── Types ────────────────────────────────────────────────────────────

interface UserMessageV2Props {
  message: CopilotMessage;
  onReply: (message: CopilotMessage) => void;
}

// ── Component ────────────────────────────────────────────────────────

/**
 * V2 user message — renders message.blocks[] via BlockDispatcher when present,
 * falls back to plain content string for legacy messages.
 * Aligned to the right per standard chat convention.
 */
export const UserMessageV2 = memo(function UserMessageV2({ message, onReply }: UserMessageV2Props) {
  return (
    <div
      className={cn(
        "group relative flex justify-end gap-2.5 animate-in slide-in-from-bottom-2 fade-in duration-300",
      )}
      data-message-id={message.id}
      data-role="user"
    >
      {/* Context menu — visible on group hover, on the left side for user messages */}
      <div className="flex items-center self-start mt-0.5">
        <MessageContextMenu message={message} onReply={onReply} />
      </div>

      {/* Content */}
      <div className="max-w-[85%]">
        <div className="rounded-2xl rounded-br-sm bg-purple-600 px-4 py-2.5 text-sm text-white">
          {message.blocks && message.blocks.length > 0 ? (
            <div className="space-y-2">
              {message.blocks.map((block, idx) => (
                <BlockDispatcher
                  key={block.id}
                  block={block}
                  messageId={message.id}
                  actionIndex={idx}
                />
              ))}
            </div>
          ) : (
            <div className="whitespace-pre-wrap break-words">{message.content}</div>
          )}
        </div>
      </div>
    </div>
  );
});
UserMessageV2.displayName = "UserMessageV2";
