"use client";

import { useBrandSettings } from "@/features/brand/hooks/useBrandSettings";
import { VisualsForm } from "./visuals-form";
import { Loader2 } from "lucide-react";

export function VisualsManager() {
  const { settings, updateVisuals, loading, saving } = useBrandSettings();

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!settings) return null;

  return (
    <VisualsForm
      initialData={settings.visuals ?? {}}
      onSave={updateVisuals}
      isSaving={saving}
    />
  );
}
