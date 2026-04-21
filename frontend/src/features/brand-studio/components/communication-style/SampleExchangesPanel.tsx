"use client";

import { Loader2, RefreshCw } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { useSimulatePersonality } from "@/features/brand-studio/api/personality";

import type { SampleExchange } from "@/features/brand-studio/types/personality";

interface ExchangeCardProps {
  exchange: SampleExchange;
}

function ExchangeCard({ exchange }: ExchangeCardProps) {
  return (
    <div className="rounded-lg border border-border bg-card/50 p-4 space-y-2 text-[13px]">
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
        Contexto: {exchange.context}
      </p>
      <div className="space-y-1.5">
        <div className="flex gap-2">
          <span className="w-8 flex-shrink-0 text-xs font-medium text-muted-foreground">Lead</span>
          <p className="text-foreground/80">{exchange.other_message}</p>
        </div>
        <div className="flex gap-2">
          <span className="w-8 flex-shrink-0 text-xs font-medium text-primary">Tú</span>
          <p className="text-foreground">{exchange.author_response}</p>
        </div>
      </div>
    </div>
  );
}

interface SampleExchangesPanelProps {
  profileId: string;
  initialExchanges: SampleExchange[];
}

/**
 * Shows up to 3 sample exchanges for the active personality profile and
 * provides a "Regenerar" button that calls POST /{profileId}/simulate to
 * refresh the examples. The displayed exchanges update optimistically on
 * success; errors fall back to the previous list.
 */
export function SampleExchangesPanel({ profileId, initialExchanges }: SampleExchangesPanelProps) {
  const [exchanges, setExchanges] = useState<SampleExchange[]>(initialExchanges.slice(0, 3));
  const simulate = useSimulatePersonality();

  const handleRegenerate = async () => {
    try {
      const result = await simulate.mutateAsync(profileId);
      const mapped: SampleExchange[] = result.responses.slice(0, 3).map((r) => ({
        context: r.context,
        other_message: r.prospect_message,
        author_response: r.agent_response,
      }));
      setExchanges(mapped);
      toast.success("Ejemplos regenerados.");
    } catch {
      toast.error("(no pudimos generar una respuesta — revisa tu configuración)");
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Ejemplos de conversación
        </p>
        <Button
          size="sm"
          variant="ghost"
          onClick={handleRegenerate}
          disabled={simulate.isPending}
          className="h-7 gap-1 px-2 text-xs"
          aria-label="Regenerar ejemplos de conversación"
        >
          {simulate.isPending ? (
            <Loader2 className="h-3 w-3 animate-spin" aria-hidden />
          ) : (
            <RefreshCw className="h-3 w-3" aria-hidden />
          )}
          Regenerar
        </Button>
      </div>
      <div className="space-y-3">
        {exchanges.map((ex, idx) => (
          <ExchangeCard key={`${ex.context}-${idx}`} exchange={ex} />
        ))}
      </div>
    </div>
  );
}
