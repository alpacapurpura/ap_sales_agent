"use client";

import { memo } from "react";

import { AppSidebar } from "@/components/shared/layout/AppSidebar";
import { SidebarProvider, useSidebar } from "@/components/shared/layout/SidebarContext";
import { CopilotSidebar } from "@/features/copilot/components/CopilotSidebar";
import { NotificationCenter } from "@/features/notifications/components/NotificationCenter";
import { cn } from "@/lib/utils";

interface DashboardShellClientProps {
  tenantId: string;
  children: React.ReactNode;
}

const MemoizedChildren = memo(function MemoizedChildren({
  children,
}: {
  children: React.ReactNode;
}) {
  return <div className="h-full">{children}</div>;
});
MemoizedChildren.displayName = "MemoizedChildren";

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
 * Client Component that owns all interactive shell state.
 *
 * Phase 1: Identical JSX to DashboardLayoutClient — pure passthrough.
 * `tenantId` prop received for future use by useShellMutex (T-4).
 *
 * AD1: Client boundary for hooks (useSidebar, useShellMutex in T-4).
 */
export function DashboardShellClient({ tenantId: _tenantId, children }: DashboardShellClientProps) {
  // _tenantId: reserved for useShellMutex integration in T-4.
  // Phase 1: no-op. Prefixed with _ to satisfy TypeScript unused-var rule.
  return (
    <SidebarProvider>
      <DashboardContent>{children}</DashboardContent>
    </SidebarProvider>
  );
}
