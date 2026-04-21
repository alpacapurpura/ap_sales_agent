"use client";

import { ChevronRight } from "lucide-react";
import Link from "next/link";
import { useParams, usePathname } from "next/navigation";
import { useMemo } from "react";

import { FinderColumn } from "@/components/form-runtime/FinderColumn";
import { cn } from "@/lib/utils";

import {
  SETTINGS_GROUP_LABELS,
  SETTINGS_SECTIONS,
  type SettingsGroup,
  type SettingsSectionMeta,
} from "../lib/section-catalog";

/**
 * Column 1 of the Settings Finder layout — grouped list of settings sections.
 *
 * Mirrors BrandStudioNavRail exactly:
 *   - width 260px (--brand-col-sections)
 *   - row height ~36px, padding 9px 14px
 *   - group headers (Principal / Ventas / Desarrolladores)
 *   - chevron on the right of every row
 *   - aria-current="page" on the active section
 */
export function SettingsNavRail() {
  const params = useParams<{ tenantId?: string }>();
  const tenantId = params?.tenantId ?? "";
  const pathname = usePathname();
  const activeSlug = pathname.split("/settings/")[1]?.split("/")[0] ?? null;

  const grouped = useMemo(() => groupSections(SETTINGS_SECTIONS), []);

  return (
    <FinderColumn
      title="Configuración"
      count={SETTINGS_SECTIONS.length}
      widthClass="w-[var(--brand-col-sections)]"
      ariaLabel="Secciones de Configuración"
    >
      <div className="flex flex-col">
        {grouped.map(([group, sections]) => (
          <section key={group} className="flex flex-col">
            <header className="px-[14px] pt-3 pb-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              {SETTINGS_GROUP_LABELS[group]}
            </header>
            <ul className="flex flex-col">
              {sections.map((s) => (
                <SectionRow
                  key={s.slug}
                  tenantId={tenantId}
                  section={s}
                  isActive={s.slug === activeSlug}
                />
              ))}
            </ul>
          </section>
        ))}
      </div>
    </FinderColumn>
  );
}

function groupSections(
  sections: readonly SettingsSectionMeta[],
): [SettingsGroup, SettingsSectionMeta[]][] {
  const order: SettingsGroup[] = ["principal", "ventas", "desarrolladores"];
  const byGroup = new Map<SettingsGroup, SettingsSectionMeta[]>();
  for (const s of sections) {
    const bucket = byGroup.get(s.group);
    if (bucket) {
      bucket.push(s);
    } else {
      byGroup.set(s.group, [s]);
    }
  }
  const result: [SettingsGroup, SettingsSectionMeta[]][] = [];
  for (const g of order) {
    const bucket = byGroup.get(g);
    if (bucket) result.push([g, bucket]);
  }
  return result;
}

interface SectionRowProps {
  tenantId: string;
  section: SettingsSectionMeta;
  isActive: boolean;
}

function SectionRow({ tenantId, section, isActive }: SectionRowProps) {
  const Icon = section.icon;
  return (
    <li>
      <Link
        href={`/${tenantId}/settings/${section.slug}`}
        aria-current={isActive ? "page" : undefined}
        className={cn(
          "relative flex items-center gap-2 border-b border-border/50",
          "px-[14px] py-[9px] text-[13px] transition-colors",
          isActive ? "bg-muted/60" : "hover:bg-muted/30",
          isActive &&
            "before:absolute before:inset-y-0 before:left-0 before:w-[2px] before:bg-brand",
        )}
      >
        <Icon
          className={cn("h-4 w-4 shrink-0", isActive ? "text-foreground" : "text-muted-foreground")}
          aria-hidden="true"
        />
        <span
          className={cn("flex-1 truncate", isActive ? "text-foreground" : "text-foreground/90")}
        >
          {section.label}
        </span>
        <ChevronRight className="h-3 w-3 shrink-0 text-muted-foreground" aria-hidden="true" />
      </Link>
    </li>
  );
}
