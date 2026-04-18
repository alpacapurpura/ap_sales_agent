"use client";

import { useParams } from "next/navigation";
import { useCallback, useMemo } from "react";

import { UniversalEditableSection } from "@/components/form-runtime";
import { useBuyerPersona } from "@/features/brand-studio/hooks/use-buyer-persona";
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
 * Buyer persona detail page. Reads the persona via useBuyerPersona (which
 * uses the shared useAutoSave primitive) and wires it into the form-runtime
 * via UniversalEditableSection + the buyer-persona schema. URL-driven per
 * field — active field is taken from the route's [fieldId] segment.
 *
 * Route: /{tenantId}/brand-studio/publico/persona/{personaId}/{fieldId?}
 */
export function PersonaDetailPage() {
  const params = useParams<{
    tenantId?: string;
    personaId?: string;
    fieldId?: string | string[];
  }>();
  const tenantId = params?.tenantId ?? "";
  const personaId = params?.personaId ?? "";

  const activeFieldId = useMemo(() => {
    const raw = params?.fieldId;
    if (!raw) return null;
    return Array.isArray(raw) ? (raw[0] ?? null) : raw;
  }, [params]);

  const getFieldHref = useCallback(
    (fieldId: string | null) => {
      const base = `/${tenantId}/brand-studio/publico/persona/${personaId}`;
      return fieldId === null ? base : `${base}/${fieldId}`;
    },
    [tenantId, personaId],
  );

  const { persona, isLoading, save } = useBuyerPersona(tenantId, personaId);

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
    />
  );
}
