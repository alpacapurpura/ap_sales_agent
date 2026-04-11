"use client";

import { Image as ImageIcon } from "lucide-react";

/**
 * Placeholder for the Assets tab. Real gallery, filters and CRUD land in
 * FE Chunk 4.
 */
export function AssetsView({ offerId }: { offerId: string }) {
  return (
    <div className="p-6" role="region" aria-label="Biblioteca de assets">
      <div className="rounded-lg border border-dashed p-12 text-center">
        <ImageIcon
          className="mx-auto h-12 w-12 text-muted-foreground"
          aria-hidden
        />
        <h3 className="mt-4 font-semibold">Biblioteca de assets</h3>
        <p className="mt-2 text-sm text-muted-foreground">
          Implementación completa en FE Chunk 4 (galería, filtros, CRUD).
        </p>
        <p className="mt-1 text-xs text-muted-foreground">Oferta: {offerId}</p>
      </div>
    </div>
  );
}
