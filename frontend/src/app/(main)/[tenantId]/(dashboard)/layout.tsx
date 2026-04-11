"use client";

import { memo } from "react";
import { usePathname } from "next/navigation";
import { AppSidebar } from "@/components/shared/layout/app-sidebar";
import { SidebarProvider, useSidebar } from "@/components/shared/layout/sidebar-context";
import { CopilotPanel } from "@/features/copilot/components/CopilotPanel";
import { useCopilotStore } from "@/features/copilot/store/copilot-store";
import { cn } from "@/lib/utils";

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
  // Full-width routes: workspace-style screens that need every pixel
  // between the sidebar and the copilot panel. Add new entries here when
  // a new studio/editor needs the same treatment.
  const isFullWidth =
    pathname.includes("/sales/studio") ||
    pathname.includes("/offer-studio/offer/");

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
