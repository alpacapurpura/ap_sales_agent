"use client";

import * as React from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";

import { useLaunchCampaignMutation } from "../api/use-launch-campaign-mutation";

import type { CampaignStatus } from "../types";

interface CampaignLifecycleButtonsProps {
  campaignId: string;
  status: CampaignStatus;
  onStatusChange?: () => void;
}

/**
 * Botones de ciclo de vida de una campaña.
 * Acciones según status:
 *   DRAFT → "Lanzar"
 *   SCHEDULED → "Cancelar"
 *   RUNNING → "Pausar" (placeholder)
 *   PAUSED / COMPLETED / CANCELLED → sin acciones
 */
export function CampaignLifecycleButtons({
  campaignId,
  status,
  onStatusChange,
}: CampaignLifecycleButtonsProps) {
  const launchMutation = useLaunchCampaignMutation();
  const { isPending } = launchMutation;

  async function handleLaunch() {
    try {
      await launchMutation.mutateAsync({ campaignId });
      toast.success("Campaña lanzada correctamente.");
      onStatusChange?.();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Error al lanzar la campaña.";
      toast.error(message);
    }
  }

  if (status === "DRAFT" || status === "SCHEDULED") {
    return (
      <div className="flex items-center gap-2">
        {status === "DRAFT" && (
          <Button
            type="button"
            onClick={() => void handleLaunch()}
            disabled={isPending}
            aria-busy={isPending}
          >
            {isPending ? "Lanzando…" : "Lanzar campaña"}
          </Button>
        )}
        {status === "SCHEDULED" && (
          <Button type="button" variant="secondary" disabled aria-disabled="true">
            Programada (cancelar — próximo PI)
          </Button>
        )}
      </div>
    );
  }

  if (status === "RUNNING") {
    return (
      <div className="flex items-center gap-2">
        <Button type="button" variant="secondary" disabled aria-disabled="true">
          Pausar (próximo PI)
        </Button>
      </div>
    );
  }

  return null;
}
