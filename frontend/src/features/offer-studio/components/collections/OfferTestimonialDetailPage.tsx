"use client";

export interface OfferTestimonialDetailPageProps {
  offerId: string;
  testimonialId: string;
}

/** Detail view for an offer testimonial. Stub until F7 mounts the form. */
export function OfferTestimonialDetailPage({
  offerId,
  testimonialId,
}: OfferTestimonialDetailPageProps) {
  return (
    <div className="p-6">
      <p className="mb-2 text-xs uppercase tracking-wider text-muted-foreground">Testimonio</p>
      <h1 className="text-xl font-semibold">Editar testimonio</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Oferta: <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">{offerId}</code>
      </p>
      <p className="mt-1 text-sm text-muted-foreground">
        Testimonio:{" "}
        <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">{testimonialId}</code>
      </p>
      <p className="mt-4 text-sm italic text-muted-foreground">
        El formulario real llega en F7 junto al endpoint de la API.
      </p>
    </div>
  );
}
