"use client";

import { AlertTriangle, Bot, User } from "lucide-react";

import { useTenantLocale } from "@/features/tenant/context/tenant-locale-context";
import { cn } from "@/lib/utils";

import { formatDistanceToNow } from "../../utils/format";

import { CampaignTag } from "./CampaignTag";

import type { ConversationListItem } from "../../types";

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

function getChannelAbbr(channel: string): string {
  if (channel === "instagram") return "IG";
  if (channel === "telegram") return "TG";
  if (channel === "whatsapp") return "WA";
  return channel;
}

/**
 * Ítem de conversación en la lista del inbox del Closer Studio.
 * Muestra el avatar, nombre, última actividad y badges de estado.
 * Incluye chip de campaña (PR-8) cuando la conversación proviene de una campaña.
 */
export function ConversationItem({ conversation: c, isSelected, onSelect }: ConversationItemProps) {
  const { timezone } = useTenantLocale();
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
            // eslint-disable-next-line @next/next/no-img-element -- avatar URL is tenant-controlled; next/image requires known domains config
            <img src={c.avatar_url} alt="" className="h-10 w-10 rounded-full object-cover" />
          ) : (
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted text-xs font-semibold text-muted-foreground">
              {initials}
            </div>
          )}
          {/* Temperature dot */}
          {c.temperature && (
            <div
              className={cn(
                "absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-background",
                TEMP_DOT[c.temperature] ?? "bg-gray-400",
              )}
            />
          )}
        </div>

        {/* Content */}
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <span className="truncate text-sm font-semibold">{c.display_name}</span>
            <span className="whitespace-nowrap text-[10px] text-muted-foreground">
              {c.last_message_at ? formatDistanceToNow(c.last_message_at, timezone) : ""}
            </span>
          </div>

          {/* Preview */}
          <p className="mt-0.5 truncate text-xs text-muted-foreground">
            {c.last_message_preview ?? "Sin mensajes"}
          </p>

          {/* Badges row */}
          <div className="mt-1 flex flex-wrap items-center gap-1.5">
            {/* Handler badge */}
            {c.handler_mode === "ai" ? (
              <span className="inline-flex items-center gap-0.5 rounded-full bg-violet-100 px-1.5 py-0.5 text-[10px] text-violet-600">
                <Bot className="h-2.5 w-2.5" /> AI
              </span>
            ) : (
              <span className="inline-flex items-center gap-0.5 rounded-full bg-green-100 px-1.5 py-0.5 text-[10px] text-green-700">
                <User className="h-2.5 w-2.5" /> Tu
              </span>
            )}

            {/* Funnel stage */}
            <span className="rounded-full bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">
              {STAGE_LABEL[c.funnel_stage] ?? c.funnel_stage}
            </span>

            {/* Channel */}
            {c.channel && (
              <span className="text-[10px] uppercase text-muted-foreground">
                {getChannelAbbr(c.channel)}
              </span>
            )}

            {/* Frozen indicator */}
            {c.is_frozen && <AlertTriangle className="h-3 w-3 text-orange-500" />}

            {/* Campaign tag — PR-8 enrichment */}
            {c.campaign_id && c.campaign_name && (
              <CampaignTag
                campaignId={c.campaign_id}
                campaignName={c.campaign_name}
                variant="list"
              />
            )}

            {/* Unread badge */}
            {c.unread_count > 0 && (
              <span className="ml-auto min-w-[18px] rounded-full bg-violet-600 px-1.5 py-0.5 text-center text-[10px] font-bold text-white">
                {c.unread_count}
              </span>
            )}
          </div>
        </div>
      </div>
    </button>
  );
}
