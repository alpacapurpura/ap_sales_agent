"use client";

import { useState } from "react";
import { useAuditLeads } from "@/lib/api/audit";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";
import { es } from "date-fns/locale";

interface LeadListProps {
  selectedLeadId: string | null;
  onSelectLead: (leadId: string) => void;
}

export function LeadList({ selectedLeadId, onSelectLead }: LeadListProps) {
  const { data: leads, isLoading } = useAuditLeads();
  const [search, setSearch] = useState("");

  const filteredLeads = leads?.filter((item) =>
    (item.lead.full_name || "").toLowerCase().includes(search.toLowerCase()) ||
    (item.lead.telegram_id || "").includes(search) ||
    (item.lead.whatsapp_id || "").includes(search)
  );

  return (
    <Card className="h-full flex flex-col border-r rounded-none border-y-0 border-l-0">
      <CardHeader className="p-4 border-b">
        <CardTitle className="text-lg">Leads</CardTitle>
        <Input
          placeholder="Buscar Lead..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="mt-2"
        />
      </CardHeader>
      <ScrollArea className="flex-1">
        <div className="p-2 space-y-2">
          {isLoading && <div className="p-4 text-center text-muted-foreground">Cargando...</div>}
          {!isLoading && filteredLeads?.length === 0 && (
             <div className="p-4 text-center text-muted-foreground">No se encontraron leads</div>
          )}
          {filteredLeads?.map((item) => (
            <div
              key={item.lead.id}
              onClick={() => onSelectLead(item.lead.id)}
              className={cn(
                "p-3 rounded-lg cursor-pointer transition-colors flex items-center gap-3 hover:bg-muted",
                selectedLeadId === item.lead.id ? "bg-muted" : "bg-transparent"
              )}
            >
              <Avatar className="h-10 w-10">
                <AvatarFallback>{(item.lead.full_name || "??").substring(0, 2).toUpperCase()}</AvatarFallback>
              </Avatar>
              <div className="flex-1 overflow-hidden">
                <div className="font-medium truncate">{item.lead.full_name || "Sin Nombre"}</div>
                <div className="text-xs text-muted-foreground flex justify-between">
                  <span>
                    {item.lead.telegram_id ? "Telegram" : item.lead.whatsapp_id ? "WhatsApp" : "Web"}
                  </span>
                  <span>
                    {item.last_activity && formatDistanceToNow(new Date(item.last_activity), { addSuffix: true, locale: es })}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>
    </Card>
  );
}
