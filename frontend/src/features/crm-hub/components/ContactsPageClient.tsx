"use client";

import { MessageCircle, Mail, Phone } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import * as React from "react";
import { toast } from "sonner";

import { DataTable } from "@/components/shared/data-table/DataTable";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";

import { useContactDetailQuery } from "../api/use-contact-detail-query";
import { useContactsQuery } from "../api/use-contacts-query";
import { filtersToSearchParams } from "../utils/url-state";

import { ContactDetailContent } from "./ContactDetailContent";
import { ContactFiltersPanel } from "./ContactFiltersPanel";
import { CreateSegmentDialog } from "./CreateSegmentDialog";
import { LaunchCampaignChoiceDialog } from "./LaunchCampaignChoiceDialog";
import { LifecycleStageChip } from "./LifecycleStageChip";
import { ScoreBadge } from "./ScoreBadge";
import { SelectedContactsBar } from "./SelectedContactsBar";

import type { ContactFilterParams, ContactListItem, SelectedContactsBarAction } from "../types";
import type { ColumnDef } from "@tanstack/react-table";

interface ContactsPageClientProps {
  initialFilters: ContactFilterParams;
  initialLimit: number;
  initialOffset: number;
}

function formatRelative(isoString: string | null): string {
  if (!isoString) return "—";
  try {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    if (diffDays === 0) return "hoy";
    if (diffDays === 1) return "hace 1 día";
    if (diffDays < 30) return `hace ${diffDays} días`;
    if (diffDays < 365) return `hace ${Math.floor(diffDays / 30)} mes`;
    return `hace ${Math.floor(diffDays / 365)} año`;
  } catch {
    return isoString;
  }
}

function buildColumns(
  onSelectRow: (id: string, checked: boolean) => void,
  selectedIds: string[],
  onRowClick: (row: ContactListItem) => void,
): ColumnDef<ContactListItem>[] {
  return [
    {
      id: "select",
      header: () => null,
      cell: ({ row }) => (
        <Checkbox
          checked={selectedIds.includes(row.original.id)}
          onCheckedChange={(v) => {
            onSelectRow(row.original.id, v === true);
          }}
          onClick={(e) => e.stopPropagation()}
          aria-label={`Seleccionar ${row.original.full_name ?? row.original.primary_email ?? "contacto"}`}
        />
      ),
      enableSorting: false,
      size: 40,
    },
    {
      accessorKey: "full_name",
      header: "Nombre",
      cell: ({ row }) => (
        <button
          type="button"
          className="text-left hover:underline focus:outline-none focus-visible:underline"
          onClick={() => onRowClick(row.original)}
        >
          {row.original.full_name ?? (
            <span className="text-muted-foreground italic">Sin nombre</span>
          )}
        </button>
      ),
    },
    {
      accessorKey: "primary_email",
      header: "Email",
      cell: ({ row }) => <span className="text-sm">{row.original.primary_email ?? "—"}</span>,
    },
    {
      accessorKey: "primary_phone",
      header: "Teléfono",
      cell: ({ row }) => <span className="text-sm">{row.original.primary_phone ?? "—"}</span>,
    },
    {
      accessorKey: "lifecycle_stage",
      header: "Etapa",
      cell: ({ row }) => <LifecycleStageChip stage={row.original.lifecycle_stage} />,
    },
    {
      accessorKey: "lead_score",
      header: "Score",
      cell: ({ row }) => <ScoreBadge score={Math.round(row.original.lead_score)} />,
    },
    {
      accessorKey: "last_activity_at",
      header: "Última actividad",
      cell: ({ row }) => (
        <span className="text-sm text-muted-foreground">
          {formatRelative(row.original.last_activity_at)}
        </span>
      ),
    },
    {
      id: "channels",
      header: "Canales",
      cell: ({ row }) => (
        <div className="flex items-center gap-1">
          {row.original.has_telegram_id && (
            <MessageCircle className="h-3.5 w-3.5 text-muted-foreground" aria-label="Telegram" />
          )}
          {row.original.has_email && (
            <Mail className="h-3.5 w-3.5 text-muted-foreground" aria-label="Email" />
          )}
          {row.original.has_phone && (
            <Phone className="h-3.5 w-3.5 text-muted-foreground" aria-label="Teléfono" />
          )}
        </div>
      ),
      enableSorting: false,
    },
  ];
}

