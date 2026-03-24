"use client";

import { AppSidebar } from "@/components/shared/layout/app-sidebar";
import { SidebarProvider, useSidebar } from "@/components/shared/layout/sidebar-context";
import { CopilotPanel } from "@/features/copilot/components/CopilotPanel";
import { useCopilotStore } from "@/features/copilot/store/copilot-store";
import { cn } from "@/lib/utils";

function DashboardContent({ children }: { children: React.ReactNode }) {
  const { isCollapsed } = useSidebar();
  const isCopilotOpen = useCopilotStore((s) => s.isOpen);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <AppSidebar />
      <main
        className={cn(
          "min-h-screen pt-16 md:pt-0 transition-all duration-300 ease-in-out",
          isCollapsed ? "md:pl-20" : "md:pl-64",
          isCopilotOpen ? "pr-[380px]" : "pr-[60px]"
        )}
      >
        <div className="container mx-auto p-6 md:p-8 max-w-7xl h-full">
          {children}
        </div>
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
