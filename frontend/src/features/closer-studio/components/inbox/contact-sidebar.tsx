"use client";

import { cn } from "@/lib/utils";
import { ScoreRing } from "@/features/sales/components/atoms/ScoreRing";
import { X, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useConversationDetail } from "../../hooks/use-conversation-detail";
import { useCloserStore } from "../../store/closer-store";

interface ContactSidebarProps {
  leadId: string;
}

const LIFECYCLE_STAGES = ["SUBSCRIBER", "LEAD", "MQL", "SQL", "OPPORTUNITY", "CUSTOMER"];

export function ContactSidebar({ leadId }: ContactSidebarProps) {
  const { data: detail } = useConversationDetail(leadId);
  const setSidebarOpen = useCloserStore((s) => s.setSidebarOpen);

  if (!detail) return null;

  const leadData = detail.lead_data ?? {};
  const qa = detail.qualification_answers ?? {};
  const currentStageIdx = LIFECYCLE_STAGES.indexOf(
    (detail.pipeline_stage ?? "LEAD").toUpperCase(),
  );

  return (
    <div className="p-4 space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center text-sm font-bold">
            {detail.display_name.slice(0, 2).toUpperCase()}
          </div>
          <div>
            <div className="font-semibold text-sm">{detail.display_name}</div>
            {detail.channel && (
              <span className="text-xs text-muted-foreground uppercase">{detail.channel}</span>
            )}
          </div>
        </div>
        <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => setSidebarOpen(false)}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Scores */}
      <div className="flex items-center justify-around py-2">
        <div className="text-center">
          <ScoreRing score={detail.lead_score} size={48} />
          <div className="text-[10px] text-muted-foreground mt-1">Score</div>
        </div>
        <div className="text-center">
          <div className="text-2xl">
            {detail.temperature === "hot" ? "🔥" : detail.temperature === "warm" ? "🌡️" : "❄️"}
          </div>
          <div className="text-[10px] text-muted-foreground mt-1">
            {detail.temperature ?? "N/A"}
          </div>
        </div>
      </div>

      {/* Lifecycle bar */}
      <div>
        <div className="text-xs font-medium text-muted-foreground mb-2">Lifecycle</div>
        <div className="flex gap-0.5">
          {LIFECYCLE_STAGES.map((stage, i) => (
            <div
              key={stage}
              className={cn(
                "flex-1 h-1.5 rounded-full",
                i <= currentStageIdx
                  ? i === currentStageIdx
                    ? "bg-yellow-400"
                    : "bg-violet-500"
                  : "bg-muted",
              )}
              title={stage}
            />
          ))}
        </div>
        <div className="text-[10px] text-muted-foreground mt-1">
          {detail.pipeline_stage ?? "LEAD"}
        </div>
      </div>

      {/* Lead data */}
      {Object.keys(leadData).length > 0 && (
        <div>
          <div className="text-xs font-medium text-muted-foreground mb-2">Datos del contacto</div>
          <div className="space-y-1.5">
            {Object.entries(leadData).map(([key, val]) =>
              val ? (
                <div key={key} className="flex justify-between text-xs">
                  <span className="text-muted-foreground capitalize">{key.replace(/_/g, " ")}</span>
                  <span className="font-medium truncate ml-2 max-w-[140px]">{String(val)}</span>
                </div>
              ) : null,
            )}
          </div>
        </div>
      )}

      {/* Qualification */}
      {Object.keys(qa).length > 0 && (
        <div>
          <div className="text-xs font-medium text-muted-foreground mb-2">Calificacion AI</div>
          <div className="space-y-1.5">
            {Object.entries(qa).map(([key, val]) =>
              val ? (
                <div key={key} className="flex justify-between text-xs">
                  <span className="text-muted-foreground capitalize">{key.replace(/_/g, " ")}</span>
                  <span className="font-medium truncate ml-2 max-w-[140px]">{String(val)}</span>
                </div>
              ) : null,
            )}
          </div>
        </div>
      )}

      {/* Buying signals */}
      {detail.buying_signals.length > 0 && (
        <div>
          <div className="text-xs font-medium text-muted-foreground mb-2">
            Senales de compra ({detail.buying_signals.length})
          </div>
          <div className="flex flex-wrap gap-1">
            {detail.buying_signals.map((signal, i) => (
              <span
                key={i}
                className="text-[10px] bg-green-100 text-green-700 px-1.5 py-0.5 rounded dark:bg-green-900/30 dark:text-green-300"
              >
                {String(signal.type || signal)}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
