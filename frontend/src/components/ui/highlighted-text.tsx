import React from "react";
import { cn } from "@/lib/utils";

interface HighlightedTextProps {
  text: string;
  query: string;
  className?: string;
  highlightClassName?: string;
}

/**
 * Highlights matches of a query within a text string.
 * Case-insensitive.
 */
export function HighlightedText({
  text,
  query,
  className,
  highlightClassName = "bg-yellow-200 text-black rounded-[1px] px-0.5",
}: HighlightedTextProps) {
  if (!query || !text) {
    return <span className={className}>{text}</span>;
  }

  // Escape special regex characters in query
  const escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const parts = text.split(new RegExp(`(${escapedQuery})`, "gi"));

  return (
    <span className={className}>
      {parts.map((part, i) => {
        // Check if this part matches the query (case-insensitive)
        if (part.toLowerCase() === query.toLowerCase()) {
          return (
            <mark key={i} className={cn("font-medium", highlightClassName)}>
              {part}
            </mark>
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </span>
  );
}
