import { fetchClient } from "@/lib/http-client";
import { config } from "@/lib/config";

const API_URL = config.api.baseUrl;

export interface DocumentProcessingResponse {
  delta: Record<string, unknown>;
  summary: string;
  source_documents: string[];
  fields_extracted: string[];
  fields_skipped: string[];
}

export async function processInterviewDocuments(
  sessionId: string,
  files: File[],
  token: string,
): Promise<DocumentProcessingResponse> {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }

  const res = await fetchClient(`${API_URL}/api/v1/copilot/interview/${sessionId}/documents`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  if (!res.ok) {
    throw new Error(`Document processing failed: ${res.status}`);
  }

  return res.json() as Promise<DocumentProcessingResponse>;
}
