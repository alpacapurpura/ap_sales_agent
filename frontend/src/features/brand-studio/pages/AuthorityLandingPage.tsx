"use client";

import { Award } from "lucide-react";
import { useParams } from "next/navigation";

import { AuthorityItemInstancePicker } from "@/features/brand-studio/components/AuthorityItemInstancePicker";

/**
 * Landing view for ``/brand-studio/authority`` (no item selected yet).
 */
export function AuthorityLandingPage() {
  const params = useParams<{ tenantId?: string }>();
  const tenantId = params?.tenantId ?? "";

  return (
    <div className="flex min-h-0 min-w-0 flex-1">
      <AuthorityItemInstancePicker tenantId={tenantId} activeItemId={null} />
      <div className="flex min-h-0 min-w-0 flex-1 items-center justify-center bg-card p-12 text-center">
        <div className="max-w-[420px]">
          <div className="mx-auto mb-5 flex h-12 w-12 items-center justify-center rounded-full bg-brand/15 text-brand">
            <Award className="h-6 w-6" aria-hidden="true" />
          </div>
          <h1 className="mb-3 text-xl font-semibold text-foreground">
            Elige o agrega una señal de autoridad
          </h1>
          <p className="text-sm leading-relaxed text-muted-foreground">
            Premios, certificaciones, menciones en medios, logos de clientes y publicaciones son las
            señales que construyen credibilidad. Se reutilizan en landings, ofertas y en la voz del
            Sales Agent.
          </p>
          <p className="mt-4 text-xs text-muted-foreground">
            Selecciona una del panel izquierdo o toca{" "}
            <span className="font-medium text-foreground">Agregar señal de autoridad</span>.
          </p>
        </div>
      </div>
    </div>
  );
}
