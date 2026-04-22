import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { BlockDispatcher } from "../BlockDispatcher";

import type { MessageBlock } from "../../../types/message-blocks";

// Mock react-markdown to keep test fast
vi.mock("react-markdown", () => ({
  default: ({ children }: { children: string }) => <div data-testid="markdown">{children}</div>,
}));
vi.mock("remark-gfm", () => ({ default: () => {} }));
vi.mock("rehype-sanitize", () => ({ default: () => {}, defaultSchema: {} }));

describe("BlockDispatcher", () => {
  it("renders TextBlock for text type", () => {
    const block: MessageBlock = { id: "1", type: "text", markdown: "Hola mundo" };
    render(<BlockDispatcher block={block} />);
    expect(screen.getByTestId("markdown")).toBeInTheDocument();
  });

  it("renders CodeBlock for code type", () => {
    const block: MessageBlock = {
      id: "2",
      type: "code",
      language: "python",
      source: "print('hola')",
    };
    render(<BlockDispatcher block={block} />);
    expect(screen.getByText("print('hola')")).toBeInTheDocument();
    expect(screen.getByText("python")).toBeInTheDocument();
  });

  it("renders DocumentBlock for document type", () => {
    const block: MessageBlock = {
      id: "3",
      type: "document",
      asset_id: "a1",
      url: "https://example.com/doc.pdf",
      mime: "application/pdf",
      filename: "brief.pdf",
      size_bytes: 2048,
    };
    render(<BlockDispatcher block={block} />);
    expect(screen.getByText("brief.pdf")).toBeInTheDocument();
    expect(screen.getByText("2 KB")).toBeInTheDocument();
  });

  it("renders CitationBlock for citation type", () => {
    const block: MessageBlock = {
      id: "4",
      type: "citation",
      source: "Brand Studio",
      snippet: "Los pilares de metodología...",
    };
    render(<BlockDispatcher block={block} />);
    expect(screen.getByText("Brand Studio")).toBeInTheDocument();
  });

  it("renders ToolResultBlock for tool_result type", () => {
    const block: MessageBlock = {
      id: "5",
      type: "tool_result",
      tool_name: "brand_health_check",
      arguments: {},
      result_preview: '{"score": 72}',
      ok: true,
    };
    render(<BlockDispatcher block={block} />);
    expect(screen.getByText("brand_health_check")).toBeInTheDocument();
  });

  it("renders QuoteReplyBlock for quote_reply type", () => {
    const block: MessageBlock = {
      id: "6",
      type: "quote_reply",
      ref_message_id: "msg-123",
      preview: "¿Cómo está mi funnel?",
      ref_author_role: "user",
    };
    render(<BlockDispatcher block={block} />);
    expect(screen.getByText("Tú")).toBeInTheDocument();
    expect(screen.getByText(/¿Cómo está mi funnel\?/)).toBeInTheDocument();
  });
});
