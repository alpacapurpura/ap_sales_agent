"use client";

import { memo, useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { AppSidebar } from "@/components/shared/layout/app-sidebar";
import { SidebarProvider, useSidebar } from "@/components/shared/layout/sidebar-context";
import { CopilotPanel } from "@/features/copilot/components/CopilotPanel";
import { useCopilotStore } from "@/features/copilot/store/copilot-store";
import { cn } from "@/lib/utils";

// Routes that should render in workspace-style full-width mode. Add new
// entries here when a new studio/editor needs the same treatment.
const FULL_WIDTH_PATTERNS = [
  "/sales/studio",
  "/offer-studio/offer/",
] as const;

function matchesFullWidth(pathname: string): boolean {
  return FULL_WIDTH_PATTERNS.some((pattern) => pathname.includes(pattern));
}

const MemoizedChildren = memo(function MemoizedChildren({
  children,
  isFullWidth,
}: {
  children: React.ReactNode;
  isFullWidth: boolean;
}) {
  return isFullWidth ? (
    <div className="h-screen pt-16 md:pt-0">{children}</div>
  ) : (
    <div className="container mx-auto p-6 md:p-8 max-w-7xl h-full">
      {children}
    </div>
  );
});

function DashboardContent({ children }: { children: React.ReactNode }) {
  const { isCollapsed } = useSidebar();
  const isCopilotOpen = useCopilotStore((s) => s.isOpen);
  const pathname = usePathname() ?? "";

  // Defer the full-width decision to post-mount to avoid hydration
  // mismatches. Next.js Turbopack dev can serve a stale SSR bundle after
  // the list of patterns changes, which causes server/client className
  // diffs on first load. By starting with `false` (matching the default
  // centered wrapper) and flipping inside useEffect, both renders agree
  // on the initial DOM and React cleanly swaps wrappers after hydration.
  const [isFullWidth, setIsFullWidth] = useState(false);
  useEffect(() => {
    setIsFullWidth(matchesFullWidth(pathname));
  }, [pathname]);

  return (
    <div className="min-h-screen">
      <AppSidebar />
      <main
        className={cn(
          "min-h-screen pt-16 md:pt-0 transition-all duration-300 ease-in-out",
          isCollapsed ? "md:ml-20" : "md:ml-64",
          isCopilotOpen ? "pr-[380px]" : "pr-[60px]"
        )}
      >
        <MemoizedChildren isFullWidth={isFullWidth}>
          {children}
        </MemoizedChildren>
      </main>
      <CopilotPanel />
    </div>
  );
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <SidebarProvider>
      <DashboardContent>{children}</DashboardContent>
    </SidebarProvider>
  );
}
