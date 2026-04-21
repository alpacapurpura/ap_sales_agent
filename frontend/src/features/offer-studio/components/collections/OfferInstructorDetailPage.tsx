"use client";

export interface OfferInstructorDetailPageProps {
  offerId: string;
  instructorId: string;
}

/** Detail view for an offer instructor. Stub until F7 mounts the form. */
export function OfferInstructorDetailPage({
  offerId,
  instructorId,
}: OfferInstructorDetailPageProps) {
  return (
    <div className="p-6">
      <p className="mb-2 text-xs uppercase tracking-wider text-muted-foreground">Instructor</p>
      <h1 className="text-xl font-semibold">Editar instructor</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Oferta: <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">{offerId}</code>
      </p>
      <p className="mt-1 text-sm text-muted-foreground">
        Instructor:{" "}
        <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">{instructorId}</code>
      </p>
      <p className="mt-4 text-sm italic text-muted-foreground">
        En F7 este formulario reusará el picker de equipo de Brand Studio.
      </p>
    </div>
  );
}
