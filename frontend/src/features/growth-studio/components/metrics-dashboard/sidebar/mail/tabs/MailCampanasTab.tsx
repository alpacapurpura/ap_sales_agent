"use client";

import { Loader2, ArrowUp, ArrowDown, Star, ChevronDown } from "lucide-react";
import { useState, useMemo } from "react";

import { cn } from "@/lib/utils";

import { useMailCampaigns } from "../../../../../hooks/use-mail-dashboard";
import {
  AUTOMATION_METRIC_INFO,
  type MetricInfo,
} from "../../../../../utils/automation-metric-info";
import { computeCampaignHealthScore } from "../../../../../utils/campaign-health";
import { ChartInfoTooltip } from "../../shared/ChartInfoTooltip";
import { ChartSection } from "../../shared/ChartSection";
import { CampaignDetailSidebar } from "../components/CampaignDetailSidebar";
import { MetricInfoTooltip } from "../components/MetricInfoTooltip";

import type {
  EmailCampaign,
  EmailTypePerformance,
  EmailCampaignSummary,
} from "../../../../../types/mail-types";
import type { MetaAdsPeriod } from "../../../../../types/metrics";

interface MailCampanasTabProps {
  period: MetaAdsPeriod;
}

// Type card colors and icons
const TYPE_CONFIG: Record<
  string,
  {
    icon: string;
    color: string;
    bgClass: string;
    textClass: string;
    borderClass: string;
    tagBg: string;
    tagText: string;
  }
> = {
  newsletter: {
    icon: "\uD83D\uDCF0",
    color: "gray",
    bgClass: "bg-neutral-500/5",
    textClass: "text-neutral-400",
    borderClass: "border-t-neutral-400",
    tagBg: "bg-neutral-500/10",
    tagText: "text-neutral-400",
  },
  lanzamiento: {
    icon: "\uD83D\uDE80",
    color: "purple",
    bgClass: "bg-violet-500/5",
    textClass: "text-violet-400",
    borderClass: "border-t-violet-400",
    tagBg: "bg-violet-500/10",
    tagText: "text-violet-400",
  },
  promocion: {
    icon: "\uD83C\uDF81",
    color: "amber",
    bgClass: "bg-amber-500/5",
    textClass: "text-amber-400",
    borderClass: "border-t-amber-400",
    tagBg: "bg-amber-500/10",
    tagText: "text-amber-400",
  },
  contenido: {
    icon: "\uD83D\uDCDA",
    color: "blue",
    bgClass: "bg-blue-500/5",
    textClass: "text-blue-400",
    borderClass: "border-t-blue-400",
    tagBg: "bg-blue-500/10",
    tagText: "text-blue-400",
  },
  reengagement: {
    icon: "\uD83D\uDC8C",
    color: "red",
    bgClass: "bg-red-500/5",
    textClass: "text-red-400",
    borderClass: "border-t-red-400",
    tagBg: "bg-red-500/10",
    tagText: "text-red-400",
  },
};

const DEFAULT_TYPE_CONFIG = TYPE_CONFIG.newsletter;

// Sort column types
type SortColumn =
  | "campaignName"
  | "campaignType"
  | "sentDate"
  | "emailsSent"
  | "openRate"
  | "clickRate"
  | "clickToOpenRate"
  | "bounceRate"
  | "unsubscribes"
  | "healthScore";

type SortDirection = "asc" | "desc";

const OPEN_RATE_BENCHMARK = 21.5;
const CTOR_BENCHMARK = 10.5;

/**
 *
 */
