"use client";

import { Copy, Reply, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import type { CopilotMessage } from "../../store/copilot-store";

// ── Types ────────────────────────────────────────────────────────────

interface MessageContextMenuProps {
  message: CopilotMessage;
  onReply: (message: CopilotMessage) => void;
  onDelete?: (message: CopilotMessage) => void;
}

// ── Helpers ──────────────────────────────────────────────────────────

function getMessageText(message: CopilotMessage): string {
  if (message.blocks) {
    return message.blocks
      .filter((b) => b.type === "text")
      .map((b) => (b.type === "text" ? b.markdown : ""))
      .join("\n");
  }
  return message.content;
}

// ── Component ────────────────────────────────────────────────────────

/**
 * Context menu for individual messages (reply, copy, delete).
 * Shown as a hover-triggered icon button that opens a DropdownMenu.
 */
export function MessageContextMenu({ message, onReply, onDelete }: MessageContextMenuProps) {
  const handleCopy = () => {
    const text = getMessageText(message);
    void navigator.clipboard.writeText(text);
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          aria-label="Opciones del mensaje"
          className="h-6 w-6 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-foreground"
        >
          <span className="sr-only">Opciones</span>
          <span aria-hidden="true" className="text-xs leading-none">
            •••
          </span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" side="top" className="w-36">
        <DropdownMenuItem
          onClick={() => onReply(message)}
          className="flex items-center gap-2 text-xs"
        >
          <Reply className="h-3.5 w-3.5" aria-hidden="true" />
          Responder
        </DropdownMenuItem>
        <DropdownMenuItem onClick={handleCopy} className="flex items-center gap-2 text-xs">
          <Copy className="h-3.5 w-3.5" aria-hidden="true" />
          Copiar
        </DropdownMenuItem>
        {onDelete && (
          <DropdownMenuItem
            onClick={() => onDelete(message)}
            className="flex items-center gap-2 text-xs text-destructive focus:text-destructive"
          >
            <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
            Eliminar
          </DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

MessageContextMenu.displayName = "MessageContextMenu";
