"use client";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export function OfferLegend() {
  return (
    <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground bg-muted/30 p-2 rounded-lg border border-border/50">
      <span className="font-medium mr-1">Modelos de Entrega:</span>

      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
          <span className="font-medium text-foreground">DIY</span>
          <span className="hidden sm:inline">(Hazlo tú)</span>
        </div>
      </div>

      <div className="w-px h-3 bg-border" />

      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-blue-500" />
          <span className="font-medium text-foreground">DWY</span>
          <span className="hidden sm:inline">(Hazlo con nosotros)</span>
        </div>
      </div>

      <div className="w-px h-3 bg-border" />

      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-purple-600" />
          <span className="font-medium text-foreground">DFY</span>
          <span className="hidden sm:inline">(Lo hacemos por ti)</span>
        </div>
      </div>

      <div className="w-px h-3 bg-border" />

      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-yellow-500" />
          <span className="font-medium text-foreground">B2B</span>
          <span className="hidden sm:inline">(Corporativo)</span>
        </div>
      </div>
    </div>
  );
}
