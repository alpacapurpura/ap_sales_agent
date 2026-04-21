import { fetchClient } from "@/lib/http-client";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface OfferCopilotResult {
  /** Section slug returned by the backend tool. */
  sectionSlug: string;
  /**
   * Draft field values to apply to the form. The caller is responsible for
   * applying these via the form's setValue — never auto-applied (R3 decision).
   */
  draftFields: Record<string, unknown>;
  /** Human-readable improvement suggestions from the tool. */
  suggestions: string[];
  /** 0.0–1.0 confidence score. */
  confidence: number;
  /** Backend data sources cited by the tool. */
  citations: string[];
}

interface InvokeToolParams {
  toolKey: string;
  offerId: string;
  sectionSlug: string;
  editionCode: string | undefined;
  toolArgs: Record<string, string>;
  token: string;
}

// ---------------------------------------------------------------------------
// API
// ---------------------------------------------------------------------------

/**
 * Invoke a named offer-section copilot tool.
 *
 * Route: POST /api/v1/copilot/offer-section-tools/{toolKey}
 */
export async function invokeOfferSectionTool({
  toolKey,
  offerId,
  sectionSlug,
  editionCode,
  toolArgs,
  token,
}: InvokeToolParams): Promise<OfferCopilotResult> {
  const response = await fetchClient(
    `/api/v1/copilot/offer-section-tools/${encodeURIComponent(toolKey)}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        offer_id: offerId,
        section_slug: sectionSlug,
        edition_code: editionCode ?? null,
        tool_args: toolArgs,
      }),
    },
  );

  if (!response.ok) {
    const detail = await response
      .json()
      .then((d: { detail?: string }) => d.detail ?? "Error desconocido")
      .catch(() => "Error desconocido");
    throw new Error(detail);
  }

  // Backend returns snake_case; convert to camelCase here.
  const data = (await response.json()) as {
    section_slug: string;
    draft_fields: Record<string, unknown>;
    suggestions: string[];
    confidence: number;
    citations: string[];
  };

  return {
    sectionSlug: data.section_slug,
    draftFields: data.draft_fields,
    suggestions: data.suggestions,
    confidence: data.confidence,
    citations: data.citations,
  };
}
