"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useAuthorityItems } from "@/features/brand-studio/hooks/use-authority-items";
import { useSocialProofForSurface } from "@/features/brand-studio/hooks/use-social-proof-for-surface";
import { useTeamMembers } from "@/features/brand-studio/hooks/use-team-members";
import { useTestimonials } from "@/features/brand-studio/hooks/use-testimonials";
import { placementApi, type SourceTable } from "@/lib/api/placement";

export interface AddFromBrandVaultModalProps {
  open: boolean;
  onClose: () => void;
  offerId: string;
}

interface VaultRow {
  id: string;
  source_table: SourceTable;
  primary: string;
  secondary: string;
}

/**
 * Modal that lists every tenant-scoped social-proof item NOT yet placed on
 * the current offer, and lets the user link selected rows to this offer
 * surface in one batch. Each successful placement POST emits a
 * ``PlacementAdded`` domain event on the backend.
 */
export function AddFromBrandVaultModal({ open, onClose, offerId }: AddFromBrandVaultModalProps) {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  const { testimonials } = useTestimonials();
  const { authorityItems } = useAuthorityItems();
  const { teamMembers } = useTeamMembers();
  const { data: resolved } = useSocialProofForSurface({
    surfaceType: "offer",
    surfaceRefId: offerId,
    enabled: open,
  });

  const [selected, setSelected] = useState<Set<string>>(new Set());

  const currentIds = useMemo(() => {
    const s = new Set<string>();
    resolved?.testimonials.forEach((p) => s.add(`testimonial:${p.testimonial.id}`));
    resolved?.authority_items.forEach((p) => s.add(`authority_item:${p.authority_item.id}`));
    resolved?.team_members.forEach((p) => s.add(`team_member:${p.team_member.id}`));
    return s;
  }, [resolved]);

  const rows = useMemo<VaultRow[]>(() => {
    const allRows: VaultRow[] = [
      ...testimonials.map((t) => ({
        id: t.id,
        source_table: "testimonial" as SourceTable,
        primary: t.author_name,
        secondary: t.author_role || (t.content?.slice(0, 60) ?? ""),
      })),
      ...authorityItems.map((a) => ({
        id: a.id,
        source_table: "authority_item" as SourceTable,
        primary: a.entity_name,
        secondary: a.authority_type,
      })),
      ...teamMembers.map((m) => ({
        id: m.id,
        source_table: "team_member" as SourceTable,
        primary: m.name,
        secondary: m.role ?? "",
      })),
    ];
    return allRows.filter((r) => !currentIds.has(`${r.source_table}:${r.id}`));
  }, [testimonials, authorityItems, teamMembers, currentIds]);

  const linkMutation = useMutation({
    mutationFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No auth token");
      const picks = rows.filter((r) => selected.has(`${r.source_table}:${r.id}`));
      await Promise.all(
        picks.map((r) =>
          placementApi.create(token, {
            source_table: r.source_table,
            source_id: r.id,
            surface_type: "offer",
            surface_ref_id: offerId,
          }),
        ),
      );
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["social_proof_for_surface"] });
      setSelected(new Set());
      onClose();
    },
  });

  const toggle = (key: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  return (
    <Dialog open={open} onOpenChange={(v) => (v ? undefined : onClose())}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Agregar desde la marca</DialogTitle>
          <DialogDescription>
            Selecciona testimonios, autoridad o miembros del equipo del catálogo de la marca para
            vincularlos a esta oferta. Los cambios se reflejan en landings y en el Sales Agent.
          </DialogDescription>
        </DialogHeader>

        {rows.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">
            Todo el catálogo de la marca ya está vinculado a esta oferta.
          </p>
        ) : (
          <ul className="max-h-[420px] space-y-2 overflow-y-auto">
            {rows.map((r) => {
              const key = `${r.source_table}:${r.id}`;
              return (
                <li
                  key={key}
                  className="flex items-start gap-3 rounded-md border border-border bg-card p-3"
                >
                  <Checkbox
                    checked={selected.has(key)}
                    onCheckedChange={() => toggle(key)}
                    aria-label={`Seleccionar ${r.primary}`}
                  />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-foreground">{r.primary}</p>
                    {r.secondary ? (
                      <p className="truncate text-xs text-muted-foreground">{r.secondary}</p>
                    ) : null}
                    <p className="mt-1 text-[11px] uppercase tracking-wide text-muted-foreground">
                      {r.source_table.replace("_", " ")}
                    </p>
                  </div>
                </li>
              );
            })}
          </ul>
        )}

        <DialogFooter>
          <Button variant="ghost" onClick={onClose}>
            Cancelar
          </Button>
          <Button
            onClick={() => linkMutation.mutate()}
            disabled={selected.size === 0 || linkMutation.isPending}
          >
            {linkMutation.isPending ? "Vinculando…" : `Vincular ${selected.size || ""}`.trim()}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
