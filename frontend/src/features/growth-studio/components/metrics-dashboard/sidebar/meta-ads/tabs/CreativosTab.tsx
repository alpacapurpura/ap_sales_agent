"use client";

import { useState, useCallback } from "react";
import { Clock, ExternalLink, Film, Image, Loader2 } from "lucide-react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";

import { cn } from "@/lib/utils";
import { formatMoney } from "@/lib/format-money";
import {
  DetailPanel,
  DetailPanelHeader,
  DetailPanelTitle,
  DetailPanelClose,
} from "@/components/ui/detail-panel";
import { ChartSection } from "../../shared/ChartSection";
import {
  useCreativesOverview,
  useAdPerformance,
  useFormatComparison,
} from "../../../../../api/campaigns-api";
import type { AdMetrics, FormatComparisonItem } from "../../../../../api/campaigns-api";
import type { ChannelDashboardData, MetaAdsPeriod } from "../../../../../types/metrics";

interface CreativosTabProps {
  data: ChannelDashboardData | undefined;
  isLoading: boolean;
  period?: MetaAdsPeriod;
}

// ── Helpers ──────────────────────────────────────────────────────────

function formatCompact(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}k`;
  return value.toFixed(0);
}

function roasColor(roas: number | null): string {
  if (roas == null) return "text-muted-foreground";
  if (roas >= 3) return "text-emerald-400";
  if (roas >= 1) return "text-amber-400";
  return "text-red-400";
}

function performanceTagLabel(tag: string): { label: string; className: string } {
  switch (tag) {
    case "top_performer":
      return { label: "Top performer", className: "bg-emerald-500/10 text-emerald-400" };
    case "underperformer":
      return { label: "Peor rendimiento", className: "bg-red-500/10 text-red-400" };
    default:
      return { label: "", className: "" };
  }
}

function formatTypeBadge(formatType: string): {
  label: string;
  icon: typeof Film;
  className: string;
} {
  switch (formatType) {
    case "video":
      return { label: "Video", icon: Film, className: "bg-blue-500/10 text-blue-400" };
    case "carousel":
      return { label: "Carrusel", icon: Image, className: "bg-purple-500/10 text-purple-400" };
    case "image":
    default:
      return { label: "Imagen", icon: Image, className: "bg-zinc-500/10 text-zinc-400" };
  }
}

function statusDot(status: string | null): string {
  switch (status) {
    case "ACTIVE":
      return "bg-emerald-400";
    case "PAUSED":
    case "CAMPAIGN_PAUSED":
      return "bg-amber-400";
    default:
      return "bg-zinc-400";
  }
}

function ctaLabel(cta: string | null): string | null {
  if (!cta) return null;
  const labels: Record<string, string> = {
    LEARN_MORE: "Más info",
    SHOP_NOW: "Comprar",
    SIGN_UP: "Registrarse",
    VIEW_INSTAGRAM_PROFILE: "Ver perfil",
    WATCH_MORE: "Ver más",
    CONTACT_US: "Contactar",
    SEND_MESSAGE: "Mensaje",
    BOOK_NOW: "Reservar",
    DOWNLOAD: "Descargar",
    GET_OFFER: "Ver oferta",
  };
  return labels[cta] ?? cta.replace(/_/g, " ").toLowerCase();
}

// ── Ad Card ──────────────────────────────────────────────────────────

function AdCard({
  ad,
  currency,
  onSelect,
}: {
  ad: AdMetrics;
  currency: string;
  onSelect: (ad: AdMetrics) => void;
}) {
  const isUnderperformer = ad.performanceTag === "underperformer";
  const tagInfo = performanceTagLabel(ad.performanceTag);
  const formatInfo = formatTypeBadge(ad.formatType);
  const FormatIcon = formatInfo.icon;
  const cta = ctaLabel(ad.creativeCta);

  // Smart KPIs: show metrics that have data
  const hasConversions = ad.conversions > 0;
  const kpis = hasConversions
    ? [
        {
          label: "ROAS",
          value: ad.roas != null ? `${ad.roas.toFixed(1)}x` : "-",
          color: roasColor(ad.roas),
        },
        { label: "Ventas", value: formatCompact(ad.conversions), color: "" },
        { label: "CPA", value: ad.cpa != null ? formatMoney(ad.cpa, currency) : "-", color: "" },
      ]
    : [
        { label: "Gasto", value: formatMoney(ad.spend, currency), color: "" },
        {
          label: "CTR",
          value: ad.ctr != null ? `${ad.ctr.toFixed(1)}%` : "-",
          color: ad.ctr != null && ad.ctr >= 2 ? "text-emerald-400" : "",
        },
        { label: "CPC", value: ad.cpc != null ? formatMoney(ad.cpc, currency) : "-", color: "" },
      ];

  return (
    <button
      type="button"
      onClick={() => onSelect(ad)}
      className={cn(
        "rounded-xl border bg-card p-3 space-y-2.5 text-left transition-colors hover:border-primary/30 hover:bg-accent/30 w-full",
        isUnderperformer && "border-red-500/20",
      )}
    >
      {/* Thumbnail */}
      {ad.thumbnailUrl ? (
        /* eslint-disable-next-line @next/next/no-img-element */
        <img
          src={ad.thumbnailUrl}
          alt={ad.adName}
          className="h-32 w-full rounded-lg object-cover"
        />
      ) : (
        <div className="h-32 rounded-lg bg-muted flex items-center justify-center text-xs text-muted-foreground">
          Sin preview
        </div>
      )}

      {/* Format + Status row */}
      <div className="flex items-center gap-1.5">
        <span
          className={cn(
            "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[9px]",
            formatInfo.className,
          )}
        >
          <FormatIcon className="h-2.5 w-2.5" />
          {formatInfo.label}
        </span>
        <span className={cn("h-1.5 w-1.5 rounded-full", statusDot(ad.effectiveStatus))} />
        {cta && (
          <span className="rounded-full bg-muted px-2 py-0.5 text-[9px] text-muted-foreground">
            {cta}
          </span>
        )}
      </div>

      {/* Name + Campaign */}
      <div>
        <p className="text-xs font-medium truncate">{ad.adName}</p>
        <p className="text-[10px] text-muted-foreground truncate">
          {ad.campaignName ?? "Sin campa\u00f1a"}
        </p>
      </div>

      {/* Copy preview */}
      {ad.creativeBody && (
        <p className="text-[10px] text-muted-foreground line-clamp-2 leading-relaxed italic">
          &ldquo;{ad.creativeBody}&rdquo;
        </p>
      )}

      {/* KPIs Grid */}
      <div className="grid grid-cols-3 gap-2 text-center">
        {kpis.map((kpi) => (
          <div key={kpi.label}>
            <p className="text-[9px] text-muted-foreground">{kpi.label}</p>
            <p className={cn("text-sm font-bold tabular-nums", kpi.color)}>{kpi.value}</p>
          </div>
        ))}
      </div>

      {/* Badges */}
      <div className="flex items-center justify-between">
        <div>
          {tagInfo.label && (
            <span className={cn("rounded-full px-2 py-0.5 text-[9px]", tagInfo.className)}>
              {tagInfo.label}
            </span>
          )}
        </div>
        <span className="text-[9px] text-primary/60">Ver detalle &rarr;</span>
      </div>
    </button>
  );
}

// ── Ad Detail Panel (Sidebar) ───────────────────────────────────────

function AdDetailPanel({
  ad,
  currency,
  open,
  onClose,
}: {
  ad: AdMetrics | null;
  currency: string;
  open: boolean;
  onClose: () => void;
}) {
  if (!ad) return null;

  const formatInfo = formatTypeBadge(ad.formatType);
  const FormatIcon = formatInfo.icon;
  const cta = ctaLabel(ad.creativeCta);
  const hasConversions = ad.conversions > 0;

  const allMetrics = [
    { label: "Gasto total", value: formatMoney(ad.spend, currency) },
    { label: "Impresiones", value: formatCompact(ad.impressions) },
    { label: "Clicks", value: formatCompact(ad.clicks) },
    { label: "CTR", value: ad.ctr != null ? `${ad.ctr.toFixed(2)}%` : "-" },
    { label: "CPC", value: ad.cpc != null ? formatMoney(ad.cpc, currency) : "-" },
    ...(hasConversions
      ? [
          { label: "Conversiones", value: formatCompact(ad.conversions) },
          { label: "ROAS", value: ad.roas != null ? `${ad.roas.toFixed(2)}x` : "-" },
          { label: "CPA", value: ad.cpa != null ? formatMoney(ad.cpa, currency) : "-" },
        ]
      : []),
  ];

  return (
    <DetailPanel open={open} onClose={onClose} size="md">
      {/* Header */}
      <DetailPanelHeader>
        <div className="flex items-center justify-between">
          <DetailPanelTitle className="truncate pr-4">{ad.adName}</DetailPanelTitle>
          <div className="flex items-center gap-2 shrink-0">
            {ad.previewUrl && (
              <a
                href={ad.previewUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1 text-xs hover:bg-accent transition-colors"
              >
                <ExternalLink className="h-3 w-3" />
                Ver en Meta
              </a>
            )}
            <DetailPanelClose onClose={onClose} />
          </div>
        </div>
      </DetailPanelHeader>

      <div className="space-y-5 p-6">
        {/* Full preview image */}
        {ad.thumbnailUrl && (
          /* eslint-disable-next-line @next/next/no-img-element */
          <img
            src={ad.thumbnailUrl}
            alt={ad.adName}
            className="w-full rounded-lg object-cover max-h-[300px]"
          />
        )}

        {/* Format + Status + CTA */}
        <div className="flex items-center gap-2 flex-wrap">
          <span
            className={cn(
              "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs",
              formatInfo.className,
            )}
          >
            <FormatIcon className="h-3 w-3" />
            {formatInfo.label}
          </span>
          <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
            <span className={cn("h-2 w-2 rounded-full", statusDot(ad.effectiveStatus))} />
            {ad.effectiveStatus?.replace(/_/g, " ") ?? "Desconocido"}
          </span>
          {cta && (
            <span className="rounded-full bg-muted px-2.5 py-1 text-xs text-muted-foreground">
              CTA: {cta}
            </span>
          )}
        </div>

        {/* Campaign */}
        <div>
          <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-0.5">
            Campa\u00f1a
          </p>
          <p className="text-sm">{ad.campaignName ?? "Sin campa\u00f1a"}</p>
        </div>

        {/* Creative Body (full copy) */}
        {ad.creativeBody && (
          <div>
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">
              Copy del anuncio
            </p>
            <div className="rounded-lg border bg-muted/30 p-3">
              <p className="text-sm leading-relaxed whitespace-pre-line">{ad.creativeBody}</p>
            </div>
          </div>
        )}

        {/* Performance Metrics */}
        <div>
          <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-2">
            M\u00e9tricas de rendimiento
          </p>
          <div className="grid grid-cols-3 gap-3">
            {allMetrics.map((metric) => (
              <div key={metric.label} className="rounded-lg border bg-card p-2.5">
                <p className="text-[10px] text-muted-foreground">{metric.label}</p>
                <p className="text-lg font-bold tabular-nums mt-0.5">{metric.value}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Performance tag */}
        {ad.performanceTag !== "average" && (
          <div className="pt-1">
            {(() => {
              const tag = performanceTagLabel(ad.performanceTag);
              return tag.label ? (
                <span className={cn("rounded-full px-3 py-1 text-xs", tag.className)}>
                  {tag.label}
                </span>
              ) : null;
            })()}
          </div>
        )}
      </div>
    </DetailPanel>
  );
}

// ── Format Comparison Row ────────────────────────────────────────────

function FormatRow({ format, currency }: { format: FormatComparisonItem; currency: string }) {
  const scoreColor =
    format.performanceScore >= 70
      ? "bg-emerald-500/60"
      : format.performanceScore >= 40
        ? "bg-amber-500/60"
        : "bg-red-500/60";

  const valueColor =
    format.performanceScore >= 70
      ? "text-emerald-400"
      : format.performanceScore >= 40
        ? "text-amber-400"
        : "text-red-400";

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm">{format.emoji}</span>
          <span className="text-xs">{format.formatType}</span>
        </div>
        <div className="flex items-center gap-4 text-xs tabular-nums">
          <span>
            CTR <strong className={valueColor}>{(format.avgCtr * 100).toFixed(1)}%</strong>
          </span>
          <span>
            CPA{" "}
            <strong className={valueColor}>
              {format.avgCpa != null ? formatMoney(format.avgCpa, currency) : "-"}
            </strong>
          </span>
          <span>
            ROAS{" "}
            <strong className={valueColor}>
              {format.avgRoas != null ? `${format.avgRoas.toFixed(1)}x` : "-"}
            </strong>
          </span>
        </div>
      </div>
      <div className="w-full rounded-full bg-muted h-2">
        <div
          className={cn("h-2 rounded-full", scoreColor)}
          style={{ width: `${Math.min(format.performanceScore, 100)}%` }}
        />
      </div>
    </div>
  );
}

// ── Main Component ──────────────────────────────────────────────────

export function CreativosTab({ data, isLoading, period }: CreativosTabProps) {
  const activePeriod = period ?? "30d";
  const { data: creatives } = useCreativesOverview(activePeriod);
  const { data: adPerf, isLoading: isAdPerfLoading } = useAdPerformance(activePeriod, 3);
  const { data: formatComp } = useFormatComparison(activePeriod);

  // URL-addressable sidebar
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const adParam = searchParams.get("ad");

  // Manual selection overrides URL param; URL param provides initial state
  const [manualAdId, setManualAdId] = useState<string | null>(null);
  const activeAdId = manualAdId ?? adParam;

  const selectedAd =
    activeAdId && adPerf?.ads ? (adPerf.ads.find((a) => a.adId === activeAdId) ?? null) : null;

  const panelOpen = selectedAd !== null;

  const handleSelectAd = useCallback(
    (ad: AdMetrics) => {
      setManualAdId(ad.adId);
      const params = new URLSearchParams(searchParams.toString());
      params.set("ad", ad.adId);
      router.replace(`${pathname}?${params.toString()}`, { scroll: false });
    },
    [searchParams, router, pathname],
  );

  const handleClosePanel = useCallback(() => {
    setManualAdId(null);
    const params = new URLSearchParams(searchParams.toString());
    params.delete("ad");
    router.replace(`${pathname}?${params.toString()}`, { scroll: false });
  }, [searchParams, router, pathname]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="py-24 text-center text-sm text-muted-foreground">
        No hay datos disponibles
      </div>
    );
  }

  const topAds = adPerf?.ads ?? [];
  const formats = formatComp?.formats ?? [];
  const retention = creatives?.videoRetention;
  const hasRetention = retention && retention.plays > 0;
  const currency = adPerf?.currency ?? formatComp?.currency ?? "USD";

  return (
    <div className="space-y-6">
      {/* ── Top Anuncios por Rendimiento ─────────────────────────── */}
      <ChartSection slug="top-creativos">
        <div>
          <h3 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3">
            Top anuncios por rendimiento
          </h3>

          {isAdPerfLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : topAds.length > 0 ? (
            <div className="grid grid-cols-3 gap-3">
              {topAds.map((ad) => (
                <AdCard key={ad.adId} ad={ad} currency={currency} onSelect={handleSelectAd} />
              ))}
            </div>
          ) : (
            <div className="rounded-lg border bg-card p-8 text-center text-sm text-muted-foreground">
              <Film className="h-8 w-8 mx-auto mb-2 opacity-40" />
              <p className="font-medium">Sin datos de rendimiento por anuncio</p>
              <p className="mt-1 text-xs">
                Los datos aparecerán cuando haya anuncios activos con métricas de rendimiento.
              </p>
            </div>
          )}
        </div>
      </ChartSection>

      {/* ── 2-Column: Format Comparison + Video Retention ────────── */}
      <div className="grid grid-cols-2 gap-4">
        {/* Format Comparison */}
        <ChartSection slug="comparacion-formato">
          <div>
            <h3 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3">
              Rendimiento por formato
            </h3>
            <div className="rounded-lg border bg-card p-4 space-y-3">
              {formats.length > 0 ? (
                formats.map((fmt) => (
                  <FormatRow key={fmt.formatType} format={fmt} currency={currency} />
                ))
              ) : (
                <p className="py-4 text-center text-xs text-muted-foreground">
                  Sin datos de formatos disponibles
                </p>
              )}
            </div>
          </div>
        </ChartSection>

        {/* Video Retention */}
        <ChartSection slug="retencion-video">
          <div>
            <h3
              className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3"
              title="Cu\u00e1ntas personas ven tu video hasta cada punto. Ideal: >30% completa el video."
            >
              Retenci&oacute;n de video
            </h3>
            {hasRetention ? (
              <div className="rounded-lg border bg-card p-4">
                <div className="flex items-end gap-2 h-[180px] px-2">
                  {[
                    { label: "Play", value: retention.plays, pct: 100 },
                    {
                      label: "25%",
                      value: retention.p25,
                      pct: (retention.p25 / retention.plays) * 100,
                    },
                    {
                      label: "50%",
                      value: retention.p50,
                      pct: (retention.p50 / retention.plays) * 100,
                    },
                    {
                      label: "75%",
                      value: retention.p75,
                      pct: (retention.p75 / retention.plays) * 100,
                    },
                    {
                      label: "100%",
                      value: retention.p100,
                      pct: (retention.p100 / retention.plays) * 100,
                    },
                  ].map((step, i) => (
                    <div key={step.label} className="flex-1 flex flex-col items-center gap-1">
                      <p className="text-[10px] font-semibold tabular-nums">
                        {formatCompact(step.value)}
                      </p>
                      <div
                        className={cn(
                          "w-full rounded-t",
                          i === 4
                            ? "bg-emerald-500/50"
                            : i >= 3
                              ? "bg-amber-500/40"
                              : "bg-blue-500/50",
                        )}
                        style={{ height: `${Math.max(step.pct * 1.6, 4)}px` }}
                      />
                      <p className="text-[9px] text-muted-foreground">{step.label}</p>
                      {i > 0 && <p className="text-[8px] text-blue-400">{step.pct.toFixed(0)}%</p>}
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="rounded-lg border bg-card p-8 text-center text-sm text-muted-foreground">
                <p className="font-medium">Pr&oacute;ximamente</p>
                <p className="mt-1 text-xs">
                  Gr&aacute;fico de retenci&oacute;n: Play &rarr; 25% &rarr; 50% &rarr; 75% &rarr;
                  100% completado.
                </p>
              </div>
            )}
          </div>
        </ChartSection>
      </div>

      {/* ── Video KPIs (only if retention data exists) ────────────── */}
      {hasRetention && (
        <div className="grid grid-cols-4 gap-2.5">
          <div className="rounded-lg border bg-card p-3">
            <p className="text-[10px] text-muted-foreground">Video Views</p>
            <p className="text-xl font-bold tabular-nums mt-1">{formatCompact(retention.plays)}</p>
          </div>
          <div className="rounded-lg border bg-card p-3">
            <p className="text-[10px] text-muted-foreground">Vistas 30s+</p>
            <p className="text-xl font-bold tabular-nums mt-1">
              {formatCompact(retention.views30s ?? retention.p50)}
            </p>
          </div>
          <div className="rounded-lg border bg-card p-3">
            <p className="text-[10px] text-muted-foreground">Completados</p>
            <p className="text-xl font-bold tabular-nums mt-1">{formatCompact(retention.p100)}</p>
            <p className="text-[9px] text-emerald-500">
              {((retention.p100 / retention.plays) * 100).toFixed(0)}% completion rate
            </p>
          </div>
          <div className="rounded-lg border bg-card p-3">
            <p className="text-[10px] text-muted-foreground">
              <Clock className="mr-1 inline h-3 w-3" />
              Duraci&oacute;n promedio
            </p>
            <p className="text-xl font-bold tabular-nums mt-1">
              {retention.avgWatchTime != null && retention.avgWatchTime > 0
                ? `${retention.avgWatchTime.toFixed(0)}s`
                : `${((retention.p75 / retention.plays) * 100).toFixed(0)}%`}
            </p>
            {retention.avgWatchTime != null && retention.avgWatchTime > 0 && (
              <p className="text-[9px] text-muted-foreground">tiempo promedio de vista</p>
            )}
          </div>
        </div>
      )}

      {/* ── Ad Detail Sidebar ────────────────────────────────────── */}
      <AdDetailPanel
        ad={selectedAd}
        currency={currency}
        open={panelOpen}
        onClose={handleClosePanel}
      />
    </div>
  );
}
