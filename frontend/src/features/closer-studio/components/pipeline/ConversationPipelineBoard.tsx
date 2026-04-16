"use client";

import { useAuth } from "@clerk/nextjs";
import {
  DndContext,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import { useMemo, useState, useCallback } from "react";

import { cn } from "@/lib/utils";

import { useConversations } from "../../hooks/use-conversations";
import { useCloserStore } from "../../store/closer-store";

import { PipelineCard } from "./PipelineCard";
import { PipelineColumn } from "./PipelineColumn";

import type { ConversationListItem } from "../../types";

const COLUMNS = [
  { id: "rapport", label: "Nuevo", color: "bg-slate-400" },
  { id: "discovery", label: "Calificando", color: "bg-blue-500" },
  { id: "presentation", label: "Negociando", color: "bg-violet-500" },
  { id: "closing", label: "Cerrando", color: "bg-amber-500" },
  { id: "won", label: "Ganado", color: "bg-green-500" },
  { id: "lost", label: "Perdido", color: "bg-red-500" },
];

export function ConversationPipelineBoard() {
  const { data } = useConversations();
  const setSelectedLeadId = useCloserStore((s) => s.setSelectedLeadId);
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 8 } }));

  const grouped = useMemo(() => {
    const map: Record<string, ConversationListItem[]> = {};
    for (const col of COLUMNS) map[col.id] = [];

    for (const conv of data?.conversations ?? []) {
      const stage = conv.funnel_stage || "rapport";
      // Map pipeline stages to column IDs
      const mapped = stage === "closing" && conv.pipeline_stage === "CUSTOMER" ? "won" : stage;
      if (map[mapped]) {
        map[mapped].push(conv);
      } else {
        map.rapport.push(conv);
      }
    }
    return map;
  }, [data]);

  const handleDragEnd = useCallback(async (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over) return;

    const leadId = active.id as string;
    const newStage = over.id as string;

    // Stage override via CRM pipeline endpoint
    // This would call PUT /api/v1/crm/pipeline/{profile_id}/stage
    // For now, we just invalidate
    console.log("Move", leadId, "to", newStage);
  }, []);

  return (
    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <div className="flex gap-3 p-4 h-full overflow-x-auto">
        {COLUMNS.map((col) => (
          <PipelineColumn
            key={col.id}
            id={col.id}
            label={col.label}
            color={col.color}
            count={grouped[col.id].length}
          >
            {grouped[col.id].map((conv) => (
              <PipelineCard
                key={conv.lead_id}
                conversation={conv}
                onClick={() => setSelectedLeadId(conv.lead_id)}
              />
            ))}
          </PipelineColumn>
        ))}
      </div>
    </DndContext>
  );
}
