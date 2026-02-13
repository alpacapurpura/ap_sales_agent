import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FunnelStage } from "../types";
import { Filter } from "lucide-react";

interface FunnelChartProps {
  data: FunnelStage[];
  isLoading?: boolean;
}

export function FunnelChart({ data, isLoading }: FunnelChartProps) {
  // Find max value to scale bars
  const maxCount = Math.max(...data.map((d) => d.count), 1);

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Filter className="h-5 w-5 text-primary" />
          Embudo de Conversión
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div>Cargando...</div>
        ) : (
          <div className="space-y-4">
            {data.map((stage, index) => {
              const percentage = Math.round((stage.count / maxCount) * 100);
              // Color gradient logic could be added here
              return (
                <div key={stage.stage} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-medium text-muted-foreground">
                      {stage.stage.replace('_', ' ')}
                    </span>
                    <span className="font-bold">{stage.count}</span>
                  </div>
                  <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary transition-all duration-500 ease-out"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
