"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { ExternalLink, Megaphone, Plus } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import { formatMoney } from "@/lib/format-money";
import { useTenantLocale } from "@/features/tenant/context/tenant-locale-context";
import { useOfferCampaigns } from "../../hooks/use-campaigns";
import { useOfferShell } from "../container/offer-shell";
import type {
  CampaignStatusFilter,
  OfferCampaignRow,
  OfferCampaignsKPIs,
  OfferCampaignsQuery,
} from "../../types/campaigns";

const STATUS_FILTERS: { value: CampaignStatusFilter; label: string }[] = [
  { value: "all", label: "Todas" },
  { value: "active", label: "Activas" },
  { value: "paused", label: "Pausadas" },
  { value: "ended", label: "Finalizadas" },
];

const CHANNEL_FILTERS: {
  value: "all" | "meta" | "google" | "tiktok";
  label: string;
}[] = [
  { value: "all", label: "Todos los canales" },
  { value: "meta", label: "Meta" },
  { value: "google", label: "Google" },
  { value: "tiktok", label: "TikTok" },
];

const STATUS_LABEL: Record<string, string> = {
  active: "Activa",
  paused: "Pausada",
  ended: "Finalizada",
  finished: "Finalizada",
};

const STATUS_CLASSES: Record<string, string> = {
  active: "bg-success/15 text-success border-success/30",
  paused: "bg-warning/15 text-warning border-warning/30",
  ended: "bg-muted/40 text-muted-foreground border-border",
  finished: "bg-muted/40 text-muted-foreground border-border",
};

