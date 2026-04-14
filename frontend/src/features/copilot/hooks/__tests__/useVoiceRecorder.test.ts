import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";

// ── Mocks ──────────────────────────────────────────────────────────────────

// Mock Clerk auth
const mockGetToken = vi.fn().mockResolvedValue("test-token");
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: mockGetToken,
  }),
}));

// Mock voice API
const mockTranscribeAudio = vi.fn();
vi.mock("../../api/voice-api", () => ({
  transcribeAudio: (...args: unknown[]) => mockTranscribeAudio(...args),
}));

// ── MediaRecorder mock ─────────────────────────────────────────────────────

interface MockMediaRecorderInstance {
  start: ReturnType<typeof vi.fn>;
  stop: ReturnType<typeof vi.fn>;
  state: "inactive" | "recording";
  mimeType: string;
  ondataavailable: ((event: { data: Blob }) => void) | null;
  onstop: (() => void) | null;
  onerror: ((event: { error: Error }) => void) | null;
}

let latestRecorderInstance: MockMediaRecorderInstance | null = null;

function MockMediaRecorderConstructor(_stream: MediaStream, options?: { mimeType?: string }) {
  const instance: MockMediaRecorderInstance = {
    start: vi.fn(() => {
      instance.state = "recording";
    }),
    stop: vi.fn(() => {
      instance.state = "inactive";
      // Simulate the data + stop events that real MediaRecorder fires
      setTimeout(() => {
        if (instance.ondataavailable) {
          instance.ondataavailable({
            data: new Blob(["audio-data"], { type: "audio/webm" }),
          });
        }
        if (instance.onstop) {
          instance.onstop();
        }
      }, 0);
    }),
    state: "inactive" as "inactive" | "recording",
    mimeType: options?.mimeType ?? "audio/webm",
    ondataavailable: null,
    onstop: null,
    onerror: null,
  };
  latestRecorderInstance = instance;
  return instance;
}

// Mock getUserMedia
const mockGetUserMedia = vi.fn().mockResolvedValue({
  getTracks: () => [{ stop: vi.fn() }],
});

// ── Setup ──────────────────────────────────────────────────────────────────

