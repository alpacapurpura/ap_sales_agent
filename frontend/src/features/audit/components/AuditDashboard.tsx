"use client";

import { useState } from "react";

import { ChatTimeline } from "@/features/audit/components/ChatTimeline";
import { LeadList } from "@/features/audit/components/UserList";
import { cn } from "@/lib/utils";

export function AuditDashboard() {
  const [selectedLeadId, setSelectedLeadId] = useState<string | null>(null);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <div className="h-[calc(100vh-4rem)] flex gap-0">
      <div
        className={cn(
          "flex-none h-full overflow-hidden border-r transition-all duration-300 ease-in-out",
          isCollapsed ? "w-20" : "w-80",
        )}
      >
        <LeadList
          selectedLeadId={selectedLeadId}
          onSelectLead={setSelectedLeadId}
          isCollapsed={isCollapsed}
          onToggle={() => setIsCollapsed(!isCollapsed)}
        />
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
