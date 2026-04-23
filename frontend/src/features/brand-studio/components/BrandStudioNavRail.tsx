"use client";

import { Check, ChevronRight } from "lucide-react";
import Link from "next/link";
import { useParams, usePathname } from "next/navigation";

import { FinderColumn } from "@/components/form-runtime/FinderColumn";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { useSectionStatus } from "@/features/copilot/hooks/use-section-status";
import { cn } from "@/lib/utils";

import { BRAND_SECTIONS, type BrandSectionMeta } from "../lib/section-catalog";

import type { SectionStatusEntry } from "@/features/copilot/hooks/use-section-status";

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
  const sectionStatus = useSectionStatus("brand");

  return (
    <TooltipProvider>
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
              statusEntry={sectionStatus[section.slug]}
            />
          ))}
        </ul>
      </FinderColumn>
    </TooltipProvider>
  );
}

interface SectionRowProps {
  tenantId: string;
  section: BrandSectionMeta;
  isActive: boolean;
  statusEntry?: SectionStatusEntry;
}

function SectionRow({ tenantId, section, isActive, statusEntry }: SectionRowProps) {
  const Icon = section.icon;
  const status = statusEntry?.status ?? "idle";

  const linkContent = (
    <Link
      href={`/${tenantId}/brand-studio/${section.slug}`}
      aria-current={isActive ? "page" : undefined}
      className={cn(
        "relative flex min-h-[36px] items-center gap-2 border-b border-border/50",
        "px-[14px] py-[9px] text-[13px] transition-colors",
        isActive ? "bg-muted/60" : "hover:bg-muted/30",
        isActive && "before:absolute before:inset-y-0 before:left-0 before:w-[2px] before:bg-brand",
      )}
    >
      <Icon
        className={cn("h-4 w-4 shrink-0", isActive ? "text-foreground" : "text-muted-foreground")}
        aria-hidden="true"
      />
      <span className={cn("flex-1 truncate", isActive ? "text-foreground" : "text-foreground/90")}>
        {section.label}
      </span>
      <SectionBadge statusEntry={statusEntry} />
      <ChevronRight className="h-3 w-3 shrink-0 text-muted-foreground" aria-hidden="true" />
    </Link>
  );

  if ((status === "running" || status === "completed") && statusEntry?.fieldIds?.length) {
    const tooltipText = statusEntry.fieldIds.join(", ");
    return (
      <li>
        <Tooltip>
          <TooltipTrigger asChild>{linkContent}</TooltipTrigger>
          <TooltipContent side="right" className="max-w-[200px] text-xs">
            {tooltipText}
          </TooltipContent>
        </Tooltip>
      </li>
    );
  }

  return <li>{linkContent}</li>;
}

// ── Badge component ───────────────────────────────────────────────────────────

interface SectionBadgeProps {
  statusEntry?: SectionStatusEntry;
}

function SectionBadge({ statusEntry }: SectionBadgeProps) {
  const status = statusEntry?.status ?? "idle";
  const count = statusEntry?.fieldCount ?? 0;

  if (status === "idle") return null;

  if (status === "queued") {
    return (
      <span
        className="shrink-0 rounded-full bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground"
        aria-label="En cola"
      >
        ·
      </span>
    );
  }

  if (status === "running") {
    return (
      <span className="flex shrink-0 items-center gap-1 rounded-full bg-brand/10 px-1.5 py-0.5 text-[10px] text-brand">
        <span
          className="h-2 w-2 rounded-full border-2 border-brand border-t-transparent animate-spin"
          aria-hidden="true"
        />
        {count > 0 ? `${count} entrando` : "…"}
      </span>
    );
  }

  // completed
  return (
    <span className="flex shrink-0 items-center gap-1 rounded-full bg-success/10 px-1.5 py-0.5 text-[10px] text-success">
      <Check className="h-2.5 w-2.5" aria-hidden="true" />
      {`${count} sugeridos`}
    </span>
  );
}
