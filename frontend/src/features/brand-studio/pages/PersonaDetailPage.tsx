"use client";

import { useParams } from "next/navigation";

import "@/features/brand-studio/actions/registry";

import { useBuyerPersona } from "@/features/brand-studio/hooks/use-buyer-persona";

/**
 * Single buyer persona detail view. Sprint 1 stub — Sprint 2 replaces the
 * placeholder with the ported avatar-form rich action wrapped in
 * UniversalEditableSection once the buyer-persona sub-schema is defined.
 */
export function PersonaDetailPage() {
  const params = useParams<{ tenantId: string; personaId: string }>();
  const tenantId = params?.tenantId ?? "";
  const personaId = params?.personaId ?? "";

  const { persona, isLoading } = useBuyerPersona(tenantId, personaId);

  if (isLoading) return <div className="p-4 text-sm text-muted-foreground">Cargando…</div>;
  if (!persona)
    return <div className="p-4 text-sm text-muted-foreground">Persona no encontrada</div>;

  return (
    <section className="p-4">
      <h1 className="text-lg font-semibold">{persona.name ?? "Buyer persona"}</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Editor detallado pendiente de portar en Sprint 2 (AvatarAction).
      </p>
    </section>
  );
}
