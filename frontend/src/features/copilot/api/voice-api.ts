// [COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md
// D-9: URL swap + shape adapter for voice transcription (PR-1 PI-2 S2).
// Legacy /voice/transcribe returned 410 Gone since S1 PR-1.
// New endpoint /voice/upload-and-transcribe has different response shape —
// this adapter preserves TranscriptionResponse consumers without changes.

import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

const API_URL = config.api.baseUrl;

export interface TranscriptionResponse {
  text: string;
  language: string;
  duration_seconds: number;
}

// Internal shape of /upload-and-transcribe (mirror VoiceUploadAndTranscribeResponse)
interface UploadAndTranscribeResponse {
  block: {
    id: string;
    asset_id: string;
    url: string;
    mime: string;
    duration_ms?: number | null;
    transcript: string;
    transcript_language?: string | null;
  };
}

/**
 * Send an audio blob to the backend for speech-to-text transcription.
 * Uses FormData so the request is sent as multipart/form-data.
 *
 * D-9: migrated from legacy /voice/transcribe (410 Gone) to
 * /voice/upload-and-transcribe. Adapts the new AudioBlock response shape
 * to the legacy TranscriptionResponse shape for backward-compat consumers.
 *
 * Note: fetchClient auto-injects X-Tenant-ID from URL/localStorage.
 * We only need to add Authorization manually.
 */
export async function transcribeAudio(
  audioBlob: Blob,
  token: string,
): Promise<TranscriptionResponse> {
  const formData = new FormData();
  formData.append("file", audioBlob, "recording.webm");

  // D-9: URL swap to new combined upload+STT endpoint
  const response = await fetchClient(`${API_URL}/api/v1/copilot/voice/upload-and-transcribe`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Transcription failed (${response.status}): ${errorText}`);
  }

  // D-9: adapt new AudioBlock shape → legacy TranscriptionResponse
  const payload = (await response.json()) as UploadAndTranscribeResponse;
  return {
    text: payload.block.transcript,
    language: payload.block.transcript_language ?? "",
    duration_seconds: (payload.block.duration_ms ?? 0) / 1000,
  };
}
