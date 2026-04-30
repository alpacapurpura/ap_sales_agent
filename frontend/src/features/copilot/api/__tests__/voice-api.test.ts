/**
 * Tests for voice-api.ts — D-9 adapter (URL swap + shape adapter).
 * TDD: these tests were written RED before the URL swap implementation.
 *
 * [COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// ── Module mocks ──────────────────────────────────────────────────────

vi.mock("@/lib/config", () => ({
  config: { api: { baseUrl: "http://localhost:8000" } },
}));

const mockFetchClient = vi.fn();
vi.mock("@/lib/http-client", () => ({
  fetchClient: (...args: unknown[]) => mockFetchClient(...args),
}));

// ── Import after mocks ────────────────────────────────────────────────

import { transcribeAudio } from "../voice-api";

describe("transcribeAudio (D-9 adapter)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("posts to /voice/upload-and-transcribe URL (not legacy /voice/transcribe)", async () => {
    mockFetchClient.mockResolvedValue({
      ok: true,
      json: async () => ({
        block: {
          id: "block-1",
          asset_id: "asset-1",
          url: "https://example.com/audio.webm",
          mime: "audio/webm",
          transcript: "hola mundo",
          transcript_language: "es",
          duration_ms: 3000,
        },
      }),
    });

    const blob = new Blob(["audio"], { type: "audio/webm" });
    await transcribeAudio(blob, "test-token");

    const calledUrl: string = mockFetchClient.mock.calls[0][0];
    expect(calledUrl).toContain("/voice/upload-and-transcribe");
    expect(calledUrl).not.toContain("/voice/transcribe\b");
  });

  it("adapts new backend shape to legacy TranscriptionResponse", async () => {
    mockFetchClient.mockResolvedValue({
      ok: true,
      json: async () => ({
        block: {
          id: "block-1",
          asset_id: "asset-1",
          url: "https://example.com/audio.webm",
          mime: "audio/webm",
          transcript: "hola mundo",
          transcript_language: "es",
          duration_ms: 5000,
        },
      }),
    });

    const blob = new Blob(["audio"], { type: "audio/webm" });
    const result = await transcribeAudio(blob, "test-token");

    expect(result).toEqual({
      text: "hola mundo",
      language: "es",
      duration_seconds: 5,
    });
  });

  it("handles missing optional fields gracefully (null transcript_language, null duration_ms)", async () => {
    mockFetchClient.mockResolvedValue({
      ok: true,
      json: async () => ({
        block: {
          id: "block-1",
          asset_id: "asset-1",
          url: "https://example.com/audio.webm",
          mime: "audio/webm",
          transcript: "hi",
          transcript_language: null,
          duration_ms: null,
        },
      }),
    });

    const blob = new Blob(["audio"], { type: "audio/webm" });
    const result = await transcribeAudio(blob, "test-token");

    expect(result).toEqual({
      text: "hi",
      language: "",
      duration_seconds: 0,
    });
  });

  it("throws on non-ok response", async () => {
    mockFetchClient.mockResolvedValue({
      ok: false,
      status: 400,
      text: async () => "Bad Request",
    });

    const blob = new Blob(["audio"], { type: "audio/webm" });
    await expect(transcribeAudio(blob, "test-token")).rejects.toThrow("Transcription failed (400)");
  });

  it("sends Authorization header with token", async () => {
    mockFetchClient.mockResolvedValue({
      ok: true,
      json: async () => ({
        block: {
          id: "b",
          asset_id: "a",
          url: "u",
          mime: "m",
          transcript: "x",
          transcript_language: "es",
          duration_ms: 100,
        },
      }),
    });

    const blob = new Blob(["audio"], { type: "audio/webm" });
    await transcribeAudio(blob, "my-secret-token");

    const options = mockFetchClient.mock.calls[0][1] as { headers: Record<string, string> };
    expect(options.headers.Authorization).toBe("Bearer my-secret-token");
  });
});
