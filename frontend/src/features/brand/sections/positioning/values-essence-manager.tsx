"use client";

import { useBrandSettings } from "@/features/brand/hooks/useBrandSettings";

import { ValuesEssenceForm } from "./values-essence-form";

export function ValuesEssenceManager() {
  const { settings, saving, updatePositioning } = useBrandSettings();
  if (!settings) return null;

  return (
    <ValuesEssenceForm
      positioning={settings.positioning ?? { reasons_to_believe: [] }}
      onSave={updatePositioning}
      isSaving={saving}
    />
  );
}
