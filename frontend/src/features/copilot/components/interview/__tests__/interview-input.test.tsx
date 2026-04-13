import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

// ── Mocks ──────────────────────────────────────────────────────────────────

const mockStartRecording = vi.fn();
const mockStopRecording = vi.fn().mockResolvedValue("transcribed text");
const mockCancelRecording = vi.fn();

vi.mock("@/features/copilot/hooks/useVoiceRecorder", () => ({
  useVoiceRecorder: () => ({
    isRecording: false,
    isTranscribing: false,
    startRecording: mockStartRecording,
    stopRecording: mockStopRecording,
    cancelRecording: mockCancelRecording,
    error: null,
    duration: 0,
  }),
}));

vi.mock("@/features/copilot/components/shared/attachment-button", () => ({
  AttachmentButton: ({
    onFilesSelected,
    disabled,
  }: {
    onFilesSelected: (files: File[]) => void;
    disabled?: boolean;
  }) => (
    <button
      type="button"
      aria-label="Adjuntar documento"
      disabled={disabled}
      onClick={() =>
        onFilesSelected([
          new File(["content"], "test.pdf", { type: "application/pdf" }),
        ])
      }
    >
      Attach
    </button>
  ),
}));

vi.mock("@/features/copilot/components/shared/document-chip", () => ({
  DocumentChip: ({
    file,
    onRemove,
  }: {
    file: File;
    status: string;
    onRemove?: () => void;
  }) => (
    <div data-testid="document-chip">
      <span>{file.name}</span>
      {onRemove && (
        <button type="button" onClick={onRemove} aria-label="Eliminar documento">
          X
        </button>
      )}
    </div>
  ),
}));

import { InterviewInput } from "../interview-input";

describe("InterviewInput", () => {
  const onSend = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ── Text input ──────────────────────────────────────────────────────────

  it("renders text input with correct aria-label", () => {
    render(<InterviewInput onSend={onSend} />);
    expect(screen.getByLabelText("Mensaje")).toBeInTheDocument();
  });

  it("sends text on Enter key", () => {
    render(<InterviewInput onSend={onSend} />);
    const input = screen.getByLabelText("Mensaje");
    fireEvent.change(input, { target: { value: "Hola mundo" } });
    fireEvent.keyDown(input, { key: "Enter", shiftKey: false });
    expect(onSend).toHaveBeenCalledWith("Hola mundo");
  });

  it("does not send empty text", () => {
    render(<InterviewInput onSend={onSend} />);
    const sendButton = screen.getByRole("button", { name: "Enviar" });
    fireEvent.click(sendButton);
    expect(onSend).not.toHaveBeenCalled();
  });

  it("clears input after sending", () => {
    render(<InterviewInput onSend={onSend} />);
    const input = screen.getByLabelText("Mensaje") as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "test" } });
    fireEvent.keyDown(input, { key: "Enter", shiftKey: false });
    expect(input.value).toBe("");
  });

  // ── Mic button ──────────────────────────────────────────────────────────

  it("renders mic button with correct aria-label", () => {
    render(<InterviewInput onSend={onSend} />);
    const micButton = screen.getByRole("button", { name: /micr.fono/i });
    expect(micButton).toBeInTheDocument();
    expect(micButton).not.toBeDisabled();
  });

  it("calls startRecording when mic button is clicked", () => {
    render(<InterviewInput onSend={onSend} />);
    const micButton = screen.getByRole("button", { name: /micr.fono/i });
    fireEvent.click(micButton);
    expect(mockStartRecording).toHaveBeenCalled();
  });

  // ── Attachment button ───────────────────────────────────────────────────

  it("renders attachment button", () => {
    render(<InterviewInput onSend={onSend} />);
    expect(
      screen.getByRole("button", { name: "Adjuntar documento" })
    ).toBeInTheDocument();
  });

  it("shows document chips when files are attached", () => {
    render(<InterviewInput onSend={onSend} />);
    const attachButton = screen.getByRole("button", {
      name: "Adjuntar documento",
    });
    fireEvent.click(attachButton);
    expect(screen.getByTestId("document-chip")).toBeInTheDocument();
  });

  it("removes document chip when remove is clicked", () => {
    render(<InterviewInput onSend={onSend} />);
    const attachButton = screen.getByRole("button", {
      name: "Adjuntar documento",
    });
    fireEvent.click(attachButton);
    expect(screen.getByTestId("document-chip")).toBeInTheDocument();

    const removeButton = screen.getByRole("button", {
      name: "Eliminar documento",
    });
    fireEvent.click(removeButton);
    expect(screen.queryByTestId("document-chip")).not.toBeInTheDocument();
  });

  // ── Disabled state ──────────────────────────────────────────────────────

  it("disables all interactive elements when disabled prop is true", () => {
    render(<InterviewInput onSend={onSend} disabled />);

    expect(screen.getByLabelText("Mensaje")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();
    expect(screen.getByRole("button", { name: /micr.fono/i })).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Adjuntar documento" })
    ).toBeDisabled();
  });

  // ── Send with attachments ───────────────────────────────────────────────

  it("calls onFilesAttached and onSend when sending with files", () => {
    const onFilesAttached = vi.fn();
    render(
      <InterviewInput
        onSend={onSend}
        onFilesAttached={onFilesAttached}
      />
    );

    // Attach a file
    const attachButton = screen.getByRole("button", {
      name: "Adjuntar documento",
    });
    fireEvent.click(attachButton);

    // Type text and send
    const input = screen.getByLabelText("Mensaje");
    fireEvent.change(input, { target: { value: "Analiza esto" } });
    const sendButton = screen.getByRole("button", { name: "Enviar" });
    fireEvent.click(sendButton);

    expect(onFilesAttached).toHaveBeenCalledWith([
      expect.objectContaining({ name: "test.pdf" }),
    ]);
    expect(onSend).toHaveBeenCalledWith("Analiza esto");
  });

  it("clears attached files after sending", () => {
    render(<InterviewInput onSend={onSend} />);

    // Attach a file
    fireEvent.click(
      screen.getByRole("button", { name: "Adjuntar documento" })
    );
    expect(screen.getByTestId("document-chip")).toBeInTheDocument();

    // Type and send
    const input = screen.getByLabelText("Mensaje");
    fireEvent.change(input, { target: { value: "send" } });
    fireEvent.click(screen.getByRole("button", { name: "Enviar" }));

    // Files should be cleared
    expect(screen.queryByTestId("document-chip")).not.toBeInTheDocument();
  });

  // ── Send button enabled with files even without text ────────────────────

  it("enables send button when files are attached even without text", () => {
    render(<InterviewInput onSend={onSend} />);
    fireEvent.click(
      screen.getByRole("button", { name: "Adjuntar documento" })
    );
    const sendButton = screen.getByRole("button", { name: "Enviar" });
    expect(sendButton).not.toBeDisabled();
  });
});
