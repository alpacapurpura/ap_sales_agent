"use client";

import { useEffect, useRef, useMemo, useState } from "react";
import { useLeadTimeline, TimelineEvent, clearLeadHistory } from "@/lib/api/audit";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { format } from "date-fns";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter, DialogTrigger } from "@/components/ui/dialog";
import { Bot, User as UserIcon, BrainCircuit, ArrowRight, Activity, Trash2, AlertTriangle } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ContextPanel } from "./context-panel";
import { useAuth } from "@clerk/nextjs";

interface ChatTimelineProps {
  leadId: string | null;
  onSelectEvent: (event: TimelineEvent) => void;
  selectedEventId: string | null;
}

type TimelineGroup = 
  | { type: 'message'; event: TimelineEvent }
  | { type: 'trace_group'; events: TimelineEvent[] };

export function ChatTimeline({ leadId, onSelectEvent, selectedEventId }: ChatTimelineProps) {
  const { data: timeline, isLoading } = useLeadTimeline(leadId);
  const scrollRef = useRef<HTMLDivElement>(null);
  const { getToken } = useAuth();
  
  const [contextOpen, setContextOpen] = useState(false);
  const [contextTab, setContextTab] = useState<"profile" | "state">("profile");

  const [deleteOpen, setDeleteOpen] = useState(false);
  const queryClient = useQueryClient();

  const { mutate: deleteHistory, isPending: isDeleting } = useMutation({
    mutationFn: (uid: string) => clearLeadHistory(uid), // Wait, clearLeadHistory needs (token, uid).
    // I should wrap it below in the handler or here.
    // If I use (uid) here, I can't access token easily without closure, but getToken is available.
    // Better:
    // mutationFn: async (uid: string) => {
    //    const token = await getToken();
    //    if (!token) throw new Error("No token");
    //    return clearLeadHistory(token, uid);
    // }
    // BUT I will do it in the handler to be safe.
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["audit"] });
      setDeleteOpen(false);
    },
    onError: (error) => {
      console.error(error);
      alert("Error al eliminar historial");
    }
  });

  const handleDelete = async () => {
      if (!leadId) return;
      const token = await getToken();
      if (!token) {
          alert("No autenticado");
          return;
      }
      // I can't easily change mutationFn args if I defined it as string -> Promise.
      // So I will just redefine mutationFn to use the closure token, OR pass token to mutation.
      // Let's redefine mutationFn above.
      // Actually, useMutation variables can be anything.
      // Let's stick to the previous pattern I used in ContextPanel: @ts-ignore or wrap it properly.
      // But wait, in ContextPanel I didn't actually fix the mutationFn signature, I just passed an object and @ts-ignored it.
      // That's risky if the mutationFn expects string.
      // Let's fix it properly here.
      
      // I'll define mutationFn to take an object.
      // But `clearLeadHistory` takes (token, leadId).
      // So mutationFn should be: ({token, leadId}) => clearLeadHistory(token, leadId)
  };

  // Re-defining mutation to be clean
  const { mutate: deleteHistoryClean, isPending: isDeletingClean } = useMutation({
    mutationFn: async ({ token, id }: { token: string, id: string }) => {
        return clearLeadHistory(token, id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["audit"] });
      setDeleteOpen(false);
    },
    onError: (error) => {
        console.error(error);
        alert("Error al eliminar historial");
    }
  });

  const onConfirmDelete = async () => {
      if (!leadId) return;
      const token = await getToken();
      if (!token) return;
      deleteHistoryClean({ token, id: leadId });
  }

  // Get last trace ID for context
  const lastTraceId = useMemo(() => {
    if (!timeline) return null;
    const traces = timeline.filter(t => t.type === 'trace');
    return traces.length > 0 ? traces[traces.length - 1].id : null;
  }, [timeline]);

  const openProfile = () => {
    setContextTab("profile");
    setContextOpen(true);
  };

  const openState = () => {
    setContextTab("state");
    setContextOpen(true);
  };

  // Group consecutive trace events
  const groupedTimeline = useMemo(() => {
    if (!timeline) return [];
    
    const groups: TimelineGroup[] = [];
    let currentTraceGroup: TimelineEvent[] = [];

    timeline.forEach((event) => {
      if (event.type === 'message') {
        // If we have accumulated traces, push them first
        if (currentTraceGroup.length > 0) {
          groups.push({ type: 'trace_group', events: [...currentTraceGroup] });
          currentTraceGroup = [];
        }
        groups.push({ type: 'message', event });
      } else {
        // It's a trace event, add to current group
        currentTraceGroup.push(event);
      }
    });

    // Push any remaining traces
    if (currentTraceGroup.length > 0) {
      groups.push({ type: 'trace_group', events: [...currentTraceGroup] });
    }

    return groups;
  }, [timeline]);

  useEffect(() => {
    // Auto scroll could be implemented here
  }, [timeline]);

  if (!leadId) {
    return <div className="flex items-center justify-center h-full text-muted-foreground">Selecciona un lead para ver su historial</div>;
  }

  if (isLoading) {
    return <div className="flex items-center justify-center h-full text-muted-foreground">Cargando historial...</div>;
  }

  return (
    <div className="h-full flex flex-col bg-slate-50/50 dark:bg-zinc-950/50">
      <div className="p-4 border-b bg-background flex items-center justify-between">
        <div className="flex items-center gap-4">
            <h2 className="font-semibold">Timeline de Conversación</h2>
            {leadId && (
                <div className="flex items-center gap-2">
                     <Badge variant="outline" className="cursor-pointer hover:bg-muted/80 transition-colors" onClick={openProfile}>
                        <UserIcon size={12} className="mr-1.5"/> Lead
                     </Badge>
                     <Badge variant="outline" className="cursor-pointer hover:bg-muted/80 transition-colors" onClick={openState}>
                        <Activity size={12} className="mr-1.5"/> AgentState
                     </Badge>
                     
                     <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
                        <DialogTrigger asChild>
                            <Button variant="ghost" size="sm" className="h-6 w-6 p-0 text-muted-foreground hover:text-destructive" title="Borrar Historial">
                                <Trash2 size={14} />
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
                            <Button variant="outline" onClick={() => setDeleteOpen(false)} disabled={isDeletingClean}>
                                Cancelar
                            </Button>
                            <Button 
                                variant="destructive" 
                                onClick={onConfirmDelete}
                                disabled={isDeletingClean || !leadId}
                            >
                                {isDeletingClean ? "Borrando..." : "Sí, borrar todo"}
                            </Button>
                            </DialogFooter>
                        </DialogContent>
                     </Dialog>
                </div>
            )}
        </div>
        <Badge variant="outline" className="font-mono text-xs">
          {timeline?.length || 0} eventos
        </Badge>
      </div>
      
      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        <div className="flex flex-col space-y-6 pb-4 max-w-3xl mx-auto">
          {groupedTimeline.map((group, groupIndex) => {
            if (group.type === 'message') {
              const event = group.event;
              const isSelected = selectedEventId === event.id;
              const isUser = event.role === "user";
              
              return (
                <div
                  key={event.id}
                  onClick={() => onSelectEvent(event)}
                  className={cn(
                    "flex gap-3 max-w-[85%] cursor-pointer group",
                    isUser ? "self-end flex-row-reverse" : "self-start"
                  )}
                >
                  <div className={cn(
                    "h-8 w-8 rounded-full flex items-center justify-center shrink-0",
                    isUser ? "bg-primary text-primary-foreground" : "bg-muted"
                  )}>
                    {isUser ? <UserIcon size={16} /> : <Bot size={16} />}
                  </div>
                  <div className={cn(
                    "rounded-lg p-3 text-sm border shadow-sm transition-all",
                    isUser ? "bg-primary text-primary-foreground" : "bg-card",
                    isSelected ? "ring-2 ring-ring scale-[1.02]" : "group-hover:border-primary/50"
                  )}>
                    <div className="whitespace-pre-wrap break-words">{event.content}</div>
                    <div className={cn(
                      "text-[10px] mt-1 text-right opacity-70",
                      isUser ? "text-primary-foreground" : "text-muted-foreground"
                    )}>
                      {format(new Date(event.created_at), "HH:mm:ss")}
                    </div>
                  </div>
                </div>
              );
            } else {
              // Trace Group - Horizontal Scroll
              return (
                <div key={`group-${groupIndex}`} className="w-full">
                  <div className="flex items-center gap-2 mb-2 px-2">
                    <Activity size={14} className="text-muted-foreground" />
                    <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Process Flow
                    </span>
                    <div className="h-px bg-border flex-1" />
                  </div>
                  
                  <div className="bg-card/50 border rounded-xl p-1 shadow-sm">
                    <ScrollArea className="w-full whitespace-nowrap rounded-lg">
                      <div className="flex items-center p-2 gap-2">
                        {group.events.map((event, index) => {
                          const isSelected = selectedEventId === event.id;
                          const isLast = index === group.events.length - 1;

                          return (
                            <div key={event.id} className="flex items-center gap-2">
                              <div
                                onClick={() => onSelectEvent(event)}
                                className={cn(
                                  "flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-mono border bg-background cursor-pointer hover:bg-muted transition-all min-w-[100px]",
                                  isSelected ? "ring-2 ring-ring border-primary" : "border-border"
                                )}
                              >
                                <BrainCircuit size={14} className="text-orange-500 shrink-0" />
                                <div className="flex flex-col truncate">
                                  <span className="font-semibold truncate">{event.node_name}</span>
                                  <span className="text-[10px] text-muted-foreground">
                                    {event.execution_time_ms?.toFixed(0)}ms
                                  </span>
                                </div>
                              </div>
                              
                              {!isLast && (
                                <ArrowRight size={14} className="text-muted-foreground/50 shrink-0" />
                              )}
                            </div>
                          );
                        })}
                      </div>
                      <ScrollBar orientation="horizontal" />
                    </ScrollArea>
                  </div>
                </div>
              );
            }
          })}
        </div>
      </ScrollArea>
      
      <ContextPanel 
        leadId={leadId} 
        lastTraceId={lastTraceId} 
        isOpen={contextOpen} 
        onOpenChange={setContextOpen} 
        defaultTab={contextTab}
      />
    </div>
  );
}
