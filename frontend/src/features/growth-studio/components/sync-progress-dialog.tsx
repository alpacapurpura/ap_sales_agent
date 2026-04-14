"use client";

import { useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { CheckCircle2, AlertCircle, Zap } from "lucide-react";
import { useGrowthSync } from "../context/growth-sync-context";

export function SyncProgressDialog() {
  const { isSyncing, syncResult, syncError, resetSync, startSync } = useGrowthSync();

  const isOpen = isSyncing || !!syncResult || !!syncError;
  const state: "processing" | "success" | "error" = syncError
    ? "error"
    : syncResult
      ? "success"
      : "processing";

  // Auto-close on success after 3s
  useEffect(() => {
    if (state !== "success") return;
    const timer = setTimeout(() => resetSync(), 3000);
    return () => clearTimeout(timer);
  }, [state, resetSync]);

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => {
        if (!open && state !== "processing") resetSync();
      }}
    >
      <DialogContent
        className="sm:max-w-md"
        onInteractOutside={(e) => {
          if (state === "processing") e.preventDefault();
        }}
      >
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-primary" />
            Sincronizando fuentes
          </DialogTitle>
          <DialogDescription>Actualizando datos de tus canales conectados</DialogDescription>
        </DialogHeader>

        <div className="py-4 space-y-4">
          {state === "processing" && (
            <>
              <Progress value={60} className="h-2 animate-pulse" />
              <p className="text-sm text-center text-muted-foreground">
                Esto puede tardar hasta 30 segundos. No cierres esta ventana.
              </p>
            </>
          )}

          {state === "success" && syncResult && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
                <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
                <span className="font-medium">
                  {syncResult.total_loaded > 0
                    ? `${syncResult.providers_synced} fuentes sincronizadas, ${syncResult.total_loaded} días cargados`
                    : "Todo al día — no hay datos nuevos"}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">Se cierra automáticamente...</p>
            </div>
          )}

          {state === "error" && syncError && (
            <div className="space-y-3">
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{syncError.message}</AlertDescription>
              </Alert>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" size="sm" onClick={resetSync}>
                  Cancelar
                </Button>
                <Button
                  size="sm"
                  onClick={() => {
                    resetSync();
                    startSync(30);
                  }}
                >
                  Reintentar
                </Button>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
