import { SettingsBreadcrumb } from "@/features/settings/components/SettingsBreadcrumb";
import { SettingsNavRail } from "@/features/settings/components/SettingsNavRail";

import type { ReactNode } from "react";

/**
 * Settings layout — Finder-style navigation shell.
 *
 * Mirrors brand-studio/layout.tsx exactly:
 *   - 48px sticky topbar with dynamic breadcrumb
 *   - 260px nav rail (column 1, grouped by Principal / Ventas / Desarrolladores)
 *   - child page in the remaining space with independent scroll
 *
 * CSS vars used: --brand-topbar-h (48px), --brand-col-sections (260px).
 */
export default function SettingsLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-full min-h-[calc(100vh-4rem)] flex-col">
      <header
        className="flex h-[var(--brand-topbar-h)] shrink-0 items-center gap-3 border-b border-border bg-background px-5"
        aria-label="Ruta de Configuración"
      >
        <SettingsBreadcrumb />
      </header>
      <div className="flex min-h-0 flex-1">
        <SettingsNavRail />
        <div className="flex min-w-0 flex-1 overflow-auto">{children}</div>
      </div>
    </div>
  );
}
