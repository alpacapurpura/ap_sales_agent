"use client";

import { useParams } from "next/navigation";
import { useMemo } from "react";

import { UniversalEditableSection } from "@/components/form-runtime";
import { BuyerPersonaInstancePicker } from "@/features/brand-studio/components/BuyerPersonaInstancePicker";
import { useBuyerPersona } from "@/features/brand-studio/hooks/use-buyer-persona";
import { useBrandStudioFieldRouting } from "@/features/brand-studio/hooks/use-field-routing";
import { buyerPersonaSchema } from "@/features/brand-studio/schemas/buyer-persona.schema";

import "@/features/brand-studio/schemas";
import type { BuyerPersona, BuyerPersonaSectionUpdateDTO } from "@/lib/api/buyer-persona";

const EDITABLE_FIELDS = [
  "name",
  "tagline",
  "demographics",
  "psychographics",
  "pain_points",
  "desires",
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
 * Buyer persona editor wired inside the Finder 4-column layout:
 *   Col 1 (layout.tsx) · sections rail
 *   Col 2 (instanceColumn) · BuyerPersonaInstancePicker — all personas for this tenant
 *   Col 3 (UniversalEditableSection · fields) · persona schema fields
 *   Col 4 (UniversalEditableSection · editor) · active field editor + Recomendaciones
 *
 * Route: /{tenantId}/brand-studio/publico/persona/{personaId}/{fieldId?}
 */
export function PersonaDetailPage() {
  const params = useParams<{ tenantId?: string; personaId?: string }>();
  const tenantId = params?.tenantId ?? "";
  const personaId = params?.personaId ?? "";

  const { persona, isLoading, save } = useBuyerPersona(tenantId, personaId);
  const { activeFieldId, getFieldHref } = useBrandStudioFieldRouting(
    `publico/persona/${personaId}`,
  );

  const values = useMemo(() => toEditable(persona ?? null), [persona]);

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
    <UniversalEditableSection<BuyerPersonaSectionUpdateDTO>
      schema={buyerPersonaSchema}
      values={values}
      isLoading={isLoading}
      onSave={save}
      activeFieldId={activeFieldId}
      getFieldHref={getFieldHref}
      instanceColumn={
        <BuyerPersonaInstancePicker tenantId={tenantId} activePersonaId={personaId} />
      }
    />
  );
}
