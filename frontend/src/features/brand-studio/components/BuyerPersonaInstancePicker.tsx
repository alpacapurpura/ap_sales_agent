"use client";

import { useMemo } from "react";

import { InstancePicker, type InstancePickerInstance } from "@/components/form-runtime";
import { useGuidedEntityCreation } from "@/features/copilot/hooks/use-guided-entity-creation";

import { useBuyerPersonas } from "../hooks/use-buyer-personas";

import type { BuyerPersona } from "@/lib/api/buyer-persona";

export interface BuyerPersonaInstancePickerProps {
  tenantId: string;
  activePersonaId: string | null;
}

const DEFAULT_PERSONA_NAME = "Nueva persona";

function nextDefaultName(currentCount: number): string {
  return currentCount === 0 ? DEFAULT_PERSONA_NAME : `${DEFAULT_PERSONA_NAME} ${currentCount + 1}`;
}

/**
 * Column 2 of the Finder layout when the user is inside the Buyer Personas
 * section. Lists every persona for the current tenant and triggers the
 * AI-led create flow: the copilot opens in guided mode and the user can
 * speak, paste a URL or upload a document to fill the persona end-to-end.
 *
 * "Manual" creation is intentionally not exposed — the copilot is the
 * default entry point. If the chat is unavailable, the hook still navigates
 * to the freshly-created persona so the user can edit it by hand from the
 * detail page.
 */
export function BuyerPersonaInstancePicker({
  tenantId,
  activePersonaId,
}: BuyerPersonaInstancePickerProps) {
  const { personas, create } = useBuyerPersonas();

  const instances = useMemo<InstancePickerInstance[]>(
    () =>
      personas.map((persona) => ({
        id: persona.id,
        primary: persona.name || "Sin nombre",
        secondary: persona.tagline || (persona.is_primary ? "Avatar ideal" : "Persona secundaria"),
        completion: persona.completeness_score ?? 0,
      })),
    [personas],
  );

  const { create: handleCreate, creating } = useGuidedEntityCreation<BuyerPersona>({
    domain: "buyer_persona",
    tenantId,
    createEntity: () =>
      create({
        name: nextDefaultName(personas.length),
        scope: "GLOBAL",
      }),
  });

  return (
    <InstancePicker
      title="Personas"
      createLabel={creating ? "Creando…" : "Crear nueva persona"}
      onCreate={handleCreate}
      activeInstanceId={activePersonaId}
      instances={instances}
      getInstanceHref={(id) => `/${tenantId}/brand-studio/publico/persona/${id}`}
    />
  );
}
