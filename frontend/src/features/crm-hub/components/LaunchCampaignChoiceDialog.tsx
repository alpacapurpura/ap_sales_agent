"use client";

import { useRouter } from "next/navigation";
import * as React from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface LaunchCampaignChoiceDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  segmentId: string;
  segmentName: string;
}

/**
 * Dialog de elección post-creación de segmento.
 * "Sí, crear campaña" → navega a /sales/campañas/nuevo?segment_id={id}.
 * "Más tarde" → cierra.
 */
export function LaunchCampaignChoiceDialog({
  open,
  onOpenChange,
  segmentId,
  segmentName,
}: LaunchCampaignChoiceDialogProps) {
  const router = useRouter();

  function handleCreateCampaign() {
    onOpenChange(false);
    router.push(`/sales/campa%C3%B1as/nuevo?segment_id=${encodeURIComponent(segmentId)}`);
  }

  function handleDismiss() {
    onOpenChange(false);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[440px]">
        <DialogHeader>
          <DialogTitle>Segmento &quot;{segmentName}&quot; creado</DialogTitle>
          <DialogDescription>
            ¿Quieres lanzar una campaña Telegram a estos contactos ahora?
          </DialogDescription>
        </DialogHeader>

        <DialogFooter className="mt-4 flex-col-reverse sm:flex-row gap-2">
          <Button type="button" variant="ghost" onClick={handleDismiss}>
            Más tarde
          </Button>
          <Button type="button" onClick={handleCreateCampaign}>
            Sí, crear campaña
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
