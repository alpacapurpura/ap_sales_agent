"use client";

import { cn } from "@/lib/utils";
import { Bot, User, AlertTriangle } from "lucide-react";
import type { ConversationListItem } from "../../types";
import { formatDistanceToNow } from "../../utils/format";

interface ConversationItemProps {
  conversation: ConversationListItem;
  isSelected: boolean;
  onSelect: (leadId: string) => void;
}

const TEMP_DOT: Record<string, string> = {
  hot: "bg-red-500",
  warm: "bg-orange-400",
  cold: "bg-blue-400",
};

const STAGE_LABEL: Record<string, string> = {
  rapport: "Nuevo",
  discovery: "Calificando",
  presentation: "Negociando",
  closing: "Cerrando",
};

export function ConversationItem({ conversation: c, isSelected, onSelect }: ConversationItemProps) {
  const initials = c.display_name
    .split(" ")
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <button
      onClick={() => onSelect(c.lead_id)}
      className={cn(
        "w-full text-left px-3 py-3 border-b border-border/50 transition-colors hover:bg-muted/50",
        isSelected && "bg-primary/5 border-l-2 border-l-primary",
        c.handler_mode === "human" && !isSelected && "border-l-2 border-l-green-500",
        c.unread_count > 0 && "bg-violet-500/5",
      )}
    >
      <div className="flex items-start gap-3">
        {/* Avatar */}
        <div className="relative shrink-0">
          {c.avatar_url ? (
            <img src={c.avatar_url} alt="" className="w-10 h-10 rounded-full object-cover" />
          ) : (
            <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center text-xs font-semibold text-muted-foreground">
              {initials}
            </div>
          )}
          {/* Temperature dot */}
          {c.temperature && (
            <div
              className={cn(
                "absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-background",
                TEMP_DOT[c.temperature] ?? "bg-gray-400",
              )}
            />
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <span className="text-sm font-semibold truncate">{c.display_name}</span>
            <span className="text-[10px] text-muted-foreground whitespace-nowrap">
              {c.last_message_at ? formatDistanceToNow(c.last_message_at) : ""}
            </span>
          </div>

          {/* Preview */}
          <p className="text-xs text-muted-foreground truncate mt-0.5">
            {c.last_message_preview || "Sin mensajes"}
          </p>

          {/* Badges row */}
          <div className="flex items-center gap-1.5 mt-1">
            {/* Handler badge */}
            {c.handler_mode === "ai" ? (
              <span className="inline-flex items-center gap-0.5 text-[10px] text-violet-600 bg-violet-100 px-1.5 py-0.5 rounded-full">
                <Bot className="h-2.5 w-2.5" /> AI
              </span>
            ) : (
              <span className="inline-flex items-center gap-0.5 text-[10px] text-green-700 bg-green-100 px-1.5 py-0.5 rounded-full">
                <User className="h-2.5 w-2.5" /> Tu
              </span>
            )}

            {/* Funnel stage */}
            <span className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded-full">
              {STAGE_LABEL[c.funnel_stage] ?? c.funnel_stage}
            </span>

            {/* Channel */}
            {c.channel && (
              <span className="text-[10px] text-muted-foreground uppercase">
                {c.channel === "instagram" ? "IG" : c.channel === "telegram" ? "TG" : c.channel === "whatsapp" ? "WA" : c.channel}
              </span>
            )}

            {/* Frozen indicator */}
            {c.is_frozen && (
              <AlertTriangle className="h-3 w-3 text-orange-500" />
            )}

            {/* Unread badge */}
            {c.unread_count > 0 && (
              <span className="ml-auto rounded-full bg-violet-600 text-white text-[10px] px-1.5 py-0.5 font-bold min-w-[18px] text-center">
                {c.unread_count}
              </span>
            )}
          </div>
        </div>
      </div>
    </button>
  );
}
