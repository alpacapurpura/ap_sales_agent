"use client";

import { useEffect, useRef, useMemo, useState } from "react";
import { useLeadTimeline, TimelineEvent, clearLeadHistory } from "@/lib/api/audit";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { format, isToday, isYesterday } from "date-fns";
import { es } from "date-fns/locale";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter, DialogTrigger } from "@/components/ui/dialog";
import { Bot, User as UserIcon, ArrowRight, Activity, Trash2, AlertTriangle } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ContextPanel } from "./context-panel";
import { NodeDetailsPanel } from "./node-details-panel";
import { getNodeIcon, getNodeColor } from "./node-icons";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { useAuth } from "@clerk/nextjs";

interface ChatTimelineProps {
  leadId: string | null;
  onSelectEvent: (event: TimelineEvent) => void;
  selectedEventId: string | null;
}

type TimelineGroup = 
  | { type: 'message'; event: TimelineEvent }
  | { type: 'trace_group'; events: TimelineEvent[] };

function formatMessageDate(dateStr: string) {
  const date = new Date(dateStr);
  
  if (isToday(date)) {
    return `Hoy ${format(date, "HH:mm:ss")}`;
  }
  
  if (isYesterday(date)) {
    return `Ayer ${format(date, "HH:mm:ss")}`;
  }

  // Format: "Lunes 02 de Febrero del 2026 - 23:54:48"
  // date-fns pattern: "EEEE dd 'de' MMMM 'del' yyyy - HH:mm:ss"
  const formatted = format(date, "EEEE dd 'de' MMMM 'del' yyyy - HH:mm:ss", { locale: es });
  
  // Capitalize first letter (Day name)
  return formatted.charAt(0).toUpperCase() + formatted.slice(1);
}

export function ChatTimeline({ leadId, onSelectEvent, selectedEventId }: ChatTimelineProps) {
  const { data: timeline, isLoading } = useLeadTimeline(leadId);
  const scrollRef = useRef<HTMLDivElement>(null);
  const { getToken } = useAuth();
  
  const [contextOpen, setContextOpen] = useState(false);
  const [contextTab, setContextTab] = useState<"profile" | "state">("profile");
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null);

  const [deleteOpen, setDeleteOpen] = useState(false);
  const queryClient = useQueryClient();

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
    let pendingBotEvent: TimelineEvent | null = null;

    timeline.forEach((event) => {
      if (event.type === 'message') {
        if (event.role === 'user') {
            // Flush any pending bot stuff
            if (currentTraceGroup.length > 0) {
                groups.push({ type: 'trace_group', events: [...currentTraceGroup] });
                currentTraceGroup = [];
            }
            if (pendingBotEvent) {
                groups.push({ type: 'message', event: pendingBotEvent });
                pendingBotEvent = null;
            }
            
            // Push user message immediately
            groups.push({ type: 'message', event });
        } else {
            // It's a bot message
            // If we already have a pending bot message, flush it and its traces
            if (pendingBotEvent) {
                 if (currentTraceGroup.length > 0) {
                    groups.push({ type: 'trace_group', events: [...currentTraceGroup] });
                    currentTraceGroup = [];
                }
                groups.push({ type: 'message', event: pendingBotEvent });
            }
            // Set new pending bot
            pendingBotEvent = event;
        }
      } else {
        // Trace event
        currentTraceGroup.push(event);
      }
    });

    // Final flush
    if (currentTraceGroup.length > 0) {
      groups.push({ type: 'trace_group', events: [...currentTraceGroup] });
    }
    if (pendingBotEvent) {
      groups.push({ type: 'message', event: pendingBotEvent });
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
                      {formatMessageDate(event.created_at)}
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
                          const hasLLM = !!event.llm_summary;
                          const NodeIcon = getNodeIcon(event.node_name, hasLLM);
                          const nodeColor = hasLLM ? "text-pink-500" : getNodeColor(event.node_name);

                          return (
                            <div key={event.id} className="flex items-center gap-2">
                              <TooltipProvider>
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <div
                                      onClick={() => {
                                        onSelectEvent(event);
                                        setSelectedTraceId(event.id);
                                      }}
                                      className={cn(
                                        "flex flex-col items-center justify-center w-11 h-11 rounded-lg border bg-background cursor-pointer hover:bg-muted/80 transition-all shadow-sm",
                                        isSelected ? "ring-2 ring-ring border-primary" : "border-border hover:border-primary/50"
                                      )}
                                    >
                                      <NodeIcon size={16} className={cn("mb-0.5", nodeColor)} />
                                      <span className="text-[9px] text-muted-foreground font-mono leading-none">
                                        {event.execution_time_ms?.toFixed(0)}ms
                                      </span>
                                    </div>
                                  </TooltipTrigger>
                                  <TooltipContent>
                                    <p className="font-semibold mb-1">{event.node_name}</p>
                                    {event.llm_summary && (
                                      <div className="text-xs text-muted-foreground space-y-0.5 border-t pt-1 mt-1">
                                        <div className="flex items-center gap-1.5">
                                            <span className="font-mono text-[10px] bg-muted px-1 rounded">{event.llm_summary.model}</span>
                                        </div>
                                        <div className="font-mono text-[10px]">
                                            {event.llm_summary.total_tokens} tokens
                                        </div>
                                      </div>
                                    )}
                                    <p className="text-[10px] text-muted-foreground mt-1">Click para ver detalles</p>
                                  </TooltipContent>
                                </Tooltip>
                              </TooltipProvider>
                              
                              {!isLast && (
                                <ArrowRight size={12} className="text-muted-foreground/30 shrink-0" />
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
      
      <NodeDetailsPanel 
        traceId={selectedTraceId}
        isOpen={!!selectedTraceId}
        onOpenChange={(open) => !open && setSelectedTraceId(null)}
      />
    </div>
  );
}
