"use client";

import { useMemo } from "react";

import { Button } from "@/components/ui/button";
import { useEnrollments } from "@/features/closer-studio/hooks/use-enrollments";
import { EnrollmentStatus, type Enrollment } from "@/features/closer-studio/types/enrollment";
import { cn } from "@/lib/utils";

export interface OfferVentasTabProps {
  offerId: string;
  /** Currently-selected edition id (null when none — we list offer-wide). */
  currentEditionId: string | null;
  tenantId: string;
}

function formatMoney(amount: number | null, currency: string | null): string {
  if (amount == null) return "—";
  return new Intl.NumberFormat("es-PE", {
    style: "currency",
    currency: currency ?? "USD",
    maximumFractionDigits: 0,
  }).format(amount);
}

const STATUS_STYLES: Record<EnrollmentStatus, string> = {
  [EnrollmentStatus.INTENT]: "bg-muted text-muted-foreground",
  [EnrollmentStatus.WAITLIST]: "bg-purple-100 text-purple-700",
  [EnrollmentStatus.PAYMENT_PENDING]: "bg-amber-100 text-amber-700",
  [EnrollmentStatus.PAID]: "bg-emerald-100 text-emerald-700",
  [EnrollmentStatus.ATTENDED]: "bg-blue-100 text-blue-700",
  [EnrollmentStatus.REFUNDED]: "bg-red-100 text-red-700",
  [EnrollmentStatus.CANCELLED]: "bg-muted text-muted-foreground",
};

const STATUS_LABELS: Record<EnrollmentStatus, string> = {
  [EnrollmentStatus.INTENT]: "Intención",
  [EnrollmentStatus.WAITLIST]: "Waitlist",
  [EnrollmentStatus.PAYMENT_PENDING]: "Pendiente",
  [EnrollmentStatus.PAID]: "Pagada",
  [EnrollmentStatus.ATTENDED]: "Asistió",
  [EnrollmentStatus.REFUNDED]: "Reembolsada",
  [EnrollmentStatus.CANCELLED]: "Cancelada",
};

/**
 * Offer Studio → Ventas tab.
 *
 * KPI strip + table of enrollments scoped to the active edition (when
 * one is selected) or offer-wide otherwise. Deep links to the global
 * Closer Studio view for richer operational controls.
 */
export function OfferVentasTab({ offerId, currentEditionId, tenantId }: OfferVentasTabProps) {
  const filters = useMemo(
    () => ({
      offer_id: offerId,
      ...(currentEditionId ? { edition_id: currentEditionId } : {}),
    }),
    [offerId, currentEditionId],
  );
  const { data, isLoading, error } = useEnrollments(filters);
  const items = data?.items ?? [];

  const paid = items.filter((e) => e.status === EnrollmentStatus.PAID);
  const pending = items.filter((e) => e.status === EnrollmentStatus.PAYMENT_PENDING);
  const waitlist = items.filter((e) => e.status === EnrollmentStatus.WAITLIST);
  const revenue = paid.reduce((acc, e) => acc + (e.pricing_amount ?? 0), 0);
  const currency = items.find((e) => e.currency)?.currency ?? null;

  const closerHref = currentEditionId
    ? `/${tenantId}/sales/enrollments?offer_id=${offerId}&edition_id=${currentEditionId}`
    : `/${tenantId}/sales/enrollments?offer_id=${offerId}`;

  return (
    <div className="space-y-5 px-8 py-5">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
        <Kpi label="Inscriptos" value={items.length} />
        <Kpi label="Pagadas" value={paid.length} color="emerald" />
        <Kpi label="Pendientes" value={pending.length} color="amber" />
        <Kpi label="Revenue" value={formatMoney(revenue, currency)} />
        <Kpi label="Waitlist" value={waitlist.length} color="purple" />
      </div>

      {isLoading ? <LoadingState /> : null}
      {error ? <ErrorState message={error.message} /> : null}
      {!isLoading && !error && items.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="overflow-hidden rounded-xl border bg-background">
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/40 text-xs text-muted-foreground">
              <tr>
                <th className="p-3 text-left font-medium">Contacto</th>
                <th className="p-3 text-left font-medium">Estado</th>
                <th className="p-3 text-left font-medium">Tier</th>
                <th className="p-3 text-left font-medium">Monto</th>
                <th className="p-3 text-left font-medium">Pagado</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {items.map((enrollment) => (
                <EnrollmentRow key={enrollment.id} enrollment={enrollment} />
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="flex items-center justify-between rounded-xl border border-blue-200 bg-blue-50 p-4">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 text-blue-700">
            🎯
          </span>
          <div>
            <p className="text-sm font-semibold text-blue-900">
              ¿Necesitás más detalle por inscripción?
            </p>
            <p className="text-xs text-blue-700">
              Ver conversaciones, timeline y follow-ups en Closer Studio.
            </p>
          </div>
        </div>
        <a href={closerHref}>
          <Button>Ir a Closer Studio →</Button>
        </a>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────

interface KpiProps {
  label: string;
  value: number | string;
  color?: "emerald" | "amber" | "purple";
}

function Kpi({ label, value, color }: KpiProps) {
  const colorClass =
    color === "emerald"
      ? "text-emerald-600"
      : color === "amber"
        ? "text-amber-600"
        : color === "purple"
          ? "text-purple-600"
          : "text-foreground";
  return (
    <div className="rounded-xl border bg-background p-4">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className={cn("text-2xl font-bold", colorClass)}>{value}</p>
    </div>
  );
}

function EnrollmentRow({ enrollment }: { enrollment: Enrollment }) {
  return (
    <tr className="hover:bg-muted/30">
      <td className="p-3">
        <div className="font-medium">Contacto {enrollment.contact_id.slice(0, 8)}</div>
        <div className="text-xs text-muted-foreground">{enrollment.source_channel ?? "—"}</div>
      </td>
      <td className="p-3">
        <span
          className={cn(
            "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold",
            STATUS_STYLES[enrollment.status],
          )}
        >
          {STATUS_LABELS[enrollment.status]}
        </span>
      </td>
      <td className="p-3 text-xs">{enrollment.pricing_tier_label ?? "—"}</td>
      <td className="p-3 font-semibold">
        {formatMoney(enrollment.pricing_amount, enrollment.currency)}
      </td>
      <td className="p-3 text-xs text-muted-foreground">
        {enrollment.paid_at ? new Date(enrollment.paid_at).toLocaleDateString("es-PE") : "—"}
      </td>
    </tr>
  );
}

function LoadingState() {
  return (
    <div className="rounded-xl border bg-background p-8 text-center text-sm text-muted-foreground">
      Cargando inscripciones…
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-destructive bg-destructive/5 p-6 text-center text-sm text-destructive">
      Error al cargar: {message}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="rounded-xl border bg-background p-10 text-center text-sm text-muted-foreground">
      <p className="font-medium">Sin inscripciones todavía para esta edición</p>
      <p className="mt-1 text-xs">Cuando un lead se inscriba aparecerá acá.</p>
    </div>
  );
}
