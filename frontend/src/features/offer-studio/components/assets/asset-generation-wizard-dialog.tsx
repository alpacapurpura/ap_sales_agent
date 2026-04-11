"use client";

import { Sparkles } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

export interface AssetGenerationWizardDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/**
 * Stub for the future asset-generation wizard. The full multi-step flow
 * (type → params → generate → preview → save) is out of scope for this
 * feature. For now it explains the upcoming capability and closes.
 */
export function AssetGenerationWizardDialog({
  open,
  onOpenChange,
}: AssetGenerationWizardDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <div className="mb-2 inline-flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
            <Sparkles className="h-5 w-5 text-primary" aria-hidden />
          </div>
          <DialogTitle>Generar asset con IA</DialogTitle>
          <DialogDescription>
            Próximamente. El wizard te permitirá elegir el tipo (flyer, video,
            carrusel), ajustar parámetros y generar el asset con IA usando la
            información de tu oferta.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Entendido
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
