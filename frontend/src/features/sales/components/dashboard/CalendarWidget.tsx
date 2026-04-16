"use client";

import { useAuth } from "@clerk/nextjs";
import { format, startOfMonth, endOfMonth, isSameDay, parseISO } from "date-fns";
import { es } from "date-fns/locale";
import {
  Calendar as CalendarIcon,
  Clock,
  Settings2,
  Loader2,
  ChevronRight,
  MapPin,
} from "lucide-react";
import { useState, useEffect } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { connectionsApi } from "@/lib/api/connections";

/** Google Calendar event shape returned by the connections API. */
interface CalendarAppointment {
  id?: string;
  summary: string;
  start: string;
  end: string;
  meet_link?: string;
  attendees?: string[];
  location?: string;
}

interface CalendarWidgetProps {
  onAppointmentClick: (appointment: CalendarAppointment) => void;
  onConfigClick: () => void;
}

export function CalendarWidget({ onAppointmentClick, onConfigClick }: CalendarWidgetProps) {
  const { getToken } = useAuth();
  const [date, setDate] = useState<Date | undefined>(new Date());
  const [appointments, setAppointments] = useState<CalendarAppointment[]>([]);
  const [loading, setLoading] = useState(false);
  const [month, setMonth] = useState<Date>(new Date());

  useEffect(() => {
    const fetchAppointments = async () => {
      try {
        setLoading(true);
        const token = await getToken();
        if (!token) return;

        const start = startOfMonth(month);
        const end = endOfMonth(month);

        const data = await connectionsApi.listAppointments(
          format(start, "yyyy-MM-dd"),
          format(end, "yyyy-MM-dd"),
          token,
        );
        setAppointments(data as CalendarAppointment[]);
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };
    void fetchAppointments();
  }, [month, getToken]);

  const handleMonthChange = (newMonth: Date) => {
    setMonth(newMonth);
  };

  const selectedDayAppointments = appointments.filter(
    (appt) => date && isSameDay(parseISO(appt.start), date),
  );

  // Mark days with appointments
  const daysWithAppointments = appointments.map((appt) => new Date(appt.start));

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-base font-semibold">Agenda</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 p-0 flex flex-col md:flex-row h-full">
        <div className="p-4 border-r md:w-auto flex justify-center">
          <Calendar
            mode="single"
            selected={date}
            onSelect={setDate}
            month={month}
            onMonthChange={handleMonthChange}
            locale={es}
            className="rounded-md border shadow-sm"
            modifiers={{
              booked: daysWithAppointments,
            }}
            modifiersStyles={{
              booked: { fontWeight: "bold", textDecoration: "underline", color: "var(--primary)" },
            }}
          />
        </div>

        <div className="flex-1 p-4 overflow-y-auto max-h-[400px] md:max-h-none">
          <h4 className="text-sm font-medium mb-4 text-muted-foreground capitalize">
            {date ? format(date, "EEEE d 'de' MMMM", { locale: es }) : "Selecciona un día"}
          </h4>

          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : selectedDayAppointments.length > 0 ? (
            <div className="space-y-3">
              {selectedDayAppointments.map((appt) => (
                <div
                  key={appt.id}
                  onClick={() => onAppointmentClick(appt)}
                  className="group flex flex-col gap-2 p-3 rounded-lg border bg-card hover:bg-accent/50 cursor-pointer transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <span className="font-medium text-sm line-clamp-1">{appt.summary}</span>
                    <Badge variant="outline" className="text-[10px] h-5 px-1.5 font-normal">
                      Confirmado
                    </Badge>
                  </div>

                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <Clock className="h-3.5 w-3.5" />
                      <span>
                        {format(parseISO(appt.start), "HH:mm")} -{" "}
                        {format(parseISO(appt.end), "HH:mm")}
                      </span>
                    </div>
                    {appt.location && (
                      <div className="flex items-center gap-1">
                        <MapPin className="h-3.5 w-3.5" />
                        <span className="truncate max-w-[100px]">{appt.location}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-40 text-muted-foreground bg-muted/10 rounded-lg border border-dashed">
              <CalendarIcon className="h-8 w-8 mb-2 opacity-20" />
              <p className="text-sm">No hay citas para este día</p>
              <Button variant="link" size="sm" className="mt-2 text-xs" onClick={onConfigClick}>
                Configurar horarios
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
