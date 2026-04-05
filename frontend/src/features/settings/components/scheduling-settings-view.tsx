"use client"

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { AvailabilityView } from "@/features/sales/components/availability-view"
import { EventTypeView } from "@/features/sales/components/event-type-view"
import { Clock, Settings2 } from "lucide-react"

export function SchedulingSettingsView() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Configuración de Agenda</CardTitle>
        <CardDescription>
          Gestiona tu disponibilidad y tipos de eventos.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="availability">
          <div className="border-b bg-muted/20 -mx-6 px-6">
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

          <div className="pt-6">
            <TabsContent value="availability" className="mt-0">
              <div className="max-w-3xl mx-auto">
                <AvailabilityView />
              </div>
            </TabsContent>
            <TabsContent value="event-types" className="mt-0">
              <div className="max-w-3xl mx-auto">
                <EventTypeView />
              </div>
            </TabsContent>
          </div>
        </Tabs>
      </CardContent>
    </Card>
  )
}
