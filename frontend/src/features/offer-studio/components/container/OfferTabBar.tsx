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
}

interface TabConfig {
  key: "editor" | "ventas" | "assets" | "campaigns";
  label: string;
  icon: LucideIcon;
  /** Path suffix appended to `/{tenantId}/offer-studio/offer/{offerId}`. */
  suffix: "" | "ventas" | "assets" | "campaigns";
  badge?: (counts: OfferCountsResponse) => number;
}

const TABS: TabConfig[] = [
  { key: "editor", label: "Info", icon: LayoutDashboard, suffix: "" },
  { key: "ventas", label: "Ventas", icon: DollarSign, suffix: "ventas" },
  {
    key: "assets",
    label: "Assets",
    icon: ImageIcon,
    suffix: "assets",
    badge: (c) => c.assets,
  },
  {
    key: "campaigns",
    label: "Campañas",
    icon: Megaphone,
    suffix: "campaigns",
    badge: (c) => c.campaigns,
  },
];

/**
 * Persistent tab bar for the Offer Studio shell. Four tabs (Info · Ventas ·
 * Assets · Campañas) on the left, Landing action button on the right.
 *
 * Knowledge is not a tab — it lives as a section inside Info.
 */
export function OfferTabBar({ tenantId, offerId, counts }: OfferTabBarProps) {
  const pathname = usePathname();
  const basePath = `/${tenantId}/offer-studio/offer/${offerId}`;

  return (
    <nav
      aria-label="Secciones de la oferta"
      className="flex h-[44px] items-stretch justify-between gap-2 border-b bg-background px-6"
    >
      <div className="flex items-stretch gap-1">
        {TABS.map((tab) => {
          const href = tab.suffix ? `${basePath}/${tab.suffix}` : basePath;
          const isActive = tab.suffix
            ? (pathname?.startsWith(href) ?? false)
            : pathname === basePath;
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
