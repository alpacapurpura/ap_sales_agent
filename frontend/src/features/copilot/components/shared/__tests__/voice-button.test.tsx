import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { VoiceButton, RecordingIndicator, TranscribingIndicator } from "../VoiceButton";

describe("VoiceButton", () => {
  it("renders mic button with correct idle aria-label", () => {
    render(<VoiceButton isRecording={false} isTranscribing={false} onMicClick={vi.fn()} />);
    expect(screen.getByRole("button", { name: "Micrófono" })).toBeInTheDocument();
  });

  it("renders mic button with recording aria-label when recording", () => {
    render(<VoiceButton isRecording={true} isTranscribing={false} onMicClick={vi.fn()} />);
    expect(screen.getByRole("button", { name: "Detener grabación" })).toBeInTheDocument();
  });

  it("calls onMicClick when button is clicked", async () => {
    const onMicClick = vi.fn().mockResolvedValue(undefined);
    render(<VoiceButton isRecording={false} isTranscribing={false} onMicClick={onMicClick} />);
    fireEvent.click(screen.getByRole("button", { name: "Micrófono" }));
    expect(onMicClick).toHaveBeenCalledTimes(1);
  });

  it("is disabled when isTranscribing is true", () => {
    render(<VoiceButton isRecording={false} isTranscribing={true} onMicClick={vi.fn()} />);
    expect(screen.getByRole("button", { name: "Micrófono" })).toBeDisabled();
  });

  it("is disabled when disabled prop is true", () => {
    render(
      <VoiceButton
        isRecording={false}
        isTranscribing={false}
        disabled={true}
        onMicClick={vi.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: "Micrófono" })).toBeDisabled();
  });
});

describe("RecordingIndicator", () => {
  it("displays formatted duration", () => {
    render(
      <RecordingIndicator
        duration={65}
        onCancel={vi.fn()}
        onStop={vi.fn().mockResolvedValue(undefined)}
      />,
    );
    expect(screen.getByText("01:05")).toBeInTheDocument();
  });

  it("shows Grabando... label", () => {
    render(
      <RecordingIndicator
        duration={0}
        onCancel={vi.fn()}
        onStop={vi.fn().mockResolvedValue(undefined)}
      />,
    );
    expect(screen.getByText("Grabando...")).toBeInTheDocument();
  });

  it("calls onCancel when cancel button clicked", () => {
    const onCancel = vi.fn();
    render(
      <RecordingIndicator
        duration={10}
        onCancel={onCancel}
        onStop={vi.fn().mockResolvedValue(undefined)}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Cancelar grabación" }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it("calls onStop when stop button clicked", () => {
    const onStop = vi.fn().mockResolvedValue(undefined);
    render(<RecordingIndicator duration={10} onCancel={vi.fn()} onStop={onStop} />);
    fireEvent.click(screen.getByRole("button", { name: "Detener grabación" }));
    expect(onStop).toHaveBeenCalledTimes(1);
  });
});

describe("TranscribingIndicator", () => {
  it("renders transcribing message", () => {
    render(<TranscribingIndicator />);
    expect(screen.getByText("Transcribiendo...")).toBeInTheDocument();
  });
});
