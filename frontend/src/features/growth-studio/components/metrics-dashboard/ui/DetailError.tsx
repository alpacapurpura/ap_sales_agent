"use client";

import { AlertTriangle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

interface DetailErrorProps {
  /** The error that occurred while loading metrics */
  error: Error;
  /** Callback to re-trigger the data fetch */
  onRetry: () => void;
  /** Last successfully fetched data, displayed in muted gray when available */
  lastData?: unknown;
}

/**
 * Error state banner for a detail panel when the API call fails.
 *
 * - Shows AlertTriangle icon + Spanish error message
 * - Displays a "Reintentar" button using the destructive variant
 * - If lastData is provided, shows "Ultimos datos en cache:" section below
 */
export function DetailError({ error, onRetry, lastData }: DetailErrorProps) {
  return (
    <div className="space-y-3">
      {/* Error banner */}
      <Card className="border-destructive/50 bg-destructive/5">
        <CardContent className="flex items-start gap-3 py-4 px-4">
          <AlertTriangle
            className="h-5 w-5 text-destructive mt-0.5 flex-shrink-0"
            aria-hidden="true"
          />
          <div className="flex-1 space-y-2">
            <p className="text-sm text-destructive font-medium">
              Error al cargar metricas: {error.message}
            </p>
            <p className="text-xs text-muted-foreground">
              No se pudo conectar con el servidor. Verifica tu conexion e intenta nuevamente.
            </p>
            <Button variant="destructive" size="sm" onClick={onRetry} className="mt-1">
              Reintentar
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Cached data fallback */}
      {lastData != null && (
        <Card className="border-muted">
          <CardContent className="py-3 px-4">
            <p className="text-xs font-medium text-muted-foreground mb-2">
              Ultimos datos en cache:
            </p>
            <pre className="text-[10px] text-muted-foreground overflow-x-auto whitespace-pre-wrap break-words max-h-32 overflow-y-auto">
              {JSON.stringify(lastData, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
