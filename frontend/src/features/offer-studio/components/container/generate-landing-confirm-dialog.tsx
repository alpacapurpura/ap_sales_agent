"use client";

import { Loader2 } from "lucide-react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

export interface GenerateLandingConfirmDialogProps {
  open: boolean;
  isSubmitting?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

/**
 * Confirmation dialog shown before firing the landing-generation mutation.
 *
 * The flow is intentionally minimal — the user needs to understand that the
 * operation is asynchronous (≈30s) and uses the current offer data. Actual
 * polling and toasts are handled by `useLandingStatus`.
 */
export function GenerateLandingConfirmDialog({
  open,
  isSubmitting = false,
  onConfirm,
  onCancel,
}: GenerateLandingConfirmDialogProps) {
  return (
    <AlertDialog
      open={open}
      onOpenChange={(next) => {
        if (!next && !isSubmitting) onCancel();
      }}
    >
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Generar landing con IA</AlertDialogTitle>
          <AlertDialogDescription>
            Voy a generar la landing page de esta oferta usando la información
            del editor. El proceso tarda alrededor de 30 segundos y podés
            seguir editando mientras termina.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isSubmitting} onClick={onCancel}>
            Cancelar
          </AlertDialogCancel>
          <AlertDialogAction
            disabled={isSubmitting}
            onClick={(event) => {
              event.preventDefault();
              onConfirm();
            }}
          >
            {isSubmitting ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden />
            ) : null}
            Generar ahora
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
