"use client";

import { cn } from "@/lib/utils";

export interface DragHandleProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /**
   * Reserved for @dnd-kit integration (Sprint siguiente).
   * Currently no-op — handle is purely visual.
   */
  dragHandleProps?: Record<string, unknown>;
}

/**
 * Visual drag handle (⋮⋮). Cursor grab, no-op until @dnd-kit is installed.
 * Props forwarded via dragHandleProps when the drag library is wired.
 */
export function ArrayDragHandle({ className, dragHandleProps: _drag, ...props }: DragHandleProps) {
  return (
    <button
      type="button"
      aria-label="Reordenar"
      className={cn(
        "cursor-grab touch-none select-none text-muted-foreground",
        "hover:text-foreground active:cursor-grabbing",
        "px-0.5 text-sm",
        className,
      )}
      {...props}
    >
      ⋮⋮
    </button>
  );
}

ArrayDragHandle.displayName = "ArrayDragHandle";