beforeEach(() => {
  vi.clearAllMocks();
  vi.useFakeTimers();
  latestRecorderInstance = null;

  // Stub navigator.mediaDevices.getUserMedia
  vi.stubGlobal("navigator", {
    ...navigator,
    mediaDevices: {
      getUserMedia: mockGetUserMedia,
    },
  });

  // Stub MediaRecorder global
  vi.stubGlobal(
    "MediaRecorder",
    Object.assign(MockMediaRecorderConstructor, {
      isTypeSupported: vi.fn().mockReturnValue(true),
    }),
  );
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

// ── Tests ──────────────────────────────────────────────────────────────────

describe("useVoiceRecorder", () => {
  // Dynamic import to ensure mocks are registered first
  async function importHook() {
    const mod = await import("../useVoiceRecorder");
    return mod.useVoiceRecorder;
  }

  it("starts in idle state", async () => {
    const useVoiceRecorder = await importHook();
    const { result } = renderHook(() => useVoiceRecorder());

    expect(result.current.isRecording).toBe(false);
    expect(result.current.isTranscribing).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.duration).toBe(0);
  });

  it("sets isRecording to true after startRecording", async () => {
    const useVoiceRecorder = await importHook();
    const { result } = renderHook(() => useVoiceRecorder());

    await act(async () => {
      await result.current.startRecording();
    });

    expect(result.current.isRecording).toBe(true);
    expect(result.current.error).toBeNull();
    expect(mockGetUserMedia).toHaveBeenCalledWith({ audio: true });
  });

  it("increments duration while recording", async () => {
    const useVoiceRecorder = await importHook();
    const { result } = renderHook(() => useVoiceRecorder());

    await act(async () => {
      await result.current.startRecording();
    });

    expect(result.current.duration).toBe(0);

    act(() => {
      vi.advanceTimersByTime(3000);
    });

    expect(result.current.duration).toBe(3);
  });

  it("sets error when getUserMedia fails", async () => {
    mockGetUserMedia.mockRejectedValueOnce(new DOMException("Permission denied"));

    const useVoiceRecorder = await importHook();
    const { result } = renderHook(() => useVoiceRecorder());

    await act(async () => {
      await result.current.startRecording();
    });

    expect(result.current.isRecording).toBe(false);
    expect(result.current.error).toBe("No se pudo acceder al micrófono. Verifica los permisos.");
  });

  it("stopRecording transcribes audio and returns text", async () => {
    mockTranscribeAudio.mockResolvedValueOnce({
      text: "Hola mundo",
      language: "es",
      duration_seconds: 2.5,
    });

    const useVoiceRecorder = await importHook();
    const { result } = renderHook(() => useVoiceRecorder());

    await act(async () => {
      await result.current.startRecording();
    });

    let transcript = "";
    await act(async () => {
      // stop() fires ondataavailable + onstop via setTimeout(0)
      // We need to flush the microtask + timers
      const promise = result.current.stopRecording();
      vi.advanceTimersByTime(1);
      transcript = await promise;
    });

    expect(transcript).toBe("Hola mundo");
    expect(result.current.isRecording).toBe(false);
    expect(result.current.isTranscribing).toBe(false);
    expect(mockTranscribeAudio).toHaveBeenCalledWith(expect.any(Blob), "test-token");
  });

  it("sets error when transcription fails", async () => {
    mockTranscribeAudio.mockRejectedValueOnce(new Error("API error"));

    const useVoiceRecorder = await importHook();
    const { result } = renderHook(() => useVoiceRecorder());

    await act(async () => {
      await result.current.startRecording();
    });

    let transcript = "";
    await act(async () => {
      const promise = result.current.stopRecording();
      vi.advanceTimersByTime(1);
      transcript = await promise;
    });

    expect(transcript).toBe("");
    expect(result.current.error).toBe("Error al transcribir el audio. Intenta de nuevo.");
    expect(result.current.isTranscribing).toBe(false);
  });

  it("cancelRecording stops without transcribing", async () => {
    const useVoiceRecorder = await importHook();
    const { result } = renderHook(() => useVoiceRecorder());

    await act(async () => {
      await result.current.startRecording();
    });

    expect(result.current.isRecording).toBe(true);

    act(() => {
      result.current.cancelRecording();
    });

    expect(result.current.isRecording).toBe(false);
    expect(result.current.isTranscribing).toBe(false);
    expect(mockTranscribeAudio).not.toHaveBeenCalled();
  });

  it("resets duration when starting a new recording", async () => {
    const useVoiceRecorder = await importHook();
    const { result } = renderHook(() => useVoiceRecorder());

    // First recording
    await act(async () => {
      await result.current.startRecording();
    });
    act(() => {
      vi.advanceTimersByTime(5000);
    });
    expect(result.current.duration).toBe(5);

    // Cancel
    act(() => {
      result.current.cancelRecording();
    });

    // Second recording — duration should reset
    await act(async () => {
      await result.current.startRecording();
    });
    expect(result.current.duration).toBe(0);
  });

  it("sets error when getToken returns null", async () => {
    mockGetToken.mockResolvedValueOnce(null);

    const useVoiceRecorder = await importHook();
    const { result } = renderHook(() => useVoiceRecorder());

    await act(async () => {
      await result.current.startRecording();
    });

    let transcript = "";
    await act(async () => {
      const promise = result.current.stopRecording();
      vi.advanceTimersByTime(1);
      transcript = await promise;
    });

    expect(transcript).toBe("");
    expect(result.current.error).toBe("No se pudo obtener el token de autenticación.");
    expect(mockTranscribeAudio).not.toHaveBeenCalled();
  });

  it("stopRecording returns empty string when recorder is inactive", async () => {
    const useVoiceRecorder = await importHook();
    const { result } = renderHook(() => useVoiceRecorder());

    // Don't start recording — just try to stop
    let transcript = "";
    await act(async () => {
      transcript = await result.current.stopRecording();
    });

    expect(transcript).toBe("");
  });

  void latestRecorderInstance; // referenced in setup, used to verify instance state
});
