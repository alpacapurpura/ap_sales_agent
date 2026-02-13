import { useDashboardSummary } from "../hooks/use-dashboard";
import { MetricCard } from "./MetricCard";
import { WarRoomWidget } from "./WarRoomWidget";
import { AgendaWidget } from "./AgendaWidget";
import { FunnelChart } from "./FunnelChart";
import { DollarSign, Users, TrendingUp, Activity } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

export function DashboardLayout() {
  const { data, isLoading, error } = useDashboardSummary();

  if (error) {
    return (
      <div className="p-8 text-center text-red-500">
        Error al cargar el dashboard. Por favor recarga la página.
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Centro de Comando</h1>
        <div className="flex items-center space-x-2">
          {/* Date Picker or Filters could go here */}
        </div>
      </div>

      {/* Top Row: Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Pipeline Total"
          value={isLoading ? "..." : `$${data?.metrics.pipeline_value.toLocaleString()}`}
          description="Valor potencial en juego"
          icon={DollarSign}
        />
        <MetricCard
          title="Leads Activos"
          value={isLoading ? "..." : data?.metrics.active_leads_count ?? 0}
          description="Interactuando esta semana"
          icon={Users}
        />
        <MetricCard
          title="Tasa de Conversión"
          value={isLoading ? "..." : `${data?.metrics.conversion_rate}%`}
          description="Leads a Citas"
          icon={TrendingUp}
        />
        <MetricCard
          title="Salud del Agente"
          value="98%"
          description="Uptime operativo"
          icon={Activity}
        />
      </div>

      {/* Main Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        {/* War Room: Takes 4 columns */}
        <div className="col-span-4">
          <WarRoomWidget 
            items={data?.action_items || []} 
            isLoading={isLoading} 
          />
        </div>

        {/* Agenda: Takes 3 columns */}
        <div className="col-span-3">
          <AgendaWidget 
            items={data?.agenda || []} 
            isLoading={isLoading} 
          />
        </div>
      </div>

      {/* Bottom Row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <div className="col-span-3">
           <FunnelChart 
             data={data?.funnel || []} 
             isLoading={isLoading} 
           />
        </div>
        <div className="col-span-4">
           {/* Placeholder for future "Knowledge Gaps" or "Sentiment Analysis" */}
           <div className="h-full min-h-[200px] rounded-xl border bg-card text-card-foreground shadow flex items-center justify-center text-muted-foreground border-dashed">
             Próximamente: Análisis de Sentimiento y Lagunas de Conocimiento
           </div>
        </div>
      </div>
    </div>
  );
}
