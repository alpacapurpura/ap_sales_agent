import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

const API_URL = config.api.baseUrl;

/**
 *
 */
export async function analyzeVoiceStyle(token: string | null, formData: FormData) {
  const res = await fetchClient(`${API_URL}/api/v1/brand/style/analyze-style`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  if (!res.ok) {
    const err = (await res.json()) as { detail?: string };
    throw new Error(err.detail || "Analysis failed");
  }

  return res.json() as Promise<Record<string, unknown>>;
}
