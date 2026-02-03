"use client";

import { useState } from "react";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useLeadDetails, useTraceDetails, clearLeadHistory } from "@/lib/api/audit";
import { Loader2, Trash2, AlertTriangle } from "lucide-react";
import { useQueryClient, useMutation } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";

interface ContextPanelProps {
  leadId: string | null;
  lastTraceId: string | null;
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  defaultTab?: "profile" | "state";
}

export function ContextPanel({ leadId, lastTraceId, isOpen, onOpenChange, defaultTab = "profile" }: ContextPanelProps) {
  const { data: lead, isLoading: loadingLead } = useLeadDetails(leadId);
  const { data: trace, isLoading: loadingTrace } = useTraceDetails(lastTraceId);
  
  const [deleteOpen, setDeleteOpen] = useState(false);
  const queryClient = useQueryClient();

  const { mutate: deleteHistory, isPending: isDeleting } = useMutation({
    mutationFn: async ({ token, leadId }: { token: string, leadId: string }) => {
        return clearLeadHistory(token, leadId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["audit"] });
      setDeleteOpen(false);
      onOpenChange(false); // Close panel after delete
    },
    onError: (error) => {
      console.error(error);
      alert("Error al eliminar historial");
    }
  });

  const { getToken } = useAuth();
  
  const handleDelete = async () => {
      if (!leadId) return;
      const token = await getToken();
      if (!token) {
          alert("No autenticado");
          return;
      }
      deleteHistory({ token, leadId });
  };

  return (
    <Sheet open={isOpen} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[400px] sm:w-[540px] flex flex-col p-0 gap-0">
        <SheetHeader className="px-6 py-4 border-b">
          <SheetTitle>Panel de Contexto del Lead</SheetTitle>
          <SheetDescription>Información detallada del lead y estado del agente</SheetDescription>
        </SheetHeader>
        
        <Tabs key={defaultTab} defaultValue={defaultTab} className="flex-1 flex flex-col min-h-0">
          <div className="px-6 border-b bg-muted/40 flex items-center gap-2 py-2">
            <TabsList className="grid flex-1 grid-cols-2">
              <TabsTrigger value="profile">Perfil Lead</TabsTrigger>
              <TabsTrigger value="state">Agent State</TabsTrigger>
            </TabsList>
            
            <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
              <DialogTrigger asChild>
                <Button variant="destructive" size="icon" title="Borrar Historial" disabled={!leadId}>
                  <Trash2 className="h-4 w-4" />
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle className="flex items-center gap-2 text-destructive">
                    <AlertTriangle className="h-5 w-5" />
                    Borrar Historial del Lead
                  </DialogTitle>
                  <DialogDescription>
                    Esta acción eliminará permanentemente todos los mensajes, trazas y memoria de este lead. 
                    El lead volverá al inicio del funnel.
                    <br/><br/>
                    <strong>Esta acción no se puede deshacer.</strong>
                  </DialogDescription>
                </DialogHeader>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setDeleteOpen(false)} disabled={isDeleting}>
                    Cancelar
                  </Button>
                  <Button 
                    variant="destructive" 
                    onClick={handleDelete}
                    disabled={isDeleting || !leadId}
                  >
                    {isDeleting ? "Borrando..." : "Sí, borrar todo"}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          <TabsContent value="profile" className="flex-1 m-0 min-h-0 relative">
             <ScrollArea className="h-full">
                <div className="p-6 space-y-6">
                   {loadingLead ? (
                      <div className="flex justify-center p-8"><Loader2 className="animate-spin" /></div>
                   ) : lead ? (
                      <div className="space-y-4">
                         {/* Basic Info */}
                         <div className="grid grid-cols-2 gap-4">
                            <div>
                               <label className="text-xs font-medium text-muted-foreground">ID</label>
                               <div className="text-sm font-mono truncate" title={lead.id}>{lead.id}</div>
                            </div>
                            <div>
                               <label className="text-xs font-medium text-muted-foreground">Nombre</label>
                               <div className="text-sm font-medium">{lead.full_name}</div>
                            </div>
                            <div>
                               <label className="text-xs font-medium text-muted-foreground">Creado</label>
                               <div className="text-sm">{new Date(lead.created_at).toLocaleDateString()}</div>
                            </div>
                            <div>
                               <label className="text-xs font-medium text-muted-foreground">Canales</label>
                               <div className="flex gap-1 flex-wrap">
                                  {lead.telegram_id && <span className="text-[10px] bg-blue-100 text-blue-800 px-1.5 rounded">TG</span>}
                                  {lead.whatsapp_id && <span className="text-[10px] bg-green-100 text-green-800 px-1.5 rounded">WA</span>}
                               </div>
                            </div>
                         </div>
                         
                         {/* JSON Dump */}
                         <div>
                            <label className="text-xs font-medium text-muted-foreground mb-2 block">Profile Data (JSON Completo)</label>
                            <pre className="bg-slate-950 text-slate-50 p-4 rounded-lg text-xs font-mono overflow-auto whitespace-pre-wrap break-all max-h-[500px]">
                               {JSON.stringify(lead.profile_data || {}, null, 2)}
                            </pre>
                         </div>
                      </div>
                   ) : (
                      <div className="text-muted-foreground text-center">Lead no encontrado</div>
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
                         <p>No hay trazas disponibles para este lead.</p>
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
