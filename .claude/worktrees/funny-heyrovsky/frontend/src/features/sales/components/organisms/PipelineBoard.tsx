import { Lead, LeadStatus } from "../../types";
import { LeadCard } from "../molecules/LeadCard";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";

interface PipelineBoardProps {
  leads: Lead[];
  onLeadClick?: (lead: Lead) => void;
  className?: string;
}

const STATUS_CONFIG: Record<LeadStatus, { label: string; color: string }> = {
  new: { label: "Nuevo", color: "bg-blue-500/10 border-blue-500/20" },
  contacted: { label: "Contactado", color: "bg-yellow-500/10 border-yellow-500/20" },
  qualified: { label: "Calificado", color: "bg-purple-500/10 border-purple-500/20" },
  proposal: { label: "Propuesta", color: "bg-orange-500/10 border-orange-500/20" },
  won: { label: "Ganado", color: "bg-green-500/10 border-green-500/20" },
  lost: { label: "Perdido", color: "bg-gray-500/10 border-gray-500/20" },
};

export function PipelineBoard({ leads, onLeadClick, className }: PipelineBoardProps) {
  const columns: LeadStatus[] = ['new', 'contacted', 'qualified', 'proposal', 'won', 'lost'];

  const getLeadsByStatus = (status: LeadStatus) => {
    return leads.filter((lead) => lead.status === status);
  };

  return (
    <div className={cn("h-full w-full flex flex-col bg-muted/5", className)}>
      <ScrollArea className="flex-1 w-full whitespace-nowrap rounded-md border">
        <div className="flex w-max space-x-4 p-4">
          {columns.map((status) => {
            const statusLeads = getLeadsByStatus(status);
            const config = STATUS_CONFIG[status];
            
            return (
              <div 
                key={status} 
                className={cn(
                  "w-[350px] shrink-0 rounded-lg border bg-card text-card-foreground shadow-sm flex flex-col max-h-[calc(100vh-200px)]",
                  config.color
                )}
              >
                <div className="p-4 font-semibold flex justify-between items-center border-b bg-muted/40 rounded-t-lg sticky top-0 z-10 backdrop-blur-sm">
                  <span className="capitalize text-sm">{config.label}</span>
                  <span className="bg-background/80 text-muted-foreground px-2 py-0.5 rounded-full text-xs border shadow-sm">
                    {statusLeads.length}
                  </span>
                </div>
                
                <div className="p-2 space-y-3 overflow-y-auto flex-1 custom-scrollbar">
                  {statusLeads.length === 0 ? (
                    <div className="h-24 flex items-center justify-center text-muted-foreground text-xs italic border-2 border-dashed rounded-md m-2">
                      Sin leads
                    </div>
                  ) : (
                    statusLeads.map((lead) => (
                      <div key={lead.id} onClick={() => onLeadClick?.(lead)}>
                        <LeadCard lead={lead} />
                      </div>
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
        <ScrollBar orientation="horizontal" />
      </ScrollArea>
    </div>
  );
}
