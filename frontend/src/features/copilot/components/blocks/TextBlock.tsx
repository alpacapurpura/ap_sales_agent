"use client";

import ReactMarkdown from "react-markdown";
import rehypeSanitize, { defaultSchema } from "rehype-sanitize";
import remarkGfm from "remark-gfm";

import { cn } from "@/lib/utils";

import type { TextBlock as TextBlockType } from "../../types/message-blocks";

interface TextBlockProps {
  block: TextBlockType;
  isStreaming?: boolean;
  className?: string;
}

// Sanitize schema: allow code, pre, links with safe rels, tables, images
const sanitizeSchema = {
  ...defaultSchema,
  attributes: {
    ...defaultSchema.attributes,
    a: [["href", /^https?:/], ["rel"], ["target"]],
    code: ["className"],
    pre: ["className"],
    img: ["src", "alt", "width", "height"],
  },
};

/**
 * Renders a markdown text block with streaming cursor support.
 * Uses react-markdown + remark-gfm + rehype-sanitize.
 */
export function TextBlock({ block, isStreaming, className }: TextBlockProps) {
  return (
    <div role="region" aria-label="Mensaje del asistente" className={cn("text-sm", className)}>
      <div aria-live="polite" aria-atomic="false">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[[rehypeSanitize, sanitizeSchema]]}
          components={{
            // Links open in new tab safely
            a: ({ href, children, ...props }) => (
              <a
                href={href}
                rel="noopener noreferrer"
                target="_blank"
                className="text-purple-600 underline hover:text-purple-700 dark:text-purple-400"
                {...props}
              >
                {children}
              </a>
            ),
            // Code blocks inline
            code: ({ className: codeClass, children, ...props }) => {
              const isBlock = Boolean(codeClass);
              if (isBlock) {
                return (
                  <code
                    className={cn(
                      "block rounded bg-muted px-3 py-2 font-mono text-xs text-foreground overflow-x-auto",
                      codeClass,
                    )}
                    {...props}
                  >
                    {children}
                  </code>
                );
              }
              return (
                <code
                  className="rounded bg-muted px-1 py-0.5 font-mono text-xs text-foreground"
                  {...props}
                >
                  {children}
                </code>
              );
            },
            pre: ({ children, ...props }) => (
              <pre className="overflow-x-auto rounded-md bg-muted p-0" {...props}>
                {children}
              </pre>
            ),
            // Tables
            table: ({ children, ...props }) => (
              <div className="overflow-x-auto">
                <table className="w-full border-collapse text-xs" {...props}>
                  {children}
                </table>
              </div>
            ),
            th: ({ children, ...props }) => (
              <th
                className="border border-border bg-muted px-2 py-1 text-left font-medium"
                {...props}
              >
                {children}
              </th>
            ),
            td: ({ children, ...props }) => (
              <td className="border border-border px-2 py-1" {...props}>
                {children}
              </td>
            ),
            // Lists
            ul: ({ children, ...props }) => (
              <ul className="list-disc pl-4 space-y-0.5" {...props}>
                {children}
              </ul>
            ),
            ol: ({ children, ...props }) => (
              <ol className="list-decimal pl-4 space-y-0.5" {...props}>
                {children}
              </ol>
            ),
            // Headings
            h1: ({ children, ...props }) => (
              <h1 className="text-base font-semibold mt-2 mb-1" {...props}>
                {children}
              </h1>
            ),
            h2: ({ children, ...props }) => (
              <h2 className="text-sm font-semibold mt-2 mb-1" {...props}>
                {children}
              </h2>
            ),
            h3: ({ children, ...props }) => (
              <h3 className="text-sm font-medium mt-1.5 mb-0.5" {...props}>
                {children}
              </h3>
            ),
            p: ({ children, ...props }) => (
              <p className="mb-1.5 last:mb-0 leading-relaxed" {...props}>
                {children}
              </p>
            ),
            blockquote: ({ children, ...props }) => (
              <blockquote
                className="border-l-2 border-muted-foreground/40 pl-3 italic text-muted-foreground"
                {...props}
              >
                {children}
              </blockquote>
            ),
          }}
        >
          {block.markdown}
        </ReactMarkdown>
        {isStreaming && (
          <span
            className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-purple-500"
            aria-hidden="true"
          />
        )}
      </div>
    </div>
  );
}

TextBlock.displayName = "TextBlock";
