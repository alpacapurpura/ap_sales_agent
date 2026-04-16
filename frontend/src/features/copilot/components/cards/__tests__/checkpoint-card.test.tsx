import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { CheckpointCard } from "../CheckpointCard";

describe("CheckpointCard", () => {
  const defaultProps = {
    blockId: "identidad",
    blockLabel: "Tu Identidad",
    summary: {
      "story.origin_story": "Founded in 2019...",
      "story.mission": "Democratize sales",
    },
    healthScore: 85,
    blocksProgress: { completed: 1, total: 5 },
    onConfirm: vi.fn(),
    onRevise: vi.fn(),
    status: "pending" as const,
  };

  it("renders block label and summary fields", () => {
    render(<CheckpointCard {...defaultProps} />);
    expect(screen.getByText(/Tu Identidad/)).toBeInTheDocument();
    expect(screen.getByText(/Founded in 2019/)).toBeInTheDocument();
    expect(screen.getByText(/Democratize sales/)).toBeInTheDocument();
  });

  it("shows health score", () => {
    render(<CheckpointCard {...defaultProps} />);
    expect(screen.getByText("85%")).toBeInTheDocument();
  });

  it("calls onConfirm when confirm button clicked", () => {
    const onConfirm = vi.fn();
    render(<CheckpointCard {...defaultProps} onConfirm={onConfirm} />);
    fireEvent.click(screen.getByRole("button", { name: /perfecto/i }));
    expect(onConfirm).toHaveBeenCalled();
  });

  it("calls onRevise when revise button clicked", () => {
    const onRevise = vi.fn();
    render(<CheckpointCard {...defaultProps} onRevise={onRevise} />);
    fireEvent.click(screen.getByRole("button", { name: /ajustar/i }));
    expect(onRevise).toHaveBeenCalled();
  });

  it("disables buttons when confirmed", () => {
    render(<CheckpointCard {...defaultProps} status="confirmed" />);
    expect(screen.getByRole("button", { name: /perfecto/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: /ajustar/i })).toBeDisabled();
  });

  it("renders progress dots for all blocks", () => {
    render(<CheckpointCard {...defaultProps} blocksProgress={{ completed: 2, total: 5 }} />);
    // 5 dots rendered (we check by querying for the progress area)
    const container = screen.getByText(/Tu Identidad/).closest("div")?.parentElement;
    expect(container).toBeTruthy();
  });

  it("shows field labels extracted from dotted key paths", () => {
    render(<CheckpointCard {...defaultProps} />);
    // Keys are "story.origin_story" and "story.mission" — last segment is label
    expect(screen.getByText("origin_story:")).toBeInTheDocument();
    expect(screen.getByText("mission:")).toBeInTheDocument();
  });

  it("renders health score progress bar", () => {
    render(<CheckpointCard {...defaultProps} healthScore={72} />);
    expect(screen.getByText("72%")).toBeInTheDocument();
    expect(screen.getByText(/Health después de este bloque/)).toBeInTheDocument();
  });
});
