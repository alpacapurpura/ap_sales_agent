"use client";

import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useTraceDetails } from "@/lib/api/audit";
import { Loader2, Clock, Calendar } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { getNodeIcon, getNodeColor } from "./node-icons";
import { cn } from "@/lib/utils";

interface NodeDetailsPanelProps {
  traceId: string | null;
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
}

export function NodeDetailsPanel({ traceId, isOpen, onOpenChange }: NodeDetailsPanelProps) {
  const { data: trace, isLoading } = useTraceDetails(traceId);
  const Icon = trace ? getNodeIcon(trace.node_name) : Loader2;
  const iconColor = trace ? getNodeColor(trace.node_name) : "text-slate-500";

  return (
    <Sheet open={isOpen} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[400px] sm:w-[540px] flex flex-col p-0 gap-0">
        <SheetHeader className="px-6 py-4 border-b">
          <SheetTitle className="flex items-center gap-2">
            {trace && <Icon className={cn("h-5 w-5", iconColor)} />}
            Detalle del Nodo
          </SheetTitle>
          <SheetDescription>
            Información de ejecución del paso seleccionado
          </SheetDescription>
        </SheetHeader>

        <ScrollArea className="flex-1 h-full">
          <div className="p-6 space-y-6">
            {isLoading ? (
              <div className="flex justify-center p-8">
                <Loader2 className="animate-spin h-8 w-8 text-muted-foreground" />
              </div>
            ) : trace ? (
              <div className="space-y-6">
                {/* Header Info */}
                <div className="grid grid-cols-2 gap-4 bg-muted/30 p-4 rounded-lg border">
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">Nombre del Nodo</label>
                    <div className="text-sm font-semibold">{trace.node_name}</div>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-muted-foreground">ID Ejecución</label>
                    <div className="text-xs font-mono truncate" title={trace.id}>{trace.id}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="h-3.5 w-3.5 text-muted-foreground" />
                    <div className="text-sm font-mono">{trace.execution_time_ms.toFixed(0)}ms</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                    <div className="text-sm">{new Date(trace.created_at).toLocaleTimeString()}</div>
                  </div>
                </div>

                {/* LLM Logs if available */}
                {trace.llm_logs && trace.llm_logs.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
                      <Badge variant="secondary">LLM Generation</Badge>
                    </h3>
                    <div className="space-y-4">
                      {trace.llm_logs.map((log) => (
                        <div key={log.id} className="border rounded-lg p-3 bg-card space-y-3">
                           <div className="flex justify-between items-center text-xs text-muted-foreground">
                              <span>{log.model}</span>
                              <span>Tokens: {log.tokens_input} &rarr; {log.tokens_output}</span>
                           </div>
                           <div className="space-y-1">
                              <label className="text-[10px] uppercase font-bold text-muted-foreground">Prompt</label>
                              <pre className="text-xs bg-muted p-2 rounded whitespace-pre-wrap max-h-40 overflow-auto">
                                {log.prompt_rendered}
                              </pre>
                           </div>
                           <div className="space-y-1">
                              <label className="text-[10px] uppercase font-bold text-muted-foreground">Response</label>
                              <pre className="text-xs bg-muted p-2 rounded whitespace-pre-wrap max-h-40 overflow-auto border-l-2 border-green-500">
                                {log.response_text}
                              </pre>
                           </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Input State */}
                <div>
                  <h3 className="text-sm font-medium mb-2">Input State</h3>
                  <div className="bg-slate-950 text-slate-50 p-4 rounded-lg text-xs font-mono overflow-auto whitespace-pre-wrap break-all max-h-[300px]">
                    {JSON.stringify(trace.input_state || {}, null, 2)}
                  </div>
                </div>

                {/* Output State */}
                <div>
                  <h3 className="text-sm font-medium mb-2">Output State</h3>
                  <div className="bg-slate-950 text-slate-50 p-4 rounded-lg text-xs font-mono overflow-auto whitespace-pre-wrap break-all max-h-[300px]">
                    {JSON.stringify(trace.output_state || {}, null, 2)}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center text-muted-foreground py-10">
                No se encontró información para este nodo.
              </div>
            )}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
