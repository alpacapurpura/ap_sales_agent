"use client";

import { cn } from "@/lib/utils";

import type { QuoteReplyBlock as QuoteReplyBlockType } from "../../types/message-blocks";

interface QuoteReplyBlockProps {
  block: QuoteReplyBlockType;
  className?: string;
}

const PREVIEW_MAX = 100;

/**
 * Quote-reply block: shows a truncated preview of the cited message
 * with border-l accent. Clicking scrolls to the original message.
 */
export function QuoteReplyBlock({ block, className }: QuoteReplyBlockProps) {
  const roleLabel = block.ref_author_role === "user" ? "Tú" : "Copilot";
  const preview =
    block.preview.length > PREVIEW_MAX
      ? `${block.preview.slice(0, PREVIEW_MAX)}...`
      : block.preview;

  const handleClick = () => {
    const el = document.getElementById(block.ref_message_id);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      aria-label={`Mensaje citado de ${roleLabel}`}
      className={cn(
        "block w-full text-left rounded-r-md border-l-2 border-muted-foreground/40 bg-muted/40 pl-3 pr-2 py-1.5",
        "hover:border-purple-400 hover:bg-muted/60 transition-colors",
        className,
      )}
    >
      <p className="text-[10px] font-medium text-muted-foreground">{roleLabel}</p>
      <p className="text-xs text-foreground leading-relaxed">&ldquo;{preview}&rdquo;</p>
    </button>
  );
}

QuoteReplyBlock.displayName = "QuoteReplyBlock";
