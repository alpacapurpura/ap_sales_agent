"use client";

import { Check, Copy } from "lucide-react";
import { useState } from "react";

import { cn } from "@/lib/utils";

import type { CodeBlock as CodeBlockType } from "../../types/message-blocks";

interface CodeBlockProps {
  block: CodeBlockType;
  className?: string;
}

/**
 * Code block with syntax highlighting (Tailwind-only, no Shiki installed),
 * language label, and copy button.
 *
 * [COPILOT-SHIKI-UPGRADE] — When shiki is added to package.json, replace
 * the <pre> render with Shiki's codeToHtml() and dangerouslySetInnerHTML.
 * Themes: github-light / github-dark per system preference.
 */
export function CodeBlock({ block, className }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    void navigator.clipboard.writeText(block.source).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div
      className={cn(
        "rounded-xl border border-border overflow-hidden bg-muted/60 max-w-full",
        className,
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between bg-muted px-3 py-1.5">
        <span className="text-xs font-mono text-muted-foreground">{block.language || "text"}</span>
        <button
          type="button"
          onClick={handleCopy}
          aria-label={copied ? "Copiado" : "Copiar código"}
          className="flex items-center gap-1 rounded px-2 py-0.5 text-xs text-muted-foreground transition-colors hover:bg-background hover:text-foreground"
        >
          {copied ? (
            <>
              <Check className="h-3 w-3 text-green-500" aria-hidden="true" />
              Copiado
            </>
          ) : (
            <>
              <Copy className="h-3 w-3" aria-hidden="true" />
              Copiar
            </>
          )}
        </button>
      </div>

      {/* Code body */}
      <div className="overflow-x-auto">
        <pre className="px-4 py-3 text-xs font-mono leading-relaxed text-foreground whitespace-pre">
          <code>{block.source}</code>
        </pre>
      </div>
    </div>
  );
}

CodeBlock.displayName = "CodeBlock";
