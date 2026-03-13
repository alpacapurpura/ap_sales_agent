"use client";

import { useBrandSettings } from "@/features/brand/hooks/useBrandSettings";
import { IdentityForm } from "./identity-form";
import { Loader2 } from "lucide-react";

export function IdentityManager() {
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
    <IdentityForm
      initialData={settings.identity ?? {}}
      onSave={updateIdentity}
      isSaving={saving}
    />
  );
}
