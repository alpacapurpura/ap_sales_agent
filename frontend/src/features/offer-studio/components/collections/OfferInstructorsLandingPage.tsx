"use client";

import { Plus, Users } from "lucide-react";

import { Button } from "@/components/ui/button";

import { useOfferInstructors } from "../../hooks/use-offer-instructors";

export interface OfferInstructorsLandingPageProps {
  offerId: string;
}

/** Collection landing — instructors list for an offer (stub until F7). */
export function OfferInstructorsLandingPage({ offerId }: OfferInstructorsLandingPageProps) {
  const { instructors, loading } = useOfferInstructors(offerId);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
        Cargando instructores…
      </div>
    );
  }

  if (instructors.length === 0) {
    return (
      <div className="flex min-h-0 min-w-0 flex-1 items-center justify-center bg-card p-12 text-center">
        <div className="max-w-[420px]">
          <div className="mx-auto mb-5 flex h-12 w-12 items-center justify-center rounded-full bg-brand/15 text-brand">
            <Users className="h-6 w-6" aria-hidden="true" />
          </div>
          <h1 className="mb-3 text-xl font-semibold text-foreground">
            Agrega instructores a esta oferta
          </h1>
          <p className="text-sm leading-relaxed text-muted-foreground">
            Cada instructor aparece en la landing con bio, foto y redes. Puedes reutilizar a los
            miembros del equipo ya definidos en Brand Studio.
          </p>
          <div className="mt-5 flex items-center justify-center gap-2">
            <Button size="sm">
              <Plus className="mr-1.5 h-4 w-4" />
              Agregar instructor
            </Button>
            <Button size="sm" variant="outline">
              Reutilizar del equipo (Brand)
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-3 p-6 sm:grid-cols-2 lg:grid-cols-3">
      {instructors.map((i) => (
        <div
          key={i.id}
          className="rounded-lg border border-border bg-card p-4 text-sm text-muted-foreground"
        >
          <p className="mb-1 font-semibold text-foreground">{i.name}</p>
          <p className="line-clamp-3 text-xs">{i.role ?? "Instructor"}</p>
        </div>
      ))}
    </div>
  );
}
