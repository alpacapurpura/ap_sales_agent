"use client";

import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { BusinessTypesSelector } from "@/features/tenant-profile/components/BusinessTypesSelector";
import { ChangeBusinessTypesConfirmDialog } from "@/features/tenant-profile/components/ChangeBusinessTypesConfirmDialog";
import { useTenantProfile } from "@/features/tenant-profile/hooks/use-tenant-profile";
import { useUpdateTenantProfile } from "@/features/tenant-profile/hooks/use-update-tenant-profile";
import { formatNextAllowed } from "@/features/tenant-profile/utils/rate-limit";

import type {
  ExpertBusinessTypeSlug,
  TenantProfileResponse,
} from "@/features/tenant-profile/types/tenant-profile";

interface PerfilNegocioSettingsClientProps {
  /** Server-fetched initial profile (may be null on first load). */
  initialProfile: TenantProfileResponse | null;
}

/**
 * Client component for the settings/perfil-negocio page.
 *
 * Hydrates from the server-rendered initialProfile, then switches to
 * the React Query hook for subsequent interactions.
 *
 * Shows confirm dialog before submitting post-declaration changes.
 * Shows tooltip on disabled submit when can_change_now is false.
 *
 * CONTRACT §6.5
 */
export function PerfilNegocioSettingsClient({ initialProfile }: PerfilNegocioSettingsClientProps) {
  const { data: liveProfile } = useTenantProfile();
  const profile = liveProfile ?? initialProfile;

  const [selected, setSelected] = useState<ExpertBusinessTypeSlug[]>(profile?.business_types ?? []);
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
        `No podés cambiar el tipo de negocio hasta el ${nextAllowedLabel ?? "próximo período"}.`,
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
