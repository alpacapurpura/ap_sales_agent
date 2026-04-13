import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CopilotInput } from "../components/copilot-input";

// Mock the voice recorder hook
vi.mock("../hooks/useVoiceRecorder", () => ({
  useVoiceRecorder: () => ({
    isRecording: false,
    isTranscribing: false,
    startRecording: vi.fn(),
    stopRecording: vi.fn().mockResolvedValue(""),
    cancelRecording: vi.fn(),
    error: null,
    duration: 0,
  }),
}));

// Mock Clerk
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue("token") }),
}));

describe("CopilotInput", () => {
  const defaultProps = {
    onSend: vi.fn(),
    disabled: false,
  };

  it("renders textarea", () => {
    render(<CopilotInput {...defaultProps} />);
    expect(screen.getByPlaceholderText(/escribe/i)).toBeInTheDocument();
  });

  it("renders mic button", () => {
    render(<CopilotInput {...defaultProps} />);
    // Look for the mic button by its aria-label or test-id
    const micButton = screen.getByLabelText(/micrófono|mic|audio|voz/i);
    expect(micButton).toBeInTheDocument();
  });

  it("renders attachment button", () => {
    render(<CopilotInput {...defaultProps} />);
    const attachButton = screen.getByLabelText(/adjuntar|attach/i);
    expect(attachButton).toBeInTheDocument();
  });

  it("calls onSend when pressing Enter", async () => {
    const onSend = vi.fn();
    render(<CopilotInput {...defaultProps} onSend={onSend} />);
    const textarea = screen.getByPlaceholderText(/escribe/i);
    await userEvent.type(textarea, "Hello{Enter}");
    expect(onSend).toHaveBeenCalledWith("Hello");
  });

  it("does not send empty messages", async () => {
    const onSend = vi.fn();
    render(<CopilotInput {...defaultProps} onSend={onSend} />);
    const textarea = screen.getByPlaceholderText(/escribe/i);
    await userEvent.type(textarea, "{Enter}");
    expect(onSend).not.toHaveBeenCalled();
  });

  it("disables input when disabled prop is true", () => {
    render(<CopilotInput {...defaultProps} disabled />);
    const textarea = screen.getByPlaceholderText(/escribe/i);
    expect(textarea).toBeDisabled();
  });
});
