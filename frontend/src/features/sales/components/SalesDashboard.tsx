"use client";

import { MessageSquare } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";

import { ConversionCommandCenter } from "./dashboard/ConversionCommandCenter";
import { SalesInboxSheet } from "./overlay/SalesInboxSheet";

/**
 *
 */
export function SalesDashboard() {
  const [isInboxOpen, setIsInboxOpen] = useState(false);

  return (
    <div className="space-y-6">
      {/* Header / Quick Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Closer Studio</h2>
          <p className="text-muted-foreground">Tu área Comercial y Ventas</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            onClick={() => setIsInboxOpen(true)}
            className="bg-primary text-primary-foreground"
          >
            <MessageSquare className="mr-2 h-4 w-4" />
            Inbox
          </Button>
        </div>
      </div>

      {/* Conversion Command Center (The 3 Lanes) */}
      <ConversionCommandCenter />

      {/* Overlays */}
      <SalesInboxSheet open={isInboxOpen} onOpenChange={setIsInboxOpen} />
    </div>
  );
}
