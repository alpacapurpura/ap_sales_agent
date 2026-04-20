"use client";

import { ChevronRight } from "lucide-react";
import Link from "next/link";
import { useParams, usePathname } from "next/navigation";

import { FinderColumn } from "@/components/form-runtime/FinderColumn";
import { cn } from "@/lib/utils";

import { BRAND_SECTIONS, type BrandSectionMeta } from "../lib/section-catalog";

/**
 * Column 1 of the Finder layout — the fixed list of Brand Studio sections.
 * Dimensions locked by UI-SPEC-locked-dimensions.md:
 *  - width 260px (--brand-col-sections)
 *  - row height ~36px, padding 9px 14px
 *  - chevron on the right of every row
 *  - optional completion preview ("3/9", "2 ítems") rendered mid-row
 */
export function BrandStudioNavRail() {
  const params = useParams<{ tenantId?: string }>();
  const tenantId = params?.tenantId ?? "";
  const pathname = usePathname();
  const activeSlug = pathname.split("/brand-studio/")[1]?.split("/")[0] ?? null;

  return (
    <FinderColumn
      title="Secciones"
      count={BRAND_SECTIONS.length}
      widthClass="w-[var(--brand-col-sections)]"
      ariaLabel="Secciones de Brand Studio"
    >
      <ul className="flex flex-col">
        {BRAND_SECTIONS.map((section) => (
          <SectionRow
            key={section.slug}
            tenantId={tenantId}
            section={section}
            isActive={section.slug === activeSlug}
          />
        ))}
      </ul>
    </FinderColumn>
  );
}

interface SectionRowProps {
  tenantId: string;
  section: BrandSectionMeta;
  isActive: boolean;
}

function SectionRow({ tenantId, section, isActive }: SectionRowProps) {
  const Icon = section.icon;
  return (
    <li>
      <Link
        href={`/${tenantId}/brand-studio/${section.slug}`}
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
