"use client";

/**
 * Derivation hook for the Meta Ads Resumen tab.
 *
 * Pure, memoised transformation of the `metricsByOffer` payload (+ a fallback
 * `ChannelDashboardData` for the `all` filter's `timeSeries`) into the shape
 * the KPI grid, InversionChart and MetaAdsMiniFunnel actually consume.
 *
 * Source of truth for the filter semantics:
 *   `docs/superpowers/specs/2026-04-10-meta-ads-resumen-offer-filter-design.md`
 *   `docs/superpowers/artifacts/2026-04-10-meta-ads-resumen/UI-SPEC.md` §3.
 *
 * No side effects. No fetch. No side state. The only inputs are the already
 * loaded response and the current segmenter selection.
 */

import { useMemo } from "react";

import type {
  ChannelDashboardData,
  FunnelStep as MiniFunnelStep,
  MetricTimeSeries,
} from "../../../../../types/metrics";
import type {
  BrandingAggregate,
  FunnelStep as OfferFunnelStep,
  MetricsByOffer,
  OfferMetrics,
  UnassignedAggregate,
} from "../../../../../types/offer-association";
import type { OfferSegmenterSelection } from "../OfferSegmenter";

// ---------------------------------------------------------------------------
// Public types
// ---------------------------------------------------------------------------

export type ResumenKpiUnit = "currency" | "count" | "percentage" | "ratio";

export type ResumenKpiKind =
  | "value" // normal value rendered
  | "unavailable" // backend returned null → render "—" with tooltip
  | "cta"; // special action card (only used in the unassigned filter)

export interface ResumenKpiCard {
  /**
   * Stable key inside the grid. Used as React key and for tests that want
   * to assert on a specific card.
   */
  key: string;

  /** Label rendered in uppercase small caps at the top of the card. */
  label: string;

  /**
   * Tooltip key from `RESUMEN_TOOLTIPS`. Cards MUST always declare one —
   * if the card is `unavailable`, the consumer combines the generic tooltip
   * (`unavailable_*`) with this one so the user sees both "what this is"
   * and "why it's empty".
   */
  tooltipKey: string;

  /**
   * Unavailability reason (tooltip key from `RESUMEN_TOOLTIPS`) when
   * `kind === 'unavailable'`. null otherwise.
   */
  unavailableTooltipKey: string | null;

  /**
   * The numeric value, when available. `null` signals the card should
   * render "—" (pair with `kind === 'unavailable'`).
   */
  value: number | null;

  /** ISO 4217 currency code. Used only when `unit === 'currency'`. */
  currency: string;

  /** Display unit — drives the formatter. */
  unit: ResumenKpiUnit;

  /**
   * For delta color semantics:
   *   true  = higher is better (ROAS, CTR, reach, …)
   *   false = lower is better (CPA, CPL, CPM, …)
   *   null  = neutral (no color)
   */
  higherIsBetter: boolean | null;

  /**
   * Delta vs previous period. Null when the backend doesn't provide it
   * (which is every filter except `all` today — see spec open question #2).
   */
  deltaPct: number | null;

  /** One of the shapes described above. */
  kind: ResumenKpiKind;
}

export interface ResumenViewData {
  /** The active filter (mirrors `selectedOfferId`). */
  filter: "all" | "offer" | "branding" | "unassigned";

  /**
   * Human-readable context label for the line under the segmenter
   * and for the screen-reader announcement.
   */
  contextLabel: string;

  /**
   * 6 KPIs in the order specified in UI-SPEC §3 per filter. Always
   * exactly 6 cards — if a metric is unavailable, the slot is still a
   * card with `kind === 'unavailable'`.
   */
  kpis: ResumenKpiCard[];

  /**
   * Time series for the InversionChart. Same shape that the chart
   * already consumes — spend + conversions (or the offer's primary
   * result).
   */
  timeSeries: MetricTimeSeries[];

  /**
   * Funnel adapted to the MetaAdsMiniFunnel component's shape
   * (`FunnelStep` with `conversionRate`, not `conversionRateFromPrevious`).
   */
  funnel: MiniFunnelStep[];

