"use client";

import { Sparkles } from "lucide-react";
import { useParams } from "next/navigation";

import { BuyerPersonaInstancePicker } from "@/features/brand-studio/components/BuyerPersonaInstancePicker";

/**
 * Landing view for `/brand-studio/publico` (no persona selected yet). Renders
 * the BuyerPersonaInstancePicker as column 2 and a welcome pane that invites
 * the user to pick or create a persona — the editor stays empty until then.
 *
 * Once the user clicks a row, they land on
 * `/brand-studio/publico/persona/{id}` → `PersonaDetailPage`, where the full
 * 4-column Finder layout takes over.
 */
export function BuyerPersonasLandingPage() {
  const params = useParams<{ tenantId?: string }>();
  const tenantId = params?.tenantId ?? "";

  return (
    <div className="flex min-h-0 min-w-0 flex-1">
      <BuyerPersonaInstancePicker tenantId={tenantId} activePersonaId={null} />
      <div className="flex min-h-0 min-w-0 flex-1 items-center justify-center bg-card p-12 text-center">
        <div className="max-w-[420px]">
          <div className="mx-auto mb-5 flex h-12 w-12 items-center justify-center rounded-full bg-brand/15 text-brand">
            <Sparkles className="h-6 w-6" aria-hidden="true" />
          </div>
          <h1 className="mb-3 text-xl font-semibold text-foreground">
            Elige o crea una buyer persona
          </h1>
          <p className="text-sm leading-relaxed text-muted-foreground">
            Las buyer personas son el mapa emocional de tu cliente ideal. Cada una acumula dolores,
            deseos, objeciones y disparadores que alimentan al Sales Agent y al generador de copy.
          </p>
          <p className="mt-4 text-xs text-muted-foreground">
            Selecciona una del panel izquierdo o toca{" "}
            <span className="font-medium text-foreground">Crear nueva persona</span>.
          </p>
        </div>
      </div>
    </div>
  );
}
