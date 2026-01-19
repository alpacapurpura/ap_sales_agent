"use client";

import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useUserDetails, useTraceDetails } from "@/lib/api/audit";
import { Loader2 } from "lucide-react";

interface ContextPanelProps {
  userId: string | null;
  lastTraceId: string | null;
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  defaultTab?: "profile" | "state";
}

export function ContextPanel({ userId, lastTraceId, isOpen, onOpenChange, defaultTab = "profile" }: ContextPanelProps) {
  const { data: user, isLoading: loadingUser } = useUserDetails(userId);
  const { data: trace, isLoading: loadingTrace } = useTraceDetails(lastTraceId);

  return (
    <Sheet open={isOpen} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[400px] sm:w-[540px] flex flex-col p-0 gap-0">
        <SheetHeader className="px-6 py-4 border-b">
          <SheetTitle>Panel de Contexto</SheetTitle>
          <SheetDescription>Información detallada del usuario y estado del agente</SheetDescription>
        </SheetHeader>
        
        {/* Key forces re-mount when defaultTab changes (e.g. clicking different button) */}
        <Tabs key={defaultTab} defaultValue={defaultTab} className="flex-1 flex flex-col min-h-0">
          <div className="px-6 border-b bg-muted/40">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="profile">Perfil Usuario</TabsTrigger>
              <TabsTrigger value="state">Agent State</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="profile" className="flex-1 m-0 min-h-0 relative">
             <ScrollArea className="h-full">
                <div className="p-6 space-y-6">
                   {loadingUser ? (
                      <div className="flex justify-center p-8"><Loader2 className="animate-spin" /></div>
                   ) : user ? (
                      <div className="space-y-4">
                         {/* Basic Info */}
                         <div className="grid grid-cols-2 gap-4">
                            <div>
                               <label className="text-xs font-medium text-muted-foreground">ID</label>
                               <div className="text-sm font-mono truncate" title={user.id}>{user.id}</div>
                            </div>
                            <div>
                               <label className="text-xs font-medium text-muted-foreground">Nombre</label>
                               <div className="text-sm font-medium">{user.full_name}</div>
                            </div>
                            <div>
                               <label className="text-xs font-medium text-muted-foreground">Creado</label>
                               <div className="text-sm">{new Date(user.created_at).toLocaleDateString()}</div>
                            </div>
                            <div>
                               <label className="text-xs font-medium text-muted-foreground">Canales</label>
                               <div className="flex gap-1 flex-wrap">
                                  {user.telegram_id && <span className="text-[10px] bg-blue-100 text-blue-800 px-1.5 rounded">TG</span>}
                                  {user.whatsapp_id && <span className="text-[10px] bg-green-100 text-green-800 px-1.5 rounded">WA</span>}
                               </div>
                            </div>
                         </div>
                         
                         {/* JSON Dump */}
                         <div>
                            <label className="text-xs font-medium text-muted-foreground mb-2 block">Profile Data (JSON Completo)</label>
                            <pre className="bg-slate-950 text-slate-50 p-4 rounded-lg text-xs font-mono overflow-auto whitespace-pre-wrap break-all max-h-[500px]">
                               {JSON.stringify(user.profile_data || {}, null, 2)}
                            </pre>
                         </div>
                      </div>
                   ) : (
                      <div className="text-muted-foreground text-center">Usuario no encontrado</div>
                   )}
                </div>
             </ScrollArea>
          </TabsContent>

          <TabsContent value="state" className="flex-1 m-0 min-h-0 relative">
             <ScrollArea className="h-full">
                <div className="p-6">
                   {loadingTrace ? (
                      <div className="flex justify-center p-8"><Loader2 className="animate-spin" /></div>
                   ) : trace ? (
                      <div className="space-y-4">
                         <div className="flex items-center justify-between">
                            <span className="text-sm font-medium">Último Nodo: {trace.node_name}</span>
                            <span className="text-xs text-muted-foreground">{new Date(trace.created_at).toLocaleString()}</span>
                         </div>
                         <div>
                            <label className="text-xs font-medium text-muted-foreground mb-2 block">Output State (JSON Completo)</label>
                            <pre className="bg-slate-950 text-slate-50 p-4 rounded-lg text-xs font-mono overflow-auto whitespace-pre-wrap break-all max-h-[600px]">
                               {JSON.stringify(trace.output_state || {}, null, 2)}
                            </pre>
                         </div>
                      </div>
                   ) : (
                      <div className="text-muted-foreground text-center py-8">
                         <p>No hay trazas disponibles para este usuario.</p>
                         <p className="text-xs mt-2">El estado se genera cuando el agente ejecuta nodos.</p>
                      </div>
                   )}
                </div>
             </ScrollArea>
          </TabsContent>
        </Tabs>
      </SheetContent>
    </Sheet>
  );
}
