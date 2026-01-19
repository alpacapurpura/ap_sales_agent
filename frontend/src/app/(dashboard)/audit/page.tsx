"use client";

import { useState } from "react";
import { UserList } from "@/components/audit/user-list";
import { ChatTimeline } from "@/components/audit/chat-timeline";
import { TraceInspector } from "@/components/audit/trace-inspector";
import { TimelineEvent } from "@/lib/api/audit";

export default function AuditPage() {
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<TimelineEvent | null>(null);

  return (
    <div className="h-[calc(100vh-4rem)] flex gap-4">
      {/* Sidebar: Users List */}
      <div className="w-80 border rounded-lg overflow-hidden bg-white dark:bg-slate-950 flex flex-col shrink-0">
        <div className="p-4 border-b bg-slate-50 dark:bg-slate-900">
          <h2 className="font-semibold">Usuarios</h2>
        </div>
        <UserList 
          selectedUserId={selectedUserId} 
          onSelectUser={setSelectedUserId} 
        />
      </div>

      {/* Main Content: Timeline */}
      <div className="flex-1 border rounded-lg overflow-hidden bg-white dark:bg-slate-950 relative">
        <ChatTimeline 
          userId={selectedUserId} 
          onSelectEvent={setSelectedEvent}
          selectedEventId={selectedEvent?.id || null}
        />
      </div>

      {/* Detail Inspector (Sheet) */}
      <TraceInspector 
        event={selectedEvent} 
        onClose={() => setSelectedEvent(null)} 
      />
    </div>
  );
}