/**
 * Componente cliente de la página de contactos.
 * Gestiona: filtros URL, paginación URL, selección local, drawer detalle.
 * PR-12: inyecta "Crear segmento" en SelectedContactsBar + wire dialogs.
 * URL state via useRouter + useSearchParams (deep-link friendly).
 */
export function ContactsPageClient({
  initialFilters,
  initialLimit,
  initialOffset,
}: ContactsPageClientProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  // -- State --
  const [filters, setFilters] = React.useState<ContactFilterParams>(initialFilters);
  const [limit] = React.useState(initialLimit);
  const [offset, setOffset] = React.useState(initialOffset);
  const [selectedIds, setSelectedIds] = React.useState<string[]>([]);
  const [selectedContactId, setSelectedContactId] = React.useState<string | null>(
    searchParams.get("contact"),
  );
  const [searchValue, setSearchValue] = React.useState(initialFilters.q ?? "");

  // PR-12: segment creation + campaign choice dialog state
  const [createSegmentOpen, setCreateSegmentOpen] = React.useState(false);
  const [launchChoiceOpen, setLaunchChoiceOpen] = React.useState(false);
  const [createdSegmentId, setCreatedSegmentId] = React.useState<string | null>(null);
  const [createdSegmentName, setCreatedSegmentName] = React.useState<string>("");

  // -- Debounced URL sync --
  React.useEffect(() => {
    const t = setTimeout(() => {
      const sp = filtersToSearchParams(filters, { limit, offset });
      if (selectedContactId) sp.set("contact", selectedContactId);
      router.replace(`?${sp.toString()}`, { scroll: false });
    }, 300);
    return () => clearTimeout(t);
  }, [filters, limit, offset, selectedContactId, router]);

  // -- Handlers --
  function handleFiltersChange(next: ContactFilterParams) {
    setFilters(next);
    setOffset(0); // reset to page 1 on filter change
  }

  function handleSearchChange(e: React.ChangeEvent<HTMLInputElement>) {
    const q = e.target.value;
    setSearchValue(q);
    handleFiltersChange({ ...filters, q: q || undefined });
  }

  function handleRowClick(row: ContactListItem) {
    setSelectedContactId(row.id);
  }

  function handleSelectRow(id: string, checked: boolean) {
    setSelectedIds((prev) => (checked ? [...prev, id] : prev.filter((x) => x !== id)));
  }

  function handleSelectionChange(ids: string[]) {
    setSelectedIds(ids);
  }

  function handlePageChange(newOffset: number) {
    setOffset(Math.max(0, newOffset));
  }

  // PR-12: callback invoked after segment successfully created (name passed from dialog form)
  const handleSegmentCreated = React.useCallback((segmentId: string, segmentName: string) => {
    setCreatedSegmentId(segmentId);
    setCreatedSegmentName(segmentName);
    setLaunchChoiceOpen(true);
  }, []);

  // PR-12: slot action injected into SelectedContactsBar
  const barActions = React.useMemo<SelectedContactsBarAction[]>(
    () => [
      {
        id: "create-segment",
        label: "Crear segmento",
        variant: "default",
        requiresSelection: true,
        onClick: () => {
          setCreateSegmentOpen(true);
        },
      },
    ],
    [],
  );

  // -- Data --
  const { data, isLoading, isError } = useContactsQuery({ filters, limit, offset });
  const { data: contactDetail, isLoading: isDetailLoading } =
    useContactDetailQuery(selectedContactId);

  React.useEffect(() => {
    if (isError) {
      toast.error("No pudimos cargar contactos. Reintenta.");
    }
  }, [isError]);

  // -- Columns (memoized for stability) --
  const columns = React.useMemo(
    () => buildColumns(handleSelectRow, selectedIds, handleRowClick),

    [selectedIds],
  );

  const items = data?.items ?? [];
  const totalCount = data?.total_count ?? 0;

  const emptyMessage = Object.values(filters).some((v) => v !== undefined && v !== null)
    ? "Ningún contacto coincide. Ajusta filtros o limpia la búsqueda."
    : "Aún no tienes contactos. Conecta canales o importa una lista.";

  // -- Render --
  const filtersPanel = (
    <ContactFiltersPanel filters={filters} onChange={handleFiltersChange} className="h-full" />
  );

  const tablePanel = (
    <div className="flex flex-col gap-3 flex-1 min-w-0">
      {/* Search */}
      <div className="px-4 pt-4">
        <Input
          value={searchValue}
          onChange={handleSearchChange}
          placeholder="Buscar nombre, email o teléfono…"
          aria-label="Buscar contactos"
          className="w-full"
        />
      </div>

      {/* Table */}
      <div className="flex-1 px-4 pb-4">
        <DataTable
          data={items}
          columns={columns}
          totalCount={totalCount}
          limit={limit}
          offset={offset}
          onPageChange={handlePageChange}
          onRowClick={handleRowClick}
          selectedIds={selectedIds}
          onSelectionChange={handleSelectionChange}
          getRowId={(row) => row.id}
          isLoading={isLoading}
          emptyMessage={emptyMessage}
        />
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop: sidebar + table (≥1024px) */}
      <div className="hidden lg:flex flex-1 min-h-0 overflow-hidden">
        <aside className="w-60 xl:w-72 shrink-0 border-r overflow-hidden" aria-label="Filtros">
          {filtersPanel}
        </aside>
        {tablePanel}
      </div>

      {/* Mobile / md: tabs */}
      <div className="flex lg:hidden flex-1 min-h-0 overflow-hidden">
        <Tabs defaultValue="tabla" className="flex flex-col flex-1 min-h-0">
          <div className="px-4 pt-2 border-b">
            <TabsList className="w-full">
              <TabsTrigger value="filtros" className="flex-1">
                Filtros
              </TabsTrigger>
              <TabsTrigger value="tabla" className="flex-1">
                Tabla
              </TabsTrigger>
            </TabsList>
          </div>
          <TabsContent value="filtros" className="flex-1 overflow-auto mt-0">
            {filtersPanel}
          </TabsContent>
          <TabsContent value="tabla" className="flex-1 overflow-hidden mt-0">
            {tablePanel}
          </TabsContent>
        </Tabs>
      </div>

      {/* Drawer — contact detail */}
      <Sheet
        open={!!selectedContactId}
        onOpenChange={(open) => {
          if (!open) setSelectedContactId(null);
        }}
      >
        <SheetContent
          side="right"
          className="w-full sm:w-[480px] overflow-y-auto"
          aria-labelledby="contact-detail-title"
          role="dialog"
        >
          <SheetHeader className="pb-4">
            <SheetTitle id="contact-detail-title" className="sr-only">
              Detalle de contacto
            </SheetTitle>
          </SheetHeader>
          <ContactDetailContent
            detail={contactDetail ?? null}
            isLoading={isDetailLoading}
            className="pb-8"
          />
        </SheetContent>
      </Sheet>

      {/* SelectedContactsBar — PR-12 injects "Crear segmento" action */}
      <SelectedContactsBar
        selectedIds={selectedIds}
        actions={barActions}
        onClearSelection={() => setSelectedIds([])}
      />

      {/* PR-12: CreateSegmentDialog */}
      <CreateSegmentDialog
        open={createSegmentOpen}
        onOpenChange={setCreateSegmentOpen}
        selectedLeadIds={selectedIds}
        onSuccess={handleSegmentCreated}
      />

      {/* PR-12: LaunchCampaignChoiceDialog (shown after segment created) */}
      {createdSegmentId !== null && (
        <LaunchCampaignChoiceDialog
          open={launchChoiceOpen}
          onOpenChange={setLaunchChoiceOpen}
          segmentId={createdSegmentId}
          segmentName={createdSegmentName}
        />
      )}
    </>
  );
}
