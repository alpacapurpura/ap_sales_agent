"use client";

import { ChatTimeline } from "@/components/audit/chat-timeline";
import { LeadList } from "@/components/audit/user-list";
import { useState } from "react";

export default function AuditPage() {
  const [selectedLeadId, setSelectedLeadId] = useState<string | null>(null);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);

  return (
    <div className="h-[calc(100vh-4rem)] flex gap-0">
      <div className="w-80 flex-none h-full overflow-hidden border-r">
        <LeadList selectedLeadId={selectedLeadId} onSelectLead={setSelectedLeadId} />
      </div>
      <div className="flex-1 min-w-0 h-full overflow-hidden">
        {selectedLeadId ? (
          <div className="h-full">
            <ChatTimeline 
              leadId={selectedLeadId} 
              onSelectEvent={(event) => setSelectedEventId(event.id)} 
              selectedEventId={selectedEventId} 
            />
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            Selecciona un lead para ver su historial
          </div>
        )}
      </div>
    </div>
  );
}
