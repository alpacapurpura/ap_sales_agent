"use client";
import { useAuth } from "@clerk/nextjs";
import { format, parseISO } from "date-fns";
import { Calendar, Video, Clock, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { crmDashboardApi } from "@/lib/api/crm-dashboard-api";

import type { AgendaItem } from "@/lib/api/crm-dashboard-api";

export const AgendaLane = () => {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const [appointments, setAppointments] = useState<AgendaItem[]>([]);
  const [range, setRange] = useState<"today" | "week">("today");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      if (!isLoaded || !isSignedIn) return;

      setLoading(true);
      try {
        const token = await getToken();
        if (!token) return;
        console.log("Fetching agenda...", range);
        const data = await crmDashboardApi.getAgenda(token, range);
        console.log("Agenda data:", data);
        setAppointments(data);
      } catch (error) {
        console.error("Failed to fetch agenda", error);
      } finally {
        setLoading(false);
      }
    };
    void fetch();
  }, [getToken, isLoaded, isSignedIn, range]);

  return (
    <Card className="flex flex-col h-full bg-slate-50/50 dark:bg-slate-900/20 border-l-4 border-l-blue-500">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-bold text-blue-700 dark:text-blue-500 flex items-center gap-2">
            <span>Conversión & Cierre</span>
            <Calendar className="w-5 h-5" />
          </CardTitle>
          <div className="flex bg-muted rounded-lg p-1">
            <Button
              variant={range === "today" ? "secondary" : "ghost"}
              size="sm"
              className="h-6 text-xs"
              onClick={() => setRange("today")}
            >
              Today
            </Button>
            <Button
              variant={range === "week" ? "secondary" : "ghost"}
              size="sm"
              className="h-6 text-xs"
              onClick={() => setRange("week")}
            >
              Week
            </Button>
          </div>
        </div>
        <p className="text-xs text-muted-foreground">Upcoming Appointments</p>
      </CardHeader>
      <CardContent className="flex-1 p-0">
        <ScrollArea className="h-[500px] px-4">
          <div className="space-y-3 py-4">
            {appointments.map((appt) => (
              <div
                key={appt.id}
                className="p-3 bg-white dark:bg-slate-950 rounded-lg border shadow-sm"
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="font-semibold text-sm">{appt.summary}</div>
                  <Badge variant="secondary" className="text-[10px]">
                    {appt.status}
                  </Badge>
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
                  <Clock className="w-3 h-3" />
                  <span>
                    {format(parseISO(appt.start_time), "EEE, h:mm a")} -{" "}
                    {format(parseISO(appt.end_time), "h:mm a")}
                  </span>
                </div>
                <div className="flex justify-between items-center mt-3">
                  <span className="text-xs font-medium">{appt.lead_name}</span>
                  {appt.meeting_link && (
                    <Button size="sm" variant="outline" className="h-7 text-xs gap-1" asChild>
                      <a href={appt.meeting_link} target="_blank" rel="noopener noreferrer">
                        <Video className="w-3 h-3" />
                        Join
                      </a>
                    </Button>
                  )}
                </div>
              </div>
            ))}
            {!loading && appointments.length === 0 && (
              <div className="text-center text-sm text-muted-foreground py-10">
                No appointments scheduled
              </div>
            )}
            {loading && (
              <div className="flex justify-center items-center py-10">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
};
