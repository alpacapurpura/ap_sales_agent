"use client";

import { memo } from "react";

import { AppSidebar } from "@/components/shared/layout/AppSidebar";
import { SidebarProvider, useSidebar } from "@/components/shared/layout/SidebarContext";
import { CopilotSidebar } from "@/features/copilot/components/CopilotSidebar";
import { NotificationCenter } from "@/features/notifications/components/NotificationCenter";
import { cn } from "@/lib/utils";

const MemoizedChildren = memo(function MemoizedChildren({
  children,
}: {
  children: React.ReactNode;
}) {
  return <div className="h-full">{children}</div>;
});

function DashboardContent({ children }: { children: React.ReactNode }) {
  const { isCollapsed } = useSidebar();

  return (
    <div className="flex h-screen overflow-hidden">
      <AppSidebar />
      <main
        className={cn(
          "relative flex-1 min-w-0 overflow-y-auto",
          "pt-16 md:pt-0 transition-[margin] duration-300 ease-in-out",
          isCollapsed ? "md:ml-20" : "md:ml-64",
        )}
      >
        <MemoizedChildren>{children}</MemoizedChildren>
        <NotificationCenter />
      </main>
      <CopilotSidebar />
    </div>
  );
}

/**
 *
 */
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <SidebarProvider>
      <DashboardContent>{children}</DashboardContent>
    </SidebarProvider>
  );
}
