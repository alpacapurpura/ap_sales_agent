"use client";

import { BusinessTypesChipBar } from "@/features/tenant-profile/components/BusinessTypesChipBar";
import { cn } from "@/lib/utils";

interface TenantContextBarProps {
  className?: string;
}

/**
 * Global shell strip that shows the tenant's declared business types
 * as chips on every authenticated dashboard page.
 *
 * Renders ``BusinessTypesChipBar`` from the tenant-profile feature.
 * Clicking the settings icon routes to /settings/perfil-negocio.
 *
 * CONTRACT §6.2 — global shell integration.
 */
export function TenantContextBar({ className }: TenantContextBarProps) {
  return (
    <div
      className={cn(
        "flex items-center px-4 py-2 border-b border-border/40 bg-background/50",
        className,
      )}
    >
      <BusinessTypesChipBar />
    </div>
  );
}
