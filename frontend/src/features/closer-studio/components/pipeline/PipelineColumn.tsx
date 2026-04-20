"use client";

import { useDroppable } from "@dnd-kit/core";

import { cn } from "@/lib/utils";

interface PipelineColumnProps {
  id: string;
  label: string;
  color: string;
  count: number;
  children: React.ReactNode;
}

/**
 *
 */
export function PipelineColumn({ id, label, color, count, children }: PipelineColumnProps) {
  const { isOver, setNodeRef } = useDroppable({ id });

  return (
    <div
      ref={setNodeRef}
      className={cn(
        "flex flex-col w-64 shrink-0 rounded-lg bg-muted/30 border",
        isOver && "ring-2 ring-primary/50 bg-primary/5",
      )}
    >
      {/* Header */}
      <div className="flex items-center gap-2 px-3 py-2.5 border-b">
        <div className={cn("w-2.5 h-2.5 rounded-full", color)} />
        <span className="text-sm font-semibold">{label}</span>
        <span className="ml-auto text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded-full">
          {count}
        </span>
      </div>

      {/* Cards */}
      <div className="flex-1 overflow-y-auto p-2 space-y-2">{children}</div>
    </div>
  );
}
