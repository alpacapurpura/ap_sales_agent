import { BrandStudioBreadcrumb } from "@/features/brand-studio/components/BrandStudioBreadcrumb";
import { BrandStudioNavRail } from "@/features/brand-studio/components/BrandStudioNavRail";

import type { ReactNode } from "react";

/**
 * Brand Studio layout — Finder-style navigation shell.
 *
 * Renders a 48px sticky topbar with the dynamic breadcrumb, the 260px nav
 * rail (column 1) and the child page, which contributes its own FinderColumn
 * columns (fields / editor / optional instance picker).
 *
 * Dimensions locked in
 * docs/ux-sessions/2026-04-20-brand-studio-finder-nav/UI-SPEC-locked-dimensions.md.
 */
export default function BrandStudioLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-full min-h-[calc(100vh-4rem)] flex-col">
      <header
        className="flex h-[var(--brand-topbar-h)] shrink-0 items-center gap-3 border-b border-border bg-background px-5"
        aria-label="Ruta de Brand Studio"
      >
        <BrandStudioBreadcrumb />
      </header>
      <div className="flex min-h-0 flex-1">
        <BrandStudioNavRail />
        <div className="flex min-w-0 flex-1">{children}</div>
      </div>
    </div>
  );
}
