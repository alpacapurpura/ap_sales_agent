"use client";

import { format } from "date-fns";
import { es } from "date-fns/locale";
import { Calendar as CalendarIcon, Clock, Video, User, XCircle, CheckCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from "@/components/ui/sheet";

/** Google Calendar event shape returned by the connections API. */
interface CalendarAppointment {
  summary: string;
  start: string;
  end: string;
  meet_link?: string;
  attendees?: string[];
}

interface AppointmentSheetProps {
  appointment: CalendarAppointment | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AppointmentSheet({ appointment, open, onOpenChange }: AppointmentSheetProps) {
  if (!appointment) return null;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>Detalle de la Cita</SheetTitle>
          <SheetDescription>Información del evento y del lead.</SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          <div className="space-y-4">
            <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
              Evento
            </h4>
            <div className="bg-muted/30 p-4 rounded-md space-y-3">
              <div className="flex items-start gap-3">
                <CalendarIcon className="h-5 w-5 text-blue-500 mt-0.5" />
                <div>
                  <p className="font-medium">{appointment.summary}</p>
                  <p className="text-sm text-muted-foreground capitalize">
                    {format(new Date(appointment.start), "EEEE d MMMM, yyyy", { locale: es })}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Clock className="h-5 w-5 text-blue-500" />
                <p className="text-sm">
                  {format(new Date(appointment.start), "HH:mm")} -{" "}
                  {format(new Date(appointment.end), "HH:mm")}
                </p>
              </div>
              {appointment.meet_link && (
                <div className="flex items-center gap-3">
                  <Video className="h-5 w-5 text-blue-500" />
                  <a
                    href={appointment.meet_link}
                    target="_blank"
                    rel="noreferrer"
                    className="text-sm text-blue-600 hover:underline truncate"
                  >
                    Unirse con Google Meet
                  </a>
                </div>
              )}
            </div>
          </div>

          <div className="space-y-4">
            <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
              Asistentes
            </h4>
            <div className="space-y-2">
              {appointment.attendees?.map((email: string) => (
                <div key={email} className="flex items-center gap-2 p-2 border rounded-md">
                  <User className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">{email}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <SheetFooter className="mt-8 flex-col sm:flex-col gap-2">
          <Button className="w-full" variant="default">
            <CheckCircle className="mr-2 h-4 w-4" /> Marcar como Asistió
          </Button>
          <div className="flex gap-2 w-full">
            <Button className="flex-1" variant="outline">
              Reprogramar
            </Button>
            <Button className="flex-1" variant="destructive">
              <XCircle className="mr-2 h-4 w-4" /> Cancelar
            </Button>
          </div>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
