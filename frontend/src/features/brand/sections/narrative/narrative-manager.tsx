"use client";

import { useBrandSettings } from "../../hooks/useBrandSettings";
import { NarrativeForm } from "./narrative-form";

export function NarrativeManager() {
  const { settings, saving, updateNarrative } = useBrandSettings();
  if (!settings) return null;
  return (
    <NarrativeForm
      narrative={settings.narrative ?? { plan: [] }}
      onSave={updateNarrative}
      isSaving={saving}
    />
  );
}
