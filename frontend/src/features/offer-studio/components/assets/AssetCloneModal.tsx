"use client";

// AssetCloneModal — Phase 3 scaffold.
//
// Lets an editor pick assets from *other* editions of the same offer and
// promote them into the current edition. The component is a controlled
// picker: it surfaces the selected ids through ``onConfirm`` and leaves
// the side effect (re-bind / copy backend call) to the parent, so
// backends that want either MOVE or COPY semantics can wire the same
// modal. Phase 9 will replace this scaffold with the full UX (filters,
// "update dates" toggle, provenance badges) — the data contract stays.

import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import { useAssets } from "../../hooks/use-assets";

import type { AssetResponse } from "../../types/assets";

export interface AssetCloneModalProps {
  offerId: string;
  /** Current edition — assets in this edition are hidden from the picker. */
  currentEditionId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Called with the ids the user confirmed. Parent owns the backend call. */
  onConfirm: (assetIds: string[]) => Promise<void> | void;
}

/**
 * Modal that lets the user pick assets from other editions of the same
 * offer and pull them into the current edition. Controlled picker — the
 * caller owns the backend call via ``onConfirm(assetIds)``.
 */
export function AssetCloneModal({
  offerId,
  currentEditionId,
  open,
  onOpenChange,
  onConfirm,
}: AssetCloneModalProps) {
  const { data, isLoading } = useAssets(offerId);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [submitting, setSubmitting] = useState(false);

  // Show only assets that belong to a different edition — the ones worth
  // "pulling over". Offer-level (edition_id == null) assets are already
  // visible from every edition listing in the API, so duplicating them
  // adds nothing but confusion.
  const candidates: AssetResponse[] = useMemo(() => {
    if (!data?.items) return [];
    return data.items.filter(
      (asset) => asset.edition_id !== null && asset.edition_id !== currentEditionId,
    );
  }, [data, currentEditionId]);

  const toggle = (assetId: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(assetId)) {
        next.delete(assetId);
      } else {
        next.add(assetId);
      }
      return next;
    });
  };

  const handleConfirm = async () => {
    if (selected.size === 0) return;
    setSubmitting(true);
    try {
      await onConfirm(Array.from(selected));
      setSelected(new Set());
      onOpenChange(false);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Jalar recursos de otra edición</DialogTitle>
          <DialogDescription>
            Selecciona flyers, videos o documentos de ediciones anteriores para incluirlos en esta
            edición.
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <p className="text-sm text-muted-foreground">Cargando recursos…</p>
        ) : candidates.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Todavía no hay recursos en otras ediciones para traer.
          </p>
        ) : (
          <ul className="max-h-72 space-y-2 overflow-y-auto">
            {candidates.map((asset) => (
              <li key={asset.id}>
                <label className="flex cursor-pointer items-center gap-3 rounded-md border p-3 hover:bg-accent">
                  <input
                    type="checkbox"
                    checked={selected.has(asset.id)}
                    onChange={() => toggle(asset.id)}
                  />
                  <span className="flex flex-col">
                    <span className="text-sm font-medium">{asset.name}</span>
                    <span className="text-xs text-muted-foreground">
                      {asset.type} · {asset.source}
                    </span>
                  </span>
                </label>
              </li>
            ))}
          </ul>
        )}

        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)} disabled={submitting}>
            Cancelar
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={selected.size === 0 || submitting}
            data-testid="asset-clone-confirm"
          >
            {submitting ? "Copiando…" : `Copiar ${selected.size || ""}`.trim()}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
