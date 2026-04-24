"use client";

import { ChevronRight } from "lucide-react";
import { useParams, usePathname } from "next/navigation";
import { useMemo } from "react";

import { cn } from "@/lib/utils";

import { useBrandSectionLabelResolver } from "../hooks/use-brand-section-catalog";

interface Crumb {
  label: string;
  /** Absolute href for navigation, undefined on the active leaf. */
  href?: string;
  /** Visual tag rendered before the label (avatar, initial, …). */
  leading?: string;
}

/**
 * Dynamic breadcrumb driven by the URL: Brand Studio › {section} › [{instance}]
 * › {field}. The active leaf is rendered without a link so the user cannot
 * navigate to themselves.
 *
 * Path patterns understood:
 *   /{t}/brand-studio                                               → "Brand Studio"
 *   /{t}/brand-studio/{section}                                     → + section
 *   /{t}/brand-studio/{section}/{fieldId}                           → + field
 *   /{t}/brand-studio/{section}/instance/{instanceId}               → + instance
 *   /{t}/brand-studio/{section}/instance/{instanceId}/{fieldId}     → + field
 *   /{t}/brand-studio/publico/persona/{personaId}/{fieldId}         → legacy alias
 */
export function BrandStudioBreadcrumb() {
  const params = useParams<{ tenantId?: string }>();
  const tenantId = params?.tenantId ?? "";
  const pathname = usePathname();
  const resolveLabel = useBrandSectionLabelResolver();

  const crumbs = useMemo<Crumb[]>(() => {
    return buildCrumbs(pathname, tenantId, resolveLabel);
  }, [pathname, tenantId, resolveLabel]);

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

interface InstanceCrumbArgs {
  instanceId: string | undefined;
  fieldId: string | undefined;
  href: string;
  label: (id: string) => string;
}

function appendInstanceCrumb(crumbs: Crumb[], args: InstanceCrumbArgs): void {
  const { instanceId, fieldId, href, label } = args;
  if (instanceId) {
    crumbs.push({
      label: label(instanceId),
      href,
      leading: instanceId.slice(0, 1).toUpperCase(),
    });
  }
  if (fieldId) crumbs.push({ label: fieldId });
}

/** Build breadcrumb list from a pathname + tenant id. Exported for tests.
 *
 * ``resolveSectionLabel`` is injected so the function stays pure and
 * testable without mocking React hooks.
 */
export function buildCrumbs(
  pathname: string,
  tenantId: string,
  resolveSectionLabel: (slug: string) => string,
): Crumb[] {
  const root: Crumb = {
    label: "Brand Studio",
    href: tenantId ? `/${tenantId}/brand-studio` : undefined,
  };
  if (!pathname || !tenantId) return [root];

  const parts = pathname.split("/").filter(Boolean);
  const brandIdx = parts.indexOf("brand-studio");
  if (brandIdx < 0) return [root];

  const rest = parts.slice(brandIdx + 1);
  if (rest.length === 0) return [root];

  const [section, ...tail] = rest;
  if (!section) return [root];

  const crumbs: Crumb[] = [
    root,
    {
      label: resolveSectionLabel(section),
      href: `/${tenantId}/brand-studio/${section}`,
    },
  ];

  if (section === "publico" && tail[0] === "persona") {
    appendInstanceCrumb(crumbs, {
      instanceId: tail[1],
      fieldId: tail[2],
      href: `/${tenantId}/brand-studio/publico/persona/${tail[1] ?? ""}`,
      label: (id) => `Persona #${id.slice(0, 8)}`,
    });
    return crumbs;
  }

  if (tail[0] === "instance") {
    appendInstanceCrumb(crumbs, {
      instanceId: tail[1],
      fieldId: tail[2],
      href: `/${tenantId}/brand-studio/${section}/instance/${tail[1] ?? ""}`,
      label: (id) => `Instancia #${id.slice(0, 8)}`,
    });
    return crumbs;
  }

  const [fieldId] = tail;
  if (fieldId) crumbs.push({ label: fieldId });
  return crumbs;
}
