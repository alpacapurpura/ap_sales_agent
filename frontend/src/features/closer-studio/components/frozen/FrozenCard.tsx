"use client";

import { Snowflake, RotateCcw, Stethoscope, ChevronDown } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useTenantLocale } from "@/features/tenant/context/tenant-locale-context";
import { cn } from "@/lib/utils";

import { useConversationActions } from "../../hooks/use-conversation-actions";
import { formatDistanceToNow } from "../../utils/format";

import type { FrozenConversation } from "../../types";

interface FrozenCardProps {
  conversation: FrozenConversation;
}

export function FrozenCard({ conversation: c }: FrozenCardProps) {
  const { timezone } = useTenantLocale();
  const [expanded, setExpanded] = useState(false);
  const [objective, setObjective] = useState("");
  const actions = useConversationActions(c.lead_id);

  const diagnosis = c.frozen_diagnosis as { summary?: string; recommendation?: string } | null;

  return (
    <div className="border rounded-lg bg-card overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-3">
        <div className="w-10 h-10 rounded-full bg-orange-50 flex items-center justify-center dark:bg-orange-950/30">
          <Snowflake className="h-5 w-5 text-orange-500" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold truncate">{c.display_name}</span>
            {c.channel && (
              <span className="text-[10px] text-muted-foreground uppercase">{c.channel}</span>
            )}
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>Score: {c.lead_score}</span>
            <span>·</span>
            <span>{c.funnel_stage}</span>
            {c.frozen_at && (
              <>
                <span>·</span>
                <span>Congelada {formatDistanceToNow(c.frozen_at, timezone)}</span>
              </>
            )}
          </div>
          {c.frozen_reason && <p className="text-xs text-orange-600 mt-0.5">{c.frozen_reason}</p>}
        </div>

        {/* Quick actions */}
        <div className="flex items-center gap-1.5 shrink-0">
          <Button
            size="sm"
            variant="outline"
            onClick={() => actions.diagnose.mutate()}
            disabled={actions.diagnose.isPending}
            title="Diagnostico AI"
          >
            <Stethoscope className="h-3.5 w-3.5" />
          </Button>
          <Button
            size="sm"
            variant="default"
            onClick={() => actions.reactivate.mutate(objective || undefined)}
            disabled={actions.reactivate.isPending}
            className="bg-green-600 hover:bg-green-700"
          >
            <RotateCcw className="h-3.5 w-3.5 mr-1" />
            Reactivar
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setExpanded(!expanded)}>
            <ChevronDown className={cn("h-4 w-4 transition-transform", expanded && "rotate-180")} />
          </Button>
        </div>
      </div>

      {/* Expandable section */}
      {expanded && (
        <div className="border-t px-4 py-3 space-y-3 bg-muted/30">
          {/* Diagnosis */}
          {diagnosis && (
            <div className="space-y-1.5">
              <div className="text-xs font-medium text-muted-foreground">Diagnostico AI</div>
              {diagnosis.summary && <p className="text-xs">{diagnosis.summary}</p>}
              {diagnosis.recommendation && (
                <p className="text-xs text-violet-600 bg-violet-50 px-2 py-1.5 rounded dark:bg-violet-950/30 dark:text-violet-300">
                  💡 {diagnosis.recommendation}
                </p>
              )}
            </div>
          )}

          {/* Preview */}
          {c.last_message_preview && (
            <div>
              <div className="text-xs font-medium text-muted-foreground mb-1">Ultimo mensaje</div>
              <p className="text-xs text-muted-foreground italic">
                &ldquo;{c.last_message_preview}&rdquo;
              </p>
            </div>
          )}

          {/* Custom objective */}
          <div>
            <div className="text-xs font-medium text-muted-foreground mb-1">
              Objetivo personalizado (opcional)
            </div>
            <div className="flex gap-2">
              <Input
                value={objective}
                onChange={(e) => setObjective(e.target.value)}
                placeholder="Ej: Ofrece una sesion gratuita..."
                className="h-8 text-xs"
              />
              <Button
                size="sm"
                onClick={() => actions.reactivate.mutate(objective || undefined)}
                disabled={actions.reactivate.isPending}
                className="h-8 bg-green-600 hover:bg-green-700"
              >
                Enviar
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
