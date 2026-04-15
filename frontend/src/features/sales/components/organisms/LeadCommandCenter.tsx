import {
  History,
  MessageSquare,
  PhoneCall,
  Send,
  Mic,
  Paperclip,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";

import { IdentityHeader } from "../molecules/IdentityHeader";

import type { Lead } from "../../types";

interface LeadCommandCenterProps {
  lead: Lead;
  onBack?: () => void;
}

export function LeadCommandCenter({ lead, onBack }: LeadCommandCenterProps) {
  return (
    <div className="flex flex-col h-full bg-background">
      <IdentityHeader lead={lead} onBack={onBack} />

      <div className="flex-1 grid grid-cols-12 gap-6 p-6 overflow-hidden">
        {/* Left Column: Context & Details */}
        <div className="col-span-12 lg:col-span-4 flex flex-col gap-6 overflow-y-auto pr-2">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-medium flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-primary" />
                Contexto de Ventas
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="pain-points">Puntos de Dolor</Label>
                <Textarea
                  id="pain-points"
                  placeholder="Describe los problemas principales..."
                  className="min-h-[100px] resize-none"
                  defaultValue="Cliente busca automatizar procesos de ventas pero tiene presupuesto limitado."
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="budget">Presupuesto Estimado</Label>
                <Input id="budget" type="text" defaultValue="$5,000 - $10,000" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="timeline">Timeline</Label>
                <Input id="timeline" type="text" defaultValue="Q3 2024" />
              </div>
            </CardContent>
          </Card>

          <Card className="flex-1">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-medium flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                Próximos Pasos
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-start gap-3 p-3 bg-muted/30 rounded-lg border">
                  <div className="mt-0.5 h-2 w-2 rounded-full bg-red-500" />
                  <div className="space-y-1">
                    <p className="text-sm font-medium">Enviar Propuesta Revisada</p>
                    <p className="text-xs text-muted-foreground">Vence: Mañana a las 10:00 AM</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 bg-muted/30 rounded-lg border">
                  <div className="mt-0.5 h-2 w-2 rounded-full bg-yellow-500" />
                  <div className="space-y-1">
                    <p className="text-sm font-medium">Llamada de Seguimiento</p>
                    <p className="text-xs text-muted-foreground">Vence: Viernes 15</p>
                  </div>
                </div>
              </div>
              <Button variant="outline" size="sm" className="w-full mt-4">
                Agregar Tarea
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Center/Right Column: Activity & Actions */}
        <div className="col-span-12 lg:col-span-8 flex flex-col gap-6 h-full overflow-hidden">
          <Card className="flex-1 flex flex-col overflow-hidden shadow-sm">
            <div className="border-b px-4 py-3 bg-muted/20">
              <Tabs defaultValue="activity" className="w-full">
                <TabsList>
                  <TabsTrigger value="activity">Actividad</TabsTrigger>
                  <TabsTrigger value="notes">Notas</TabsTrigger>
                  <TabsTrigger value="files">Archivos</TabsTrigger>
                </TabsList>
              </Tabs>
            </div>

            <ScrollArea className="flex-1 p-4">
              <div className="space-y-6">
                {/* Mock Activity Timeline */}
                <div className="flex gap-4">
                  <div className="flex flex-col items-center">
                    <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600">
                      <MessageSquare className="h-4 w-4" />
                    </div>
                    <div className="w-0.5 flex-1 bg-border my-2" />
                  </div>
                  <div className="pb-8">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-sm">Mensaje de WhatsApp</span>
                      <span className="text-xs text-muted-foreground">Hoy, 10:23 AM</span>
                    </div>
                    <div className="p-3 bg-muted/40 rounded-lg text-sm border">
                      Hola Chris, me interesa agendar una demo para ver el módulo de CRM.
                    </div>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="flex flex-col items-center">
                    <div className="h-8 w-8 rounded-full bg-green-100 flex items-center justify-center text-green-600">
                      <PhoneCall className="h-4 w-4" />
                    </div>
                    <div className="w-0.5 flex-1 bg-border my-2" />
                  </div>
                  <div className="pb-8">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-sm">Llamada Saliente</span>
                      <span className="text-xs text-muted-foreground">Ayer, 4:15 PM</span>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      Llamada de 15 min. Discutimos requerimientos iniciales.
                    </div>
                  </div>
                </div>
              </div>
            </ScrollArea>

            <div className="p-4 bg-background border-t mt-auto">
              <div className="relative">
                <Textarea
                  placeholder="Escribe una nota o mensaje..."
                  className="min-h-[80px] resize-none pr-12 pb-10"
                />
                <div className="absolute bottom-2 left-2 flex gap-2">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-muted-foreground hover:text-foreground"
                  >
                    <Paperclip className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-muted-foreground hover:text-foreground"
                  >
                    <Mic className="h-4 w-4" />
                  </Button>
                </div>
                <Button size="icon" className="absolute bottom-2 right-2 h-8 w-8">
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
