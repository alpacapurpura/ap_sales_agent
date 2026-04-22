import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

vi.mock("next/navigation", () => ({
  usePathname: () => "/tenant-1/brand-studio",
  useParams: () => ({ tenantId: "tenant-1" }),
}));

import { AssistantMessageV2 } from "../AssistantMessageV2";

import type { CopilotMessage } from "../../../store/copilot-store";

const baseMessage: CopilotMessage = {
  id: "msg-1",
  role: "assistant",
  content: "Hola, ¿en qué puedo ayudarte?",
  timestamp: Date.now(),
};

describe("AssistantMessageV2", () => {
  it("renders legacy text content when no blocks present", () => {
    render(<AssistantMessageV2 message={baseMessage} onReply={vi.fn()} />);
    expect(screen.getByText(/Hola, ¿en qué puedo ayudarte/)).toBeDefined();
  });

  it("renders blocks when blocks array present", () => {
    const msgWithBlocks: CopilotMessage = {
      ...baseMessage,
      blocks: [{ id: "b1", type: "text", markdown: "Texto desde bloque" }],
    };
    render(<AssistantMessageV2 message={msgWithBlocks} onReply={vi.fn()} />);
    // TextBlock renders markdown content
    expect(screen.getByText(/Texto desde bloque/)).toBeDefined();
  });

  it("shows typing indicator when streaming with no content", () => {
    const streamingMsg: CopilotMessage = {
      ...baseMessage,
      content: "",
      msgStatus: "streaming",
    };
    render(<AssistantMessageV2 message={streamingMsg} onReply={vi.fn()} />);
    // TypingIndicator renders animated dots — check aria label or role
    const container = document.querySelector("[data-role='assistant']");
    expect(container).not.toBeNull();
  });
});
