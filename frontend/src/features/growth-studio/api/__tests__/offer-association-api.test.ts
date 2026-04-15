import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock config before importing the module under test
vi.mock("@/lib/config", () => ({
  config: { api: { baseUrl: "https://api.test.com" } },
}));

// Mock fetchClient to capture URL + options
const mockFetchClient = vi.fn();
vi.mock("@/lib/http-client", () => ({
  fetchClient: (...args: unknown[]) => mockFetchClient(...args),
}));

import {
  fetchAssociations,
  createAssociation,
  deleteAssociation,
  autoDetectSuggestions,
  applySuggestions,
  fetchMetaHealthCheck,
  fetchMetricsByOffer,
  fetchCampaignTemplateForOffer,
} from "../offer-association-api";

import type {
  AssociationCreatePayload,
  AssociationSuggestion,
} from "../../types/offer-association";

const TOKEN = "test-token";

function makeResponse(body: unknown, ok = true, status = 200): Response {
  return {
    ok,
    status,
    json: () => Promise.resolve(body),
  } as unknown as Response;
}

describe("offer-association-api URL routing", () => {
  beforeEach(() => {
    mockFetchClient.mockReset();
  });

  it("fetchAssociations hits /api/v1/advertising/associations", async () => {
    mockFetchClient.mockResolvedValueOnce(makeResponse([]));
    await fetchAssociations(TOKEN);
    const url = mockFetchClient.mock.calls[0][0] as string;
    expect(url).toContain("/api/v1/advertising/associations");
  });

  it("fetchAssociations appends query params", async () => {
    mockFetchClient.mockResolvedValueOnce(makeResponse([]));
    await fetchAssociations(TOKEN, { targetType: "campaign", offerId: "offer-1" });
    const url = mockFetchClient.mock.calls[0][0] as string;
    expect(url).toContain("target_type=campaign");
    expect(url).toContain("offer_id=offer-1");
  });

  it("createAssociation POSTs to /associations with camel→snake payload", async () => {
    mockFetchClient.mockResolvedValueOnce(makeResponse({ id: "a1" }, true, 201));
    const payload: AssociationCreatePayload = {
      targetType: "campaign",
      targetExternalId: "camp-123",
      offerId: "off-1",
      associationType: "manual",
    };
    await createAssociation(TOKEN, payload);
    const [, options] = mockFetchClient.mock.calls[0];
    expect(options.method).toBe("POST");
    const body = JSON.parse(options.body as string);
    expect(body.target_type).toBe("campaign");
    expect(body.target_external_id).toBe("camp-123");
    expect(body.offer_id).toBe("off-1");
    expect(body.association_type).toBe("manual");
  });

  it("deleteAssociation DELETEs /associations/{id}", async () => {
    mockFetchClient.mockResolvedValueOnce(makeResponse(null, true, 204));
    await deleteAssociation(TOKEN, "assoc-99");
    const [url, options] = mockFetchClient.mock.calls[0];
    expect(url).toContain("/api/v1/advertising/associations/assoc-99");
    expect(options.method).toBe("DELETE");
  });

  it("autoDetectSuggestions POSTs to /auto-detect and returns camelCase", async () => {
    mockFetchClient.mockResolvedValueOnce(
      makeResponse([
        {
          target_type: "campaign",
          target_external_id: "camp-1",
          target_name: "Campaign 1",
          suggested_offer_id: "off-1",
          suggested_offer_name: "MasterClass",
          association_type: "auto_landing_url",
          confidence: "high",
          reason: "URL match",
        },
      ]),
    );
    const res = await autoDetectSuggestions(TOKEN);
    expect(res).toHaveLength(1);
    expect(res[0].targetType).toBe("campaign");
    expect(res[0].suggestedOfferId).toBe("off-1");
    expect(res[0].associationType).toBe("auto_landing_url");
  });

  it("applySuggestions POSTs suggestions list snake-cased", async () => {
    mockFetchClient.mockResolvedValueOnce(makeResponse([]));
    const suggestions: AssociationSuggestion[] = [
      {
        targetType: "campaign",
        targetExternalId: "camp-1",
        targetName: "Campaign 1",
        suggestedOfferId: "off-1",
        suggestedOfferName: "MasterClass",
        associationType: "auto_landing_url",
        confidence: "high",
        reason: "URL match",
      },
    ];
    await applySuggestions(TOKEN, suggestions);
    const [, options] = mockFetchClient.mock.calls[0];
    expect(options.method).toBe("POST");
    const body = JSON.parse(options.body as string);
    expect(Array.isArray(body)).toBe(true);
    expect(body[0].target_type).toBe("campaign");
    expect(body[0].target_external_id).toBe("camp-1");
    expect(body[0].offer_id).toBe("off-1");
  });

  it("fetchMetaHealthCheck hits /health-check with provider query", async () => {
    mockFetchClient.mockResolvedValueOnce(
      makeResponse({
        overall_status: "healthy",
        active_campaigns: [],
        offers_coverage: [],
        unassigned_targets: [],
        recommendations: [],
        summary_text: "All good",
      }),
    );
    const res = await fetchMetaHealthCheck(TOKEN);
    const url = mockFetchClient.mock.calls[0][0] as string;
    expect(url).toContain("/api/v1/advertising/health-check");
    expect(url).toContain("provider=meta");
    expect(res.overallStatus).toBe("healthy");
    expect(res.summaryText).toBe("All good");
  });

  it("fetchMetricsByOffer hits /metrics-by-offer with period", async () => {
    mockFetchClient.mockResolvedValueOnce(
      makeResponse({
        period: "30d",
        start_date: "2026-03-11",
        end_date: "2026-04-10",
        currency: "PEN",
        offers: [],
        unassigned: { target_count: 0, total_spend: 0, impressions: 0, clicks: 0 },
        branding_only: { target_count: 0, total_spend: 0, reach: 0, impressions: 0 },
      }),
    );
    const res = await fetchMetricsByOffer(TOKEN, "30d");
    const url = mockFetchClient.mock.calls[0][0] as string;
    expect(url).toContain("/api/v1/advertising/metrics-by-offer");
    expect(url).toContain("period=30d");
    expect(res.period).toBe("30d");
    expect(res.startDate).toBe("2026-03-11");
    expect(res.brandingOnly.targetCount).toBe(0);
  });

  it("fetchCampaignTemplateForOffer hits /campaign-templates/suggest", async () => {
    mockFetchClient.mockResolvedValueOnce(
      makeResponse({
        id: "tpl-1",
        offer_archetype: "PRODUCTO",
        offer_onboarding_action: null,
        offer_is_lead_magnet: false,
        name: "Producto Digital",
        description: "Venta directa",
        recommended_objective: "OUTCOME_SALES",
        recommended_objective_label_es: "Ventas",
        recommended_optimization_goal: null,
        recommended_destination_type: null,
        structure_hints: {},
        priority: 100,
      }),
    );
    const res = await fetchCampaignTemplateForOffer(TOKEN, "off-1");
    expect(res).not.toBeNull();
    expect(res?.recommendedObjective).toBe("OUTCOME_SALES");
    const url = mockFetchClient.mock.calls[0][0] as string;
    expect(url).toContain("/api/v1/advertising/campaign-templates/suggest");
    expect(url).toContain("offer_id=off-1");
  });

  it("fetchCampaignTemplateForOffer returns null on 404", async () => {
    mockFetchClient.mockResolvedValueOnce(makeResponse(null, false, 404));
    const res = await fetchCampaignTemplateForOffer(TOKEN, "nope");
    expect(res).toBeNull();
  });

  it("propagates errors on non-ok responses for non-template fetches", async () => {
    mockFetchClient.mockResolvedValueOnce(makeResponse(null, false, 500));
    await expect(fetchAssociations(TOKEN)).rejects.toThrow();
  });
});
