"use client";

import { memo } from "react";

import { AppSidebar } from "@/components/shared/layout/AppSidebar";
import { ShellMutexProvider } from "@/components/shared/layout/ShellMutexContext";
import { SidebarProvider, useSidebar } from "@/components/shared/layout/SidebarContext";
import { CopilotFAB } from "@/features/copilot/components/CopilotFAB";
import { CopilotSidebar } from "@/features/copilot/components/CopilotSidebar";
import { NotificationCenter } from "@/features/notifications/components/NotificationCenter";
import { useShellMutex } from "@/hooks/use-shell-mutex";
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

/**
 * AD3: Min content width floor 720px @≥1024.
 *
 * The CSS variable is provided by the parent wrapper div so it can be
 * overridden by tests or future theming without touching the class string.
 * The Tailwind class `lg:min-w-[var(--shell-content-min-width,720px)]` applies
 * the floor only at the `lg` breakpoint (≥1024px) — below 1024px there is
 * no floor (mobile/tablet layouts handle space differently).
 */
const SHELL_MIN_WIDTH_VAR = "--shell-content-min-width";
const SHELL_MIN_WIDTH_PX = "720px";

/**
 * Inner content component — must be rendered inside SidebarProvider so that
 * useShellMutex (which calls useSidebar internally) can access sidebar state.
 *
 * T-4: Mounts useShellMutex with tenantId. Provides ShellMutexContext so
 * AppSidebar and CopilotSidebar can consume mutex state without prop-drilling.
 */
function DashboardContent({ tenantId, children }: { tenantId: string; children: React.ReactNode }) {
  const { isCollapsed } = useSidebar();

  // T-4: Mount useShellMutex — effects now fire with viewport-aware policy.
  // Must be called inside SidebarProvider so useSidebar() is available.
  const shellMutex = useShellMutex(tenantId);

  return (
    <ShellMutexProvider value={shellMutex}>
      <div
        className="flex h-screen overflow-hidden"
        style={{ [SHELL_MIN_WIDTH_VAR]: SHELL_MIN_WIDTH_PX } as React.CSSProperties}
      >
        <AppSidebar />
        <main
          className={cn(
            "relative flex-1 min-w-0 overflow-y-auto",
            "lg:min-w-[var(--shell-content-min-width,720px)]",
            "pt-16 md:pt-0 transition-[margin] duration-300 ease-in-out",
            isCollapsed ? "md:ml-20" : "md:ml-64",
          )}
        >
          <MemoizedChildren>{children}</MemoizedChildren>
          <NotificationCenter />
        </main>
        <CopilotSidebar />
        {/* T-5: Mobile FAB to reopen copilot. Returns null when not on mobile or copilot not collapsed. */}
        <CopilotFAB />
      </div>
    </ShellMutexProvider>
  );
}

/**
 * Client Component that owns all interactive shell state.
 *
 * T-4: `tenantId` is now actively consumed by `useShellMutex` (via DashboardContent).
 * `useShellMutex` enforces viewport-aware mutex policy between AppSidebar and CopilotSidebar.
 *
 * AD1: Client boundary for hooks (useSidebar, useShellMutex).
 */
export function DashboardShellClient({ tenantId, children }: DashboardShellClientProps) {
  return (
    <SidebarProvider>
      <DashboardContent tenantId={tenantId}>{children}</DashboardContent>
    </SidebarProvider>
  );
}
