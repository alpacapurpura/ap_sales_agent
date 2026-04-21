"use client";

import { Lightbulb, Loader2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { useMigrateFromVoiceTone } from "@/features/brand-studio/api/personality";

const DISMISSED_KEY = "nicolify_voice_tone_migration_dismissed";

interface MigrationCardProps {
  voiceToneText: string;
  onConverted: () => void;
}

/**
 * One-time migration card shown when the tenant has a legacy `voice_tone`
 * string but no active `PersonalityProfile`. Offers two actions:
 *  - "Convertir en estilo inicial": POST /from-voice-tone → activates the
 *    resulting migrated profile.
 *  - "Empezar de cero": dismisses the card (localStorage flag) and shows
 *    the normal EmptyState.
 *
 * Uses amber/warning tones to indicate it's a transitional prompt, not an
 * error.
 */
export function MigrationCard({ voiceToneText, onConverted }: MigrationCardProps) {
  const [dismissed, setDismissed] = useState(() => {
    try {
      return localStorage.getItem(DISMISSED_KEY) === "true";
    } catch {
      return false;
    }
  });
  const migrate = useMigrateFromVoiceTone();

  if (dismissed) return null;

  const handleConvert = async () => {
    try {
      await migrate.mutateAsync();
      toast.success("Estilo inicial creado desde tu tono de voz.");
      onConverted();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Error al convertir.";
      toast.error(message);
    }
  };

  const handleDismiss = () => {
    try {
      localStorage.setItem(DISMISSED_KEY, "true");
    } catch {
      // storage unavailable — degrade gracefully
    }
    setDismissed(true);
  };

  return (
    <div className="rounded-xl border border-amber-200 bg-amber-50 p-5 dark:border-amber-900/40 dark:bg-amber-950/20">
      <div className="flex items-start gap-3">
        <Lightbulb
          className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-600 dark:text-amber-400"
          aria-hidden
        />
        <div className="flex-1 space-y-2">
          <p className="text-sm font-medium text-amber-900 dark:text-amber-200">
            Tienes un tono de voz cargado desde antes:
          </p>
          <p className="line-clamp-3 rounded-md bg-amber-100 px-3 py-2 text-xs italic text-amber-800 dark:bg-amber-900/40 dark:text-amber-300">
            &ldquo;{voiceToneText}&rdquo;
          </p>
          <p className="text-xs text-amber-700 dark:text-amber-400">
            ¿Quieres que lo convirtamos en un estilo inicial? Puedes ajustarlo después.
          </p>
          <div className="flex flex-wrap gap-2 pt-1">
            <Button
              size="sm"
              className="bg-amber-600 text-white hover:bg-amber-700"
              onClick={handleConvert}
              disabled={migrate.isPending}
              aria-label="Convertir tono de voz existente en un estilo inicial"
            >
              {migrate.isPending && <Loader2 className="mr-2 h-3 w-3 animate-spin" aria-hidden />}
              Convertir en estilo inicial
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={handleDismiss}
              disabled={migrate.isPending}
              aria-label="Ignorar y empezar de cero"
              className="text-amber-700 hover:bg-amber-100 dark:text-amber-400 dark:hover:bg-amber-900/30"
            >
              Empezar de cero
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