export function MailCampanasTab({ period }: MailCampanasTabProps) {
  const { data, isLoading } = useMailCampaigns(period);
  const [sortColumn, setSortColumn] = useState<SortColumn>("openRate");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");
  const [activeTypeFilter, setActiveTypeFilter] = useState<string | null>(null);
  const [selectedCampaign, setSelectedCampaign] = useState<EmailCampaign | null>(null);

  const filteredCampaigns = useMemo(() => {
    if (!data) return [];
    let campaigns = [...data.campaigns];
    if (activeTypeFilter) {
      campaigns = campaigns.filter((c) => c.campaignType === activeTypeFilter);
    }
    campaigns.sort((a, b) => {
      // Health score is computed, not a direct field
      if (sortColumn === "healthScore") {
        const aScore = computeCampaignHealthScore(a);
        const bScore = computeCampaignHealthScore(b);
        return sortDirection === "asc" ? aScore - bScore : bScore - aScore;
      }
      const aVal = a[sortColumn];
      const bVal = b[sortColumn];
      if (typeof aVal === "string" && typeof bVal === "string") {
        return sortDirection === "asc" ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
      }
      const aNum = (aVal as number | null) ?? 0;
      const bNum = (bVal as number | null) ?? 0;
      return sortDirection === "asc" ? aNum - bNum : bNum - aNum;
    });
    return campaigns;
  }, [data, activeTypeFilter, sortColumn, sortDirection]);

  const handleSort = (column: SortColumn) => {
    if (sortColumn === column) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortColumn(column);
      setSortDirection("desc");
    }
  };

  const handleRowClick = (campaign: EmailCampaign) => {
    setSelectedCampaign(campaign);
  };

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
        No hay datos de campañas disponibles para este periodo.
      </div>
    );
  }

  return (
    <>
      <div className="space-y-8 max-w-[1200px] mx-auto">
        {/* Section 1: Type Performance Cards */}
        {data.typePerformance.length > 0 && (
          <ChartSection slug="rendimiento-por-tipo">
            <TypePerformanceCards types={data.typePerformance} />
          </ChartSection>
        )}

        {/* Section 2: Horizontal Bar Charts (Open Rate + CTOR by type) */}
        {data.typePerformance.length > 0 && (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <ChartSection slug="open-rate-por-tipo">
              <HorizontalBarChart
                title="Open Rate por Tipo"
                subtitle={`Comparación visual con benchmark de industria (línea naranja = ${OPEN_RATE_BENCHMARK}%)`}
                types={data.typePerformance}
                valueKey="avgOpenRate"
                benchmarkValue={OPEN_RATE_BENCHMARK}
                maxScale={50}
              />
            </ChartSection>

            <ChartSection slug="ctor-por-tipo">
              <HorizontalBarChart
                title="CTOR por Tipo"
                subtitle={`Click-to-Open Rate (benchmark: ${CTOR_BENCHMARK}%)`}
                types={data.typePerformance}
                valueKey="avgCtor"
                benchmarkValue={CTOR_BENCHMARK}
                maxScale={30}
              />
            </ChartSection>
          </div>
        )}

        {/* Section 3: Full Campaign Table */}
        <ChartSection slug="todas-campanas">
          <div className="rounded-lg border bg-card p-5 space-y-4">
            <ChartInfoTooltip
              title="Todas las Campañas"
              description="Ordenar por cualquier columna. Filtrar por tipo."
            />

            {/* Filter Bar */}
            <div className="flex flex-wrap items-center gap-2">
              <FilterButton
                label={`Todas (${data.campaigns.length})`}
                active={activeTypeFilter === null}
                onClick={() => setActiveTypeFilter(null)}
              />
              {data.typePerformance.map((tp) => (
                <FilterButton
                  key={tp.campaignType}
                  label={`${tp.campaignType} (${tp.campaignCount})`}
                  active={activeTypeFilter === tp.campaignType}
                  onClick={() =>
                    setActiveTypeFilter(
                      activeTypeFilter === tp.campaignType ? null : tp.campaignType,
                    )
                  }
                />
              ))}
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
              <CampaignTable
                campaigns={filteredCampaigns}
                sortColumn={sortColumn}
                sortDirection={sortDirection}
                onSort={handleSort}
                onRowClick={handleRowClick}
              />
            </div>
          </div>
        </ChartSection>

        {/* Section 4: Subject Lines + Insights */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {data.topSubjects.length > 0 && (
            <ChartSection slug="mejores-subjects">
              <TopSubjectLines subjects={data.topSubjects} />
            </ChartSection>
          )}

          <ChartSection slug="insights-campanas">
            <CampaignInsights types={data.typePerformance} campaigns={data.campaigns} />
          </ChartSection>
        </div>
      </div>
      <CampaignDetailSidebar
        campaign={selectedCampaign}
        onClose={() => setSelectedCampaign(null)}
      />
    </>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function TypePerformanceCards({ types }: { types: EmailTypePerformance[] }) {
  return (
    <div className="space-y-3">
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
        Rendimiento por Tipo de Email
      </p>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {types.map((tp) => {
          const config = TYPE_CONFIG[tp.campaignType] ?? DEFAULT_TYPE_CONFIG;
          const rankColor = tp.rankLabel.includes("Mejor")
            ? "text-emerald-500"
            : tp.rankLabel.includes("Menor")
              ? "text-red-500"
              : "text-amber-500";

          return (
            <div
              key={tp.campaignType}
              className={cn(
                "rounded-lg border border-t-[3px] p-4 space-y-3",
                config.borderClass,
                config.bgClass,
              )}
            >
              <div>
                <span className="text-lg">{config.icon}</span>
                <p className="mt-1 text-sm font-semibold">{tp.campaignType}</p>
                <p className="text-[11px] text-muted-foreground">
                  {tp.campaignCount} campaña{tp.campaignCount !== 1 ? "s" : ""} &middot;{" "}
                  {tp.totalSent.toLocaleString("en-US")} enviados
                </p>
              </div>

              <div className="space-y-1.5">
                <TypeMetricRow
                  label="Open Rate"
                  value={`${tp.avgOpenRate.toFixed(1)}%`}
                  isGood={tp.avgOpenRate > OPEN_RATE_BENCHMARK}
                />
                <TypeMetricRow
                  label="CTOR"
                  value={`${tp.avgCtor.toFixed(1)}%`}
                  isGood={tp.avgCtor > CTOR_BENCHMARK}
                />
                <TypeMetricRow label="Bajas" value={tp.totalUnsubs.toLocaleString("en-US")} />
              </div>

              <p
                className={cn("text-[10px] font-medium pt-2 border-t border-border/50", rankColor)}
              >
                {tp.rankLabel}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function TypeMetricRow({
  label,
  value,
  isGood,
}: {
  label: string;
  value: string;
  isGood?: boolean;
}) {
  return (
    <div className="flex items-center justify-between text-xs">
      <span className="text-muted-foreground">{label}</span>
      <span
        className={cn(
          "font-semibold tabular-nums",
          isGood === true && "text-emerald-600",
          isGood === false && "text-foreground",
        )}
      >
        {value}
      </span>
    </div>
  );
}

function HorizontalBarChart({
  title,
  subtitle,
  types,
  valueKey,
  benchmarkValue,
  maxScale,
}: {
  title: string;
  subtitle: string;
  types: EmailTypePerformance[];
  valueKey: "avgOpenRate" | "avgCtor";
  benchmarkValue: number;
  maxScale: number;
}) {
  const sorted = [...types].sort((a, b) => b[valueKey] - a[valueKey]);
  const benchPct = (benchmarkValue / maxScale) * 100;

  // Color gradient per type
  const BAR_GRADIENTS: Record<string, string> = {
    newsletter: "from-neutral-600 to-neutral-400",
    lanzamiento: "from-violet-600 to-violet-400",
    promocion: "from-amber-600 to-amber-400",
    contenido: "from-blue-600 to-blue-400",
    reengagement: "from-red-600 to-red-400",
  };

  return (
    <div className="rounded-lg border bg-card p-5 space-y-3">
      <ChartInfoTooltip title={title} description={subtitle} />
      <div className="space-y-3 pt-1">
        {sorted.map((tp) => {
          const value = tp[valueKey];
          const widthPct = Math.min((value / maxScale) * 100, 100);
          const gradientClass = BAR_GRADIENTS[tp.campaignType] ?? BAR_GRADIENTS.newsletter;

          return (
            <div key={tp.campaignType} className="flex items-center gap-3">
              <span className="w-[90px] text-right text-xs text-muted-foreground shrink-0 truncate">
                {tp.campaignType}
              </span>
              <div className="relative flex-1 h-7 rounded-md bg-muted/30 overflow-hidden">
                <div
                  className={cn(
                    "h-full rounded-md bg-gradient-to-r flex items-center px-2.5",
                    gradientClass,
                  )}
                  style={{ width: `${widthPct}%` }}
                >
                  <span className="text-[11px] font-semibold text-white whitespace-nowrap">
                    {value.toFixed(1)}%
                  </span>
                </div>
                {/* Benchmark line */}
                <div
                  className="absolute top-0 bottom-0 w-[2px] bg-amber-500"
                  style={{ left: `${Math.min(benchPct, 100)}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
      {/* Benchmark label */}
      <div className="flex items-center gap-1.5 text-[10px] text-amber-500 pl-[102px]">
        <span className="h-px w-3 bg-amber-500" />
        Benchmark: {benchmarkValue}%
      </div>
    </div>
  );
}

function FilterButton({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-md px-3 py-1.5 text-xs font-medium border transition-colors",
        active
          ? "bg-muted text-foreground border-border"
          : "bg-transparent text-muted-foreground border-border/50 hover:border-border",
      )}
    >
      {label}
    </button>
  );
}

function SortHeader({
  label,
  column,
  sortColumn,
  sortDirection,
  onSort,
  align = "center",
  info,
}: {
  label: string;
  column: SortColumn;
  sortColumn: SortColumn;
  sortDirection: SortDirection;
  onSort: (column: SortColumn) => void;
  align?: "left" | "center" | "right";
  info?: MetricInfo;
}) {
  const isActive = sortColumn === column;
  return (
    <th
      className={cn(
        "py-2 px-2 font-medium cursor-pointer select-none hover:text-foreground transition-colors",
        align === "left" ? "text-left" : align === "right" ? "text-right" : "text-center",
      )}
      onClick={() => onSort(column)}
    >
      <span className="inline-flex items-center gap-0.5">
        {label}
        {info && <MetricInfoTooltip info={info} side="bottom" iconSize="xs" />}
        {isActive ? (
          sortDirection === "desc" ? (
            <ArrowDown className="h-3 w-3 text-amber-500" />
          ) : (
            <ArrowUp className="h-3 w-3 text-amber-500" />
          )
        ) : (
          <ChevronDown className="h-3 w-3 opacity-30" />
        )}
      </span>
    </th>
  );
}

function HealthBar({ score }: { score: number }) {
  const barColor =
    score >= 70
      ? "bg-emerald-500"
      : score >= 40
        ? "bg-amber-500"
        : score > 0
          ? "bg-red-500"
          : "bg-muted-foreground";

  const textColor =
    score >= 70
      ? "text-emerald-500"
      : score >= 40
        ? "text-amber-500"
        : score > 0
          ? "text-red-500"
          : "text-muted-foreground";

  return (
    <div className="flex items-center gap-2 justify-center">
      <div className="h-1.5 w-12 overflow-hidden rounded-full bg-muted/30">
        <div
          className={cn("h-full rounded-full transition-all", barColor)}
          style={{ width: `${score}%` }}
        />
      </div>
      <span className={cn("text-xs font-bold tabular-nums", textColor)}>{score || "\u2014"}</span>
    </div>
  );
}

function CampaignTable({
  campaigns,
  sortColumn,
  sortDirection,
  onSort,
  onRowClick,
}: {
  campaigns: EmailCampaign[];
  sortColumn: SortColumn;
  sortDirection: SortDirection;
  onSort: (column: SortColumn) => void;
  onRowClick: (campaign: EmailCampaign) => void;
}) {
  return (
    <table className="w-full text-[11px]">
      <thead className="text-muted-foreground border-b">
        <tr>
          <th className="py-2 px-2 text-left font-medium w-[5%]">#</th>
          <SortHeader
            label="Campaña"
            column="campaignName"
            sortColumn={sortColumn}
            sortDirection={sortDirection}
            onSort={onSort}
            align="left"
          />
          <th className="py-2 px-2 text-center font-medium">Tipo</th>
          <SortHeader
            label="Fecha"
            column="sentDate"
            sortColumn={sortColumn}
            sortDirection={sortDirection}
            onSort={onSort}
          />
          <SortHeader
            label="Enviados"
            column="emailsSent"
            sortColumn={sortColumn}
            sortDirection={sortDirection}
            onSort={onSort}
            info={AUTOMATION_METRIC_INFO.enviados}
          />
          <SortHeader
            label="Open Rate"
            column="openRate"
            sortColumn={sortColumn}
            sortDirection={sortDirection}
            onSort={onSort}
            info={AUTOMATION_METRIC_INFO.openRate}
          />
          <SortHeader
            label="Click Rate"
            column="clickRate"
            sortColumn={sortColumn}
            sortDirection={sortDirection}
            onSort={onSort}
            info={AUTOMATION_METRIC_INFO.clickRate}
          />
          <SortHeader
            label="CTOR"
            column="clickToOpenRate"
            sortColumn={sortColumn}
            sortDirection={sortDirection}
            onSort={onSort}
            info={AUTOMATION_METRIC_INFO.ctor}
          />
          <SortHeader
            label="Bounces"
            column="bounceRate"
            sortColumn={sortColumn}
            sortDirection={sortDirection}
            onSort={onSort}
            info={AUTOMATION_METRIC_INFO.bounces}
          />
          <SortHeader
            label="Bajas"
            column="unsubscribes"
            sortColumn={sortColumn}
            sortDirection={sortDirection}
            onSort={onSort}
            info={AUTOMATION_METRIC_INFO.unsubs}
          />
          <SortHeader
            label="Salud"
            column="healthScore"
            sortColumn={sortColumn}
            sortDirection={sortDirection}
            onSort={onSort}
            info={AUTOMATION_METRIC_INFO.campaignHealth}
          />
          <th className="py-2 px-2 w-[5%]" />
        </tr>
      </thead>
      <tbody>
        {campaigns.map((campaign, idx) => {
          const config = TYPE_CONFIG[campaign.campaignType] ?? DEFAULT_TYPE_CONFIG;
          const isHighOpen = campaign.openRate > OPEN_RATE_BENCHMARK;
          const isLowOpen = campaign.openRate < OPEN_RATE_BENCHMARK * 0.7;
          const isHighCtor = campaign.clickToOpenRate > CTOR_BENCHMARK;

          // Bar width for Open Rate cell (visual mini bar)
          const openBarWidth = Math.min(campaign.openRate, 50);

          return (
            <tr
              key={campaign.campaignId}
              className="border-b border-border/20 hover:bg-muted/20 transition-colors cursor-pointer"
              onClick={() => onRowClick(campaign)}
            >
              <td className="py-2.5 px-2 text-muted-foreground/60">{idx + 1}</td>
              <td className="py-2.5 px-2 font-medium text-xs max-w-[200px] truncate">
                {campaign.campaignName}
              </td>
              <td className="py-2.5 px-2 text-center">
                <span
                  className={cn(
                    "inline-block rounded-full px-2 py-0.5 text-[10px] font-medium",
                    config.tagBg,
                    config.tagText,
                  )}
                >
                  {campaign.campaignType}
                </span>
              </td>
              <td className="py-2.5 px-2 text-center text-muted-foreground">
                {campaign.sentDate
                  ? new Date(campaign.sentDate).toLocaleDateString("es", {
                      day: "numeric",
                      month: "short",
                    })
                  : "-"}
              </td>
              <td className="py-2.5 px-2 text-center tabular-nums">
                {campaign.emailsSent.toLocaleString("en-US")}
              </td>
              <td className="py-2.5 px-2 text-center">
                <span
                  className={cn(
                    "font-semibold tabular-nums",
                    isHighOpen
                      ? "text-emerald-600"
                      : isLowOpen
                        ? "text-red-500"
                        : "text-foreground",
                  )}
                >
                  {campaign.openRate.toFixed(1)}%
                </span>
                <span
                  className={cn(
                    "inline-block h-1 rounded-sm ml-1.5 align-middle",
                    isHighOpen
                      ? "bg-emerald-500"
                      : isLowOpen
                        ? "bg-red-500"
                        : "bg-muted-foreground/30",
                  )}
                  style={{ width: `${openBarWidth}px` }}
                />
              </td>
              <td
                className={cn(
                  "py-2.5 px-2 text-center tabular-nums",
                  campaign.clickRate > 2.3 && "text-emerald-600",
                )}
              >
                {campaign.clickRate.toFixed(1)}%
              </td>
              <td
                className={cn(
                  "py-2.5 px-2 text-center tabular-nums",
                  isHighCtor && "text-emerald-600",
                )}
              >
                {campaign.clickToOpenRate.toFixed(1)}%
              </td>
              <td
                className={cn(
                  "py-2.5 px-2 text-center tabular-nums",
                  campaign.bounceRate > 2 && "text-amber-600",
                )}
              >
                {campaign.bounceRate.toFixed(1)}%
              </td>
              <td className="py-2.5 px-2 text-center tabular-nums">{campaign.unsubscribes}</td>
              <td className="py-2.5 px-2">
                <HealthBar score={computeCampaignHealthScore(campaign)} />
              </td>
              <td className="py-2.5 px-2 text-center">
                {idx === 0 && sortColumn === "openRate" && sortDirection === "desc" && (
                  <Star className="h-3 w-3 text-emerald-500 inline" />
                )}
                {idx === campaigns.length - 1 &&
                  sortColumn === "openRate" &&
                  sortDirection === "desc" &&
                  campaigns.length > 1 && <ArrowDown className="h-3 w-3 text-red-500 inline" />}
              </td>
            </tr>
          );
        })}
        {campaigns.length === 0 && (
          <tr>
            <td colSpan={12} className="py-8 text-center text-sm text-muted-foreground">
              No hay campañas para este filtro.
            </td>
          </tr>
        )}
      </tbody>
    </table>
  );
}

function TopSubjectLines({ subjects }: { subjects: EmailCampaignSummary[] }) {
  return (
    <div className="rounded-lg border bg-card p-5 space-y-3">
      <ChartInfoTooltip
        title="Mejores Subject Lines"
        description="Top asuntos por tasa de apertura. Analiza los patrones para replicar el éxito."
      />
      <div className="space-y-2 pt-1">
        {subjects.slice(0, 5).map((subject, idx) => {
          const isTop = idx < 2;
          return (
            <div
              key={`${subject.campaignName}-${idx}`}
              className={cn(
                "flex items-center gap-3 rounded-md p-2.5",
                "bg-muted/20 border-l-[3px]",
                isTop ? "border-emerald-500" : "border-muted-foreground/20",
              )}
            >
              <span className="text-[11px] text-muted-foreground/60 w-5 shrink-0 text-center">
                {idx + 1}
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold truncate">
                  {subject.campaignSubject ?? subject.campaignName}
                </p>
                <p className="text-[10px] text-muted-foreground mt-0.5">
                  {subject.campaignType}
                  {subject.sentDate && (
                    <>
                      {" "}
                      &middot;{" "}
                      {new Date(subject.sentDate).toLocaleDateString("es", {
                        day: "numeric",
                        month: "short",
                      })}
                    </>
                  )}
                </p>
              </div>
              <div className="text-right shrink-0">
                <p
                  className={cn(
                    "text-base font-bold tabular-nums",
                    isTop ? "text-emerald-600" : "text-foreground",
                  )}
                >
                  {subject.openRate.toFixed(1)}%
                </p>
                <p className="text-[10px] text-muted-foreground">apertura</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function CampaignInsights({
  types,
  campaigns,
}: {
  types: EmailTypePerformance[];
  campaigns: EmailCampaign[];
}) {
  const insights: { text: string; type: "positive" | "warning" }[] = [];

  // Best type vs worst type
  if (types.length >= 2) {
    const sorted = [...types].sort((a, b) => b.avgOpenRate - a.avgOpenRate);
    const best = sorted[0];
    const worst = sorted[sorted.length - 1];
    if (best.avgOpenRate > worst.avgOpenRate * 1.3) {
      const ratio = (best.avgOpenRate / worst.avgOpenRate).toFixed(1);
      insights.push({
        text: `Los emails de "${best.campaignType}" obtienen ${ratio}x más engagement que los "${worst.campaignType}". Considere reducir frecuencia de ${worst.campaignType} o mejorar sus subject lines.`,
        type: "positive",
      });
    }
  }

  // Campaigns below benchmark
  const belowBenchmark = campaigns.filter((c) => c.openRate < OPEN_RATE_BENCHMARK);
  if (belowBenchmark.length > 0 && campaigns.length > 0) {
    const pct = ((belowBenchmark.length / campaigns.length) * 100).toFixed(0);
    insights.push({
      text: `${pct}% de las campañas (${belowBenchmark.length} de ${campaigns.length}) están por debajo del benchmark de apertura (${OPEN_RATE_BENCHMARK}%). Revise segmentación y subject lines.`,
      type: "warning",
    });
  }

  // High unsubs in any type
  const highUnsubs = types.filter((t) => t.totalUnsubs > 5);
  if (highUnsubs.length > 0) {
    const names = highUnsubs.map((t) => t.campaignType).join(", ");
    insights.push({
      text: `Tipos con bajas elevadas: ${names}. Revise frecuencia de envío y relevancia del contenido.`,
      type: "warning",
    });
  }

  if (insights.length === 0) {
    insights.push({
      text: "El rendimiento general de las campañas es saludable. Mantén la estrategia actual y experimenta con nuevos formatos.",
      type: "positive",
    });
  }

  return (
    <div className="rounded-lg border bg-card p-5 space-y-3">
      <ChartInfoTooltip
        title="Insights de Campañas"
        description="Hallazgos automáticos basados en los datos del periodo seleccionado."
      />
      <div className="space-y-2 pt-1">
        {insights.map((insight, idx) => (
          <div
            key={idx}
            className={cn(
              "rounded-md border-l-[3px] px-3 py-2.5 bg-muted/20",
              insight.type === "positive" ? "border-emerald-500" : "border-amber-500",
            )}
          >
            <p className="text-xs text-muted-foreground leading-relaxed">
              <span
                className={cn(
                  "font-semibold",
                  insight.type === "positive" ? "text-emerald-600" : "text-amber-600",
                )}
              >
                {insight.type === "positive" ? "Hallazgo:" : "Alerta:"}
              </span>{" "}
              {insight.text}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
