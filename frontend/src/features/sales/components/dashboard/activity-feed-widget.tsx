"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { formatDistanceToNow } from "date-fns";
import { es } from "date-fns/locale";
import { CreditCard, CalendarCheck, UserPlus, AlertCircle } from "lucide-react";

export function ActivityFeedWidget() {
  const activities: any[] = [];

  const getIcon = (type: string) => {
    switch (type) {
      case "payment": return <CreditCard className="h-4 w-4 text-green-500" />;
      case "appointment": return <CalendarCheck className="h-4 w-4 text-blue-500" />;
      case "lead": return <UserPlus className="h-4 w-4 text-purple-500" />;
      case "alert": return <AlertCircle className="h-4 w-4 text-red-500" />;
      default: return <UserPlus className="h-4 w-4" />;
    }
  };

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <CardTitle className="text-base font-semibold">Actividad Reciente</CardTitle>
      </CardHeader>
      <CardContent className="p-0 flex-1">
        <ScrollArea className="h-[300px] lg:h-full px-4 pb-4">
          <div className="space-y-4">
            {activities.length > 0 ? (
              activities.map((activity) => (
                <div key={activity.id} className="flex items-start gap-3 pb-3 border-b last:border-0 last:pb-0">
                  <div className="mt-1 bg-muted p-1.5 rounded-full">
                    {getIcon(activity.type)}
                  </div>
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium leading-none">{activity.title}</p>
                      <span className="text-xs text-muted-foreground">
                        {formatDistanceToNow(activity.timestamp, { addSuffix: true, locale: es })}
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground line-clamp-1">
                      {activity.description}
                    </p>
                    {activity.amount && (
                      <Badge variant="secondary" className="mt-1 text-xs font-normal text-green-700 bg-green-50 border-green-200">
                        +{activity.amount}
                      </Badge>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div className="flex flex-col items-center justify-center h-40 text-muted-foreground">
                <AlertCircle className="h-8 w-8 mb-2 opacity-50" />
                <p className="text-sm">No hay actividad reciente</p>
              </div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
