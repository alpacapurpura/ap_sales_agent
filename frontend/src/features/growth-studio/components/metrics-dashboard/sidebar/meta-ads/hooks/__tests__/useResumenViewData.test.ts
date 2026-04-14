import { renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { useResumenViewData } from "../useResumenViewData";
import type {
  BrandingAggregate,
  FunnelStep,
  MetricsByOffer,
  OfferMetrics,
  UnassignedAggregate,
} from "../../../../../../types/offer-association";
import type { ChannelDashboardData } from "../../../../../../types/metrics";

// ---------------------------------------------------------------------------
// Factories
// ---------------------------------------------------------------------------

function funnelStep(overrides: Partial<FunnelStep> = {}): FunnelStep {
  return {
    label: "Impresiones",
    metricName: "impressions",
    value: 100,
    conversionRateFromPrevious: null,
    ...overrides,
  };
}

function makeOffer(overrides: Partial<OfferMetrics> = {}): OfferMetrics {
  return {
    offerId: "off-1",
    offerName: "Curso Core",
    archetype: "PROGRAMA",
    expectedMetric: "lead",
    expectedMetricLabelEs: "Leads",
    totalSpend: 500,
    currency: "PEN",
    primaryResultCount: 47,
    primaryCostPerResult: 10.64,
    primaryMetricName: "Leads",
    primaryMetricUnit: "count",
    roas: 2.4,
    impressions: 12_340,
    clicks: 518,
    ctr: 4.2,
    cpm: 5.5,
    cpc: 0.96,
    reach: null,
    frequency: null,
    funnel: [
      funnelStep({ label: "Impresiones", metricName: "impressions", value: 12_340 }),
      funnelStep({
        label: "Clics",
        metricName: "clicks",
        value: 518,
        conversionRateFromPrevious: 4.2,
      }),
      funnelStep({
        label: "Leads",
        metricName: "meta_leads",
        value: 47,
        conversionRateFromPrevious: 9.07,
      }),
    ],
    timeseries: [
      { date: "2026-04-01", spend: 50, primaryResult: 5 },
      { date: "2026-04-02", spend: 60, primaryResult: 7 },
    ],
    metricUnavailableReason: null,
    ...overrides,
  };
}

function makeBranding(overrides: Partial<BrandingAggregate> = {}): BrandingAggregate {
  return {
    targetCount: 2,
    totalSpend: 300,
    impressions: 20_000,
    clicks: 100,
    ctr: 0.5,
    cpm: 15,
    cpc: 3,
    reach: null,
    frequency: null,
    funnel: [funnelStep({ value: 20_000 })],
    ...overrides,
  };
}

function makeUnassigned(overrides: Partial<UnassignedAggregate> = {}): UnassignedAggregate {
  return {
    targetCount: 1,
    totalSpend: 80,
    impressions: 5_000,
    clicks: 40,
    ctr: 0.8,
    cpm: 16,
    cpc: 2,
    reach: null,
    funnel: [funnelStep({ value: 5_000 })],
    ...overrides,
  };
}

function makePayload(overrides: Partial<MetricsByOffer> = {}): MetricsByOffer {
  return {
    period: "30d",
    startDate: "2026-03-11",
    endDate: "2026-04-10",
    currency: "PEN",
    offers: [makeOffer()],
    unassigned: makeUnassigned(),
    brandingOnly: makeBranding(),
    funnelAll: [
      funnelStep({ value: 37_340 }),
      funnelStep({
        label: "Clics",
        metricName: "clicks",
        value: 658,
        conversionRateFromPrevious: 1.76,
      }),
    ],
    reachAll: 14_200,
    ...overrides,
  };
}

function makeChannelData(overrides: Partial<ChannelDashboardData> = {}): ChannelDashboardData {
  return {
    channelSlug: "meta-ads",
    channelName: "Meta Ads",
    industryCategory: "default",
    period: "30d",
    kpis: [
      {
        metricName: "CTR",
        displayName: "CTR",
        currentValue: 1.8,
        previousValue: null,
        deltaPct: null,
        deltaAbsolute: null,
        unit: "percentage",
        higherIsBetter: true,
        benchmark: null,
      },
    ],
    timeSeries: [
      {
        metricName: "spend",
        displayName: "Inversión",
        unit: "currency",
        dataPoints: [{ date: "2026-04-01", value: 100 }],
      },
    ],
    funnel: { steps: [] },
    frequencyAlert: null,
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("useResumenViewData", () => {
  describe("filter = all", () => {
    it("returns 6 KPIs with aggregate values and the channel funnel", () => {
      const payload = makePayload();
      const channel = makeChannelData();
      const { result } = renderHook(() =>
        useResumenViewData({
          metricsByOffer: payload,
          channelData: channel,
          selectedOfferId: "all",
          tenantCurrency: "PEN",
        }),
      );
      const view = result.current;
      expect(view.filter).toBe("all");
      expect(view.kpis).toHaveLength(6);
      expect(view.kpis.map((k) => k.key)).toEqual([
        "spend",
        "roas",
        "results",
        "cpa",
        "ctr",
        "reach",
      ]);
      // Inversión = 500 (offer) + 80 (unassigned) + 300 (branding) = 880
      expect(view.kpis[0].value).toBeCloseTo(880);
      // Resultados = suma de offers.primaryResultCount
      expect(view.kpis[2].value).toBe(47);
      // Reach = reachAll del payload
      expect(view.kpis[5].value).toBe(14_200);
      expect(view.funnel).toHaveLength(2);
      expect(view.funnel[0].conversionRate).toBeNull();
      expect(view.funnel[1].conversionRate).toBeCloseTo(1.76);
      expect(view.emptyState).toBe(false);
    });

    it("falls back to reachAll null → card kind unavailable", () => {
      const payload = makePayload({ reachAll: null });
      const { result } = renderHook(() =>
        useResumenViewData({
          metricsByOffer: payload,
          channelData: makeChannelData(),
          selectedOfferId: "all",
          tenantCurrency: "PEN",
        }),
      );
      const reachCard = result.current.kpis.find((k) => k.key === "reach");
      expect(reachCard?.kind).toBe("unavailable");
      expect(reachCard?.value).toBeNull();
      expect(reachCard?.unavailableTooltipKey).toBe("unavailable_period_pending");
    });
  });

  describe("filter = offer", () => {
    it("shows ROAS when roas is present", () => {
      const payload = makePayload();
      const { result } = renderHook(() =>
        useResumenViewData({
          metricsByOffer: payload,
          channelData: makeChannelData(),
          selectedOfferId: "off-1",
          tenantCurrency: "PEN",
        }),
      );
      const view = result.current;
      expect(view.filter).toBe("offer");
      expect(view.kpis[1].key).toBe("roas_or_cost");
      expect(view.kpis[1].label).toBe("ROAS");
      expect(view.kpis[1].value).toBeCloseTo(2.4);
      // KPI #4 uses CPL label for a lead-primary offer
      expect(view.kpis[3].label).toBe("CPL");
      expect(view.kpis[3].key).toBe("cpa");
      // Reach is null → unavailable
      expect(view.kpis[5].kind).toBe("unavailable");
      expect(view.kpis[5].unavailableTooltipKey).toBe("unavailable_reach_overlap");
      // TimeSeries is derived from the offer's own timeseries.
      expect(view.timeSeries).toHaveLength(2);
      expect(view.timeSeries[0].metricName).toBe("spend");
      expect(view.timeSeries[1].metricName).toBe("conversions");
      expect(view.timeSeries[0].dataPoints).toHaveLength(2);
      // Context label mentions the offer and CPL.
      expect(view.contextLabel).toContain("Curso Core");
      expect(view.contextLabel).toContain("CPL");
    });

    it("falls back to Costo por resultado when roas is null", () => {
      const offer = makeOffer({ roas: null, primaryCostPerResult: 5.5 });
      const payload = makePayload({ offers: [offer] });
      const { result } = renderHook(() =>
        useResumenViewData({
          metricsByOffer: payload,
          channelData: makeChannelData(),
          selectedOfferId: offer.offerId,
          tenantCurrency: "PEN",
        }),
      );
      const card = result.current.kpis[1];
      expect(card.label).toBe("Costo por resultado");
      expect(card.value).toBeCloseTo(5.5);
      expect(card.tooltipKey).toBe("cost_per_result");
    });

    it("marks all pixel-dependent cards as unavailable when metricUnavailableReason is set", () => {
      const offer = makeOffer({
        metricUnavailableReason: "pixel",
        primaryResultCount: 0,
        primaryCostPerResult: null,
      });
      const payload = makePayload({ offers: [offer] });
      const { result } = renderHook(() =>
        useResumenViewData({
          metricsByOffer: payload,
          channelData: makeChannelData(),
          selectedOfferId: offer.offerId,
          tenantCurrency: "PEN",
        }),
      );
      const view = result.current;
      expect(view.kpis[1].kind).toBe("unavailable");
      expect(view.kpis[2].kind).toBe("unavailable");
      expect(view.kpis[3].kind).toBe("unavailable");
      // CTR and spend are still real values (not pixel dependent)
      expect(view.kpis[0].kind).toBe("value");
      expect(view.kpis[4].kind).toBe("value");
    });

    it('uses the "Compras" copy for purchase-primary offers', () => {
      const offer = makeOffer({
        primaryMetricName: "Compras",
        expectedMetric: "purchase",
      });
      const payload = makePayload({ offers: [offer] });
      const { result } = renderHook(() =>
        useResumenViewData({
          metricsByOffer: payload,
          channelData: makeChannelData(),
          selectedOfferId: offer.offerId,
          tenantCurrency: "PEN",
        }),
      );
      const resultsCard = result.current.kpis[2];
      const costCard = result.current.kpis[3];
      expect(resultsCard.label).toBe("Compras");
      expect(resultsCard.tooltipKey).toBe("results_purchases");
      expect(costCard.label).toBe("CPA");
      expect(costCard.tooltipKey).toBe("cpa");
    });
  });

  describe("filter = branding", () => {
    it("returns branding-specific KPIs", () => {
      const payload = makePayload();
      const { result } = renderHook(() =>
        useResumenViewData({
          metricsByOffer: payload,
          channelData: makeChannelData(),
          selectedOfferId: "branding",
          tenantCurrency: "PEN",
        }),
      );
      const view = result.current;
      expect(view.filter).toBe("branding");
      expect(view.kpis.map((k) => k.key)).toEqual([
        "spend",
        "reach",
        "impressions",
        "cpm",
        "frequency",
        "target_count",
      ]);
      // Reach is null → unavailable
      expect(view.kpis[1].kind).toBe("unavailable");
      // Frequency is null → unavailable
      expect(view.kpis[4].kind).toBe("unavailable");
      // Impressions and CPM are real numbers
      expect(view.kpis[2].value).toBe(20_000);
      expect(view.kpis[3].value).toBe(15);
      // Context label is branding-specific
      expect(view.contextLabel).toContain("branding");
      expect(view.contextLabel).toContain("Foco: alcance");
    });
  });

  describe("filter = unassigned", () => {
    it("returns unassigned-specific KPIs including the CTA card", () => {
      const payload = makePayload();
      const { result } = renderHook(() =>
        useResumenViewData({
          metricsByOffer: payload,
          channelData: makeChannelData(),
          selectedOfferId: "unassigned",
          tenantCurrency: "PEN",
        }),
      );
      const view = result.current;
      expect(view.filter).toBe("unassigned");
      expect(view.kpis).toHaveLength(6);
      expect(view.kpis[5].kind).toBe("cta");
      expect(view.kpis[5].key).toBe("action");
      // Spend = 80
      expect(view.kpis[0].value).toBe(80);
      // Context label mentions how many campaigns
      expect(view.contextLabel).toContain("1 campaña sin offer");
    });
  });

  describe("edge cases", () => {
    it("returns empty state when metricsByOffer is undefined", () => {
      const { result } = renderHook(() =>
        useResumenViewData({
          metricsByOffer: undefined,
          channelData: undefined,
          selectedOfferId: "all",
          tenantCurrency: "USD",
        }),
      );
      expect(result.current.emptyState).toBe(true);
      expect(result.current.kpis).toHaveLength(0);
    });

    it("falls back to EMPTY when a missing offer is requested", () => {
      const payload = makePayload();
      const { result } = renderHook(() =>
        useResumenViewData({
          metricsByOffer: payload,
          channelData: makeChannelData(),
          selectedOfferId: "does-not-exist",
          tenantCurrency: "PEN",
        }),
      );
      expect(result.current.emptyState).toBe(true);
      expect(result.current.kpis).toHaveLength(0);
    });

    it("flags empty state when the whole period has zero spend and zero results", () => {
      const payload = makePayload({
        offers: [],
        unassigned: makeUnassigned({ targetCount: 0, totalSpend: 0 }),
        brandingOnly: makeBranding({ targetCount: 0, totalSpend: 0 }),
      });
      const { result } = renderHook(() =>
        useResumenViewData({
          metricsByOffer: payload,
          channelData: makeChannelData(),
          selectedOfferId: "all",
          tenantCurrency: "PEN",
        }),
      );
      expect(result.current.emptyState).toBe(true);
    });
  });
});
