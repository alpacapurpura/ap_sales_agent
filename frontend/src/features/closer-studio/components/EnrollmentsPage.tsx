"use client";

import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

import { useEnrollments } from "../hooks/use-enrollments";
import { EnrollmentStatus } from "../types/enrollment";

import type { Enrollment, EnrollmentFilters } from "../types/enrollment";

const STATUS_BADGES: Record<EnrollmentStatus, { label: string; className: string }> = {
  [EnrollmentStatus.INTENT]: { label: "💭 Intención", className: "bg-muted text-muted-foreground" },
  [EnrollmentStatus.WAITLIST]: { label: "📋 Waitlist", className: "bg-purple-100 text-purple-700" },
  [EnrollmentStatus.PAYMENT_PENDING]: {
    label: "⏳ Pendiente",
    className: "bg-amber-100 text-amber-700",
  },
  [EnrollmentStatus.PAID]: { label: "✓ Pagada", className: "bg-emerald-100 text-emerald-700" },
  [EnrollmentStatus.ATTENDED]: { label: "🎓 Asistió", className: "bg-blue-100 text-blue-700" },
  [EnrollmentStatus.REFUNDED]: { label: "↩ Reembolsada", className: "bg-red-100 text-red-700" },
  [EnrollmentStatus.CANCELLED]: {
    label: "✕ Cancelada",
    className: "bg-muted text-muted-foreground",
  },
};

function formatMoney(amount: number | null, currency: string | null): string {
  if (amount == null) return "—";
  return new Intl.NumberFormat("es-PE", {
    style: "currency",
    currency: currency ?? "USD",
    maximumFractionDigits: 0,
  }).format(amount);
}

interface Group {
  key: string;
  label: string;
  isWaitlist: boolean;
  items: Enrollment[];
}

function ensureBucket(
  buckets: Map<string, Group>,
  key: string,
  group: Omit<Group, "items">,
): Group {
  let existing = buckets.get(key);
  if (!existing) {
    existing = { ...group, items: [] };
    buckets.set(key, existing);
  }
  return existing;
}

function groupEnrollments(items: Enrollment[]): Group[] {
  const buckets = new Map<string, Group>();
  for (const item of items) {
    if (item.status === EnrollmentStatus.WAITLIST) {
      const key = `waitlist:${item.offer_id}`;
      ensureBucket(buckets, key, {
        key,
        label: "En lista de espera",
        isWaitlist: true,
      }).items.push(item);
      continue;
    }
    const editionKey = item.edition_id ?? "no-edition";
    const key = `${item.offer_id}:${editionKey}`;
    const editionLabel = editionKey === "no-edition" ? "—" : editionKey.slice(0, 8);
    ensureBucket(buckets, key, {
      key,
      label: `Oferta ${item.offer_id.slice(0, 8)} · Edición ${editionLabel}`,
      isWaitlist: false,
    }).items.push(item);
  }
  return Array.from(buckets.values());
}

/**
 *
 */
