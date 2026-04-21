"use client";

export interface OfferFaqDetailPageProps {
  offerId: string;
  faqId: string;
}

/** Detail view for an offer FAQ item. Stub until F7 mounts the form. */
export function OfferFaqDetailPage({ offerId, faqId }: OfferFaqDetailPageProps) {
  return (
    <div className="p-6">
      <p className="mb-2 text-xs uppercase tracking-wider text-muted-foreground">FAQ</p>
      <h1 className="text-xl font-semibold">Editar pregunta</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Oferta: <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">{offerId}</code>
      </p>
      <p className="mt-1 text-sm text-muted-foreground">
        Pregunta: <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">{faqId}</code>
      </p>
      <p className="mt-4 text-sm italic text-muted-foreground">
        El editor de pregunta/respuesta llega en F7.
      </p>
    </div>
  );
}
