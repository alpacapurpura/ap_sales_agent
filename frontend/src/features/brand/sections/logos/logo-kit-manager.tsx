"use client";

import { Loader2 } from "lucide-react";

import { useBrandSettings } from "@/features/brand/hooks/useBrandSettings";

import { LogoKit } from "./logo-kit";

import type { BrandLogos } from "@/features/brand/types";

export function LogoKitManager() {
  const { settings, updateVisuals, loading } = useBrandSettings();

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!settings) return null;

  const handleLogoChange = (updatedLogos: BrandLogos) => {
    void updateVisuals({ ...settings.visuals, logos: updatedLogos });
  };

  return <LogoKit logos={settings.visuals?.logos ?? {}} onChange={handleLogoChange} />;
}
