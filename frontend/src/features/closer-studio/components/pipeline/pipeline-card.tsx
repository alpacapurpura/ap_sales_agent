"use client";

import { cn } from "@/lib/utils";
import { Bot, User } from "lucide-react";
import { useDraggable } from "@dnd-kit/core";
import type { ConversationListItem } from "../../types";
import { formatDistanceToNow } from "../../utils/format";
import { useTenantLocale } from "@/features/tenant/context/tenant-locale-context";

interface PipelineCardProps {
  conversation: ConversationListItem;
  onClick: () => void;
}

const TEMP_BORDER: Record<string, string> = {
  hot: "border-l-red-500",
  warm: "border-l-orange-400",
  cold: "border-l-blue-400",
};

export function PipelineCard({ conversation: c, onClick }: PipelineCardProps) {
  const { timezone } = useTenantLocale();
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: c.lead_id,
  });

  const style = transform
    ? { transform: `translate(${transform.x}px, ${transform.y}px)` }
    : undefined;

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      onClick={onClick}
      className={cn(
        "bg-card border border-l-4 rounded-lg p-3 cursor-pointer hover:shadow-sm transition-shadow",
        TEMP_BORDER[c.temperature ?? ""] ?? "border-l-gray-300",
        isDragging && "opacity-50 shadow-lg",
      )}
    >
      {/* Name + handler */}
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-sm font-semibold truncate">{c.display_name}</span>
        {c.handler_mode === "ai" ? (
          <Bot className="h-3.5 w-3.5 text-violet-500 shrink-0" />
        ) : (
          <User className="h-3.5 w-3.5 text-green-600 shrink-0" />
        )}
      </div>

      {/* Score bar */}
      <div className="flex items-center gap-2 mb-1.5">
        <div className="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
          <div
            className={cn(
              "h-full rounded-full transition-all",
              c.lead_score >= 70
                ? "bg-green-500"
                : c.lead_score >= 40
                  ? "bg-yellow-500"
                  : "bg-red-400",
            )}
            style={{ width: `${Math.min(c.lead_score, 100)}%` }}
          />
        </div>
        <span className="text-[10px] font-mono text-muted-foreground">{c.lead_score}</span>
      </div>

      {/* Preview + time */}
      <p className="text-xs text-muted-foreground truncate">{c.last_message_preview || "—"}</p>
      {c.last_message_at && (
        <span className="text-[10px] text-muted-foreground">
          {formatDistanceToNow(c.last_message_at, timezone)}
        </span>
      )}
    </div>
  );
}
