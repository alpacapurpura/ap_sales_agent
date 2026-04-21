"use client";

import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { BusinessTypesSelector } from "@/features/tenant-profile/components/BusinessTypesSelector";
import { ChangeBusinessTypesConfirmDialog } from "@/features/tenant-profile/components/ChangeBusinessTypesConfirmDialog";
import { useTenantProfile } from "@/features/tenant-profile/hooks/use-tenant-profile";
import { useUpdateTenantProfile } from "@/features/tenant-profile/hooks/use-update-tenant-profile";
import { formatNextAllowed } from "@/features/tenant-profile/utils/rate-limit";

import type { ExpertBusinessTypeSlug } from "@/features/tenant-profile/types/tenant-profile";

/**
 * Client component for the perfil-negocio settings section.
 *
 * Loads data via React Query (useTenantProfile) — no server prefetch prop.
 * This aligns with the brand-studio pattern where all sections hydrate
 * via hooks rather than server props.
 *
 * Shows confirm dialog before submitting post-declaration changes.
 * Shows tooltip on disabled submit when can_change_now is false.
 *
 * Spanish rule 11: all user-facing text is español latinoamericano neutro.
 */
export function PerfilNegocioSection() {
  const { data: profile, isLoading } = useTenantProfile();

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-9 w-28" />
      </div>
    );
  }

  return (
    <PerfilNegocioForm initialBusinessTypes={profile?.business_types ?? []} profile={profile} />
  );
}

interface PerfilNegocioFormProps {
  initialBusinessTypes: ExpertBusinessTypeSlug[];
  profile: ReturnType<typeof useTenantProfile>["data"];
}

function PerfilNegocioForm({ initialBusinessTypes, profile }: PerfilNegocioFormProps) {
  const [selected, setSelected] = useState<ExpertBusinessTypeSlug[]>(initialBusinessTypes);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const mutation = useUpdateTenantProfile();

  const canChangeNow = profile?.can_change_now ?? true;
  const nextAllowedRaw = profile?.next_allowed_change_at ?? null;
  const nextAllowedLabel = nextAllowedRaw ? formatNextAllowed(nextAllowedRaw) : null;
  const isFirstDeclaration = !profile?.declared_at;

  const hasChanges =
    selected.length > 0 &&
    JSON.stringify([...selected].sort()) !==
      JSON.stringify([...(profile?.business_types ?? [])].sort());

  const handleSubmitClick = () => {
    if (isFirstDeclaration) {
      void handleConfirm();
    } else {
      setConfirmOpen(true);
    }
  };

  const handleConfirm = async () => {
    setConfirmOpen(false);
    const result = await mutation.mutateAsync({ business_types: selected });

    if (!result.ok) {
      toast.error(
        `No puedes cambiar el tipo de negocio hasta el ${nextAllowedLabel ?? "próximo período"}.`,
      );
      return;
    }

    toast.success("Perfil de negocio actualizado.");
  };

  const submitDisabled = !hasChanges || !canChangeNow || mutation.isPending;

  const submitButton = (
    <Button onClick={handleSubmitClick} disabled={submitDisabled}>
      {mutation.isPending ? "Guardando..." : "Guardar cambios"}
    </Button>
  );

  return (
    <TooltipProvider>
      <div className="space-y-6">
        <BusinessTypesSelector value={selected} onChange={setSelected} min={1} max={2} />

        <div className="flex items-center gap-3 pt-2">
          {!canChangeNow && nextAllowedLabel ? (
            <Tooltip>
              <TooltipTrigger asChild>
                <span tabIndex={0}>{submitButton}</span>
              </TooltipTrigger>
              <TooltipContent side="top">
                <p>Próxima edición disponible: {nextAllowedLabel}</p>
              </TooltipContent>
            </Tooltip>
          ) : (
            submitButton
          )}
        </div>
      </div>

      <ChangeBusinessTypesConfirmDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        onConfirm={handleConfirm}
        confirming={mutation.isPending}
      />
    </TooltipProvider>
  );
}
