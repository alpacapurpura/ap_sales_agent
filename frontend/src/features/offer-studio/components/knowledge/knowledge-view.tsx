"use client";

import { BookOpen } from "lucide-react";

/**
 * Placeholder for the Knowledge tab. Real ingestion, document list, processing
 * status and RAG preview land in FE Chunk 4.
 */
export function KnowledgeView({ offerId }: { offerId: string }) {
  return (
    <div className="p-6" role="region" aria-label="Base de conocimiento">
      <div className="rounded-lg border border-dashed p-12 text-center">
        <BookOpen
          className="mx-auto h-12 w-12 text-muted-foreground"
          aria-hidden
        />
        <h3 className="mt-4 font-semibold">Base de conocimiento</h3>
        <p className="mt-2 text-sm text-muted-foreground">
          Implementación completa en FE Chunk 4 (ingestión, documentos, estado
          de procesamiento).
        </p>
        <p className="mt-1 text-xs text-muted-foreground">Oferta: {offerId}</p>
      </div>
    </div>
  );
}
