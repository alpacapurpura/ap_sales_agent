import { ContactsPageClient } from "@/features/crm-hub/components/ContactsPageClient";
import { parseFiltersFromSearchParams, clampInt } from "@/features/crm-hub/utils/url-state";

import type { ContactFilterParams } from "@/features/crm-hub/types";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Contactos — Nicolify",
  description: "Tu base completa de contactos. Filtra, busca y selecciona.",
};

interface PageProps {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

/**
 * Página Server Component (thin) — hidrata filtros iniciales desde URL
 * y pasa a ContactsPageClient.
 *
 * No contiene lógica de negocio ni estado.
 */
export default async function SalesContactosPage({ searchParams }: PageProps) {
  const params = await searchParams;
  const initialFilters: ContactFilterParams = parseFiltersFromSearchParams(params);
  const initialLimit = clampInt(params.limit, 1, 100, 50);
  const initialOffset = clampInt(params.offset, 0, Number.MAX_SAFE_INTEGER, 0);

  return (
    <div className="flex flex-col h-full">
      <header className="px-6 py-4 border-b shrink-0">
        <h1 className="text-2xl font-bold">Contactos</h1>
        <p className="text-sm text-muted-foreground">
          Tu base completa. Filtra, busca y selecciona para crear segmentos o lanzar campañas.
        </p>
      </header>
      <ContactsPageClient
        initialFilters={initialFilters}
        initialLimit={initialLimit}
        initialOffset={initialOffset}
      />
    </div>
  );
}
