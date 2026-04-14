"use client";

import { useBrandSettings } from "@/features/brand/hooks/useBrandSettings";
import { BrandLogos } from "@/features/brand/types";
import { LogoKit } from "./logo-kit";
import { Loader2 } from "lucide-react";

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
    updateVisuals({ ...settings.visuals, logos: updatedLogos });
  };

  return <LogoKit logos={settings.visuals?.logos ?? {}} onChange={handleLogoChange} />;
}
