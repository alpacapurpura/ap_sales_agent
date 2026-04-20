"use client";

import { Clock, Settings2 } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AvailabilityView } from "@/features/sales/components/AvailabilityView";
import { EventTypeView } from "@/features/sales/components/EventTypeView";

interface AvailabilityModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/**
 *
 */
export function AvailabilityModal({ open, onOpenChange }: AvailabilityModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl h-[80vh] flex flex-col p-0 overflow-hidden">
        <DialogHeader className="px-6 py-4 border-b">
          <DialogTitle>Configuración de Agenda</DialogTitle>
          <DialogDescription>Gestiona tu disponibilidad y tipos de eventos.</DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="availability" className="flex-1 flex flex-col overflow-hidden">
          <div className="px-6 pt-2 border-b bg-muted/20">
            <TabsList className="bg-transparent p-0 gap-6">
              <TabsTrigger
                value="availability"
                className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none px-2 pb-2"
              >
                <Clock className="mr-2 h-4 w-4" />
                Disponibilidad
              </TabsTrigger>
              <TabsTrigger
                value="event-types"
                className="data-[state=active]:bg-transparent data-[state=active]:shadow-none data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none px-2 pb-2"
              >
                <Settings2 className="mr-2 h-4 w-4" />
                Tipos de Evento
              </TabsTrigger>
            </TabsList>
          </div>

          <div className="flex-1 overflow-y-auto bg-muted/10 p-6">
            <TabsContent value="availability" className="mt-0 h-full">
              <div className="max-w-3xl mx-auto">
                <AvailabilityView />
              </div>
            </TabsContent>
            <TabsContent value="event-types" className="mt-0 h-full">
              <div className="max-w-3xl mx-auto">
                <EventTypeView />
              </div>
            </TabsContent>
          </div>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
