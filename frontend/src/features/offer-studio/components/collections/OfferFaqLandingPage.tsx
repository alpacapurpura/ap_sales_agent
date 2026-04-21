"use client";

import { HelpCircle, Plus } from "lucide-react";

import { Button } from "@/components/ui/button";

import { useOfferFaq } from "../../hooks/use-offer-faq";

export interface OfferFaqLandingPageProps {
  offerId: string;
}

/** Collection landing — FAQ list for an offer (stub until F7). */
export function OfferFaqLandingPage({ offerId }: OfferFaqLandingPageProps) {
  const { faqItems: items, loading } = useOfferFaq(offerId);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
        Cargando preguntas…
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="flex min-h-0 min-w-0 flex-1 items-center justify-center bg-card p-12 text-center">
        <div className="max-w-[420px]">
          <div className="mx-auto mb-5 flex h-12 w-12 items-center justify-center rounded-full bg-brand/15 text-brand">
            <HelpCircle className="h-6 w-6" aria-hidden="true" />
          </div>
          <h1 className="mb-3 text-xl font-semibold text-foreground">
            Aún no configuraste preguntas frecuentes
          </h1>
          <p className="text-sm leading-relaxed text-muted-foreground">
            El copiloto puede generarlas a partir de los flags del preset y de las objeciones
            detectadas por el Sales Agent en conversaciones reales.
          </p>
          <div className="mt-5 flex items-center justify-center gap-2">
            <Button size="sm">
              <Plus className="mr-1.5 h-4 w-4" />
              Agregar pregunta
            </Button>
            <Button size="sm" variant="outline">
              Generar desde preset
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3 p-6">
      {items.map((q) => (
        <details
          key={q.id}
          className="rounded-lg border border-border bg-card p-4 text-sm text-foreground"
        >
          <summary className="cursor-pointer font-medium">{q.question}</summary>
          <p className="mt-2 text-muted-foreground">{q.answer}</p>
        </details>
      ))}
    </div>
  );
}
