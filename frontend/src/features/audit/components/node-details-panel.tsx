"use client";

import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useTraceDetails } from "@/features/audit/hooks/useAudit";
import { Loader2, Clock, Calendar, Brain, Zap, ChevronDown, ChevronRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { getNodeIcon, getNodeColor } from "./node-icons";
import { cn } from "@/lib/utils";
import { useState } from "react";

interface NodeDetailsPanelProps {
  traceId: string | null;
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
}

function StateKeyValue({ label, value }: { label: string; value: unknown }) {
  const [expanded, setExpanded] = useState(false);

  if (value === null || value === undefined) return null;

  const isObject = typeof value === "object";

  if (isObject) {
    return (
      <div className="border-b border-border/50 last:border-0">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1.5 w-full py-1.5 px-2 text-left hover:bg-muted/50 rounded text-xs"
        >
          {expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
          <span className="font-medium text-muted-foreground">{label}</span>
          <span className="text-[10px] text-muted-foreground/60 ml-auto">
            {Array.isArray(value) ? `[${value.length}]` : "{...}"}
          </span>
        </button>
        {expanded && (
          <pre className="text-[11px] bg-muted/30 p-2 mx-2 mb-1.5 rounded overflow-auto max-h-[200px] whitespace-pre-wrap break-all">
            {JSON.stringify(value, null, 2)}
          </pre>
        )}
      </div>
    );
  }

  return (
    <div className="flex items-center justify-between py-1.5 px-2 border-b border-border/50 last:border-0">
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      <span className="text-xs font-mono max-w-[60%] truncate text-right" title={String(value)}>
        {String(value)}
      </span>
    </div>
  );
}

function StateViewer({ title, state }: { title: string; state: Record<string, unknown> | null }) {
  if (!state || Object.keys(state).length === 0) {
    return (
      <div>
        <h3 className="text-sm font-medium mb-2">{title}</h3>
        <div className="text-xs text-muted-foreground italic p-3 bg-muted/30 rounded-lg">Sin datos</div>
      </div>
    );
  }

  return (
    <div>
      <h3 className="text-sm font-medium mb-2">{title}</h3>
      <div className="border rounded-lg bg-card divide-y divide-border/50">
        {Object.entries(state).map(([key, value]) => (
          <StateKeyValue key={key} label={key} value={value} />
        ))}
      </div>
    </div>
  );
}

/* eslint-disable react-hooks/static-components -- dynamic icon from registry */
function NodeIcon({ nodeName, className }: { nodeName?: string; className?: string }) {
  const Icon = nodeName ? getNodeIcon(nodeName) : Loader2;
  return <Icon className={className} />;
}
/* eslint-enable react-hooks/static-components */

export function NodeDetailsPanel({ traceId, isOpen, onOpenChange }: NodeDetailsPanelProps) {
  const { data: trace, isLoading } = useTraceDetails(traceId);
  const iconColor = trace ? getNodeColor(trace.node_name) : "text-slate-500";

  const totalTokens = trace?.llm_logs?.reduce(
    (sum, log) => sum + (log.tokens_input || 0) + (log.tokens_output || 0),
    0
  ) ?? 0;

  return (
    <Sheet open={isOpen} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[400px] sm:w-[540px] flex flex-col p-0 gap-0">
        <SheetHeader className="px-6 py-4 border-b">
          <SheetTitle className="flex items-center gap-2">
            {trace && <NodeIcon nodeName={trace.node_name} className={cn("h-5 w-5", iconColor)} />}
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
                    <div className="text-sm font-mono">{Number(trace.execution_time_ms || 0).toFixed(0)}ms</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                    <div className="text-sm">{new Date(trace.created_at).toLocaleTimeString()}</div>
                  </div>
                  {totalTokens > 0 && (
                    <div className="flex items-center gap-2 col-span-2">
                      <Zap className="h-3.5 w-3.5 text-amber-500" />
                      <div className="text-sm font-mono">{totalTokens} tokens totales</div>
                    </div>
                  )}
                </div>

                {/* LLM Logs if available */}
                {trace.llm_logs && trace.llm_logs.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
                      <Brain className="h-4 w-4 text-pink-500" />
                      LLM Calls ({trace.llm_logs.length})
                    </h3>
                    <div className="space-y-4">
                      {trace.llm_logs.map((log) => (
                        <div key={log.id} className="border rounded-lg p-3 bg-card space-y-3">
                           <div className="flex justify-between items-center text-xs text-muted-foreground">
                              <div className="flex items-center gap-2">
                                <span className="font-mono bg-muted px-1.5 py-0.5 rounded text-[10px]">{log.model}</span>
                                {log.prompt_template && log.prompt_template !== "unknown" && (
                                  <Badge variant="outline" className="text-[10px] h-5">
                                    {log.prompt_template}
                                  </Badge>
                                )}
                              </div>
                              <span className="font-mono">{log.tokens_input} &rarr; {log.tokens_output}</span>
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
                <StateViewer title="Input State" state={trace.input_state} />

                {/* Output State */}
                <StateViewer title="Output State" state={trace.output_state} />
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
