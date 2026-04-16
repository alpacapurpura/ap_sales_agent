"use client";

import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X, Loader2 } from "lucide-react";
import { Suspense, useRef, useEffect, useState } from "react";

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
import { DialogOverlay } from "@/components/ui/dialog";

import { getConnectionView } from "../../../lib/channel-view-map";

/* eslint-disable react-hooks/static-components -- dynamic view from registry */
function ConnectionViewRenderer({ channelSlug }: { channelSlug: string }) {
  const View = getConnectionView(channelSlug);
  if (!View) {
    return (
      <p className="text-sm text-muted-foreground py-8 text-center">
        No hay vista de configuración disponible para este canal.
      </p>
    );
  }
  return <View />;
}
/* eslint-enable react-hooks/static-components */

interface ChannelConnectionModalProps {
  channelSlug: string | null;
  channelName: string;
  onClose: () => void;
}

export function ChannelConnectionModal({
  channelSlug,
  channelName,
  onClose,
}: ChannelConnectionModalProps) {
  const hasInteracted = useRef(false);
  const [showConfirm, setShowConfirm] = useState(false);

  // Reset interaction tracking when channel changes
  useEffect(() => {
    hasInteracted.current = false;
  }, [channelSlug]);

  const handleClose = () => {
    if (hasInteracted.current) {
      setShowConfirm(true);
    } else {
      onClose();
    }
  };

  return (
    <>
      <DialogPrimitive.Root
        open={channelSlug !== null}
        onOpenChange={(open) => {
          if (!open) handleClose();
        }}
      >
        <DialogPrimitive.Portal>
          <DialogOverlay />
          <DialogPrimitive.Content
            className="fixed left-[50%] top-[50%] z-50 grid w-full max-w-3xl translate-x-[-50%] translate-y-[-50%] gap-4 border bg-background p-6 shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] sm:rounded-lg max-h-[85vh] overflow-y-auto"
            onInteractOutside={(e) => e.preventDefault()}
            onEscapeKeyDown={(e) => {
              e.preventDefault();
              handleClose();
            }}
            onPointerDown={() => {
              hasInteracted.current = true;
            }}
          >
            <div className="flex items-center justify-between">
              <DialogPrimitive.Title className="text-lg font-semibold leading-none tracking-tight">
                Configurar {channelName}
              </DialogPrimitive.Title>
              <button
                onClick={handleClose}
                className="rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
              >
                <X className="h-4 w-4" />
                <span className="sr-only">Cerrar</span>
              </button>
            </div>

            <DialogPrimitive.Description className="sr-only">
              Panel de configuración para conectar {channelName}
            </DialogPrimitive.Description>

            {channelSlug ? (
              <Suspense
                fallback={
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  </div>
                }
              >
                <ConnectionViewRenderer channelSlug={channelSlug} />
              </Suspense>
            ) : (
              <p className="text-sm text-muted-foreground py-8 text-center">
                No hay vista de configuración disponible para este canal.
              </p>
            )}
          </DialogPrimitive.Content>
        </DialogPrimitive.Portal>
      </DialogPrimitive.Root>

      <AlertDialog open={showConfirm} onOpenChange={setShowConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Salir de la configuración?</AlertDialogTitle>
            <AlertDialogDescription>
              Si sales ahora, podrías perder el progreso de configuración de este canal.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Continuar configurando</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                setShowConfirm(false);
                onClose();
              }}
            >
              Salir
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
