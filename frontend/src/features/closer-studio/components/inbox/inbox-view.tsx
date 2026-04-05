"use client";

import { useSearchParams } from "next/navigation";
import { useEffect } from "react";
import { useCloserStore } from "../../store/closer-store";
import { ConversationList } from "./conversation-list";
import { ConversationThread } from "./conversation-thread";
import { ContactSidebar } from "./contact-sidebar";

export function InboxView() {
  const searchParams = useSearchParams();
  const selectedLeadId = useCloserStore((s) => s.selectedLeadId);
  const setSelectedLeadId = useCloserStore((s) => s.setSelectedLeadId);
  const sidebarOpen = useCloserStore((s) => s.sidebarOpen);

  // Sync URL param → store
  useEffect(() => {
    const leadParam = searchParams?.get("lead");
    if (leadParam && leadParam !== selectedLeadId) {
      setSelectedLeadId(leadParam);
    }
  }, [searchParams, selectedLeadId, setSelectedLeadId]);

  return (
    <div className="flex h-full">
      {/* Left: Conversation List */}
      <div className="w-80 border-r shrink-0 overflow-hidden flex flex-col">
        <ConversationList />
      </div>

      {/* Center: Thread */}
      <div className="flex-1 min-w-0 overflow-hidden flex flex-col">
        {selectedLeadId ? (
          <ConversationThread leadId={selectedLeadId} />
        ) : (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            Selecciona una conversacion para ver el detalle
          </div>
        )}
      </div>

      {/* Right: Contact Sidebar */}
      {selectedLeadId && sidebarOpen && (
        <div className="w-72 border-l shrink-0 overflow-y-auto">
          <ContactSidebar leadId={selectedLeadId} />
        </div>
      )}
    </div>
  );
}
