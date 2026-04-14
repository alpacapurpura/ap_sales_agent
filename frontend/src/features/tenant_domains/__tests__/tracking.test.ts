import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { getTrackingConfig } from "../utils/tracking";
import type { TrackingConfig } from "../utils/tracking";

// Mock config module to avoid env var issues in tests
vi.mock("@/lib/config", () => ({
  config: {
    api: { baseUrl: "http://test-api" },
  },
}));

const MOCK_CONFIG: TrackingConfig = {
  gtm_container_id: "GTM-XXXXXX",
  gtm_server_url: "https://gtm.example.com",
  meta_pixel_id: "123456789",
  ga_measurement_id: "G-ABCDEFGH",
};

describe("getTrackingConfig", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns tracking config on successful fetch (200)", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_CONFIG,
    } as Response);

    const result = await getTrackingConfig("tenant-abc");

    expect(result).toEqual(MOCK_CONFIG);
    expect(fetch).toHaveBeenCalledWith(
      "http://test-api/api/v1/public/tracking/tenant-abc",
      expect.objectContaining({ next: { revalidate: 300 } }),
    );
  });

  it("returns null when response is not ok (404)", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: false,
      status: 404,
    } as Response);

    const result = await getTrackingConfig("nonexistent-tenant");

    expect(result).toBeNull();
  });

  it("returns null when fetch throws a network error", async () => {
    vi.mocked(fetch).mockRejectedValueOnce(new Error("Network error"));

    const result = await getTrackingConfig("tenant-abc");

    expect(result).toBeNull();
  });

  it("includes the tenant ID in the request URL", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_CONFIG,
    } as Response);

    await getTrackingConfig("specific-tenant-id");

    const calledUrl = vi.mocked(fetch).mock.calls[0][0] as string;
    expect(calledUrl).toContain("specific-tenant-id");
  });
});
