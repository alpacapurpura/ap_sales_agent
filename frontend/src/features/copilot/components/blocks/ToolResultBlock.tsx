"use client";

import { AlertCircle, Wrench } from "lucide-react";
import { useState } from "react";

import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { cn } from "@/lib/utils";

import type { ToolResultBlock as ToolResultBlockType } from "../../types/message-blocks";

interface ToolResultBlockProps {
  block: ToolResultBlockType;
  className?: string;
}

function formatPayload(result: string): string {
  try {
    return JSON.stringify(JSON.parse(result), null, 2);
  } catch {
    return result;
  }
}

/**
 * Collapsible tool result block.
 * Error state: red border + alert icon.
 */
export function ToolResultBlock({ block, className }: ToolResultBlockProps) {
  const [open, setOpen] = useState(false);

  return (
    <Collapsible
      open={open}
      onOpenChange={setOpen}
      className={cn(
        "rounded-lg border text-xs",
        block.ok ? "border-border bg-muted/40" : "border-destructive/40 bg-destructive/5",
        className,
      )}
      aria-label={`Resultado de herramienta: ${block.tool_name}`}
    >
      <CollapsibleTrigger asChild>
        <button
          type="button"
          className="flex w-full items-center gap-2 px-3 py-2 text-left hover:bg-muted/60 transition-colors rounded-lg"
        >
          {block.ok ? (
            <Wrench className="h-3.5 w-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
          ) : (
            <AlertCircle className="h-3.5 w-3.5 shrink-0 text-destructive" aria-hidden="true" />
          )}
          <span
            className={cn(
              "font-mono font-medium",
              block.ok ? "text-foreground" : "text-destructive",
            )}
          >
            {block.tool_name}
          </span>
          <span className="ml-auto text-muted-foreground">{open ? "▲" : "▼"}</span>
        </button>
      </CollapsibleTrigger>

      <CollapsibleContent>
        <pre className="overflow-x-auto border-t border-border px-3 py-2 font-mono text-[11px] leading-relaxed text-foreground whitespace-pre-wrap">
          {formatPayload(block.result_preview)}
        </pre>
      </CollapsibleContent>
    </Collapsible>
  );
}

ToolResultBlock.displayName = "ToolResultBlock";
