"use client";

import { AppSidebar } from "@/components/layout/app-sidebar";
import { SidebarProvider, useSidebar } from "@/components/layout/sidebar-context";
import { cn } from "@/lib/utils";

function DashboardContent({ children }: { children: React.ReactNode }) {
  const { isCollapsed } = useSidebar();
  
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <AppSidebar />
      <main 
        className={cn(
          "min-h-screen pt-16 md:pt-0 transition-all duration-300 ease-in-out",
          isCollapsed ? "md:pl-20" : "md:pl-64"
        )}
      >
        <div className="container mx-auto p-6 md:p-8 max-w-7xl h-full">
          {children}
        </div>
      </main>
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
