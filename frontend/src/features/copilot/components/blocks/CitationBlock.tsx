"use client";

import { ExternalLink } from "lucide-react";
import { useState } from "react";

import { cn } from "@/lib/utils";

import type { CitationBlock as CitationBlockType } from "../../types/message-blocks";

interface CitationBlockProps {
  block: CitationBlockType;
  index?: number;
  className?: string;
}

const SNIPPET_MAX = 120;

/**
 * RAG citation block shown below assistant text.
 * Collapsible snippet, optional source link.
 */
export function CitationBlock({ block, index, className }: CitationBlockProps) {
  const [expanded, setExpanded] = useState(false);

  const isLong = block.snippet.length > SNIPPET_MAX;
  const displayed =
    expanded || !isLong ? block.snippet : `${block.snippet.slice(0, SNIPPET_MAX)}...`;

  return (
    <aside
      aria-label={`Fuente ${index !== undefined ? `[${index}]` : ""}`}
      className={cn(
        "rounded-md border border-border bg-muted/40 px-3 py-2 text-xs space-y-1",
        className,
      )}
    >
      {/* Source header */}
      <div className="flex items-center gap-1.5 font-medium text-foreground">
        {index !== undefined && (
          <span className="text-purple-600 dark:text-purple-400">[{index}]</span>
        )}
        {block.url ? (
          <a
            href={block.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 hover:text-purple-600 dark:hover:text-purple-400"
          >
            {block.source}
            <ExternalLink className="h-2.5 w-2.5" aria-hidden="true" />
          </a>
        ) : (
          <span>{block.source}</span>
        )}
      </div>

      {/* Snippet */}
      <p className="leading-relaxed text-muted-foreground">
        &ldquo;{displayed}&rdquo;
        {isLong && (
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            className="ml-1.5 text-purple-600 underline hover:no-underline dark:text-purple-400"
          >
            {expanded ? "Ver menos" : "Ver más"}
          </button>
        )}
      </p>
    </aside>
  );
}

CitationBlock.displayName = "CitationBlock";
