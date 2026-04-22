// [COPILOT-CANONICAL-BLOCKS] → docs/domains/copilot/message-blocks.md
// Mirror of backend/src/modules/copilot/domain/message_blocks.py — same field names (snake_case).
// CONTRACT-MULTIMODAL §1.4 — TypeScript discriminated union.

export interface BlockBase {
  id: string; // UUID
}

export interface TextBlock extends BlockBase {
  type: "text";
  markdown: string;
}

export interface ImageBlock extends BlockBase {
  type: "image";
  asset_id: string;
  url: string;
  mime: string;
  width?: number;
  height?: number;
  alt?: string;
}

export interface AudioBlock extends BlockBase {
  type: "audio";
  asset_id: string;
  url: string;
  mime: string;
  duration_ms?: number;
  transcript: string;
  transcript_language?: string;
  waveform?: number[];
}

export interface VideoBlock extends BlockBase {
  type: "video";
  asset_id: string;
  url: string;
  mime: string;
  width?: number;
  height?: number;
  duration_ms?: number;
  poster_url?: string;
}

export interface DocumentBlock extends BlockBase {
  type: "document";
  asset_id: string;
  url: string;
  mime: string;
  filename: string;
  size_bytes: number;
  page_count?: number;
  preview_url?: string;
}

export interface TableBlock extends BlockBase {
  type: "table";
  caption?: string;
  columns: string[];
  rows: string[][];
}

export interface CodeBlock extends BlockBase {
  type: "code";
  language: string;
  source: string;
  filename?: string;
}

export interface CitationBlock extends BlockBase {
  type: "citation";
  source: string;
  snippet: string;
  url?: string;
  score?: number;
}

export interface QuoteReplyBlock extends BlockBase {
  type: "quote_reply";
  ref_message_id: string;
  preview: string;
  ref_author_role: "user" | "assistant";
}

export type CardKind =
  | "proposal"
  | "alternatives"
  | "clarify"
  | "checkpoint"
  | "interview_complete"
  | "metric_summary"
  | "comparison"
  | "checklist"
  | "multi_option"
  | "navigation";

export interface CardBlock extends BlockBase {
  type: "card";
  card_kind: CardKind;
  payload: Record<string, unknown>;
  status?: "pending" | "resolved" | "confirmed" | "revising";
}

export interface ToolResultBlock extends BlockBase {
  type: "tool_result";
  tool_name: string;
  arguments: Record<string, unknown>;
  result_preview: string;
  ok: boolean;
}

export type MessageBlock =
  | TextBlock
  | ImageBlock
  | AudioBlock
  | VideoBlock
  | DocumentBlock
  | TableBlock
  | CodeBlock
  | CitationBlock
  | QuoteReplyBlock
  | CardBlock
  | ToolResultBlock;

export type BlockType = MessageBlock["type"];

export type MessageStatus = "thinking" | "streaming" | "sent" | "error";
