import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { AssistantMessage } from "../components/messages/AssistantMessage";

import type { CopilotMessage } from "../store/copilot-store";

// Mock card components to verify they're rendered
vi.mock("../components/cards/AlternativesCard", () => ({
  AlternativesCard: (props: Record<string, unknown>) => (
    <div data-testid="alternatives-card" data-field-path={props.fieldPath}>
      Alternatives
    </div>
  ),
}));

vi.mock("../components/cards/ClarifyCard", () => ({
  ClarifyCard: () => <div data-testid="clarify-card">Clarify</div>,
}));

vi.mock("../components/cards/CheckpointCard", () => ({
  CheckpointCard: (props: Record<string, unknown>) => (
    <div data-testid="checkpoint-card" data-block-id={props.blockId}>
      Checkpoint
    </div>
  ),
}));

vi.mock("../components/cards/InterviewCompleteCard", () => ({
  InterviewCompleteCard: () => <div data-testid="interview-complete-card">Complete</div>,
}));

describe("AssistantMessage interview cards", () => {
  it("renders alternatives_card UIAction", () => {
    const msg: CopilotMessage = {
      id: "msg-1",
      role: "assistant",
      content: "Options:",
      timestamp: Date.now(),
      uiActions: [
        {
          type: "alternatives_card",
          field_path: "strategy.avatar",
          question: "Who is your target?",
          alternatives: [{ id: "1", title: "Opt A", description: "Desc A", recommended: true }],
          allow_custom: true,
          card_status: "pending",
        },
      ],
    };
    render(<AssistantMessage message={msg} />);
    expect(screen.getByTestId("alternatives-card")).toBeDefined();
  });

  it("renders checkpoint_card UIAction", () => {
    const msg: CopilotMessage = {
      id: "msg-2",
      role: "assistant",
      content: "Block done!",
      timestamp: Date.now(),
      uiActions: [
        {
          type: "checkpoint_card",
          block_id: "strategy",
          block_label: "Estrategia",
          summary: { name: "Test" },
          health_score: 90,
          blocks_progress: { completed: 1, total: 5 },
          card_status: "pending",
        },
      ],
    };
    render(<AssistantMessage message={msg} />);
    expect(screen.getByTestId("checkpoint-card")).toBeDefined();
  });

  it("renders interview_complete UIAction", () => {
    const msg: CopilotMessage = {
      id: "msg-3",
      role: "assistant",
      content: "Done!",
      timestamp: Date.now(),
      uiActions: [
        {
          type: "interview_complete",
          health_score: 95,
          redirect: "/brand-studio",
        },
      ],
    };
    render(<AssistantMessage message={msg} />);
    expect(screen.getByTestId("interview-complete-card")).toBeDefined();
  });

  it("does not render preview_update (silent action)", () => {
    const msg: CopilotMessage = {
      id: "msg-4",
      role: "assistant",
      content: "Noted.",
      timestamp: Date.now(),
      uiActions: [
        {
          type: "preview_update",
          delta: { name: "Test" },
        },
      ],
    };
    render(<AssistantMessage message={msg} />);
    expect(screen.queryByTestId("alternatives-card")).toBeNull();
    expect(screen.queryByTestId("checkpoint-card")).toBeNull();
    expect(screen.queryByTestId("interview-complete-card")).toBeNull();
  });
});
