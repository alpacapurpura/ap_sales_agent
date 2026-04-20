"use client";

import { useRouter } from "next/navigation";
import { useCallback, useMemo } from "react";

import { InstancePicker, type InstancePickerInstance } from "@/components/form-runtime";

import { useBuyerPersonas } from "../hooks/use-buyer-personas";

export interface BuyerPersonaInstancePickerProps {
  tenantId: string;
  activePersonaId: string | null;
}

/**
 * Column 2 of the Finder layout when the user is inside the Buyer Personas
 * section. Lists every persona for the current tenant, lets the user pick
 * one (navigates to /brand-studio/publico/persona/{id}) or create a new one.
 */
export function BuyerPersonaInstancePicker({
  tenantId,
  activePersonaId,
}: BuyerPersonaInstancePickerProps) {
  const router = useRouter();
  const { personas, create, isCreating } = useBuyerPersonas();

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

  const handleCreate = useCallback(async () => {
    if (isCreating) return;
    const persona = await create({ name: "Nueva persona", scope: "GLOBAL" });
    if (persona?.id) {
      router.push(`/${tenantId}/brand-studio/publico/persona/${persona.id}`);
    }
  }, [create, isCreating, router, tenantId]);

  return (
    <InstancePicker
      title="Personas"
      createLabel={isCreating ? "Creando…" : "Crear nueva persona"}
      onCreate={handleCreate}
      activeInstanceId={activePersonaId}
      instances={instances}
      getInstanceHref={(id) => `/${tenantId}/brand-studio/publico/persona/${id}`}
    />
  );
}
