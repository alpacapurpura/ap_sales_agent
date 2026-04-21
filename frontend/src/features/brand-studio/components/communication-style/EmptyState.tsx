"use client";

import { Clock, Dna } from "lucide-react";

import { Button } from "@/components/ui/button";

interface EmptyStateProps {
  onOpenPresetPicker: () => void;
  onOpenCloneWizard: () => void;
}

/**
 * Empty state shown when the tenant has no active personality profile.
 * Presents two CTAs: choose a preset (30 sec) or clone from material (2-4 min).
 */
export function EmptyState({ onOpenPresetPicker, onOpenCloneWizard }: EmptyStateProps) {
  return (
    <div className="flex flex-col gap-6">
      <div className="space-y-1">
        <p className="text-sm text-muted-foreground">
          Todavía no tienes un estilo activo. Elige cómo empezar:
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {/* Preset CTA */}
        <div className="flex flex-col gap-4 rounded-xl border border-border bg-card p-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-amber-100 text-xl dark:bg-amber-900/30">
            ☀️
          </div>
          <div className="space-y-1">
            <p className="text-sm font-semibold text-foreground">Empezar con un preset</p>
            <p className="text-xs text-muted-foreground">
              6 estilos base listos para usar. Ajustable después.
            </p>
          </div>
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" aria-hidden />
            <span>30 segundos</span>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={onOpenPresetPicker}
            aria-label="Ver los 6 presets disponibles"
          >
            Ver los 6 presets →
          </Button>
        </div>

        {/* Clone CTA */}
        <div className="flex flex-col gap-4 rounded-xl border border-border bg-card p-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-purple-100 text-xl dark:bg-purple-900/30">
            <Dna className="h-5 w-5 text-purple-600 dark:text-purple-400" aria-hidden />
          </div>
          <div className="space-y-1">
            <p className="text-sm font-semibold text-foreground">Clonar mi estilo</p>
            <p className="text-xs text-muted-foreground">
              Pega mensajes tuyos reales y genero uno único.
            </p>
          </div>
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" aria-hidden />
            <span>2–4 minutos</span>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={onOpenCloneWizard}
            aria-label="Empezar a clonar tu estilo"
          >
            Empezar a clonar →
          </Button>
        </div>
      </div>

      <p className="text-xs text-muted-foreground">
        Sugerencia: empieza con un preset; puedes clonar tu estilo después sin perder la
        configuración.
      </p>
    </div>
  );
}
