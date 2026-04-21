"use client";

import Link from "next/link";
import { useRouter, useParams } from "next/navigation";
import { useCallback } from "react";
import { toast } from "sonner";

import { usePersonalityPresets, useSelectPreset } from "@/features/brand-studio/api/personality";

import { CommunicationStyleNav } from "./CommunicationStyleNav";
import { PresetGrid } from "./PresetGrid";

import type { PersonalityProfile } from "@/features/brand-studio/types/personality";

interface PresetPickerViewProps {
  activeProfile: PersonalityProfile | null;
}

/**
 * Full-page preset picker accessed via `?view=preset` query param. Shows all 6
 * personality presets in a grid. Selecting one calls `useSelectPreset` and
 * navigates back to the main estilo page on success.
 */
export function PresetPickerView({ activeProfile }: PresetPickerViewProps) {
  const router = useRouter();
  const params = useParams<{ tenantId: string }>();
  const { tenantId } = params;

  const { data: presets, isLoading, error } = usePersonalityPresets();
  const selectPreset = useSelectPreset();

  const handleSelect = useCallback(
    async (key: string) => {
      try {
        await selectPreset.mutateAsync(key);
        toast.success("Estilo activado.");
        router.push(`/${tenantId}/brand-studio/estilo`);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Error al activar.";
        toast.error(message);
      }
    },
    [selectPreset, router, tenantId],
  );

  return (
    <div className="flex flex-col gap-6">
      <CommunicationStyleNav />

      <div className="space-y-1">
        <h2 className="text-xl font-semibold tracking-tight text-foreground">Elige un preset</h2>
        <p className="text-sm text-muted-foreground">
          6 estilos base. Cada uno es un punto de partida — podrás ajustar dimensiones y ejemplos
          después.
        </p>
      </div>

      <PresetGrid
        presets={presets ?? []}
        selectedKey={activeProfile?.preset_key ?? null}
        onSelect={handleSelect}
        isPending={selectPreset.isPending}
        isLoading={isLoading}
        error={error}
      />

      <p className="text-center text-xs text-muted-foreground">
        ¿Ninguno encaja del todo?{" "}
        <Link
          href={`/${tenantId}/brand-studio/estilo?view=clone`}
          className="text-primary underline-offset-2 hover:underline"
        >
          Clona tu estilo →
        </Link>
      </p>
    </div>
  );
}
