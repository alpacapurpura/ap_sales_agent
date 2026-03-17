import { describe, expect, it, vi, beforeEach } from "vitest";

const fetchClientMock = vi.fn();

vi.mock("@/lib/config", () => ({
  config: {
    api: {
      baseUrl: "http://localhost:8000",
    },
  },
}));

vi.mock("@/lib/http-client", () => ({
  fetchClient: (...args: any[]) => fetchClientMock(...args),
}));

import { aiActionsApi } from "./ai-actions";

describe("aiActionsApi", () => {
  beforeEach(() => {
    fetchClientMock.mockReset();
  });

  it("usa la ruta offer/ai para psicología de oferta", async () => {
    fetchClientMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ pains: ["p1"], desires: ["d1"] }), { status: 200 })
    );

    const result = await aiActionsApi.generateOfferPsychology(
      {
        avatar_id: "avatar-1",
        offer_name: "Oferta X",
        current_pains: [],
        current_desires: [],
      },
      "token-123"
    );

    expect(result).toEqual({ pains: ["p1"], desires: ["d1"] });
    expect(fetchClientMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/offer/ai/psychology",
      expect.objectContaining({
        method: "POST",
      })
    );
  });

  it("usa la ruta brand/tools para extracción de brand", async () => {
    fetchClientMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ brand_name: "Visionarias" }), { status: 200 })
    );

    const result = await aiActionsApi.extractBrandIdentity(
      {
        url: "https://visionarias.ai",
        type: "brand_identity",
      },
      "token-123"
    );

    expect(result).toEqual({ brand_name: "Visionarias" });
    expect(fetchClientMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/brand/tools/extract",
      expect.objectContaining({
        method: "POST",
      })
    );
  });

  it("usa FormData y ruta brand/tools para extracción full brand", async () => {
    fetchClientMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ identity: { brand_name: "Visionarias" } }), { status: 200 })
    );

    const result = await aiActionsApi.extractFullBrand(
      {
        url: "https://visionarias.ai",
        mode: "initial",
      },
      "token-123"
    );

    expect(result).toEqual({ identity: { brand_name: "Visionarias" } });
    expect(fetchClientMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/brand/tools/extract-full-brand",
      expect.objectContaining({
        method: "POST",
        body: expect.any(FormData),
      })
    );
  });
});
