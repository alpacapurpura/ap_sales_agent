"use client";

import {
  DollarSign,
  type LucideIcon,
  Image as ImageIcon,
  LayoutDashboard,
  Megaphone,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

import { LandingActionButton } from "./LandingActionButton";

import type { OfferCountsResponse } from "../../types/counts";

export interface OfferTabBarProps {
  tenantId: string;
  offerId: string;
  counts: OfferCountsResponse;
  /**
   * The edition whose tab content the bar should link to.
   *
   * - `null` → offer is evergreen (archetype without editions); tabs link at
   *   the offer root (`/offer/{id}/{tab}`).
   * - non-null → tabs link under `/offer/{id}/editions/{editionId}/{tab}`.
   *
   * Info always points to the offer root (it is offer-level).
   */
  currentEditionId: string | null;
}

interface TabConfig {
  key: "editor" | "ventas" | "assets" | "campaigns";
  label: string;
  icon: LucideIcon;
  /** Route leaf appended to the scope root. Empty for Info. */
  segment: "" | "ventas" | "assets" | "campaigns";
  badge?: (counts: OfferCountsResponse) => number;
}

const TABS: TabConfig[] = [
  { key: "editor", label: "Info", icon: LayoutDashboard, segment: "" },
  { key: "ventas", label: "Ventas", icon: DollarSign, segment: "ventas" },
  {
    key: "assets",
    label: "Assets",
    icon: ImageIcon,
    segment: "assets",
    badge: (c) => c.assets,
  },
  {
    key: "campaigns",
    label: "Campañas",
    icon: Megaphone,
    segment: "campaigns",
    badge: (c) => c.campaigns,
  },
];

/**
 * Persistent tab bar for the Offer Studio shell. Four tabs (Info · Ventas ·
 * Assets · Campañas) on the left, Landing action button on the right.
 *
 * Knowledge is not a tab — it lives as a section inside Info.
 *
 * Every tab (including Info) links under the current scope root:
 *   - Evergreen (no editions):   /offer/{id}[/tab]
 *   - With current edition:      /offer/{id}/editions/{editionId}[/tab]
 *
 * Info content is offer-level, but we keep the selected edition in the URL
 * so the rail highlight survives a tab switch. The edition-root page
 * (`/editions/{eid}`) renders the same Info content.
 *
 * Active highlighting parses the pathname shape so both URL forms map to
 * the same tab.
 */
export function OfferTabBar({ tenantId, offerId, counts, currentEditionId }: OfferTabBarProps) {
  const pathname = usePathname();
  const base = `/${tenantId}/offer-studio/offer/${offerId}`;
  const scopeRoot = currentEditionId ? `${base}/editions/${currentEditionId}` : base;
  const active = analyzePathname(pathname, base);

  return (
    <nav
      aria-label="Secciones de la oferta"
      className="flex h-[44px] items-stretch justify-between gap-2 border-b bg-background px-6"
    >
      <div className="flex items-stretch gap-1">
        {TABS.map((tab) => {
          const href = tab.segment ? `${scopeRoot}/${tab.segment}` : scopeRoot;
          const isActive = tab.segment ? active.tab === tab.segment : active.onInfo;
          const badgeValue = tab.badge?.(counts);
          const Icon = tab.icon;

          return (
            <Link
              key={tab.key}
              href={href}
              aria-current={isActive ? "page" : undefined}
              className={cn(
                "relative flex items-center gap-2 px-3 text-sm font-medium transition-colors",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
                isActive ? "text-foreground" : "text-muted-foreground hover:text-foreground",
              )}
            >
              <Icon className="h-4 w-4" aria-hidden />
              <span>{tab.label}</span>
              {typeof badgeValue === "number" ? (
                <Badge variant="secondary" className="h-5 min-w-5 px-1.5 text-[10px] tabular-nums">
                  {badgeValue}
                </Badge>
              ) : null}
              {isActive ? (
                <span aria-hidden className="absolute inset-x-0 bottom-0 h-[2px] bg-primary" />
              ) : null}
            </Link>
          );
        })}
      </div>
      <div className="flex items-center">
        <LandingActionButton offerId={offerId} tenantId={tenantId} />
      </div>
    </nav>
  );
}

interface PathnameAnalysis {
  /** True only when the pathname exactly matches the offer base (Info). */
  onInfo: boolean;
  /** The terminal tab segment (ventas/assets/campaigns) or null. */
  tab: string | null;
}

/**
 * Analyse `pathname` relative to the offer `base` and return whether the
 * user is on Info and which tab segment (if any) is active.
 *
 * Info is the scope root with no tab leaf — matches both:
 *   - `${base}`                            (evergreen Info)
 *   - `${base}/editions/{editionId}`       (Info with edition selected)
 */
function analyzePathname(pathname: string | null, base: string): PathnameAnalysis {
  if (!pathname) return { onInfo: false, tab: null };
  if (pathname === base) return { onInfo: true, tab: null };
  if (!pathname.startsWith(`${base}/`)) return { onInfo: false, tab: null };

  const rest = pathname.slice(base.length);
  const editionMatch = rest.match(/^\/editions\/[^/]+(\/([^/?#]+))?/);
  if (editionMatch) {
    const tabLeaf = editionMatch[2];
    return { onInfo: !tabLeaf, tab: tabLeaf ?? null };
  }

  const directMatch = rest.match(/^\/([^/?#]+)/);
  return { onInfo: false, tab: directMatch ? directMatch[1] : null };
}
