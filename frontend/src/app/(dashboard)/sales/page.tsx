"use client";

import { useState, useEffect, Suspense } from "react";
import { useAuth } from "@clerk/nextjs";
import { format, startOfWeek, endOfWeek, addWeeks, subWeeks, addDays, isSameDay } from "date-fns";
import { es } from "date-fns/locale";
import { connectionsApi } from "@/lib/api/connections";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { 
  ChevronLeft, 
  ChevronRight, 
  Calendar as CalendarIcon, 
  Clock, 
  Video, 
  User,
  Settings2,
  CalendarDays,
  CreditCard,
  Loader2
} from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { useSearchParams, useRouter } from "next/navigation";

// --- Components ---

import { AvailabilityView } from "@/features/sales/components/availability-view";
import { EventTypeView } from "@/features/sales/components/event-type-view";

function PlaceholderContent({ title, icon: Icon }: { title: string, icon: any }) {
  return (
    <Card className="w-full min-h-[600px]">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Icon className="h-6 w-6" />
          {title}
        </CardTitle>
        <CardDescription>Esta funcionalidad estará disponible próximamente.</CardDescription>
      </CardHeader>
      <CardContent className="h-[400px] flex items-center justify-center text-muted-foreground bg-muted/10 rounded-md border border-dashed m-6">
        <div className="text-center">
          <Icon className="h-12 w-12 mx-auto mb-4 opacity-20" />
          <p>Próximamente</p>
        </div>
      </CardContent>
    </Card>
  );
}