  /**
   * When true, the current filter has no meaningful data to render.
   * Consumers should show the section-level empty states.
   */
  emptyState: boolean;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function toMiniFunnel(steps: OfferFunnelStep[]): MiniFunnelStep[] {
  return steps.map((s) => ({
    label: s.label,
    metricName: s.metricName,
    value: s.value,
    conversionRate: s.conversionRateFromPrevious,
  }));
}

/**
 * Build the {spend, conversions} series the InversionChart expects out of
 * a `OfferMetrics.timeseries`. The chart's "conversions" series is named
 * after the offer's primary metric for display, but keyed `conversions`
 * so the chart's color rules pick it up.
 */
function offerToTimeSeries(offer: OfferMetrics): MetricTimeSeries[] {
  return [
    {
      metricName: "spend",
      displayName: "Inversión",
      unit: "currency",
      dataPoints: offer.timeseries.map((p) => ({ date: p.date, value: p.spend })),
    },
    {
      metricName: "conversions",
      displayName: offer.primaryMetricName,
      unit: offer.primaryMetricUnit,
      dataPoints: offer.timeseries.map((p) => ({
        date: p.date,
        value: p.primaryResult,
      })),
    },
  ];
}

/**
 * Map the offer's primary metric name (from the backend, free-form) to the
 * copy keys and the user-visible "CPL / CPA / Costo por …" label.
 */
interface PrimaryMetricCopy {
  resultsLabel: string;
  resultsTooltipKey: string;
  costLabel: string;
  costTooltipKey: string;
}

function primaryMetricCopy(name: string, fallback: string): PrimaryMetricCopy {
  const lower = name.trim().toLowerCase();
  if (lower.startsWith("lead")) {
    return {
      resultsLabel: "Leads",
      resultsTooltipKey: "results_leads",
      costLabel: "CPL",
      costTooltipKey: "cpl",
    };
  }
  if (lower.startsWith("compra") || lower.startsWith("purchase")) {
    return {
      resultsLabel: "Compras",
      resultsTooltipKey: "results_purchases",
      costLabel: "CPA",
      costTooltipKey: "cpa",
    };
  }
  if (lower.startsWith("mensaje") || lower.startsWith("message")) {
    return {
      resultsLabel: "Mensajes",
      resultsTooltipKey: "results_messages",
      costLabel: "Costo por mensaje",
      costTooltipKey: "cost_per_message",
    };
  }
  if (lower.startsWith("llamada") || lower.startsWith("call")) {
    return {
      resultsLabel: "Llamadas",
      resultsTooltipKey: "results_calls",
      costLabel: "Costo por llamada",
      costTooltipKey: "cost_per_call",
    };
  }
  if (
    lower.startsWith("registro") ||
    lower.startsWith("registration") ||
    lower.startsWith("subscription")
  ) {
    return {
      resultsLabel: "Registros",
      resultsTooltipKey: "results_registrations",
      costLabel: "Costo por registro",
      costTooltipKey: "cost_per_registration",
    };
  }
  if (lower.startsWith("form")) {
    return {
      resultsLabel: "Forms",
      resultsTooltipKey: "results_forms",
      costLabel: "Costo por form",
      costTooltipKey: "cost_per_form",
    };
  }
  // Unknown primary metric — use the backend label verbatim and the generic
  // cost-per-result copy so nothing invents a value.
  return {
    resultsLabel: fallback,
    resultsTooltipKey: "unavailable_metric_not_supported",
    costLabel: "Costo por resultado",
    costTooltipKey: "cost_per_result",
  };
}

// ---------------------------------------------------------------------------
// Card factories
// ---------------------------------------------------------------------------

interface BuildCardArgs {
  key: string;
  label: string;
  tooltipKey: string;
  value: number | null;
  currency: string;
  unit: ResumenKpiUnit;
  higherIsBetter?: boolean | null;
  /**
   * When the value should be rendered as "—" (even if the caller passes a
   * number). Used for the pixel-off case.
   */
  forceUnavailable?: boolean;
  unavailableTooltipKey?: string;
}

function buildCard({
  key,
  label,
  tooltipKey,
  value,
  currency,
  unit,
  higherIsBetter = null,
  forceUnavailable = false,
  unavailableTooltipKey,
}: BuildCardArgs): ResumenKpiCard {
  const isUnavailable = forceUnavailable || value === null;
  return {
    key,
    label,
    tooltipKey,
    unavailableTooltipKey: isUnavailable ? (unavailableTooltipKey ?? "unavailable_generic") : null,
    value: isUnavailable ? null : value,
    currency,
    unit,
    higherIsBetter,
    deltaPct: null, // deltas only arrive from the backend today — open question #2
    kind: isUnavailable ? "unavailable" : "value",
  };
}

// ---------------------------------------------------------------------------
// Per-filter builders
// ---------------------------------------------------------------------------

interface BuildContext {
  currency: string;
  metricsByOffer: MetricsByOffer;
  channelData: ChannelDashboardData | undefined;
}

function buildAllCards(ctx: BuildContext): ResumenKpiCard[] {
  const { metricsByOffer, currency, channelData } = ctx;

  // Aggregate across offers for the "all" view. Unassigned + branding also
  // count towards spend/ctr by definition (they're real campaigns running).
  const { offers } = metricsByOffer;
  const totalSpend =
    offers.reduce((acc, o) => acc + o.totalSpend, 0) +
    metricsByOffer.unassigned.totalSpend +
    metricsByOffer.brandingOnly.totalSpend;
  const totalResults = offers.reduce((acc, o) => acc + o.primaryResultCount, 0);

  // ROAS across offers: weighted by spend. Fall back to null if nothing
  // contributed.
  let roasNumerator = 0;
  let roasDenominator = 0;
  for (const o of offers) {
    if (o.roas != null && o.totalSpend > 0) {
      roasNumerator += o.roas * o.totalSpend;
      roasDenominator += o.totalSpend;
    }
  }
  const avgRoas = roasDenominator > 0 ? roasNumerator / roasDenominator : null;

  // CPA across offers: total spend of offers with primaryCostPerResult /
  // total results. We don't include branding/unassigned because they don't
  // have a primary result concept.
  let cpaSpend = 0;
  let cpaResults = 0;
  for (const o of offers) {
    if (o.primaryCostPerResult != null) {
      cpaSpend += o.totalSpend;
      cpaResults += o.primaryResultCount;
    }
  }
  const avgCpa = cpaResults > 0 ? cpaSpend / cpaResults : null;

  // CTR — for "all", prefer the channel-level KPI (already computed upstream).
  // If it's not there, compute from the aggregate impressions/clicks of all
  // offers + buckets.
  let channelCtr: number | null = null;
  if (channelData) {
    const ctrKpi = channelData.kpis.find((k) => k.metricName === "CTR");
    if (ctrKpi != null) channelCtr = ctrKpi.currentValue;
  }
  if (channelCtr == null) {
    const impressions =
      offers.reduce((acc, o) => acc + o.impressions, 0) +
      metricsByOffer.unassigned.impressions +
      metricsByOffer.brandingOnly.impressions;
    const clicks =
      offers.reduce((acc, o) => acc + o.clicks, 0) +
      metricsByOffer.unassigned.clicks +
      metricsByOffer.brandingOnly.clicks;
    channelCtr = impressions > 0 ? (clicks / impressions) * 100 : 0;
  }

  return [
    buildCard({
      key: "spend",
      label: "Inversión",
      tooltipKey: "spend",
      value: totalSpend,
      currency,
      unit: "currency",
    }),
    buildCard({
      key: "roas",
      label: "ROAS",
      tooltipKey: "roas",
      value: avgRoas,
      currency,
      unit: "ratio",
      higherIsBetter: true,
      unavailableTooltipKey: "unavailable_pixel",
    }),
    buildCard({
      key: "results",
      label: "Resultados",
      tooltipKey: "results_all",
      value: totalResults,
      currency,
      unit: "count",
      higherIsBetter: true,
    }),
    buildCard({
      key: "cpa",
      label: "CPA",
      tooltipKey: "cpa",
      value: avgCpa,
      currency,
      unit: "currency",
      higherIsBetter: false,
      unavailableTooltipKey: "unavailable_pixel",
    }),
    buildCard({
      key: "ctr",
      label: "CTR",
      tooltipKey: "ctr",
      value: channelCtr,
      currency,
      unit: "percentage",
      higherIsBetter: true,
    }),
    buildCard({
      key: "reach",
      label: "Alcance",
      tooltipKey: "reach_all",
      value: metricsByOffer.reachAll,
      currency,
      unit: "count",
      higherIsBetter: true,
      unavailableTooltipKey: "unavailable_period_pending",
    }),
  ];
}

function buildOfferCards(offer: OfferMetrics, ctx: BuildContext): ResumenKpiCard[] {
  const currency = offer.currency || ctx.currency;
  const copy = primaryMetricCopy(offer.primaryMetricName, offer.primaryMetricName);
  const pixelOff = offer.metricUnavailableReason != null;

  // Card #2 — ROAS if present, else Costo por resultado.
  const hasRoas = offer.roas != null;
  const resultCard2: ResumenKpiCard = hasRoas
    ? buildCard({
        key: "roas_or_cost",
        label: "ROAS",
        tooltipKey: "roas",
        value: offer.roas,
        currency,
        unit: "ratio",
        higherIsBetter: true,
        forceUnavailable: pixelOff,
        unavailableTooltipKey: offer.metricUnavailableReason
          ? `unavailable_${offer.metricUnavailableReason}`
          : "unavailable_pixel",
      })
    : buildCard({
        key: "roas_or_cost",
        label: "Costo por resultado",
        tooltipKey: "cost_per_result",
        value: offer.primaryCostPerResult,
        currency,
        unit: "currency",
        higherIsBetter: false,
        forceUnavailable: pixelOff,
        unavailableTooltipKey: offer.metricUnavailableReason
          ? `unavailable_${offer.metricUnavailableReason}`
          : "unavailable_pixel",
      });

  // Card #3 — primary result count (always a real value, 0 is valid).
  const resultsCard: ResumenKpiCard = buildCard({
    key: "results",
    label: copy.resultsLabel,
    tooltipKey: copy.resultsTooltipKey,
    value: pixelOff ? null : offer.primaryResultCount,
    currency,
    unit: "count",
    higherIsBetter: true,
    forceUnavailable: pixelOff,
    unavailableTooltipKey: offer.metricUnavailableReason
      ? `unavailable_${offer.metricUnavailableReason}`
      : "unavailable_pixel",
  });

  // Card #4 — cost-per-result with the metric-specific label.
  const costCard: ResumenKpiCard = buildCard({
    key: "cpa",
    label: copy.costLabel,
    tooltipKey: copy.costTooltipKey,
    value: offer.primaryCostPerResult,
    currency,
    unit: "currency",
    higherIsBetter: false,
    forceUnavailable: pixelOff,
    unavailableTooltipKey: offer.metricUnavailableReason
      ? `unavailable_${offer.metricUnavailableReason}`
      : "unavailable_pixel",
  });

  return [
    buildCard({
      key: "spend",
      label: "Inversión",
      tooltipKey: "spend",
      value: offer.totalSpend,
      currency,
      unit: "currency",
    }),
    resultCard2,
    resultsCard,
    costCard,
    buildCard({
      key: "ctr",
      label: "CTR",
      tooltipKey: "ctr",
      value: offer.ctr,
      currency,
      unit: "percentage",
      higherIsBetter: true,
    }),
    buildCard({
      key: "reach",
      label: "Alcance",
      tooltipKey: "reach_offer",
      value: offer.reach,
      currency,
      unit: "count",
      higherIsBetter: true,
      unavailableTooltipKey: "unavailable_reach_overlap",
    }),
  ];
}

function buildBrandingCards(aggregate: BrandingAggregate, ctx: BuildContext): ResumenKpiCard[] {
  const { currency } = ctx;
  return [
    buildCard({
      key: "spend",
      label: "Inversión",
      tooltipKey: "spend_branding",
      value: aggregate.totalSpend,
      currency,
      unit: "currency",
    }),
    buildCard({
      key: "reach",
      label: "Alcance",
      tooltipKey: "reach_branding",
      value: aggregate.reach,
      currency,
      unit: "count",
      higherIsBetter: true,
      unavailableTooltipKey: "unavailable_reach_overlap",
    }),
    buildCard({
      key: "impressions",
      label: "Impresiones",
      tooltipKey: "impressions",
      value: aggregate.impressions,
      currency,
      unit: "count",
      higherIsBetter: true,
    }),
    buildCard({
      key: "cpm",
      label: "CPM",
      tooltipKey: "cpm",
      value: aggregate.cpm,
      currency,
      unit: "currency",
      higherIsBetter: false,
    }),
    buildCard({
      key: "frequency",
      label: "Frecuencia",
      tooltipKey: "frequency",
      value: aggregate.frequency,
      currency,
      unit: "ratio",
      unavailableTooltipKey: "unavailable_reach_overlap",
    }),
    buildCard({
      key: "target_count",
      label: "Campañas activas",
      tooltipKey: "active_campaigns_branding",
      value: aggregate.targetCount,
      currency,
      unit: "count",
    }),
  ];
}

function buildUnassignedCards(aggregate: UnassignedAggregate, ctx: BuildContext): ResumenKpiCard[] {
  const { currency } = ctx;
  return [
    buildCard({
      key: "spend",
      label: "Inversión",
      tooltipKey: "spend_unassigned",
      value: aggregate.totalSpend,
      currency,
      unit: "currency",
    }),
    buildCard({
      key: "impressions",
      label: "Impresiones",
      tooltipKey: "impressions",
      value: aggregate.impressions,
      currency,
      unit: "count",
    }),
    buildCard({
      key: "clicks",
      label: "Clics",
      tooltipKey: "clicks",
      value: aggregate.clicks,
      currency,
      unit: "count",
    }),
    buildCard({
      key: "ctr",
      label: "CTR",
      tooltipKey: "ctr_unassigned",
      value: aggregate.ctr,
      currency,
      unit: "percentage",
    }),
    buildCard({
      key: "target_count",
      label: "Campañas sin asignar",
      tooltipKey: "unassigned_campaigns",
      value: aggregate.targetCount,
      currency,
      unit: "count",
      higherIsBetter: false,
    }),
    {
      key: "action",
      label: "Acción requerida",
      tooltipKey: "unassigned_campaigns",
      unavailableTooltipKey: null,
      value: null,
      currency,
      unit: "count",
      higherIsBetter: null,
      deltaPct: null,
      kind: "cta",
    },
  ];
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export interface UseResumenViewDataArgs {
  metricsByOffer: MetricsByOffer | undefined;
  channelData: ChannelDashboardData | undefined;
  selectedOfferId: OfferSegmenterSelection;
  tenantCurrency: string;
}

const EMPTY: ResumenViewData = {
  filter: "all",
  contextLabel: "",
  kpis: [],
  timeSeries: [],
  funnel: [],
  emptyState: true,
};

/**
 *
 */
export function useResumenViewData({
  metricsByOffer,
  channelData,
  selectedOfferId,
  tenantCurrency,
}: UseResumenViewDataArgs): ResumenViewData {
  // eslint-disable-next-line sonarjs/cognitive-complexity -- Irreducible: 4-way dispatch (unassigned / branding / specific offer / all) each building a distinct ResumenViewData shape. Each branch already calls a dedicated builder (buildUnassignedCards, buildBrandingCards, buildOfferCards, buildAllCards). The dispatch itself is the irreducible complexity.
  return useMemo<ResumenViewData>(() => {
    if (!metricsByOffer) return EMPTY;

    const ctx: BuildContext = {
      currency: metricsByOffer.currency ?? tenantCurrency,
      metricsByOffer,
      channelData,
    };

    // "Sin asignar" — unassigned aggregate view.
    if (selectedOfferId === "unassigned") {
      const agg = metricsByOffer.unassigned;
      const empty = agg.targetCount === 0 && agg.totalSpend === 0;
      return {
        filter: "unassigned",
        contextLabel: `${agg.targetCount} ${agg.targetCount === 1 ? "campaña sin offer" : "campañas sin offer"} · Asigná cada una para ver métricas por producto`,
        kpis: buildUnassignedCards(agg, ctx),
        timeSeries: channelData?.timeSeries ?? [],
        funnel: toMiniFunnel(agg.funnel),
        emptyState: empty,
      };
    }

    // "Branding" — branding aggregate view.
    if (selectedOfferId === "branding") {
      const agg = metricsByOffer.brandingOnly;
      const empty = agg.targetCount === 0 && agg.totalSpend === 0;
      return {
        filter: "branding",
        contextLabel: `Campañas de branding · ${agg.targetCount} ${agg.targetCount === 1 ? "activa" : "activas"} · Foco: alcance`,
        kpis: buildBrandingCards(agg, ctx),
        timeSeries: channelData?.timeSeries ?? [],
        funnel: toMiniFunnel(agg.funnel),
        emptyState: empty,
      };
    }

    // Specific offer — find and build.
    if (selectedOfferId !== "all") {
      const offer = metricsByOffer.offers.find((o) => o.offerId === selectedOfferId);
      if (!offer) return EMPTY;
      const copy = primaryMetricCopy(offer.primaryMetricName, offer.primaryMetricName);
      const empty =
        offer.totalSpend === 0 && offer.primaryResultCount === 0 && offer.timeseries.length === 0;
      const roasPart = offer.roas != null ? ` · ROAS ${offer.roas.toFixed(2)}x` : "";
      const costPart =
        offer.primaryCostPerResult != null
          ? ` · ${copy.costLabel} ${offer.primaryCostPerResult.toFixed(2)}`
          : "";
      return {
        filter: "offer",
        contextLabel: `${offer.offerName} · Métrica primaria: ${offer.primaryMetricName}${costPart}${roasPart}`,
        kpis: buildOfferCards(offer, ctx),
        timeSeries: offerToTimeSeries(offer),
        funnel: toMiniFunnel(offer.funnel),
        emptyState: empty,
      };
    }

    // Default — "Todas" aggregate view.
    const empty =
      metricsByOffer.offers.length === 0 &&
      metricsByOffer.unassigned.totalSpend === 0 &&
      metricsByOffer.brandingOnly.totalSpend === 0;
    return {
      filter: "all",
      contextLabel: "Todas las offers",
      kpis: buildAllCards(ctx),
      timeSeries: channelData?.timeSeries ?? [],
      funnel: toMiniFunnel(metricsByOffer.funnelAll),
      emptyState: empty,
    };
  }, [metricsByOffer, channelData, selectedOfferId, tenantCurrency]);
}
