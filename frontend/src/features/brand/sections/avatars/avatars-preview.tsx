"use client";

import { useAuth } from "@clerk/nextjs";
import { Users, Sparkles, PenLine, Plus } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { startInterview } from "@/features/copilot/api/interview-api";
import { FocusModeButton } from "@/features/copilot/components/FocusModeButton";
import { useCopilotStore } from "@/features/copilot/store/copilot-store";

import { useBuyerPersonas } from "../../hooks/use-buyer-personas";

export interface AvatarsSectionProps {
  // Legacy props kept for compatibility with publico-view.tsx — unused in this implementation
  visuals?: Record<string, unknown>;
  onEdit?: (item?: unknown) => void;
  onExtract?: () => void;
  onStartInterview?: () => void;
}

export function AvatarsSection(_props: AvatarsSectionProps) {
  const { getToken } = useAuth();
  const router = useRouter();
  const params = useParams<{ tenantId: string }>();
  const { tenantId } = params;

  const [showModeSelector, setShowModeSelector] = useState(false);

  const { personas, isLoading, create } = useBuyerPersonas();
  const setFocusEntity = useCopilotStore((s) => s.setFocusEntity);
  const setFocusSnapshot = useCopilotStore((s) => s.setFocusSnapshot);
  const setInterviewSession = useCopilotStore((s) => s.setInterviewSession);
  const setConversationId = useCopilotStore((s) => s.setConversationId);
  const addMessage = useCopilotStore((s) => s.addMessage);
  const clearSelectedFields = useCopilotStore((s) => s.clearSelectedFields);
  const setSidebarState = useCopilotStore((s) => s.setSidebarState);

  const handleModoInteligente = async () => {
    try {
      const persona = await create({ name: "Mi buyer persona" });
      const token = await getToken();
      if (!token) return;

      const interview = await startInterview(token, "buyer_persona", persona.id);

      // All store mutations happen atomically AFTER confirmed success
      setFocusEntity({ domain: "buyer_persona", entityId: persona.id, label: persona.name });
      setFocusSnapshot(persona as unknown as Record<string, unknown>);
      clearSelectedFields();
      setInterviewSession(interview.session_id);
      setConversationId(interview.conversation_id);
      addMessage({
        id: crypto.randomUUID(),
        role: "assistant",
        content: interview.initial_message,
        timestamp: Date.now(),
      });
      setSidebarState("expanded");
      setShowModeSelector(false);
    } catch (err) {
      console.warn("Failed to start intelligent mode:", err);
    }
  };

  const handleModoManual = async () => {
    try {
      setShowModeSelector(false);
      const persona = await create({ name: "Mi buyer persona" });
      router.push(`/${tenantId}/brand-studio/publico/persona/${persona.id}`);
    } catch (err) {
      console.warn("Failed to create persona:", err);
    }
  };

  const handleCardClick = (personaId: string) => {
    router.push(`/${tenantId}/brand-studio/publico/persona/${personaId}`);
  };

  if (isLoading) {
    return (
      <section className="group relative -mx-4 p-6 rounded-xl">
        <div className="flex items-center gap-3 mb-6 text-muted-foreground">
          <div className="p-2 rounded-md bg-muted">
            <Users className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-semibold uppercase tracking-wider">Buyer Personas</h3>
        </div>
        <div className="flex gap-4">
          <Skeleton className="h-32 w-40 rounded-xl" />
          <Skeleton className="h-32 w-40 rounded-xl" />
          <Skeleton className="h-32 w-40 rounded-xl" />
        </div>
      </section>
    );
  }

  const hasPersonas = personas.length > 0;

  return (
    <section className="group relative -mx-4 p-6 rounded-xl transition-all duration-300 hover:bg-muted/40">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6 text-muted-foreground group-hover:text-primary transition-colors">
        <div className="p-2 rounded-md bg-muted group-hover:bg-primary/10 transition-colors">
          <Users className="w-5 h-5" />
        </div>
        <h3 className="text-sm font-semibold uppercase tracking-wider">Buyer Personas</h3>
      </div>

      {!hasPersonas ? (
        /* Empty state */
        <div className="flex flex-col items-center justify-center py-10 text-center border-2 border-dashed rounded-xl bg-muted/20 hover:bg-muted/30 transition-colors">
          <div className="w-12 h-12 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center mb-4 shadow-sm">
            <Users className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-semibold mb-2">Sin Buyer Personas</h3>
          <p className="text-sm text-muted-foreground mb-6 max-w-sm leading-relaxed">
            ¿Cómo quieres crear tu primer buyer persona?
          </p>
          <div className="flex gap-4">
            <Button
              onClick={() => void handleModoInteligente()}
              className="shadow-lg shadow-purple-500/20 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white border-none"
            >
              <Sparkles className="w-4 h-4 mr-2" />
              Modo Inteligente
            </Button>
            <Button variant="outline" onClick={() => void handleModoManual()}>
              <PenLine className="w-4 h-4 mr-2" />
              Modo Manual
            </Button>
          </div>
        </div>
      ) : (
        /* Persona cards + optional mode selector */
        <>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {personas.map((persona) => (
              <div
                key={persona.id}
                className="flex flex-col items-center p-4 rounded-xl border border-border/50 bg-card hover:border-primary/30 hover:bg-muted/40 transition-all cursor-pointer"
                onClick={() => handleCardClick(persona.id)}
              >
                <Avatar className="h-14 w-14 mb-3">
                  <AvatarFallback className="text-sm font-bold bg-gradient-to-br from-purple-500 to-indigo-600 text-white">
                    {persona.name.substring(0, 2).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <h4 className="font-medium text-sm text-center truncate w-full">{persona.name}</h4>
                <div className="w-full mt-2 mb-3">
                  <Progress value={persona.completeness_score} className="h-1.5" />
                  <span className="text-[10px] text-muted-foreground mt-1 block text-center">
                    {Math.round(persona.completeness_score)}% completo
                  </span>
                </div>
                <div onClick={(e) => e.stopPropagation()}>
                  <FocusModeButton
                    domain="buyer_persona"
                    entityId={persona.id}
                    label={persona.name}
                    entityData={persona as unknown as Record<string, unknown>}
                    className="w-full rounded-full text-xs h-7"
                  />
                </div>
              </div>
            ))}

            {/* Add new persona */}
            <div
              className="flex flex-col items-center justify-center p-4 rounded-xl border-2 border-dashed border-border/50 hover:border-primary/30 hover:bg-muted/30 transition-all cursor-pointer min-h-[180px]"
              onClick={() => setShowModeSelector(true)}
            >
              <Plus className="w-6 h-6 text-muted-foreground mb-2" />
              <span className="text-sm text-muted-foreground">Nueva Persona</span>
            </div>
          </div>

          {showModeSelector && (
            <div className="mt-4 p-6 border-2 border-dashed rounded-xl bg-muted/20 text-center">
              <p className="text-sm text-muted-foreground mb-4">
                ¿Cómo quieres crear tu buyer persona?
              </p>
              <div className="flex gap-4 justify-center">
                <Button
                  onClick={() => void handleModoInteligente()}
                  className="shadow-lg shadow-purple-500/20 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white border-none"
                >
                  <Sparkles className="w-4 h-4 mr-2" />
                  Modo Inteligente
                </Button>
                <Button variant="outline" onClick={() => void handleModoManual()}>
                  <PenLine className="w-4 h-4 mr-2" />
                  Modo Manual
                </Button>
                <Button variant="ghost" onClick={() => setShowModeSelector(false)}>
                  Cancelar
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </section>
  );
}
