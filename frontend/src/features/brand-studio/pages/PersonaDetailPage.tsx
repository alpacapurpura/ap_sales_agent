"use client";

import { useAuth } from "@clerk/nextjs";
import { useParams } from "next/navigation";
import { useCallback, useMemo } from "react";

import { useBuyerPersona } from "@/features/brand-studio/hooks/use-buyer-persona";
import { buyerPersonaSchema } from "@/features/brand-studio/schemas/buyer-persona.schema";
import { startInterview } from "@/features/copilot/api/interview-api";
import { useCopilotStore } from "@/features/copilot/store/copilot-store";

import { SectionPage } from "./SectionPage";

import "@/features/brand-studio/schemas";
import type { BuyerPersona, BuyerPersonaSectionUpdateDTO } from "@/lib/api/buyer-persona";

const EDITABLE_FIELDS = [
  "name",
  "tagline",
  "demographics",
  "psychographics",
  "pain_points",
  "desires",
  "objections",
  "preferred_channels",
  "buyer_journey",
  "purchase_triggers",
  "anti_patterns",
] as const satisfies readonly (keyof BuyerPersonaSectionUpdateDTO)[];

function toEditable(persona: BuyerPersona | null): BuyerPersonaSectionUpdateDTO {
  if (!persona) return {};
  const patch: BuyerPersonaSectionUpdateDTO = {};
  for (const key of EDITABLE_FIELDS) {
    const v = persona[key];
    if (v !== null && v !== undefined) (patch as Record<string, unknown>)[key] = v;
  }
  return patch;
}

/**
 * Buyer persona detail page. Delegates rendering to SectionPage (the shared
 * brand-studio wrapper) so field routing + the "Modo entrevista" CTA stay
 * consistent with every other section. The only divergence from the factory
 * pattern is that this page resolves a single persona by id instead of a
 * BrandSettings slice — buyer personas are multi-instance entities.
 *
 * Route: /{tenantId}/brand-studio/publico/persona/{personaId}/{fieldId?}
 */
export function PersonaDetailPage() {
  const { getToken } = useAuth();
  const params = useParams<{ tenantId?: string; personaId?: string }>();
  const tenantId = params?.tenantId ?? "";
  const personaId = params?.personaId ?? "";

  const { persona, isLoading, save } = useBuyerPersona(tenantId, personaId);

  const values = useMemo(() => toEditable(persona ?? null), [persona]);

  const handleStartInterview = useCallback(async () => {
    if (!personaId) return;
    try {
      const token = await getToken();
      if (!token) return;
      const interview = await startInterview(token, "buyer_persona", personaId);
      const store = useCopilotStore.getState();
      store.setSession({
        sectionKey: "brand.buyer-persona",
        label: persona?.name ?? "Buyer persona",
        entityId: personaId,
        procedure: "interview",
        sessionId: interview.session_id,
        startedAt: new Date(),
        snapshot: {},
      });
      store.setConversationId(interview.conversation_id);
      store.addMessage({
        id: crypto.randomUUID(),
        role: "assistant",
        content: interview.initial_message,
        timestamp: Date.now(),
      });
      store.setSidebarState("open");
    } catch (err) {
      console.error("Failed to start buyer persona interview", err);
    }
  }, [getToken, persona, personaId]);

  if (!personaId) {
    return (
      <div className="p-4 text-sm text-muted-foreground">
        No se especificó el identificador del persona.
      </div>
    );
  }

  if (!isLoading && !persona) {
    return <div className="p-4 text-sm text-muted-foreground">Persona no encontrada</div>;
  }

  return (
    <SectionPage<BuyerPersonaSectionUpdateDTO>
      sectionSlug={`publico/persona/${personaId}`}
      schema={buyerPersonaSchema}
      values={values}
      isLoading={isLoading}
      onSave={save}
      onStartInterview={handleStartInterview}
    />
  );
}