export function EnrollmentsPage() {
  const [statusFilter, setStatusFilter] = useState<EnrollmentStatus | undefined>(undefined);
  const [search, setSearch] = useState<string>("");

  const filters: EnrollmentFilters = useMemo(
    () => (statusFilter ? { status: statusFilter } : {}),
    [statusFilter],
  );

  const { data, isLoading, error } = useEnrollments(filters);
  const items = useMemo(() => data?.items ?? [], [data]);
  const total = data?.total ?? 0;

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return items;
    return items.filter(
      (e) =>
        e.contact_id.toLowerCase().includes(term) ||
        (e.pricing_tier_label ?? "").toLowerCase().includes(term),
    );
  }, [items, search]);

  const groups = useMemo(() => groupEnrollments(filtered), [filtered]);

  // KPIs
  const paid = items.filter((e) => e.status === EnrollmentStatus.PAID).length;
  const pending = items.filter((e) => e.status === EnrollmentStatus.PAYMENT_PENDING).length;
  const waitlist = items.filter((e) => e.status === EnrollmentStatus.WAITLIST).length;
  const revenue = items
    .filter((e) => e.status === EnrollmentStatus.PAID)
    .reduce((acc, e) => acc + (e.pricing_amount ?? 0), 0);

  return (
    <div className="flex flex-col">
      <header className="border-b bg-background px-8 py-5">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold">Inscripciones</h1>
            <p className="mt-0.5 text-sm text-muted-foreground">
              Todos los leads inscriptos en cualquier oferta o cohorte.
            </p>
          </div>
        </div>
      </header>

      <section className="space-y-5 px-8 py-5">
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <Kpi label="Total" value={total} />
          <Kpi label="Pagadas" value={paid} color="emerald" />
          <Kpi label="Pendientes" value={pending} color="amber" />
          <Kpi label="Waitlist" value={waitlist} color="purple" />
        </div>

        <div className="flex flex-wrap items-center gap-2 rounded-xl border bg-background p-3 text-xs">
          <span className="text-muted-foreground">Estado:</span>
          <FilterPill
            active={statusFilter === undefined}
            onClick={() => setStatusFilter(undefined)}
          >
            Todas
          </FilterPill>
          <FilterPill
            active={statusFilter === EnrollmentStatus.PAID}
            onClick={() => setStatusFilter(EnrollmentStatus.PAID)}
          >
            Pagadas
          </FilterPill>
          <FilterPill
            active={statusFilter === EnrollmentStatus.PAYMENT_PENDING}
            onClick={() => setStatusFilter(EnrollmentStatus.PAYMENT_PENDING)}
          >
            Pendientes
          </FilterPill>
          <FilterPill
            active={statusFilter === EnrollmentStatus.WAITLIST}
            onClick={() => setStatusFilter(EnrollmentStatus.WAITLIST)}
          >
            Waitlist
          </FilterPill>
          <div className="ml-auto w-48">
            <Input
              placeholder="Buscar…"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>
        </div>

        {isLoading ? <LoadingState /> : null}
        {error ? <ErrorState message={error.message} /> : null}
        {!isLoading && !error && groups.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="overflow-hidden rounded-xl border bg-background">
            {groups.map((group) => (
              <GroupSection key={group.key} group={group} revenue={revenue} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

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

interface FilterPillProps {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}

function FilterPill({ active, onClick, children }: FilterPillProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-full px-2.5 py-1 text-xs transition-colors",
        active ? "bg-foreground text-background" : "text-muted-foreground hover:bg-muted",
      )}
    >
      {children}
    </button>
  );
}

interface GroupSectionProps {
  group: Group;
  revenue: number;
}

function GroupSection({ group }: GroupSectionProps) {
  return (
    <div>
      <div
        className={cn(
          "flex items-center justify-between border-b px-4 py-2",
          group.isWaitlist ? "bg-purple-50" : "bg-muted/40",
        )}
      >
        <span className={cn("text-sm font-semibold", group.isWaitlist && "text-purple-900")}>
          {group.label}{" "}
          <span
            className={cn(
              "ml-1 font-normal",
              group.isWaitlist ? "text-purple-600" : "text-muted-foreground",
            )}
          >
            ({group.items.length})
          </span>
        </span>
      </div>
      <table className="w-full text-sm">
        <tbody className="divide-y">
          {group.items.map((enrollment) => (
            <EnrollmentRow key={enrollment.id} enrollment={enrollment} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function EnrollmentRow({ enrollment }: { enrollment: Enrollment }) {
  const badge = STATUS_BADGES[enrollment.status];
  return (
    <tr className="hover:bg-muted/30">
      <td className="p-3">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-muted text-xs font-semibold text-muted-foreground">
            {enrollment.contact_id.slice(0, 2).toUpperCase()}
          </div>
          <div>
            <div className="font-medium">Contacto {enrollment.contact_id.slice(0, 8)}</div>
            <div className="text-xs text-muted-foreground">{enrollment.source_channel ?? "—"}</div>
          </div>
        </div>
      </td>
      <td className="p-3">
        <Badge variant="secondary" className={cn("text-xs", badge.className)}>
          {badge.label}
        </Badge>
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
    <div className="rounded-xl border bg-background p-6 text-center text-sm text-muted-foreground">
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
      <p className="font-medium">No hay inscripciones todavía</p>
      <p className="mt-1 text-xs">Cuando un lead se inscriba en una oferta aparecerá acá.</p>
      <Button variant="outline" size="sm" className="mt-4">
        + Crear manual
      </Button>
    </div>
  );
}
