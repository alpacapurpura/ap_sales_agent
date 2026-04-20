"use client";

import { MessageSquareQuote, Award, Users } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useSocialProofForSurface } from "@/features/brand-studio/hooks/use-social-proof-for-surface";

import { AddFromBrandVaultModal } from "./AddFromBrandVaultModal";

export interface OfferSocialProofPickerProps {
  offerId: string;
  /**
   * When true, the list also surfaces every brand-homepage placement the
   * tenant has so the offer page falls back gracefully when no item is
   * pinned explicitly. Matches the backend resolver's ``include_brand`` flag.
   */
  includeBrand?: boolean;
}

/**
 * Placement-aware social-proof manager for a single offer. Queries
 * ``/api/v1/social-proof/placements/for-surface?surface_type=offer`` and
 * renders the testimonials / authority items / team members currently
 * visible on this offer. Exposes a CTA that opens ``AddFromBrandVaultModal``
 * so the user can link (or clone) items from the brand vault.
 */
export function OfferSocialProofPicker({ offerId, includeBrand = false }: OfferSocialProofPickerProps) {
  const { data, isLoading } = useSocialProofForSurface({
    surfaceType: "offer",
    surfaceRefId: offerId,
    includeBrand,
  });
  const [modalOpen, setModalOpen] = useState(false);

  const testimonials = data?.testimonials ?? [];
  const authority = data?.authority_items ?? [];
  const team = data?.team_members ?? [];
  const totalCount = testimonials.length + authority.length + team.length;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-4">
        <div>
          <CardTitle>Prueba social</CardTitle>
          <p className="text-sm text-muted-foreground">
            {totalCount === 0
              ? "Sin testimonios, autoridad ni equipo vinculados todavía."
              : `${totalCount} elemento${totalCount === 1 ? "" : "s"} vinculado${totalCount === 1 ? "" : "s"}${includeBrand ? " (incluyendo nivel marca)" : ""}`}
          </p>
        </div>
        <Button size="sm" onClick={() => setModalOpen(true)}>
          Agregar desde la marca
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Cargando…</p>
        ) : (
          <div className="grid gap-6 md:grid-cols-3">
            <Column
              icon={<MessageSquareQuote className="h-4 w-4" aria-hidden />}
              title="Testimonios"
              items={testimonials.map((p) => ({
                id: p.testimonial.id,
                primary: p.testimonial.author_name,
                secondary: p.testimonial.author_role ?? p.testimonial.content?.slice(0, 80) ?? "",
              }))}
            />
            <Column
              icon={<Award className="h-4 w-4" aria-hidden />}
              title="Autoridad"
              items={authority.map((p) => ({
                id: p.authority_item.id,
                primary: p.authority_item.entity_name,
                secondary: p.authority_item.authority_type,
              }))}
            />
            <Column
              icon={<Users className="h-4 w-4" aria-hidden />}
              title="Equipo"
              items={team.map((p) => ({
                id: p.team_member.id,
                primary: p.team_member.name,
                secondary: p.team_member.role ?? "",
              }))}
            />
          </div>
        )}
      </CardContent>
      <AddFromBrandVaultModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        offerId={offerId}
      />
    </Card>
  );
}

interface ColumnItem {
  id: string;
  primary: string;
  secondary: string;
}

function Column({
  icon,
  title,
  items,
}: {
  icon: React.ReactNode;
  title: string;
  items: ColumnItem[];
}) {
  return (
    <div>
      <div className="mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
        {icon}
        <span>
          {title} ({items.length})
        </span>
      </div>
      {items.length === 0 ? (
        <p className="text-xs text-muted-foreground">Ninguno</p>
      ) : (
        <ul className="space-y-2">
          {items.map((item) => (
            <li key={item.id} className="rounded-md border border-border bg-card p-2">
              <p className="text-sm font-medium text-foreground">{item.primary}</p>
              {item.secondary ? (
                <p className="text-xs text-muted-foreground">{item.secondary}</p>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
