"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  CreditCard,
  MessageSquare,
  CalendarClock
} from "lucide-react";
import { PaymentGatewayConfig } from "./overlay/payment-gateway-config";
import { SalesInboxSheet } from "./overlay/sales-inbox-sheet";
import { AvailabilityModal } from "./overlay/availability-modal";
import { ConversionCommandCenter } from "./dashboard/conversion-command-center";

export function SalesDashboard() {
  const [isInboxOpen, setIsInboxOpen] = useState(false);
  const [isPaymentConfigOpen, setIsPaymentConfigOpen] = useState(false);
  const [isAvailabilityOpen, setIsAvailabilityOpen] = useState(false);

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
            variant="outline"
            onClick={() => setIsAvailabilityOpen(true)}
            className="border-primary/30 hover:bg-primary/5 hover:text-primary transition-colors"
          >
            <CalendarClock className="mr-2 h-4 w-4 text-primary" />
            <span className="font-medium text-primary">Configurar Agenda</span>
          </Button>
          <Button variant="outline" onClick={() => setIsPaymentConfigOpen(true)}>
            <CreditCard className="mr-2 h-4 w-4" />
            Configurar Pagos
          </Button>
          <Button onClick={() => setIsInboxOpen(true)} className="bg-primary text-primary-foreground">
            <MessageSquare className="mr-2 h-4 w-4" />
            Inbox
          </Button>
        </div>
      </div>

      {/* Conversion Command Center (The 3 Lanes) */}
      <ConversionCommandCenter />

      {/* Overlays */}
      <PaymentGatewayConfig
        open={isPaymentConfigOpen}
        onOpenChange={setIsPaymentConfigOpen}
      />

      <SalesInboxSheet
        open={isInboxOpen}
        onOpenChange={setIsInboxOpen}
      />

      <AvailabilityModal
        open={isAvailabilityOpen}
        onOpenChange={setIsAvailabilityOpen}
      />
    </div>
  );
}
