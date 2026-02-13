import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, ArrowRight, CheckCircle2 } from "lucide-react";
import Link from "next/link";
import { ActionItem } from "../types";

interface WarRoomWidgetProps {
  items: ActionItem[];
  isLoading?: boolean;
}

export function WarRoomWidget({ items, isLoading }: WarRoomWidgetProps) {
  if (isLoading) {
    return (
      <Card className="h-full border-red-200 dark:border-red-900 bg-red-50/10">
        <CardHeader>
          <CardTitle className="text-red-600 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5" /> Sala de Guerra
          </CardTitle>
        </CardHeader>
        <CardContent>Cargando...</CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full border-red-200 dark:border-red-900 bg-red-50/10 shadow-sm">
      <CardHeader className="pb-3">
        <CardTitle className="text-red-600 flex items-center gap-2">
          <AlertTriangle className="h-5 w-5" /> Sala de Guerra
          <Badge variant="destructive" className="ml-auto">
            {items.length} Requieren Acción
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {items.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
            <CheckCircle2 className="h-8 w-8 text-green-500 mb-2" />
            <p>Todo bajo control. Buen trabajo.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {items.map((item) => (
              <div
                key={item.id}
                className="bg-background rounded-lg p-3 border shadow-sm flex flex-col gap-2 hover:border-red-300 transition-colors"
              >
                <div className="flex justify-between items-start">
                  <div className="font-semibold text-sm">{item.title}</div>
                  <Badge variant={item.priority === "HIGH" ? "destructive" : "outline"} className="text-[10px] h-5">
                    {item.priority}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground line-clamp-2">
                  {item.description}
                </p>
                {item.link && (
                  <Button variant="ghost" size="sm" className="w-full h-7 text-xs justify-between mt-1" asChild>
                    <Link href={item.link}>
                      Resolver
                      <ArrowRight className="h-3 w-3 ml-2" />
                    </Link>
                  </Button>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
