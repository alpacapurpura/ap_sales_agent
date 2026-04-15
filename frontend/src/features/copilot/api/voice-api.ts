import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

const API_URL = config.api.baseUrl;

export interface TranscriptionResponse {
  text: string;
  language: string;
  duration_seconds: number;
}

/**
 * Send an audio blob to the backend for speech-to-text transcription.
 * Uses FormData so the request is sent as multipart/form-data.
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

  const response = await fetchClient(`${API_URL}/api/v1/copilot/voice/transcribe`, {
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

  return response.json() as Promise<TranscriptionResponse>;
}
