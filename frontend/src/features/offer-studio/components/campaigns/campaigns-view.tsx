"use client";

import { Megaphone } from "lucide-react";

/**
 * Placeholder for the Campaigns tab. Real campaign list, filters and linking
 * land in FE Chunk 4.
 */
export function CampaignsView({ offerId }: { offerId: string }) {
  return (
    <div className="p-6" role="region" aria-label="Campañas de la oferta">
      <div className="rounded-lg border border-dashed p-12 text-center">
        <Megaphone
          className="mx-auto h-12 w-12 text-muted-foreground"
          aria-hidden
        />
        <h3 className="mt-4 font-semibold">Campañas</h3>
        <p className="mt-2 text-sm text-muted-foreground">
          Implementación completa en FE Chunk 4 (listado, filtros, asociación
          con la oferta).
        </p>
        <p className="mt-1 text-xs text-muted-foreground">Oferta: {offerId}</p>
      </div>
    </div>
  );
}
