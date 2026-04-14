"use client";

import { useState, useCallback, type ReactNode } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { SectionNavRail, type SectionNavItem } from "../navigation/section-nav-rail";

interface BrandSectionShellProps {
  /** Section title shown in nav rail header and mobile header */
  title: string;
  /** Section subtitle shown in nav rail header */
  subtitle: string;
  /** Nav rail items with health data */
  navItems: SectionNavItem[];
  /** Section content (preview components) */
  children: ReactNode;
}

/**
 * Shared shell for all Brand Studio section pages.
 * Provides consistent layout: nav rail (left) + scrollable content (right).
 */
export function BrandSectionShell({ title, subtitle, navItems, children }: BrandSectionShellProps) {
  const [activeSection, setActiveSection] = useState(navItems[0]?.scrollTo ?? "");

  const handleNavigate = useCallback((scrollTo: string) => {
    setActiveSection(scrollTo);
    const el = document.getElementById(scrollTo);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, []);

  return (
    <div className="flex flex-col md:flex-row relative h-[calc(100vh-4rem)]">
      <SectionNavRail
        title={title}
        subtitle={subtitle}
        items={navItems}
        activeSection={activeSection}
        onNavigate={handleNavigate}
        className="hidden md:flex shrink-0"
      />

      <main className="flex-1 overflow-hidden flex flex-col transition-all duration-300 min-w-0">
        {/* Mobile Header */}
        <div className="md:hidden p-4 border-b bg-background flex items-center justify-between">
          <h2 className="text-lg font-bold tracking-tight">{title}</h2>
        </div>

        <div className="flex-1 overflow-hidden">
          <ScrollArea className="h-full w-full">
            <div className="max-w-5xl mx-auto pb-20 space-y-16 px-6 md:px-12 py-8">{children}</div>
          </ScrollArea>
        </div>
      </main>
    </div>
  );
}
