"use client";

import { RefreshCw, Loader2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { useSimulatePersonality } from "../../api/personality";

import type { PersonalityProfile, SampleExchange } from "../../types/personality";

interface PersonalityPreviewProps {
  profile: PersonalityProfile;
}

function ChatBubble({ message, role }: { message: string; role: "prospect" | "agent" }) {
  return (
    <div
      className={cn(
        "max-w-[80%] rounded-2xl px-4 py-2.5 text-sm",
        role === "prospect"
          ? "self-start bg-muted text-foreground rounded-tl-sm"
          : "self-end bg-primary text-primary-foreground rounded-tr-sm",
      )}
    >
      {message}
    </div>
  );
}

function ExchangeDisplay({ exchange }: { exchange: SampleExchange }) {
  return (
    <div className="flex flex-col gap-2">
      {exchange.context && (
        <p className="text-[10px] text-muted-foreground/60 uppercase tracking-wider text-center">
          {exchange.context}
        </p>
      )}
      <ChatBubble message={exchange.other_message} role="prospect" />
      <ChatBubble message={exchange.author_response} role="agent" />
    </div>
  );
}

export function PersonalityPreview({ profile }: PersonalityPreviewProps) {
  const simulate = useSimulatePersonality();
  const [exchanges, setExchanges] = useState<SampleExchange[]>(
    profile.sample_exchanges.slice(0, 2),
  );

  const handleRegenerate = async () => {
    try {
      const result = await simulate.mutateAsync(profile.id);
      if (result.responses.length > 0) {
        const mapped: SampleExchange[] = result.responses.map((r) => ({
          context: r.context,
          other_message: r.prospect_message,
          author_response: r.agent_response,
        }));
        setExchanges(mapped.slice(0, 2));
      }
    } catch {
      toast.error("No se pudo regenerar la simulación.");
    }
  };

  if (exchanges.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-muted p-6 text-center text-sm text-muted-foreground">
        No hay intercambios de muestra disponibles.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Vista previa de conversación
        </p>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => void handleRegenerate()}
          disabled={simulate.isPending}
          className="text-xs"
        >
          {simulate.isPending ? (
            <Loader2 className="w-3 h-3 mr-1.5 animate-spin" />
          ) : (
            <RefreshCw className="w-3 h-3 mr-1.5" />
          )}
          Regenerar
        </Button>
      </div>

      <div className="rounded-xl border border-border bg-card p-4 flex flex-col gap-4">
        {exchanges.map((ex, i) => (
          <ExchangeDisplay key={i} exchange={ex} />
        ))}
      </div>
    </div>
  );
}
