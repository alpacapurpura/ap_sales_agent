"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { 
  CreditCard, 
  MessageSquare, 
  TrendingUp, 
  Users, 
  CalendarCheck,
  DollarSign,
  Plus
} from "lucide-react";
import { PaymentGatewayConfig } from "./overlay/payment-gateway-config";
import { SalesInboxSheet } from "./overlay/sales-inbox-sheet";
import { AppointmentSheet } from "./overlay/appointment-sheet";
import { AvailabilityModal } from "./overlay/availability-modal";
import { CalendarWidget } from "./dashboard/calendar-widget";
import { ActivityFeedWidget } from "./dashboard/activity-feed-widget";

export function SalesDashboard() {
  const [isInboxOpen, setIsInboxOpen] = useState(false);
  const [isPaymentConfigOpen, setIsPaymentConfigOpen] = useState(false);
  const [isAvailabilityOpen, setIsAvailabilityOpen] = useState(false);
  const [selectedAppointment, setSelectedAppointment] = useState<any>(null);

  const handleAppointmentClick = (appointment: any) => {
    setSelectedAppointment(appointment);
  };

  const closeAppointmentSheet = (open: boolean) => {
    if (!open) setSelectedAppointment(null);
  };

  return (
    <div className="space-y-6">
      {/* Header / Quick Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
           <h2 className="text-3xl font-bold tracking-tight">Sales Studio</h2>
           <p className="text-muted-foreground">Centro de Comando Comercial</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => setIsPaymentConfigOpen(true)}>
            <CreditCard className="mr-2 h-4 w-4" />
            Configurar Pagos
          </Button>
          <Button onClick={() => setIsInboxOpen(true)} className="bg-primary text-primary-foreground">
            <MessageSquare className="mr-2 h-4 w-4" />
            Inbox (3)
          </Button>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Ventas Totales</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">$1,234.00</div>
            <p className="text-xs text-muted-foreground">+20.1% vs mes anterior</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Citas Agendadas</CardTitle>
            <CalendarCheck className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">+15</div>
            <p className="text-xs text-muted-foreground">+4 nuevas hoy</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tasa de Cierre</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">12.5%</div>
            <p className="text-xs text-muted-foreground">+2.1% esta semana</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Leads Activos</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">342</div>
            <p className="text-xs text-muted-foreground">87 activos ahora</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Bento Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[600px]">
        {/* Calendar Widget (Left/Center) */}
        <div className="lg:col-span-8 h-full">
           <CalendarWidget 
              onAppointmentClick={handleAppointmentClick}
              onConfigClick={() => setIsAvailabilityOpen(true)}
           />
        </div>

        {/* Activity Feed (Right) */}
        <div className="lg:col-span-4 h-full">
           <ActivityFeedWidget />
        </div>
      </div>

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

      <AppointmentSheet 
        appointment={selectedAppointment} 
        open={!!selectedAppointment} 
        onOpenChange={closeAppointmentSheet} 
      />
    </div>
  );
}
