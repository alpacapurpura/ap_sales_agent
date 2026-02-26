"use client";

import { useBrandSettings } from "@/features/brand/hooks/useBrandSettings";
import { MethodologyForm } from "./methodology-form";
import { Loader2 } from "lucide-react";

export function MethodologyManager() {
  const { settings, updateStrategy, loading, saving } = useBrandSettings();

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!settings) return null;

  return (
    <MethodologyForm
      initialData={settings.strategy}
      onSave={updateStrategy}
      isSaving={saving}
    />
  );
}
