"use client";

import { useAuth, UserButton } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { StatsCard } from "@/components/dashboard/stats-card";
import { FileText, Database, Activity, Eye } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { config } from "@/lib/config";

export default function Home() {
  const { getToken } = useAuth();
  const API_URL = config.api.baseUrl;

  const { data: stats, isLoading, isError } = useQuery({
    queryKey: ['stats'],
    queryFn: async () => {
      const token = await getToken();
      const res = await fetch(`${API_URL}/api/v1/knowledge/stats`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      if (!res.ok) throw new Error('Failed to fetch stats');
      return res.json();
    }
  });

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Resumen General</h2>
        <p className="text-muted-foreground">Estado actual de la base de conocimiento.</p>
      </div>

      {isError && (
           <div className="p-4 rounded-md bg-red-50 text-red-600 border border-red-200">
              Error al conectar con la API. Verifica que el backend esté corriendo.
           </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard 
          title="Estado API" 
          value={isError ? "Error" : "Online"} 
          icon={Activity} 
          description="Conexión con el backend"
          loading={isLoading}
        />
        <StatsCard 
          title="Vectores Indexados" 
          value={stats?.vector_count ?? 0} 
          icon={Database} 
          description="Total de fragmentos en Qdrant"
          loading={isLoading}
        />
        <StatsCard 
          title="Documentos" 
          value={stats?.doc_count ?? 0} 
          icon={FileText} 
          description="Archivos procesados"
          loading={isLoading}
        />
         <Card className="hover:bg-slate-50 transition-colors cursor-pointer group">
            <Link href="/audit">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Auditoría Agente</CardTitle>
                  <Eye className="h-4 w-4 text-muted-foreground group-hover:text-primary" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">Inspect</div>
                  <p className="text-xs text-muted-foreground">Ver trazas y mensajes</p>
                </CardContent>
            </Link>
         </Card>
      </div>
    </div>
  );
}
