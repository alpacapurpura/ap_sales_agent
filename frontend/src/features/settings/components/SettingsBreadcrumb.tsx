"use client";

import { ChevronRight } from "lucide-react";
import { useParams, usePathname } from "next/navigation";
import { useMemo } from "react";

import { cn } from "@/lib/utils";

import { getSettingsSectionLabel } from "../lib/section-catalog";

interface Crumb {
  label: string;
  /** Absolute href, undefined on the active leaf. */
  href?: string;
}

/**
 * Dynamic breadcrumb: Configuración › {section}.
 *
 * Mirrors BrandStudioBreadcrumb with the settings path pattern.
 */
export function SettingsBreadcrumb() {
  const params = useParams<{ tenantId?: string }>();
  const tenantId = params?.tenantId ?? "";
  const pathname = usePathname();

  const crumbs = useMemo<Crumb[]>(
    () => buildSettingsCrumbs(pathname, tenantId),
    [pathname, tenantId],
  );

  return (
    <nav aria-label="Ruta" className="flex items-center gap-2 text-[13px]">
      {crumbs.map((crumb, index) => {
        const isLast = index === crumbs.length - 1;
        return (
          <span key={`${crumb.label}-${index}`} className="flex items-center gap-2">
            {index > 0 && (
              <ChevronRight className="h-3 w-3 text-muted-foreground" aria-hidden="true" />
            )}
            {crumb.href && !isLast ? (
              <a
                href={crumb.href}
                className="text-muted-foreground transition-colors hover:text-foreground"
              >
                {crumb.label}
              </a>
            ) : (
              <span
                className={cn(isLast ? "font-medium text-foreground" : "text-muted-foreground")}
                aria-current={isLast ? "page" : undefined}
              >
                {crumb.label}
              </span>
            )}
          </span>
        );
      })}
    </nav>
  );
}

/** Build breadcrumb list from a pathname + tenant id. Exported for testing. */
export function buildSettingsCrumbs(pathname: string, tenantId: string): Crumb[] {
  const root: Crumb = {
    label: "Configuración",
    href: tenantId ? `/${tenantId}/settings` : undefined,
  };

  if (!pathname || !tenantId) return [root];

  const parts = pathname.split("/").filter(Boolean);
  const settingsIdx = parts.indexOf("settings");
  if (settingsIdx < 0) return [root];

  const rest = parts.slice(settingsIdx + 1);
  if (rest.length === 0) return [root];

  const [section] = rest;
  if (!section) return [root];

  return [
    root,
    {
      label: getSettingsSectionLabel(section),
      // No href on leaf — active page
    },
  ];
}
