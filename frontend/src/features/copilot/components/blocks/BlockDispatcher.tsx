"use client";

// [COPILOT-BLOCK-REGISTRY] — docs/domains/copilot/UI-SPEC.md §6
// Single switch dispatching each MessageBlock type to its renderer.
// To add a new block type:
//   1. Add entry to the MessageBlock union in types/message-blocks.ts
//   2. Create new renderer component in components/blocks/
//   3. Add case below

import { AudioBlock } from "./AudioBlock";
import { CardBlock } from "./CardBlock";
import { CitationBlock } from "./CitationBlock";
import { CodeBlock } from "./CodeBlock";
import { DocumentBlock } from "./DocumentBlock";
import { ImageBlock } from "./ImageBlock";
import { QuoteReplyBlock } from "./QuoteReplyBlock";
import { TableBlock } from "./TableBlock";
import { TextBlock } from "./TextBlock";
import { ToolResultBlock } from "./ToolResultBlock";
import { VideoBlock } from "./VideoBlock";

import type { MessageBlock } from "../../types/message-blocks";

interface BlockDispatcherProps {
  block: MessageBlock;
  /** Pass-through for interactive card blocks */
  sendCardAction?: (messageId: string, actionIndex: number, text: string) => void;
  messageId?: string;
  actionIndex?: number;
  /** Forwarded to TextBlock — true while SSE stream is active */
  isStreaming?: boolean;
}

/**
 * Dispatches a `MessageBlock` to the correct renderer component.
 * This is the single registration point for all block types.
 */
export function BlockDispatcher({
  block,
  sendCardAction,
  messageId,
  actionIndex,
  isStreaming,
}: BlockDispatcherProps) {
  switch (block.type) {
    case "text":
      return <TextBlock block={block} isStreaming={isStreaming} />;

    case "image":
      return <ImageBlock block={block} />;

    case "audio":
      return <AudioBlock block={block} />;

    case "video":
      return <VideoBlock block={block} />;

    case "document":
      return <DocumentBlock block={block} />;

    case "table":
      return <TableBlock block={block} />;

    case "code":
      return <CodeBlock block={block} />;

    case "citation":
      return <CitationBlock block={block} />;

    case "quote_reply":
      return <QuoteReplyBlock block={block} />;

    case "card":
      return (
        <CardBlock
          block={block}
          sendCardAction={sendCardAction}
          messageId={messageId}
          actionIndex={actionIndex}
        />
      );

    case "tool_result":
      return <ToolResultBlock block={block} />;

    default: {
      // Exhaustive check — TypeScript will error if a new type is added without handling
      const _exhaustive: never = block;
      void _exhaustive;
      return null;
    }
  }
}

BlockDispatcher.displayName = "BlockDispatcher";
