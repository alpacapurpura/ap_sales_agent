"use client";

import { Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { BusinessTypesSelector } from "@/features/tenant-profile/components/BusinessTypesSelector";
import { useUpdateTenantProfile } from "@/features/tenant-profile/hooks/use-update-tenant-profile";

import type { ExpertBusinessTypeSlug } from "@/features/tenant-profile/types/tenant-profile";

interface BusinessTypesOnboardingClientProps {
  tenantId: string;
  returnTo: string;
}

/**
 * Client component for the onboarding perfil-negocio page.
 *
 * Handles state, mutation, and redirect after successful save.
 * CONTRACT §6.3
 */
export function BusinessTypesOnboardingClient({
  tenantId,
  returnTo,
}: BusinessTypesOnboardingClientProps) {
  const router = useRouter();
  const [selected, setSelected] = useState<ExpertBusinessTypeSlug[]>([]);
  const mutation = useUpdateTenantProfile();

  const handleSubmit = async () => {
    if (selected.length === 0) return;

    const result = await mutation.mutateAsync({ business_types: selected });

    if (!result.ok) {
      toast.error("No se pudo guardar el tipo de negocio. Intentá de nuevo.");
      return;
    }

    toast.success("¡Listo! Tu perfil fue configurado.");
    router.push(returnTo);
  };

  const canSubmit = selected.length >= 1 && !mutation.isPending;

  return (
    <div className="space-y-6">
      <BusinessTypesSelector value={selected} onChange={setSelected} min={1} max={2} />

      <div className="flex justify-center pt-4">
        <Button size="lg" onClick={handleSubmit} disabled={!canSubmit} className="min-w-[200px]">
          {mutation.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Guardando...
            </>
          ) : (
            "Empezar"
          )}
        </Button>
      </div>

      {selected.length === 0 && (
        <p className="text-center text-xs text-muted-foreground">
          Seleccioná al menos un tipo para continuar.
        </p>
      )}
    </div>
  );
}