export function CampaignsView({ offerId }: { offerId: string }) {
  const { tenantId } = useOfferShell();
  const [statusFilter, setStatusFilter] = useState<CampaignStatusFilter>("all");
  const [channelFilter, setChannelFilter] = useState<"all" | "meta" | "google" | "tiktok">("all");

  const query = useMemo<OfferCampaignsQuery>(() => {
    const filters: OfferCampaignsQuery = {};
    if (statusFilter !== "all") filters.status = statusFilter;
    if (channelFilter !== "all") filters.channel = channelFilter;
    return filters;
  }, [statusFilter, channelFilter]);

  const { data, isLoading, isError, error, refetch } = useOfferCampaigns(offerId, query);

  return (
    <div className="space-y-5 p-6" role="region" aria-label="Campañas de la oferta">
      <CampaignsKpiRow kpis={data?.kpis} isLoading={isLoading} />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <ChipGroup
            label="Estado"
            value={statusFilter}
            options={STATUS_FILTERS}
            onChange={setStatusFilter}
          />
          <div className="hidden h-5 w-px bg-border md:block" aria-hidden />
          <ChipGroup
            label="Canal"
            value={channelFilter}
            options={CHANNEL_FILTERS}
            onChange={setChannelFilter}
          />
        </div>
        <Button size="sm" asChild>
          <Link href={`/${tenantId}/growth-studio/advertising?offer_id=${offerId}`}>
            <Plus className="mr-1.5 h-3.5 w-3.5" aria-hidden />
            Crear campaña
          </Link>
        </Button>
      </div>

      {isLoading && <CampaignsTableSkeleton />}

      {isError && !isLoading && (
        <Alert variant="destructive">
          <AlertTitle>Error al cargar las campañas</AlertTitle>
          <AlertDescription className="flex items-center justify-between gap-2">
            <span>{error?.message ?? "Intentalo nuevamente."}</span>
            <Button type="button" variant="outline" size="sm" onClick={() => refetch()}>
              Reintentar
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {!isLoading && !isError && data && data.campaigns.length === 0 && (
        <CampaignsEmptyState tenantId={tenantId} offerId={offerId} />
      )}

      {!isLoading && !isError && data && data.campaigns.length > 0 && (
        <CampaignsTable
          rows={data.campaigns}
          tenantId={tenantId}
          fallbackCurrency={data.kpis.currency}
        />
      )}
    </div>
  );
}

// ----------------------------------------------------------- KPIs

interface CampaignsKpiRowProps {
  kpis?: OfferCampaignsKPIs;
  isLoading?: boolean;
}

function CampaignsKpiRow({ kpis, isLoading }: CampaignsKpiRowProps) {
  const { currency: tenantCurrency } = useTenantLocale();
  const currency = kpis?.currency ?? tenantCurrency;

  if (isLoading || !kpis) {
    return (
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {Array.from({ length: 4 }).map((_, idx) => (
          <Skeleton key={idx} className="h-20 rounded-lg" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
      <KpiCard label="Campañas activas" value={String(kpis.active_count)} />
      <KpiCard label="Inversión 7d" value={formatMoney(kpis.spend_7d, currency)} />
      <KpiCard label="Leads 7d" value={String(kpis.leads_7d)} />
      <KpiCard
        label="CPL promedio"
        value={kpis.avg_cpl_7d !== null ? formatMoney(kpis.avg_cpl_7d, currency) : "—"}
      />
    </div>
  );
}

function KpiCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-card/30 p-3">
      <p className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="text-xl font-bold tabular-nums">{value}</p>
    </div>
  );
}

// ----------------------------------------------------------- Table

interface CampaignsTableProps {
  rows: OfferCampaignRow[];
  tenantId: string;
  fallbackCurrency: string | null;
}

function CampaignsTable({ rows, tenantId, fallbackCurrency }: CampaignsTableProps) {
  const { currency: tenantCurrency } = useTenantLocale();

  return (
    <div className="rounded-lg border border-border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Campaña</TableHead>
            <TableHead>Canal</TableHead>
            <TableHead>Estado</TableHead>
            <TableHead className="text-right">Inversión</TableHead>
            <TableHead className="text-right">Leads</TableHead>
            <TableHead className="text-right">CPL</TableHead>
            <TableHead className="w-8" aria-label="Abrir" />
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row) => {
            const rowCurrency = row.currency ?? fallbackCurrency ?? tenantCurrency;
            const statusKey = row.status.toLowerCase();
            const statusLabel = STATUS_LABEL[statusKey] ?? row.status;
            const statusClass = STATUS_CLASSES[statusKey] ?? STATUS_CLASSES.ended;
            const isFinished = statusKey === "ended" || statusKey === "finished";
            return (
              <TableRow key={row.id} className={cn(isFinished && "opacity-60")}>
                <TableCell>
                  <p className={cn("font-medium", isFinished && "line-through")}>{row.name}</p>
                </TableCell>
                <TableCell className="text-xs capitalize">{row.channel}</TableCell>
                <TableCell>
                  <span
                    className={cn(
                      "inline-flex items-center gap-1 rounded border px-2 py-0.5 text-[10px] font-bold uppercase",
                      statusClass,
                    )}
                  >
                    {statusLabel}
                  </span>
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatMoney(row.spend, rowCurrency)}
                </TableCell>
                <TableCell className="text-right tabular-nums">{row.leads}</TableCell>
                <TableCell className="text-right tabular-nums">
                  {row.cpl !== null ? formatMoney(row.cpl, rowCurrency) : "—"}
                </TableCell>
                <TableCell className="text-right">
                  <Button
                    asChild
                    variant="ghost"
                    size="icon"
                    aria-label={`Abrir ${row.name} en Growth Studio`}
                  >
                    <Link
                      href={`/${tenantId}/growth-studio/advertising?campaign_id=${row.id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <ExternalLink className="h-4 w-4 text-muted-foreground" aria-hidden />
                    </Link>
                  </Button>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}

function CampaignsTableSkeleton() {
  return (
    <div className="rounded-lg border border-border p-4" aria-label="Cargando campañas">
      {Array.from({ length: 5 }).map((_, idx) => (
        <div key={idx} className="flex items-center gap-3 py-3">
          <Skeleton className="h-8 w-8 rounded" />
          <Skeleton className="h-4 flex-1" />
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-4 w-16" />
        </div>
      ))}
    </div>
  );
}

function CampaignsEmptyState({ tenantId, offerId }: { tenantId: string; offerId: string }) {
  return (
    <div className="flex flex-col items-center gap-4 rounded-xl border border-dashed p-12 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-border bg-muted/30">
        <Megaphone className="h-8 w-8 text-muted-foreground" aria-hidden />
      </div>
      <div className="space-y-1">
        <h3 className="font-semibold">Sin campañas para esta oferta</h3>
        <p className="max-w-sm text-xs text-muted-foreground">
          Creá una campaña en Advertising Studio para empezar a promocionar esta oferta. Vas a ver
          acá sus métricas e inversión en tiempo real.
        </p>
      </div>
      <Button size="sm" asChild>
        <Link href={`/${tenantId}/growth-studio/advertising?offer_id=${offerId}`}>
          <Plus className="mr-1.5 h-3.5 w-3.5" aria-hidden />
          Crear campaña
        </Link>
      </Button>
    </div>
  );
}

// ----------------------------------------------------------- Chips

interface ChipGroupProps<T extends string> {
  label: string;
  value: T;
  options: { value: T; label: string }[];
  onChange: (value: T) => void;
}

function ChipGroup<T extends string>({ label, value, options, onChange }: ChipGroupProps<T>) {
  return (
    <div className="flex items-center gap-2" role="group" aria-label={label}>
      <span className="text-[10px] font-bold uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
      <div className="flex items-center rounded-md border border-border bg-card p-0.5 text-xs">
        {options.map((opt) => {
          const active = opt.value === value;
          return (
            <button
              type="button"
              key={opt.value}
              onClick={() => onChange(opt.value)}
              aria-pressed={active}
              className={cn(
                "rounded px-2.5 py-1 transition-colors",
                active
                  ? "bg-muted font-medium text-foreground"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              {opt.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
