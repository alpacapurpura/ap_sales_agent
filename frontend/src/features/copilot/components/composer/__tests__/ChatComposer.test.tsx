import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: () => Promise.resolve("test-token"),
    isLoaded: true,
    isSignedIn: true,
  }),
}));

vi.mock("../../../hooks/use-voice-recorder", () => ({
  useVoiceRecorder: () => ({
    isRecording: false,
    isTranscribing: false,
    startRecording: vi.fn().mockResolvedValue(undefined),
    stopRecording: vi.fn().mockResolvedValue(""),
    cancelRecording: vi.fn(),
    error: null,
    duration: 0,
  }),
}));

vi.mock("../../../hooks/use-media-upload", () => ({
  useMediaUpload: () => ({
    uploadMedia: vi.fn().mockResolvedValue("upload-id"),
    cancelUpload: vi.fn(),
    uploads: [],
    removeUpload: vi.fn(),
    validateFile: vi.fn().mockReturnValue(null),
  }),
}));

vi.mock("../../../hooks/use-suggestions", () => ({
  useSuggestions: () => ({ chips: [], isLoading: false }),
}));

vi.mock("../../../store/copilot-store", () => ({
  useCopilotStore: (selector: (s: { selectedFields: [] }) => unknown) =>
    selector({ selectedFields: [] }),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/tenant-1/brand-studio",
  useParams: () => ({ tenantId: "tenant-1" }),
}));

function wrap(ui: ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>);
}

import { ChatComposer } from "../ChatComposer";

import type { ReactElement } from "react";

describe("ChatComposer", () => {
  const onSend = vi.fn();

  beforeEach(() => {
    onSend.mockClear();
  });

  it("renders the toolbar with textarea and send button", () => {
    wrap(<ChatComposer onSend={onSend} />);
    expect(screen.getByRole("textbox", { name: /mensaje/i })).toBeDefined();
    expect(screen.getByRole("button", { name: /enviar/i })).toBeDefined();
  });

  it("send button is disabled when textarea is empty", () => {
    wrap(<ChatComposer onSend={onSend} />);
    const sendBtn = screen.getByRole("button", { name: /enviar/i });
    expect((sendBtn as HTMLButtonElement).disabled).toBe(true);
  });

  it("calls onSend with text when Enter key is pressed", () => {
    wrap(<ChatComposer onSend={onSend} />);
    const textarea = screen.getByRole("textbox", { name: /mensaje/i });
    fireEvent.change(textarea, { target: { value: "Hola mundo" } });
    fireEvent.keyDown(textarea, { key: "Enter", shiftKey: false });
    expect(onSend).toHaveBeenCalledOnce();
    expect(onSend.mock.calls[0][0]).toBe("Hola mundo");
  });

  it("does not send on Shift+Enter", () => {
    wrap(<ChatComposer onSend={onSend} />);
    const textarea = screen.getByRole("textbox", { name: /mensaje/i });
    fireEvent.change(textarea, { target: { value: "Hola" } });
    fireEvent.keyDown(textarea, { key: "Enter", shiftKey: true });
    expect(onSend).not.toHaveBeenCalled();
  });

  it("shows reply preview when replyTo is provided", () => {
    wrap(
      <ChatComposer
        onSend={onSend}
        replyTo={{ messageId: "msg-1", preview: "Mensaje original", role: "assistant" }}
      />,
    );
    expect(screen.getByText(/Respondiendo a/i)).toBeDefined();
    expect(screen.getByText(/Mensaje original/)).toBeDefined();
  });

  it("renders attachment button", () => {
    wrap(<ChatComposer onSend={onSend} />);
    expect(screen.getByRole("button", { name: /adjuntar/i })).toBeDefined();
  });
});