function AppointmentsView() {
  const { getToken } = useAuth();
  const [currentDate, setCurrentDate] = useState(new Date());
  const [today, setToday] = useState<Date | null>(null);
  const [appointments, setAppointments] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedAppointment, setSelectedAppointment] = useState<any>(null);

  const start = startOfWeek(currentDate, { weekStartsOn: 1 }); // Lunes
  const end = endOfWeek(currentDate, { weekStartsOn: 1 });

  useEffect(() => {
    setToday(new Date());
  }, []);

  const fetchAppointments = async () => {
    try {
      setLoading(true);
      const token = await getToken();
      if (!token) return;
      
      const data = await connectionsApi.listAppointments(
          format(start, 'yyyy-MM-dd'),
          format(end, 'yyyy-MM-dd'),
          token
      );
      setAppointments(data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAppointments();
  }, [currentDate]); // eslint-disable-line react-hooks/exhaustive-deps

  const nextWeek = () => setCurrentDate(addWeeks(currentDate, 1));
  const prevWeek = () => setCurrentDate(subWeeks(currentDate, 1));

  const days = Array.from({ length: 7 }).map((_, i) => addDays(start, i));

  return (
    <div className="space-y-4">
        <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium capitalize">
                {format(start, "MMMM yyyy", { locale: es })}
            </h3>
            <div className="flex items-center gap-2">
                <Button variant="outline" size="icon" onClick={prevWeek}>
                    <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button variant="outline" size="icon" onClick={() => setCurrentDate(new Date())}>
                    Hoy
                </Button>
                <Button variant="outline" size="icon" onClick={nextWeek}>
                    <ChevronRight className="h-4 w-4" />
                </Button>
            </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-7 gap-4">
            {days.map((day) => (
                <Card key={day.toISOString()} className="min-h-[200px] flex flex-col">
                    <CardHeader className="p-3 text-center border-b bg-muted/20">
                        <span className="text-sm font-medium capitalize text-muted-foreground">
                            {format(day, "EEEE", { locale: es })}
                        </span>
                        <span className={`text-xl font-bold ${today && isSameDay(day, today) ? "text-blue-600" : ""}`}>
                            {format(day, "d")}
                        </span>
                    </CardHeader>
                    <CardContent className="p-2 flex-1 space-y-2">
                        {appointments
                            .filter(appt => isSameDay(new Date(appt.start), day))
                            .map(appt => (
                                <div 
                                    key={appt.id}
                                    onClick={() => setSelectedAppointment(appt)}
                                    className="p-2 text-xs bg-blue-50 border border-blue-100 rounded cursor-pointer hover:bg-blue-100 transition-colors"
                                >
                                    <div className="font-semibold truncate">{format(new Date(appt.start), "HH:mm")}</div>
                                    <div className="truncate">{appt.summary}</div>
                                </div>
                            ))
                        }
                        {loading && (
                            <div className="flex justify-center p-2">
                                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                            </div>
                        )}
                    </CardContent>
                </Card>
            ))}
        </div>

        <Sheet open={!!selectedAppointment} onOpenChange={(open) => !open && setSelectedAppointment(null)}>
            <SheetContent>
                <SheetHeader>
                    <SheetTitle>Detalle de la Cita</SheetTitle>
                    <SheetDescription>Información del evento y del lead.</SheetDescription>
                </SheetHeader>
                {selectedAppointment && (
                    <div className="mt-6 space-y-6">
                        <div className="space-y-4">
                            <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Evento</h4>
                            <div className="bg-muted/30 p-4 rounded-md space-y-3">
                                <div className="flex items-start gap-3">
                                    <CalendarIcon className="h-5 w-5 text-blue-500 mt-0.5" />
                                    <div>
                                        <p className="font-medium">{selectedAppointment.summary}</p>
                                        <p className="text-sm text-muted-foreground capitalize">
                                            {format(new Date(selectedAppointment.start), "EEEE d MMMM, yyyy", { locale: es })}
                                        </p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3">
                                    <Clock className="h-5 w-5 text-blue-500" />
                                    <p className="text-sm">
                                        {format(new Date(selectedAppointment.start), "HH:mm")} - {format(new Date(selectedAppointment.end), "HH:mm")}
                                    </p>
                                </div>
                                {selectedAppointment.meet_link && (
                                    <div className="flex items-center gap-3">
                                        <Video className="h-5 w-5 text-blue-500" />
                                        <a href={selectedAppointment.meet_link} target="_blank" rel="noreferrer" className="text-sm text-blue-600 hover:underline truncate">
                                            Unirse con Google Meet
                                        </a>
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="space-y-4">
                            <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Asistentes</h4>
                            <div className="space-y-2">
                                {selectedAppointment.attendees.map((email: string) => (
                                    <div key={email} className="flex items-center gap-2 p-2 border rounded-md">
                                        <User className="h-4 w-4 text-muted-foreground" />
                                        <span className="text-sm">{email}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}
            </SheetContent>
        </Sheet>
    </div>
  );
}

function SalesContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const tabParam = searchParams.get("tab");
  
  const [activeTab, setActiveTab] = useState(tabParam || "reservations");

  useEffect(() => {
    if (tabParam) {
      setActiveTab(tabParam);
    }
  }, [tabParam]);

  const handleTabChange = (value: string) => {
    setActiveTab(value);
    router.push(`/sales?tab=${value}`);
  };

  return (
    <div className="flex flex-col space-y-8 lg:flex-row lg:space-x-12 lg:space-y-0">
      <Tabs value={activeTab} onValueChange={handleTabChange} className="flex flex-col lg:flex-row w-full space-y-6 lg:space-y-0 lg:space-x-12">
        {/* Sidebar de Navegación Secundaria */}
        <aside className="-mx-4 lg:w-1/5">
          <TabsList className="flex flex-col h-auto items-start justify-start bg-transparent p-0 space-y-1">
            
            {/* Grupo: Citas */}
            <div className="w-full px-4 mb-2 mt-2">
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Citas
              </h3>
            </div>
            
            <TabsTrigger 
              value="appointment-types" 
              className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
            >
              <Settings2 className="mr-2 h-4 w-4" />
              Tipo de Cita
            </TabsTrigger>
            <TabsTrigger 
              value="availability" 
              className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
            >
              <Clock className="mr-2 h-4 w-4" />
              Disponibilidad
            </TabsTrigger>
            <TabsTrigger 
              value="reservations" 
              className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
            >
              <CalendarDays className="mr-2 h-4 w-4" />
              Reservas
            </TabsTrigger>

            {/* Grupo: Ventas */}
            <div className="w-full px-4 mb-2 mt-6">
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Ventas 
              </h3>
            </div>

            <TabsTrigger 
              value="payments" 
              className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
            >
              <CreditCard className="mr-2 h-4 w-4" />
              Pagos
            </TabsTrigger>

          </TabsList>
        </aside>

        {/* Área de Contenido Principal */}
        <div className="flex-1 lg:max-w-4xl">
          <TabsContent value="appointment-types" className="mt-0">
            <EventTypeView />
          </TabsContent>
          <TabsContent value="availability" className="mt-0">
             <AvailabilityView />
          </TabsContent>
          <TabsContent value="reservations" className="mt-0">
             <Card className="w-full min-h-[600px]">
               <CardHeader>
                 <CardTitle className="flex items-center gap-2">
                   <CalendarDays className="h-6 w-6" />
                   Reservas
                 </CardTitle>
                 <CardDescription>Gestiona tus citas y reservas agendadas.</CardDescription>
               </CardHeader>
               <CardContent>
                 {/* Nested Tabs for Reservations */}
                 <Tabs defaultValue="upcoming" className="w-full">
                    <TabsList>
                      <TabsTrigger value="upcoming">Próximamente</TabsTrigger>
                      <TabsTrigger value="unconfirmed">Sin confirmar</TabsTrigger>
                      <TabsTrigger value="past">Pasado</TabsTrigger>
                      <TabsTrigger value="cancelled">Cancelado</TabsTrigger>
                    </TabsList>
                    
                    <TabsContent value="upcoming" className="mt-4">
                       <AppointmentsView />
                    </TabsContent>
                    <TabsContent value="unconfirmed" className="mt-4">
                       <PlaceholderContent title="Sin confirmar" icon={CalendarDays} />
                    </TabsContent>
                    <TabsContent value="past" className="mt-4">
                       <PlaceholderContent title="Pasado" icon={CalendarDays} />
                    </TabsContent>
                    <TabsContent value="cancelled" className="mt-4">
                       <PlaceholderContent title="Cancelado" icon={CalendarDays} />
                    </TabsContent>
                 </Tabs>
               </CardContent>
             </Card>
          </TabsContent>
          
          <TabsContent value="payments" className="mt-0">
             <PlaceholderContent title="Pagos" icon={CreditCard} />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}

export default function SalesPage() {
  return (
    <div className="hidden space-y-6 p-10 pb-16 md:block">
      <div className="space-y-0.5">
        <h2 className="text-2xl font-bold tracking-tight">Ventas</h2>
        <p className="text-muted-foreground">
          Gestiona tus citas, disponibilidad y pagos.
        </p>
      </div>
      <div className="border-t my-6" />
      <Suspense fallback={<div>Cargando ventas...</div>}>
        <SalesContent />
      </Suspense>
    </div>
  );
}
