"use client";

import { MessageSquareQuote, Plus } from "lucide-react";

import { Button } from "@/components/ui/button";

import { useOfferTestimonials } from "../../hooks/use-offer-testimonials";

export interface OfferTestimonialsLandingPageProps {
  offerId: string;
}

/**
 * Collection landing — testimonials list for an offer.
 *
 * Mirrors brand-studio's ``TestimonialsLandingPage`` (InstancePicker + welcome
 * pane). Until F7 wires the real hook, renders the empty-state card so the
 * route compiles and tests can mount it.
 */
export function OfferTestimonialsLandingPage({ offerId }: OfferTestimonialsLandingPageProps) {
  const { testimonials, loading } = useOfferTestimonials(offerId);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
        Cargando testimonios…
      </div>
    );
  }

  if (testimonials.length === 0) {
    return (
      <div className="flex min-h-0 min-w-0 flex-1 items-center justify-center bg-card p-12 text-center">
        <div className="max-w-[420px]">
          <div className="mx-auto mb-5 flex h-12 w-12 items-center justify-center rounded-full bg-brand/15 text-brand">
            <MessageSquareQuote className="h-6 w-6" aria-hidden="true" />
          </div>
          <h1 className="mb-3 text-xl font-semibold text-foreground">
            Aún no hay testimonios en esta oferta
          </h1>
          <p className="text-sm leading-relaxed text-muted-foreground">
            Los testimonios se reutilizan automáticamente en la landing y en las respuestas del
            Sales Agent. Importa los que ya viven en Brand Vault o agrega uno nuevo.
          </p>
          <div className="mt-5 flex items-center justify-center gap-2">
            <Button size="sm">
              <Plus className="mr-1.5 h-4 w-4" />
              Crear testimonio
            </Button>
            <Button size="sm" variant="outline">
              Importar desde Brand Vault
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-3 p-6 sm:grid-cols-2 lg:grid-cols-3">
      {testimonials.map((t) => (
        <div
          key={t.id}
          className="rounded-lg border border-border bg-card p-4 text-sm text-muted-foreground"
        >
          <p className="mb-2 font-semibold text-foreground">{t.author_name}</p>
          <blockquote className="line-clamp-4 italic">{t.quote}</blockquote>
        </div>
      ))}
    </div>
  );
}
