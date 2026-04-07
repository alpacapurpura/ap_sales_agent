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
  status: "queued" | "processing" | "completed" | "failed";
  progress: number;
  stage?: string;
  error?: string;
}

export type FullBrandExtractInput = FormData | {
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
  if (typeof input.include_visuals === "boolean") form.append("include_visuals", String(input.include_visuals));
  if (typeof input.include_assets === "boolean") form.append("include_assets", String(input.include_assets));
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
    return response.json();
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
    return response.json();
  },

  async pollExtractionStatus(jobId: string, token: string): Promise<ExtractionStatus> {
    const response = await fetchClient(
      `${API_URL}/api/v1/brand/tools/extract-full-brand/status/${jobId}`,
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );
    if (!response.ok) throw new Error(`Status check failed: ${response.status}`);
    return response.json();
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
      throw new Error(`Failed to start offer extraction: ${response.status} ${response.statusText}`);
    }
    return response.json();
  },

  async pollOfferExtractionStatus(jobId: string, token: string): Promise<ExtractionStatus> {
    const response = await fetchClient(
      `${API_URL}/api/v1/offer/tools/extract-full-offer/status/${jobId}`,
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );
    if (!response.ok) throw new Error(`Status check failed: ${response.status}`);
    return response.json();
  },

  async generateOfferPsychology(data: OfferPsychologyPayload, token: string): Promise<OfferPsychologyResult> {
    const response = await fetchClient(`${API_URL}/api/v1/offer/ai/psychology`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || "Error generating psychology");
    }
    return response.json();
  },
};
