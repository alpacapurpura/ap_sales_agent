"use client";

import { Loader2 } from "lucide-react";

import { useBrandSettings } from "@/features/brand/hooks/use-brand-settings";

import { LegalForm } from "./LegalForm";

export function LegalManager() {
  const { settings, updateIdentity, loading, saving } = useBrandSettings();

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!settings) return null;

  return (
    <LegalForm initialData={settings.identity ?? {}} onSave={updateIdentity} isSaving={saving} />
  );
}
