"use client";

import { Loader2, Send } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Textarea } from "@/components/ui/textarea";
import { useSimulatePersonality } from "@/features/brand-studio/api/personality";
import { cn } from "@/lib/utils";

const QUICK_CONTEXTS = [
  { label: "Saludo", message: "Hola, ¿cómo estás?" },
  { label: "Precio", message: "¿Cuánto cuesta tu programa?" },
  { label: "Objeción", message: "Es muy caro, no sé si puedo." },
  { label: "Interés", message: "Me interesa, ¿qué incluye?" },
  { label: "Cierre", message: "Quiero empezar, ¿cómo lo hago?" },
] as const;

interface SimulateDrawerProps {
  profileId: string;
  profileName: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/**
 * Drawer for testing the active personality in a simulated conversation.
 * Quick context pills preload typical sales messages into the textarea.
 * "Generar respuesta" calls POST /{profileId}/simulate and shows the
 * agent response. V1 uses stored sample exchanges; V2 will be LLM-driven.
 */
export function SimulateDrawer({
  profileId,
  profileName,
  open,
  onOpenChange,
}: SimulateDrawerProps) {
  const [message, setMessage] = useState("");
  const [response, setResponse] = useState<string | null>(null);
  const simulate = useSimulatePersonality();

  const handleQuickContext = (msg: string) => {
    setMessage(msg);
    setResponse(null);
  };

  const handleGenerate = async () => {
    try {
      const result = await simulate.mutateAsync(profileId);
      const first = result.responses[0];
      if (first) {
        setResponse(first.agent_response);
      }
    } catch {
      toast.error("(no pudimos generar una respuesta — revisa tu configuración)");
    }
  };

  const handleReset = () => {
    setMessage("");
    setResponse(null);
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="flex w-full flex-col gap-4 sm:max-w-md">
        <SheetHeader>
          <SheetTitle className="text-base">Probar en conversación</SheetTitle>
          <p className="text-xs text-muted-foreground">Estilo activo: {profileName}</p>
        </SheetHeader>

        <div className="flex flex-1 flex-col gap-4 overflow-auto">
          {/* Quick context pills */}
          <div>
            <p className="mb-2 text-xs font-medium text-muted-foreground">Contexto rápido:</p>
            <div className="flex flex-wrap gap-2">
              {QUICK_CONTEXTS.map((ctx) => (
                <button
                  key={ctx.label}
                  type="button"
                  onClick={() => handleQuickContext(ctx.message)}
                  className={cn(
                    "rounded-full border border-border px-3 py-1 text-xs transition-colors",
                    "hover:border-primary/50 hover:bg-primary/5",
                    message === ctx.message &&
                      "border-primary bg-primary/10 font-medium text-primary",
                  )}
                  aria-pressed={message === ctx.message}
                >
                  {ctx.label}
                </button>
              ))}
            </div>
          </div>

          {/* Message input */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground" htmlFor="simulate-message">
              Mensaje del lead (simulado):
            </label>
            <Textarea
              id="simulate-message"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Escribe un mensaje del lead..."
              rows={3}
              className="resize-none text-sm"
            />
          </div>

          <Button
            onClick={handleGenerate}
            disabled={!message.trim() || simulate.isPending}
            className="w-full"
            aria-label="Generar respuesta del SDR con este estilo"
          >
            {simulate.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden />
            ) : (
              <Send className="mr-2 h-4 w-4" aria-hidden />
            )}
            Generar respuesta →
          </Button>

          {/* Response area */}
          {response && (
            <div className="space-y-2">
              <p className="text-xs font-medium text-muted-foreground">
                Respuesta del SDR con este estilo:
              </p>
              <div className="rounded-lg border border-border bg-muted/30 px-4 py-3 text-sm text-foreground">
                {response}
              </div>
              <Button
                size="sm"
                variant="ghost"
                onClick={handleReset}
                className="text-xs"
                aria-label="Probar otra simulación"
              >
                Otra simulación
              </Button>
            </div>
          )}
        </div>

        <div className="flex justify-end border-t border-border pt-3">
          <Button
            size="sm"
            variant="outline"
            onClick={() => onOpenChange(false)}
            aria-label="Volver al estilo"
          >
            Volver al estilo
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
