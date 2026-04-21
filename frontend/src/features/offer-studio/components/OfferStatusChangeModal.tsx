"use client";

import { type LucideIcon } from "lucide-react";
import {
  AlertTriangle,
  Archive,
  Check,
  FileText,
  Info,
  Link2,
  PauseCircle,
  PlayCircle,
  RotateCcw,
  X,
  Loader2,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

import type { OfferLifecycleStatus } from "../types/enums";

type Tone = "success" | "warning" | "info" | "danger";

interface Consequence {
  icon: LucideIcon;
  tone: Tone;
  text: string;
}

export interface OfferStatusChangeModalProps {
  open: boolean;
  fromStatus: OfferLifecycleStatus;
  toStatus: OfferLifecycleStatus;
  offerName: string;
  isSubmitting?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

// Transition copy — hardcoded consequence library per UI-SPEC §Shared Components.
type TransitionKey = `${OfferLifecycleStatus}_${OfferLifecycleStatus}`;

const TRANSITION_META: Partial<
  Record<
    TransitionKey,
    {
      title: string;
      confirmLabel: string;
      confirmTone: "default" | "destructive";
      consequences: Consequence[];
    }
  >
> = {
  draft_active: {
    title: "Activar oferta",
    confirmLabel: "Activar",
    confirmTone: "default",
    consequences: [
      {
        icon: Check,
        tone: "success",
        text: "Tu Sales Agent empezará a proponerla en conversaciones.",
      },
      {
        icon: AlertTriangle,
        tone: "warning",
        text: "La landing se generará cuando llegues al 90% de completitud.",
      },
      {
        icon: Info,
        tone: "info",
        text: "Puedes pausarla o archivarla cuando quieras.",
      },
    ],
  },
  active_paused: {
    title: "Pausar oferta",
    confirmLabel: "Pausar",
    confirmTone: "default",
    consequences: [
      {
        icon: PauseCircle,
        tone: "warning",
        text: "El Sales Agent dejará de proponerla, pero la reconocerá si un cliente pregunta.",
      },
      {
        icon: Link2,
        tone: "info",
        text: "La landing pública sigue viva. Despublícala manualmente si quieres bajarla.",
      },
      {
        icon: RotateCcw,
        tone: "success",
        text: "Puedes reactivarla en cualquier momento sin perder nada.",
      },
    ],
  },
  active_draft: {
    title: "Volver a borrador",
    confirmLabel: "Volver a borrador",
    confirmTone: "default",
    consequences: [
      {
        icon: FileText,
        tone: "info",
        text: "La oferta vuelve a modo edición. El Sales Agent dejará de proponerla.",
      },
      {
        icon: AlertTriangle,
        tone: "warning",
        text: "La landing pública se despublicará automáticamente.",
      },
      {
        icon: RotateCcw,
        tone: "success",
        text: "Puedes volver a activarla después sin perder ningún dato.",
      },
    ],
  },
  active_archived: {
    title: "Archivar oferta",
    confirmLabel: "Archivar",
    confirmTone: "destructive",
    consequences: [
      {
        icon: Archive,
        tone: "warning",
        text: "La oferta se moverá a 'Archivadas' y el Sales Agent dejará de proponerla.",
      },
      {
        icon: X,
        tone: "danger",
        text: "La landing pública se despublicará automáticamente.",
      },
      {
        icon: RotateCcw,
        tone: "info",
        text: "Es reversible: puedes restaurarla desde el panel de archivadas.",
      },
    ],
  },
  paused_active: {
    title: "Reactivar oferta",
    confirmLabel: "Reactivar",
    confirmTone: "default",
    consequences: [
      {
        icon: PlayCircle,
        tone: "success",
        text: "El Sales Agent volverá a proponerla en conversaciones.",
      },
      {
        icon: Info,
        tone: "info",
        text: "La landing se revisa y regenera si la oferta cambió desde que se pausó.",
      },
      {
        icon: Check,
        tone: "success",
        text: "Todos los datos y configuraciones se mantienen intactos.",
      },
    ],
  },
  paused_draft: {
    title: "Volver a borrador",
    confirmLabel: "Volver a borrador",
    confirmTone: "default",
    consequences: [
      {
        icon: FileText,
        tone: "info",
        text: "La oferta vuelve a modo edición.",
      },
      {
        icon: AlertTriangle,
        tone: "warning",
        text: "La landing pública se despublicará automáticamente si estaba activa.",
      },
      {
        icon: RotateCcw,
        tone: "success",
        text: "Puedes reactivarla cuando quieras.",
      },
    ],
  },
  paused_archived: {
    title: "Archivar oferta",
    confirmLabel: "Archivar",
    confirmTone: "destructive",
    consequences: [
      {
        icon: Archive,
        tone: "warning",
        text: "La oferta se moverá a 'Archivadas' y queda fuera del Sales Agent.",
      },
      {
        icon: X,
        tone: "danger",
        text: "La landing pública se despublicará automáticamente.",
      },
      {
        icon: RotateCcw,
        tone: "info",
        text: "Es reversible: puedes restaurarla desde el panel de archivadas.",
      },
    ],
  },
  draft_archived: {
    title: "Archivar oferta",
    confirmLabel: "Archivar",
    confirmTone: "destructive",
    consequences: [
      {
        icon: Archive,
        tone: "warning",
        text: "La oferta se moverá a 'Archivadas'.",
      },
      {
        icon: Info,
        tone: "info",
        text: "No hay landing publicada para despublicar (sigue en borrador).",
      },
      {
        icon: RotateCcw,
        tone: "success",
        text: "Es reversible: puedes restaurarla desde el panel de archivadas.",
      },
    ],
  },
};

const TONE_CLASSES: Record<Tone, string> = {
  success: "text-success",
  warning: "text-warning",
  info: "text-info",
  danger: "text-destructive",
};

/**
 *
 */
export function OfferStatusChangeModal({
  open,
  fromStatus,
  toStatus,
  offerName,
  isSubmitting = false,
  onConfirm,
  onCancel,
}: OfferStatusChangeModalProps) {
  const key: TransitionKey = `${fromStatus}_${toStatus}`;
  const meta = TRANSITION_META[key];

  const title = meta?.title ?? "Cambiar estado de la oferta";
  const confirmLabel = meta?.confirmLabel ?? "Confirmar";
  const confirmTone = meta?.confirmTone ?? "default";
  const consequences = meta?.consequences ?? [];

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!next && !isSubmitting) onCancel();
      }}
    >
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>
            <span className="font-medium text-foreground">{offerName}</span>
          </DialogDescription>
        </DialogHeader>

        {consequences.length > 0 ? (
          <ul className="flex flex-col gap-3 py-2">
            {consequences.map((c: Consequence, i: number) => {
              const Icon = c.icon;
              return (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <Icon
                    className={cn("mt-0.5 h-4 w-4 shrink-0", TONE_CLASSES[c.tone])}
                    aria-hidden
                  />
                  <span className="text-muted-foreground">{c.text}</span>
                </li>
              );
            })}
          </ul>
        ) : (
          <p className="py-2 text-sm text-muted-foreground">
            ¿Quieres cambiar el estado de esta oferta?
          </p>
        )}

        <DialogFooter className="gap-2 sm:gap-2">
          <Button type="button" variant="outline" onClick={onCancel} disabled={isSubmitting}>
            Cancelar
          </Button>
          <Button
            type="button"
            variant={confirmTone === "destructive" ? "destructive" : "default"}
            onClick={onConfirm}
            disabled={isSubmitting}
          >
            {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : null}
            {confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
