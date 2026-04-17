"use client";

import { Loader2 } from "lucide-react";

import { BusinessTypesSection } from "@/features/brand/components/business-types/BusinessTypesSection";
import { useBrandSettings } from "@/features/brand/hooks/use-brand-settings";

import { IdentityForm } from "./identity-form";

/**
 *
 */
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
    <div className="space-y-6">
      <BusinessTypesSection />
      <IdentityForm
        initialData={settings.identity ?? {}}
        onSave={updateIdentity}
        isSaving={saving}
      />
    </div>
  );
}
