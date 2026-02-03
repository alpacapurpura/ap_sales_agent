"use client";

import { TimelineEvent, useTraceDetails } from "@/lib/api/audit";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { format } from "date-fns";
import { Loader2 } from "lucide-react";

interface TraceInspectorProps {
  event: TimelineEvent | null;
  onClose: () => void;
}

export function TraceInspector({ event, onClose }: TraceInspectorProps) {
  const isOpen = !!event;

  return (
    <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <SheetContent className="w-[800px] sm:w-[600px] overflow-hidden flex flex-col p-0 gap-0" side="right">
        <SheetHeader className="p-6 border-b">
          <SheetTitle className="flex items-center gap-2">
            {event?.type === "message" ? "Detalle de Mensaje" : "Traza de Ejecución"}
            {event?.type === "trace" && <Badge>{event.node_name}</Badge>}
          </SheetTitle>
          <SheetDescription>
            ID: {event?.id} • {event && format(new Date(event.created_at), "yyyy-MM-dd HH:mm:ss")}
          </SheetDescription>
        </SheetHeader>
        
        <ScrollArea className="flex-1 p-6">
          {event?.type === "message" ? (
             <MessageDetails event={event} />
          ) : (
             event && <TraceDetails event={event} />
          )}
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}

function MessageDetails({ event }: { event: TimelineEvent }) {
  return (
    <div className="space-y-4">
      <div className="grid gap-1">
        <span className="text-sm font-medium text-muted-foreground">Contenido</span>
        <div className="p-3 bg-muted rounded-md text-sm whitespace-pre-wrap">
          {event.content}
        </div>
      </div>
      <div className="grid gap-1">
        <span className="text-sm font-medium text-muted-foreground">Raw JSON</span>
        <pre className="p-3 bg-zinc-950 text-zinc-50 rounded-md text-xs overflow-auto">
          {JSON.stringify(event, null, 2)}
        </pre>
      </div>
    </div>
  );
}

function TraceDetails({ event }: { event: TimelineEvent }) {
  const { data: detail, isLoading } = useTraceDetails(event.id);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-10">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!detail) return <div>No details found</div>;

  return (
    <Tabs defaultValue="state" className="w-full">
      <TabsList className="w-full">
        <TabsTrigger value="state" className="flex-1">Estado</TabsTrigger>
        <TabsTrigger value="llm" className="flex-1">LLM Logs ({detail.llm_logs?.length || 0})</TabsTrigger>
      </TabsList>
      
      <TabsContent value="state" className="mt-4 space-y-4">
         <div className="space-y-2">
           <h4 className="text-sm font-medium">Input State</h4>
           <pre className="p-3 bg-muted rounded-md text-xs overflow-auto max-h-[400px]">
             {JSON.stringify(detail.input_state, null, 2)}
           </pre>
         </div>
         <div className="space-y-2">
           <h4 className="text-sm font-medium">Output State</h4>
           <pre className="p-3 bg-muted rounded-md text-xs overflow-auto max-h-[400px]">
             {JSON.stringify(detail.output_state, null, 2)}
           </pre>
         </div>
      </TabsContent>
      
      <TabsContent value="llm" className="mt-4">
        {detail.llm_logs?.length === 0 ? (
          <div className="text-center text-muted-foreground py-8">No LLM calls recorded</div>
        ) : (
          <Accordion type="single" collapsible className="w-full">
            {detail.llm_logs.map((log) => (
              <AccordionItem key={log.id} value={log.id}>
                <AccordionTrigger className="text-sm">
                  {log.model} - {log.prompt_template || "Raw Prompt"} ({log.tokens_input + log.tokens_output} tokens)
                </AccordionTrigger>
                <AccordionContent className="space-y-4 pt-2">
                   <div className="space-y-1">
                     <span className="text-xs font-semibold text-muted-foreground">Prompt Rendered</span>
                     <pre className="p-2 bg-zinc-950 text-zinc-50 rounded text-[10px] whitespace-pre-wrap max-h-[300px] overflow-auto">
                       {log.prompt_rendered}
                     </pre>
                   </div>
                   <div className="space-y-1">
                     <span className="text-xs font-semibold text-muted-foreground">Response</span>
                     <pre className="p-2 bg-zinc-950 text-zinc-50 rounded text-[10px] whitespace-pre-wrap max-h-[300px] overflow-auto">
                       {log.response_text}
                     </pre>
                   </div>
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        )}
      </TabsContent>
    </Tabs>
  );
}
