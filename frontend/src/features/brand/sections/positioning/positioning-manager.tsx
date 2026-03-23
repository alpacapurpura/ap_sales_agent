"use client";

import { useBrandSettings } from "@/features/brand/hooks/useBrandSettings";
import { PositioningForm } from "./positioning-form";
import { Loader2 } from "lucide-react";

export function PositioningManager() {
  const { settings, saving, updatePositioning, loading } = useBrandSettings();

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!settings) return null;

  return (
    <PositioningForm
      positioning={settings.positioning ?? { reasons_to_believe: [] }}
      onSave={updatePositioning}
      isSaving={saving}
    />
  );
}
