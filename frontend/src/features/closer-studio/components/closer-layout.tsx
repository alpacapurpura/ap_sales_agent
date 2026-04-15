"use client";

import { Inbox, KanbanSquare, Snowflake, Wifi, WifiOff } from "lucide-react";
import { usePathname } from "next/navigation";

import { NavLink } from "@/components/shared/navigation";
import { cn } from "@/lib/utils";

import { useCloserWebSocket } from "../hooks/use-closer-ws";
import { useKPIs } from "../hooks/use-kpis";
import { useCloserStore } from "../store/closer-store";

interface CloserLayoutProps {
  tenantId: string;
  children: React.ReactNode;
}

const tabs = [
  { label: "Inbox", href: "inbox", icon: Inbox },
  { label: "Pipeline", href: "pipeline", icon: KanbanSquare },
  { label: "Congeladas", href: "frozen", icon: Snowflake },
];

export function CloserLayout({ tenantId, children }: CloserLayoutProps) {
  const pathname = usePathname() ?? "";
  const { data: kpis } = useKPIs();
  const wsConnected = useCloserStore((s) => s.wsConnected);

  // Connect WS for real-time updates
  useCloserWebSocket(tenantId);

  return (
    <div className="flex flex-col h-full">
      {/* KPI Bar + Tabs */}
      <div className="border-b bg-card px-4 py-2 flex items-center justify-between gap-4 shrink-0">
        {/* Tabs */}
        <nav className="flex gap-1">
          {tabs.map((tab) => {
            const href = `/${tenantId}/sales/studio/${tab.href}`;
            const isActive = pathname.includes(`/studio/${tab.href}`);
            return (
              <NavLink
                key={tab.href}
                href={href}
                className={cn(
                  "flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                )}
              >
                <tab.icon className="h-4 w-4" />
                {tab.label}
                {tab.href === "frozen" && kpis && kpis.frozen_count > 0 && (
                  <span className="ml-1 rounded-full bg-orange-500 text-white text-xs px-1.5 py-0.5 font-bold">
                    {kpis.frozen_count}
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* KPI chips */}
        {kpis && (
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <KPIChip label="Activas" value={kpis.total_active} />
            <KPIChip label="AI" value={kpis.handled_by_ai} color="text-violet-600" />
            <KPIChip label="Manual" value={kpis.handled_by_human} color="text-green-600" />
            <span className="w-px h-4 bg-border" />
            <KPIChip label="Hot" value={kpis.hot_count} color="text-red-500" />
            <KPIChip label="Warm" value={kpis.warm_count} color="text-orange-500" />
            <KPIChip label="Cold" value={kpis.cold_count} color="text-blue-500" />
            <span className="w-px h-4 bg-border" />
            <span className="font-mono">Score avg: {kpis.avg_lead_score}</span>
            <span className="w-px h-4 bg-border" />
            {wsConnected ? (
              <Wifi className="h-3.5 w-3.5 text-green-500" />
            ) : (
              <WifiOff className="h-3.5 w-3.5 text-red-400" />
            )}
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-h-0 overflow-hidden">{children}</div>
    </div>
  );
}

function KPIChip({ label, value, color }: { label: string; value: number; color?: string }) {
  return (
    <span className="flex items-center gap-1">
      <span className={cn("font-bold font-mono", color)}>{value}</span>
      <span>{label}</span>
    </span>
  );
}
