import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CalendarClock, Video } from "lucide-react";
import { AgendaItem } from "../types";
import { format, parseISO } from "date-fns";
import { es } from "date-fns/locale";

interface AgendaWidgetProps {
  items: AgendaItem[];
  isLoading?: boolean;
}

export function AgendaWidget({ items, isLoading }: AgendaWidgetProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CalendarClock className="h-5 w-5 text-primary" />
          Próximos Cierres
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="text-sm text-muted-foreground">Cargando agenda...</div>
        ) : items.length === 0 ? (
          <div className="text-sm text-muted-foreground py-4">
            No hay citas próximas.
          </div>
        ) : (
          <div className="space-y-4">
            {items.map((item) => (
              <div key={item.id} className="flex items-center justify-between border-b pb-3 last:border-0 last:pb-0">
                <div className="space-y-1">
                  <p className="font-medium text-sm">{item.attendee_name}</p>
                  <div className="flex items-center text-xs text-muted-foreground gap-2">
                    <Video className="h-3 w-3" />
                    <span>
                      {format(parseISO(item.start_time), "EEEE d, HH:mm", { locale: es })}
                    </span>
                  </div>
                </div>
                <Badge variant={item.status === "scheduled" ? "default" : "secondary"}>
                  {item.status}
                </Badge>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
