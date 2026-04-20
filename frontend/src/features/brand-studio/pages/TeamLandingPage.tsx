"use client";

import { Users } from "lucide-react";
import { useParams } from "next/navigation";

import { TeamMemberInstancePicker } from "@/features/brand-studio/components/TeamMemberInstancePicker";

/**
 * Landing view for ``/brand-studio/team`` (no member selected yet).
 */
export function TeamLandingPage() {
  const params = useParams<{ tenantId?: string }>();
  const tenantId = params?.tenantId ?? "";

  return (
    <div className="flex min-h-0 min-w-0 flex-1">
      <TeamMemberInstancePicker tenantId={tenantId} activeMemberId={null} />
      <div className="flex min-h-0 min-w-0 flex-1 items-center justify-center bg-card p-12 text-center">
        <div className="max-w-[420px]">
          <div className="mx-auto mb-5 flex h-12 w-12 items-center justify-center rounded-full bg-brand/15 text-brand">
            <Users className="h-6 w-6" aria-hidden="true" />
          </div>
          <h1 className="mb-3 text-xl font-semibold text-foreground">
            Elige o agrega un miembro del equipo
          </h1>
          <p className="text-sm leading-relaxed text-muted-foreground">
            El equipo es la cara humana de la marca. La persona marcada como voz principal define
            cómo habla el Sales Agent. Cada miembro se reutiliza en landings y ofertas via
            placements.
          </p>
          <p className="mt-4 text-xs text-muted-foreground">
            Selecciona uno del panel izquierdo o toca{" "}
            <span className="font-medium text-foreground">Agregar miembro al equipo</span>.
          </p>
        </div>
      </div>
    </div>
  );
}
