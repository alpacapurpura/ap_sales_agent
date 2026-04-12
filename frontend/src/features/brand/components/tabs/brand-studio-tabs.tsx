"use client";

import { useMemo } from "react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  BRAND_SECTIONS,
  BRAND_SECTION_ORDER,
  type BrandSectionId,
  buildSectionNavItems,
} from "../../config/sections";
import type { BrandSettings } from "../../types";

interface BrandStudioTabsProps {
  activeTab: BrandSectionId;
  onTabChange: (tab: BrandSectionId) => void;
  settings: BrandSettings;
}

function computeSectionHealth(sectionId: BrandSectionId, settings: BrandSettings): number {
  const items = buildSectionNavItems(sectionId, settings);
  if (items.length === 0) return 0;
  return Math.round(items.reduce((sum, item) => sum + item.score, 0) / items.length);
}

function healthColor(score: number): string {
  if (score >= 80) return "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
  if (score > 0) return "bg-amber-500/15 text-amber-400 border-amber-500/30";
  return "bg-muted text-muted-foreground border-border";
}

export function BrandStudioTabs({ activeTab, onTabChange, settings }: BrandStudioTabsProps) {
  const sectionHealths = useMemo(
    () =>
      BRAND_SECTION_ORDER.reduce(
        (acc, id) => {
          acc[id] = computeSectionHealth(id, settings);
          return acc;
        },
        {} as Record<BrandSectionId, number>
      ),
    [settings]
  );

  return (
    <Tabs value={activeTab} onValueChange={(v) => onTabChange(v as BrandSectionId)}>
      <div className="border-b px-6">
        <TabsList className="h-10 bg-transparent">
          {BRAND_SECTION_ORDER.map((id) => {
            const section = BRAND_SECTIONS[id];
            const health = sectionHealths[id];
            return (
              <TabsTrigger
                key={id}
                value={id}
                className="gap-2 data-[state=active]:bg-transparent data-[state=active]:shadow-none"
              >
                {section.label}
                <Badge
                  variant="outline"
                  className={cn("text-[10px] px-1.5 py-0 h-4 font-semibold", healthColor(health))}
                >
                  {health}%
                </Badge>
              </TabsTrigger>
            );
          })}
        </TabsList>
      </div>
    </Tabs>
  );
}
