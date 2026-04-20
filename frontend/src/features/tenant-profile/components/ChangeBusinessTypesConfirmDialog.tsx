"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface ChangeBusinessTypesConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Called when the user confirms the change. */
  onConfirm: () => void;
  /** Whether the confirm action is in progress (shows loading state). */
  confirming?: boolean;
}

/**
 * Impact-warning modal shown before updating business_types post-declaration.
 *
 * Explains downstream effects (presets, landings, agent context) while
 * reassuring the user that existing offers are NOT modified.
 *
 * CONTRACT §6.5 — ChangeBusinessTypesConfirmDialog
 */
export function ChangeBusinessTypesConfirmDialog({
  open,
  onOpenChange,
  onConfirm,
  confirming = false,
}: ChangeBusinessTypesConfirmDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>¿Querés actualizar tu tipo de negocio?</DialogTitle>
          <DialogDescription asChild>
            <div className="space-y-3 text-sm text-muted-foreground">
              <p>Esto va a actualizar:</p>
              <ul className="list-disc list-inside space-y-1">
                <li>Los tipos de oferta disponibles en el wizard.</li>
                <li>Plantillas de landing sugeridas.</li>
                <li>El contexto del agente de ventas.</li>
              </ul>
              <p className="font-medium text-foreground">
                Tus ofertas y campañas actuales no se modifican.
              </p>
              <p>El cambio solo afecta lo que crees a partir de ahora.</p>
            </div>
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="gap-2 sm:gap-0">
          <Button variant="ghost" onClick={() => onOpenChange(false)} disabled={confirming}>
            Cancelar
          </Button>
          <Button onClick={onConfirm} disabled={confirming}>
            {confirming ? "Guardando..." : "Confirmar cambio"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
