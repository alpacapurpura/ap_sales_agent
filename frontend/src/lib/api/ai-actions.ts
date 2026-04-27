import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

const API_URL = config.api.baseUrl;

export interface OfferPsychologyPayload {
  avatar_id: string;
  offer_name: string;
  offer_description?: string;
  current_pains: string[];
  current_desires: string[];
}

export interface OfferPsychologyResult {
  pains: string[];
  desires: string[];
}

export interface BrandExtractPayload {
  url: string;
  type: "brand_identity";
}

export interface ExtractionStatus {
  status: "queued" | "running" | "processing" | "completed" | "failed";
  progress: number;
  stage?: string;
  started_at?: string;
  finished_at?: string | null;
  /** Cumulative list of field ids filled so far. */
  filled_fields?: string[];
  /** Field ids bucketed by section slug. */
  filled_fields_by_section?: Record<string, string[]>;
  /** Section slugs that have been touched (any field written). */
  sections_touched?: string[];
  /** Section slugs that have been fully completed. */
  sections_completed?: string[];
  /** One-shot flag set to the section slug when it just transitioned to complete. */
  newly_completed_section?: string | null;
  error?: string | null;
}

/**
 * Generic job-status poller. Takes a full endpoint URL (returned by the tool
 * in the `poll_endpoint` field) and an auth token.
 *
 * Generalisation of the old `pollExtractionStatus` which hardcoded the brand
 * extraction endpoint. Use this for all async tool jobs going forward.
 */
export async function pollJobStatus(
  pollEndpoint: string,
  token: string,
): Promise<ExtractionStatus> {
  const url = pollEndpoint.startsWith("http") ? pollEndpoint : `${API_URL}${pollEndpoint}`;
  const response = await fetchClient(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error(`Status check failed: ${response.status}`);
  return response.json() as Promise<ExtractionStatus>;
}

export type FullBrandExtractInput =
  | FormData
  | {
      url?: string;
      text?: string;
      mode?: "initial" | "update";
      update_instructions?: string;
      dry_run?: boolean;
      include_visuals?: boolean;
      include_assets?: boolean;
    };

function toFormData(input: FullBrandExtractInput): FormData {
  if (input instanceof FormData) {
    return input;
  }
  const form = new FormData();
  if (input.url) form.append("url", input.url);
  if (input.text) form.append("text", input.text);
  if (input.mode) form.append("mode", input.mode);
  if (input.update_instructions) form.append("update_instructions", input.update_instructions);
  if (typeof input.dry_run === "boolean") form.append("dry_run", String(input.dry_run));
  if (typeof input.include_visuals === "boolean")
    form.append("include_visuals", String(input.include_visuals));
  if (typeof input.include_assets === "boolean")
    form.append("include_assets", String(input.include_assets));
  return form;
}

export const aiActionsApi = {
  async extractBrandIdentity(data: BrandExtractPayload, token: string): Promise<unknown> {
    const response = await fetchClient(`${API_URL}/api/v1/brand/tools/extract`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      throw new Error("Failed to extract brand visuals");
    }
    return response.json() as Promise<unknown>;
  },

  async extractFullBrand(input: FullBrandExtractInput, token: string): Promise<{ job_id: string }> {
    const body = toFormData(input);
    const response = await fetchClient(`${API_URL}/api/v1/brand/tools/extract-full-brand`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body,
    });

    if (!response.ok) {
      throw new Error(`Failed to start extraction: ${response.status} ${response.statusText}`);
    }
    return response.json() as Promise<{ job_id: string }>;
  },

  /**
   * @deprecated Use the module-level `pollJobStatus(pollEndpoint, token)` instead.
   * Kept for backwards compatibility with brand-studio API layer.
   */
  async pollExtractionStatus(jobId: string, token: string): Promise<ExtractionStatus> {
    return pollJobStatus(`/api/v1/brand/tools/extract-full-brand/status/${jobId}`, token);
  },

  async extractFullOffer(data: FormData, token: string): Promise<{ job_id: string }> {
    const response = await fetchClient(`${API_URL}/api/v1/offer/tools/extract-full-offer`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: data,
    });
    if (!response.ok) {
      throw new Error(
        `Failed to start offer extraction: ${response.status} ${response.statusText}`,
      );
    }
    return response.json() as Promise<{ job_id: string }>;
  },

  async pollOfferExtractionStatus(jobId: string, token: string): Promise<ExtractionStatus> {
    const response = await fetchClient(
      `${API_URL}/api/v1/offer/tools/extract-full-offer/status/${jobId}`,
      {
        headers: { Authorization: `Bearer ${token}` },
      },
    );
    if (!response.ok) throw new Error(`Status check failed: ${response.status}`);
    return response.json() as Promise<ExtractionStatus>;
  },

  async generateOfferPsychology(
    data: OfferPsychologyPayload,
    token: string,
  ): Promise<OfferPsychologyResult> {
    const response = await fetchClient(`${API_URL}/api/v1/offer/ai/psychology`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const error = (await response.json().catch(() => ({ detail: response.statusText }))) as {
        detail?: string;
      };
      throw new Error(error.detail || "Error generating psychology");
    }
    return response.json() as Promise<OfferPsychologyResult>;
  },
};
