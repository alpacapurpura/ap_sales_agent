"use client";

import { Badge } from "@/components/ui/badge";
import { formatDualCurrency } from "@/lib/format-money";

import type { EvangelistData } from "../../../types/metrics";

interface Props {
  evangelist: EvangelistData;
}

export function EvangelistCard({ evangelist }: Props) {
  const initial = evangelist.fullName.charAt(0).toUpperCase();

  return (
    <div className="rounded-lg border p-3 space-y-1">
      {/* First line: avatar + name + code + status */}
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-950/30 text-purple-600 dark:text-purple-400 flex items-center justify-center text-xs font-semibold flex-shrink-0">
          {initial}
        </div>
        <div className="flex flex-col min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold truncate">{evangelist.fullName}</span>
            <Badge
              variant="secondary"
              className={
                evangelist.isActive
                  ? "bg-emerald-50 text-emerald-600 dark:bg-emerald-950/30 dark:text-emerald-400"
                  : "bg-muted text-muted-foreground"
              }
            >
              {evangelist.isActive ? "Activo" : "Inactivo"}
            </Badge>
          </div>
          <span className="text-xs text-muted-foreground font-mono">
            Codigo: {evangelist.referralCode}
          </span>
        </div>
      </div>

      {/* Metrics row */}
      <div className="flex items-center gap-4 text-xs">
        <span>Referidos enviados: {evangelist.referralsSent}</span>
        <span>Convertidos: {evangelist.conversions}</span>
        <span className="font-semibold">
          {formatDualCurrency(
            evangelist.revenueAttributed,
            evangelist.currency,
            evangelist.usdRevenue,
          )}
        </span>
      </div>
    </div>
  );
}
