"use client";

import { cn } from "@/lib/utils";
import { Bot, User, Target, Info } from "lucide-react";
import type { MessageItem } from "../../types";
import { formatMessageTime } from "../../utils/format";
import { useTenantLocale } from "@/features/tenant/context/tenant-locale-context";

interface MessageBubbleProps {
  message: MessageItem;
}

export function MessageBubble({ message: m }: MessageBubbleProps) {
  const { timezone } = useTenantLocale();
  // System events
  if (m.role === "system") {
    const isInstruction = m.sender_source === "human_instruction";
    return (
      <div
        className={cn(
          "text-center text-xs py-2 px-4 rounded-lg mx-auto max-w-md",
          isInstruction
            ? "bg-violet-50 border border-violet-200 text-violet-700 dark:bg-violet-950/30 dark:border-violet-800 dark:text-violet-300"
            : "bg-muted/50 text-muted-foreground",
        )}
      >
        <div className="flex items-center justify-center gap-1.5">
          {isInstruction ? <Target className="h-3 w-3" /> : <Info className="h-3 w-3" />}
          <span>{m.content}</span>
        </div>
        {m.created_at && (
          <span className="text-[10px] opacity-60 mt-0.5 block">
            {formatMessageTime(m.created_at, timezone)}
          </span>
        )}
      </div>
    );
  }

  const isUser = m.role === "user";
  const isHumanDirect = m.sender_source === "human_direct";

  return (
    <div className={cn("flex gap-2", isUser ? "justify-end" : "justify-start")}>
      {/* Avatar (left side only) */}
      {!isUser && (
        <div
          className={cn(
            "w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-1",
            isHumanDirect ? "bg-green-100 text-green-700" : "bg-violet-100 text-violet-700",
          )}
        >
          {isHumanDirect ? <User className="h-3.5 w-3.5" /> : <Bot className="h-3.5 w-3.5" />}
        </div>
      )}

      {/* Bubble */}
      <div
        className={cn(
          "max-w-[70%] rounded-2xl px-4 py-2.5 text-sm",
          isUser
            ? "bg-foreground text-background rounded-br-md"
            : isHumanDirect
              ? "bg-green-50 text-green-900 border border-green-200 rounded-bl-md dark:bg-green-950/30 dark:text-green-100 dark:border-green-800"
              : "bg-violet-50 text-violet-900 border border-violet-200 rounded-bl-md dark:bg-violet-950/30 dark:text-violet-100 dark:border-violet-800",
        )}
      >
        <p className="whitespace-pre-wrap break-words">{m.content}</p>
        {m.created_at && (
          <span
            className={cn(
              "text-[10px] block mt-1",
              isUser ? "text-background/60" : "text-muted-foreground",
            )}
          >
            {formatMessageTime(m.created_at, timezone)}
          </span>
        )}
      </div>
    </div>
  );
}
