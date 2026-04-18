import { BrandStudioNavRail } from "@/features/brand-studio/components/BrandStudioNavRail";

import type { ReactNode } from "react";

/**
 * Brand Studio layout.
 *
 * Minimal by design. Each section page (`/brand-studio/{section}` …)
 * renders its own form-runtime scaffold, which owns autosave, copilot
 * bridge and session state. The layout contributes only the left navigation
 * rail; everything else is delegated.
 *
 * Overlay layer (EditSheetManager, BrandVisualsWizard, SmartFillDialog)
 * from the legacy brand/ module is gone — their behaviour now lives inside
 * the form-runtime actions + Sprint 4's copilot extraction tools.
 */
export default function BrandStudioLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-full min-h-[calc(100vh-4rem)]">
      <BrandStudioNavRail />
      <div className="flex-1 overflow-auto">{children}</div>
    </div>
  );
}
