"use client";

import { useState } from "react";
import { useAuditLeads } from "@/features/audit/hooks/useAudit";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";
import { es } from "date-fns/locale";
import { PanelLeftClose, PanelLeftOpen } from "lucide-react";

interface LeadListProps {
  selectedLeadId: string | null;
  onSelectLead: (leadId: string) => void;
  isCollapsed?: boolean;
  onToggle?: () => void;
}

export function LeadList({
  selectedLeadId,
  onSelectLead,
  isCollapsed = false,
  onToggle,
}: LeadListProps) {
  const { data: leads, isLoading } = useAuditLeads();
  const [search, setSearch] = useState("");

  const filteredLeads = leads?.filter((item) =>
    (item.lead.full_name || "")
      .toLowerCase()
      .includes(search.toLowerCase()) ||
    (item.lead.telegram_id || "").includes(search) ||
    (item.lead.whatsapp_id || "").includes(search)
  );

  return (
    <Card className="h-full flex flex-col border-r rounded-none border-y-0 border-l-0 transition-all duration-300">
      <CardHeader className={cn("p-4 border-b", isCollapsed && "p-2")}>
        <div className={cn("flex items-center", isCollapsed ? "justify-center" : "justify-between")}>
          {!isCollapsed && <CardTitle className="text-lg">Leads</CardTitle>}
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggle}
            className={cn("h-8 w-8", isCollapsed && "h-10 w-10")}
          >
            {isCollapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
          </Button>
        </div>
        {!isCollapsed && (
          <Input
            placeholder="Buscar Lead..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="mt-2"
          />
        )}
      </CardHeader>
      <ScrollArea className="flex-1">
        <div className="p-2 space-y-2">
          {isLoading && (
            <div className="p-4 text-center text-muted-foreground">
              {isCollapsed ? "..." : "Cargando..."}
            </div>
          )}
          {!isLoading && filteredLeads?.length === 0 && (
            <div className="p-4 text-center text-muted-foreground">
              {isCollapsed ? "-" : "No se encontraron leads"}
            </div>
          )}
          {filteredLeads?.map((item) => {
            const leadName = item.lead.full_name || "Sin Nombre";
            const initials = (leadName || "??").substring(0, 2).toUpperCase();

            const Content = (
              <div
                onClick={() => onSelectLead(item.lead.id)}
                className={cn(
                  "rounded-lg cursor-pointer transition-colors flex items-center hover:bg-muted",
                  isCollapsed ? "justify-center p-2" : "p-3 gap-3",
                  selectedLeadId === item.lead.id ? "bg-muted" : "bg-transparent"
                )}
              >
                <Avatar className="h-10 w-10">
                  <AvatarFallback>{initials}</AvatarFallback>
                </Avatar>
                {!isCollapsed && (
                  <div className="flex-1 overflow-hidden">
                    <div className="font-medium truncate">{leadName}</div>
                    <div className="text-xs text-muted-foreground flex justify-between">
                      <span>
                        {item.lead.telegram_id
                          ? "Telegram"
                          : item.lead.whatsapp_id
                          ? "WhatsApp"
                          : "Web"}
                      </span>
                      <span>
                        {item.last_activity &&
                          formatDistanceToNow(new Date(item.last_activity), {
                            addSuffix: true,
                            locale: es,
                          })}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            );

            if (isCollapsed) {
              return (
                <TooltipProvider key={item.lead.id}>
                  <Tooltip delayDuration={0}>
                    <TooltipTrigger asChild>
                      {Content}
                    </TooltipTrigger>
                    <TooltipContent side="right">
                      <p className="font-medium">{leadName}</p>
                      <p className="text-xs text-muted-foreground">
                        {item.lead.telegram_id
                          ? "Telegram"
                          : item.lead.whatsapp_id
                          ? "WhatsApp"
                          : "Web"}
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              );
            }

            return <div key={item.lead.id}>{Content}</div>;
          })}
        </div>
      </ScrollArea>
    </Card>
  );
}
